from dataclasses import asdict
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.schemas import (
    VALID_FEATURES_EXAMPLE,
    ErrorResponse,
    Prediction,
    PredictionRequest,
    PredictionResponse,
)

# S9.3a: mueve aquí `prefix="/v1/predictions"` y `tags=["predictions"]`.
# S9.3c: declara a nivel de router `responses=` para 400, 422 y 503 con
# `{"model": ErrorResponse, "description": ...}`. Así el 422 deja de
# documentarse como `HTTPValidationError`, que ya no es lo que devolvemos.
router = APIRouter(
    prefix="/v1/predictions",
    tags=["predictions"],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request body"},
        422: {"model": ErrorResponse, "description": "Request body out of contract"},
        503: {"model": ErrorResponse, "description": "Prediction model not ready"},
    },
)

PREDICTION_EXAMPLES = {
    "valid": {
        "summary": "Valid request",
        "value": {"features": VALID_FEATURES_EXAMPLE},
    },
    "invalid_missing_feature": {
        "summary": "Missing feature: 422",
        "value": {
            "features": {
                name: value
                for name, value in VALID_FEATURES_EXAMPLE.items()
                if name != "alcohol"
            }
        },
    },
    "invalid_out_of_range": {
        "summary": "Feature out of range: 422",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": 25.0}},
    },
}


# S9.3e: añade summary, response_description y un docstring útil para
# quien consume la API (campos, rangos, decimales de confidence).
# S9.3f: ofrece en Swagger al menos tres ejemplos de cuerpo (uno válido
# y dos inválidos). Investiga `Annotated[PredictionRequest, Body(...)]` con
# `openapi_examples=`; usa VALID_FEATURES_EXAMPLE como base.
@router.post(
    "",
    summary="Create a new prediction",
    response_description="The created prediction",
)
def create_prediction(
    payload: Annotated[PredictionRequest, Body(openapi_examples=PREDICTION_EXAMPLES)],
    predictor: PredictorDep,
    request_id: RequestIdDep,
) -> PredictionResponse:
    """Crea una predicción de calidad a partir de las características del vino.

    - `features`: objeto con las once variables fisicoquímicas del vino. Cada
      campo tiene un rango inclusivo (por ejemplo, `alcohol` entre 5 y 20 % vol.)
      y no se admiten campos extra.
    - `prediction.confidence`: valor entre 0 y 1 redondeado a dos decimales.
    - `served_at`: instante en UTC, ISO 8601 con sufijo `Z`.
    - `request_id`: identificador de la petición para rastrearla en los logs.
    """
    output = predictor.predict(payload.features)
    # S9.1e
    Prediction.model_validate(output, from_attributes=True)
    return PredictionResponse(
        prediction=asdict(output),
        request_id=request_id,
        served_at=datetime.now(UTC),
    )
