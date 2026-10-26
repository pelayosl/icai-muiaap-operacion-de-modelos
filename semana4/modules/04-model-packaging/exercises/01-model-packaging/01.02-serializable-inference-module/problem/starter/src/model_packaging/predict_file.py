"""Punto de extensión del CLI de inferencia sobre un bundle."""

from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from pathlib import Path

from model_packaging.artifact import (
    DEFAULT_BUNDLE_PATH,
    infer_wine_quality,
    load_model_bundle,
)
from model_packaging.contracts import WineQualityRequest

OUTPUT_FIELDS = (
    "sample_id",
    "quality_band",
    "confidence",
    "model_version",
    "preprocessing_version",
)


def predict_file(
    input_path: Path,
    output_path: Path,
    bundle_path: Path,
) -> int:
    """Valida todas las filas y escribe el CSV solo al final."""

    bundle = load_model_bundle(bundle_path)

    with input_path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"El CSV {input_path} no contiene filas")

    # Validar todas las filas antes de inferir nada.
    requests = []
    for index, row in enumerate(rows):
        sample_id = (row.pop("sample_id", None) or "").strip()
        try:
            if not sample_id:
                raise ValueError("sample_id no puede estar vacío")
            requests.append((sample_id, WineQualityRequest.model_validate(row)))
        except ValueError as error:
            raise ValueError(
                f"Error en la fila {index} ({sample_id}): {error}"
            ) from error

    # Acumular las predicciones en memoria.
    predictions = [
        {"sample_id": sample_id, **infer_wine_quality(bundle, request).model_dump()}
        for sample_id, request in requests
    ]

    # Escribir en un temporal y renombrar, para no dejar nunca un CSV parcial.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=output_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(predictions)
        os.replace(tmp_name, output_path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise

    return len(predictions)


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE_PATH, type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        count = predict_file(
            input_path=arguments.input,
            output_path=arguments.output,
            bundle_path=arguments.bundle,
        )
    except Exception as error:
        print(error, file=sys.stderr)
        return 2
    print(f"{count} predicciones escritas en {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
