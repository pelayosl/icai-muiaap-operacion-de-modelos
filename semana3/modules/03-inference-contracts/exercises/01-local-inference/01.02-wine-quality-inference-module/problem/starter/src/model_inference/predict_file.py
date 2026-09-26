"""TODO: script CLI que encadena contratos, preprocesado e inferencia."""

# Implementa el comando:
# python -m model_inference.predict_file --input <csv> --output <csv>
# No dejes un archivo de salida parcial si alguna fila es inválida.

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

from model_inference.contracts import WineQualityPrediction, WineQualityRequest
from model_inference.inference import infer_wine_quality, load_wine_quality_model
from model_inference.preprocess import preprocess_wine_request


def predict_file(input: Path, output: Path, model_path: Path) -> None:
    model = load_wine_quality_model(model_path)
    df = pd.read_csv(input)
    requests = []

    for index, row in df.iterrows():
        sample_id = str(row.get("sample_id", ""))
        try:
            if not sample_id.strip() or sample_id == "nan":
                raise ValueError("sample_id no puede estar vacío")
            row = row.drop(labels="sample_id")
            requests.append((sample_id, WineQualityRequest(**row.to_dict())))
        except Exception as error:
            raise ValueError(
                f"Error en la fila {index} ({sample_id}): {error}"
            ) from error

    predictions = []
    for sample_id, request in requests:
        quality, confidence = infer_wine_quality(
            model, preprocess_wine_request(request).as_vector()
        )
        predictions.append(
            WineQualityPrediction(
                quality=quality,
                confidence=confidence
            ).model_dump()
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(predictions[0]))
        writer.writeheader()
        writer.writerows(predictions)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=Path, default=Path("models/wine_quality_classifier.joblib")
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        predict_file(args.input, args.output, args.model)
    except Exception as error:
        print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
