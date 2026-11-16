from fastapi import APIRouter

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.errors import ModelUnavailableError
from wine_api.schemas import ErrorResponse, HealthResponse

SERVICE_NAME = "wine-quality-prediction"


# S9.3a: declara `tags=["health"]` en el router, no en include_router().
router = APIRouter(tags=["health"])


# S9.3b: añade `summary=`, `response_description=` y un docstring que diga
# cuándo usar el endpoint y qué significa un 503. Documenta el 503 con
# `responses={503: {"model": ErrorResponse, "description": ...}}`.
@router.get(
    "/health",
    summary="Check the health of the service",
    response_description="Service and model status",
    responses={
        503: {
            "model": ErrorResponse,
            "description": "The prediction model is not ready",
        }
    },
)
def read_health(predictor: PredictorDep, request_id: RequestIdDep) -> HealthResponse:
    """Comprueba que el servicio está vivo y que el modelo está cargado.

    Úsalo como sonda de disponibilidad antes de enviar predicciones. Un `503`
    con `error.code = model_unavailable` significa que el modelo no está listo
    y que las predicciones también fallarán hasta que se cargue.
    """
    # S9.2f: sustituye el HTTPException por `ModelUnavailableError`: el
    # dominio no debería saber de HTTP y el manejador produce el sobre común.
    if not predictor.is_ready():
        raise ModelUnavailableError
    # S9.1d: declara `-> HealthResponse` y devuelve una instancia.
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        model_status="ready",
        model_version=predictor.model_version,
        request_id=request_id,
    )
