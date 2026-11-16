"""S9.4 — Tests que escribe el alumnado.

Cada test empieza en rojo con `pytest.fail`. Sustituye esa línea por el test
real; la entrega se considera completa cuando toda la suite está en verde.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wine_api.dependencies import get_predictor
from wine_api.export_openapi import render_openapi
from wine_api.predictor import UnavailablePredictor

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "openapi.json"


def test_prediction_returns_503_when_model_is_unavailable(
    client: TestClient, valid_payload: dict
) -> None:
    # S9.4a: `get_predictor` devuelve un UnavailablePredictor mediante
    # `dependency_overrides`, sin tocar el código de la API. El `finally`
    # limpia el override aunque falle una aserción.
    client.app.dependency_overrides[get_predictor] = UnavailablePredictor
    try:
        response = client.post("/v1/predictions", json=valid_payload)
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "model_unavailable"
    assert "fields" not in body["error"]
    assert body["request_id"] == response.headers["X-Request-Id"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("alcohol", 4.99, id="alcohol-below-min"),
        pytest.param("alcohol", 20.01, id="alcohol-above-max"),
        pytest.param("ph", 2.49, id="ph-below-min"),
        pytest.param("density", 1.02, id="density-above-max"),
        pytest.param("chlorides", -0.1, id="chlorides-negative"),
        pytest.param("residual_sugar", None, id="residual-sugar-null"),
        pytest.param("sulphates", "mucho", id="sulphates-text"),
        pytest.param("citric_acid", True, id="citric-acid-boolean"),
    ],
)
def test_out_of_contract_values_are_rejected(
    client: TestClient, valid_payload: dict, field: str, value: object
) -> None:
    # S9.4b: valores justo fuera de rango, nulos, texto y booleanos. Cada
    # caso es un 422 que señala exactamente el campo culpable.
    valid_payload["features"][field] = value

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert [item["field"] for item in error["fields"]] == [f"features.{field}"]


@pytest.mark.parametrize("alcohol", [5, 20, 5.0, 20.0])
def test_range_limits_are_inclusive(
    client: TestClient, valid_payload: dict, alcohol: float
) -> None:
    # S9.4c: los dos extremos de `alcohol` forman parte del contrato.
    valid_payload["features"]["alcohol"] = alcohol

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 200, response.text


def test_openapi_matches_versioned_contract() -> None:
    # S9.4d: el snapshot versionado en Git debe coincidir con el contrato que
    # genera la app. Si cambia, regenera con
    # `uv run python -m wine_api.export_openapi` y revisa el diff en el PR.
    assert CONTRACT_PATH.exists(), "Falta contracts/openapi.json"
    assert render_openapi() == CONTRACT_PATH.read_text(encoding="utf-8")
    assert "raw_score" not in CONTRACT_PATH.read_text(encoding="utf-8")
