"""Cliente HTTP que adapta la API Wine al contrato de inferencia de la UI."""

from __future__ import annotations

from collections.abc import Mapping
from threading import local
from typing import Any

import requests
from pydantic import ValidationError  # noqa: F401 - pista para el TODO S7.4

from model_ui.contracts import PredictionPayload
from model_ui.errors import (  # noqa: F401 - pistas para el TODO S7.2
    ArtifactUnavailableError,
    BackendInferenceError,
    InferenceTimeoutError,
    InputContractError,
)


class HttpInferenceGateway:
    """Implementa la frontera de inferencia mediante una llamada HTTP REST."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        session: Any | None = None,
    ) -> None:
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            raise ValueError("base_url no puede estar vacia")
        if timeout <= 0:
            raise ValueError("timeout debe ser positivo")

        self._prediction_url = f"{normalized}/v1/predictions"
        self._timeout = float(timeout)
        self._session = session if session is not None else requests.Session()
        self._request_context = local()
        self.last_request_id: str | None = None

    @property
    def last_request_id(self) -> str | None:
        """Devuelve el identificador de la ultima llamada en el contexto actual."""

        return getattr(self._request_context, "request_id", None)

    @last_request_id.setter
    def last_request_id(self, value: str | None) -> None:
        self._request_context.request_id = value

    def predict(self, values: Mapping[str, object]) -> PredictionPayload:
        """Envia la muestra por HTTP y devuelve el contrato interno de S6."""

        self.last_request_id = None

        try:
            response = self._session.post(
                self._prediction_url,
                json={"features": values},
                headers={"Accept": "application/json"},
                timeout=self._timeout,
            )

        except requests.Timeout as ex:
            raise InferenceTimeoutError(
                "La inferencia ha superado el tiempo limite"
            ) from ex
        except requests.ConnectionError as ex:
            raise ArtifactUnavailableError(
                "No se puede conectar con el backend de inferencia"
            ) from ex
        except requests.RequestException as ex:
            raise BackendInferenceError("Error inesperado en la inferencia") from ex

        self.last_request_id = self._header_request_id(response)

        status = response.status_code
        if status == 422:
            raise InputContractError("La solicitud no es válida (HTTP 422)")
        if status == 503:
            raise ArtifactUnavailableError("El servicio no está disponible (HTTP 503)")
        if not 200 <= status < 300:
            raise BackendInferenceError(
                f"Respuesta inesperada del backend: HTTP {status}"
            )

        response_json = self._read_object(response)
        self.last_request_id = self._request_id(response, response_json)
        try:
            prediction_payload = PredictionPayload.model_validate(
                response_json["prediction"]
            )
        except (KeyError, ValidationError) as ex:
            raise BackendInferenceError(
                "La respuesta no cumple el contrato de salida"
            ) from ex

        return prediction_payload

    @staticmethod
    def _read_object(response: Any) -> dict[str, Any]:
        """Lee una respuesta JSON que debe representar un objeto."""

        try:
            body = response.json()
        except ValueError as ex:
            raise BackendInferenceError("La respuesta no es un JSON válido") from ex

        if not isinstance(body, dict):
            raise BackendInferenceError("La respuesta no es un objeto JSON válido")

        return body

    @staticmethod
    def _request_id(response: Any, body: dict[str, Any]) -> str | None:
        """Obtiene request_id del cuerpo y usa la cabecera como alternativa."""

        return body.get("request_id") or HttpInferenceGateway._header_request_id(
            response
        )

    @staticmethod
    def _header_request_id(response: Any) -> str | None:
        headers = getattr(response, "headers", {})
        return headers.get("X-Request-Id")
