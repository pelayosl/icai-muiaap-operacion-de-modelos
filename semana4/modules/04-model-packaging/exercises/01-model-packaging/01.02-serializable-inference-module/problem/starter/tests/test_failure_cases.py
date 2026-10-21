from pathlib import Path

import pytest
from test_artifact import WINE_SAMPLE
from test_predict_file import write_bundle, write_input

from model_packaging.artifact import load_model_bundle
from model_packaging.predict_file import predict_file

# El assignment pedía: Añade un caso de fallo - Incluye un manifest corrupto, una fila fuera de rango o una salida de modelo no
# permitida y prueba su mensaje.
#
# Para ello he añadido estos tests. He usado IA para hacerlos.

def test_load_rejects_a_corrupt_manifest(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    (bundle_path / "manifest.json").write_text("{ esto no es JSON")

    with pytest.raises(ValueError, match="Manifiesto incompatible"):
        load_model_bundle(bundle_path)


def test_predict_file_rejects_an_out_of_range_row(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle"
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "predictions.csv"
    write_bundle(bundle_path)
    row = {
        "sample_id": "red-001",
        **{key: str(value) for key, value in WINE_SAMPLE.items()},
        "ph": "99",
    }
    write_input(input_path, rows=[row])

    with pytest.raises(ValueError, match=r"red-001(.|\n)*ph"):
        predict_file(input_path, output_path, bundle_path)

    assert not output_path.exists()
