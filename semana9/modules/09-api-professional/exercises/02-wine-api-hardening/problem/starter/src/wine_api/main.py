"""Punto de entrada de la API: `fastapi dev` usa `wine_api.main:app`."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.request_id import request_id_middleware
from wine_api.routers import health, predictions

# S9.3g: completa los metadatos que lee el consumidor en /docs:
# `version` (¿mayor, menor o parche tras S9.1c?), `summary`, una `description`
# en Markdown que explique `request_id` y el sobre de error, y `openapi_tags`
# con una descripción por tag. Comprobación: tests/test_s9_3_openapi.py
API_VERSION = "1.1.0"
API_DESCRIPTION = """
Esta API permite consultar la salud del servicio y obtener predicciones de
calidad del vino.

Todas las respuestas incluyen un `request_id` (también en la cabecera
`X-Request-Id`), útil para rastrear una petición en los logs y comunicar
incidencias.

Los errores siguen un sobre común: `{"error": {"code", "message", "fields"},
"request_id"}`. Programa contra `error.code`, que es estable, y no contra el
texto de `message`.
"""


def create_app(predictor: Predictor | None = None) -> FastAPI:
    """Crea la aplicación; los tests inyectan su propio predictor."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(
            os.environ.get("WINE_API_MODE", "ready")
        )
        yield

    app = FastAPI(
        title="Wine Quality API",
        summary="API para predecir la calidad del vino.",
        description=API_DESCRIPTION,
        version=API_VERSION,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "health", "description": "Endpoints de salud del servicio."},
            {
                "name": "predictions",
                "description": "Predicciones de calidad del vino.",
            },
        ],
    )
    app.middleware("http")(request_id_middleware)
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    return app


app = create_app()
