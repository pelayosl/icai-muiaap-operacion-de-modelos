"""Starter del cliente HTTP. Completa los TODO sin modificar la API."""

from __future__ import annotations

from typing import Any

# El TODO de la práctica usará este cliente para realizar la petición HTTP.
import requests  # noqa: F401


class PredictionClientError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def request_prediction(
    payload: dict[str, Any],
    *,
    base_url: str = "http://127.0.0.1:8000",
    timeout: float = 5.0,
    session: Any | None = None,
) -> dict[str, Any]:
    """Envía una predicción y devuelve un objeto JSON de respuesta."""

    http = session or requests

    try:
        response = http.post(
            f"{base_url.rstrip('/')}/v1/predictions",
            json=payload,
            headers={"Accept": "application/json"},
            timeout=timeout,
        )

        response.raise_for_status()
    except requests.HTTPError as e:
        raise PredictionClientError(
            f"Error HTTP {e.response.status_code}: {e.response.text}",
            status_code=e.response.status_code,
        ) from e
    except requests.Timeout as e:
        raise PredictionClientError("Timeout", status_code=None) from e
    except requests.ConnectionError as e:
        raise PredictionClientError("No se ha podido conectar al servidor", status_code=None) from e
    except requests.RequestException as e:
        raise PredictionClientError("Error de petición HTTP", status_code=None) from e

    response_json = response.json()
    if not isinstance(response_json, dict):
        raise PredictionClientError("La respuesta JSON no es un objeto", status_code=response.status_code)
    
    return response_json
