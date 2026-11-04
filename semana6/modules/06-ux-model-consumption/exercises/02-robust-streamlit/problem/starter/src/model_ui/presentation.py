"""TODOs de la vista UX: copy de salida y traducción de errores."""

from __future__ import annotations

from model_ui.contracts import PredictionPayload, PredictionView, UserFacingError
from model_ui.policies import (
    DEFAULT_CONFIDENCE_POLICY,
    DEFAULT_LATENCY_POLICY,
    ConfidencePolicy,
    LatencyPolicy,
    classify_confidence,
    classify_latency,
)

QUALITY_LABELS = {
    "needs_review": "Requiere revisión",
    "acceptable": "Resultado aceptable",
    "excellent": "Resultado excelente",
}

CONFIDENCE_COPY = {
    "low": (
        "Confianza baja",
        "El resultado es orientativo y requiere revisión; "
        "la confianza no es una garantía.",
    ),
    "medium": (
        "Confianza intermedia",
        "Usa el resultado como señal orientativa y revisa su contexto antes de actuar.",
    ),
    "high": (
        "Confianza alta",
        "La confianza es alta para este modelo, pero no garantiza "
        "que la decisión sea correcta.",
    ),
}

LATENCY_COPY = {
    "within_target": (
        "Dentro del objetivo",
        "La respuesta quedó dentro del objetivo de la demo.",
    ),
    "above_target": (
        "Por encima del objetivo",
        "La respuesta llegó, pero la latencia supera el objetivo técnico de la demo.",
    ),
}


def build_prediction_view(
    prediction: PredictionPayload,
    latency_ms: float,
    *,
    confidence_policy: ConfidencePolicy = DEFAULT_CONFIDENCE_POLICY,
    latency_policy: LatencyPolicy = DEFAULT_LATENCY_POLICY,
) -> PredictionView:
    """Construye la vista con etiquetas, confianza, latencia y versiones."""
    confidence_level = classify_confidence(prediction.confidence, confidence_policy)
    latency_status = classify_latency(latency_ms, latency_policy)

    return PredictionView(
        quality_band=prediction.quality_band,
        quality_label=QUALITY_LABELS[prediction.quality_band],
        confidence=prediction.confidence,
        confidence_level=confidence_level,
        confidence_label=CONFIDENCE_COPY[confidence_level][0],
        confidence_message=CONFIDENCE_COPY[confidence_level][1],
        latency_ms=latency_ms,
        latency_status=latency_status,
        latency_label=LATENCY_COPY[latency_status][0],
        latency_message=LATENCY_COPY[latency_status][1],
        model_version=prediction.model_version,
        preprocessing_version=prediction.preprocessing_version,
    )


def to_user_facing_error(error: Exception, request_id: str) -> UserFacingError:
    """Asigna código estable, mensaje accionable y recuperación."""
    if isinstance(error, ValueError):
        return UserFacingError(
            code="invalid_input",
            title="Entrada inválida",
            message="Algún valor del formulario no cumple el contrato del modelo.",
            recovery="Revisa los valores del formulario y vuelve a enviarlo.",
            request_id=request_id,
        )
    elif isinstance(error, FileNotFoundError):
        return UserFacingError(
            code="artifact_unavailable",
            title="Artefacto no disponible",
            message="No se pudo cargar el bundle del modelo.",
            recovery="Configura MODEL_UI_BUNDLE con un bundle válido y reinicia.",
            request_id=request_id,
        )
    elif isinstance(error, TimeoutError):
        return UserFacingError(
            code="timeout",
            title="Tiempo de espera agotado",
            message="La inferencia tardó más de lo permitido.",
            recovery="Vuelve a intentarlo más tarde.",
            request_id=request_id,
        )
    elif isinstance(error, RuntimeError):
        return UserFacingError(
            code="prediction_error",
            title="Error de backend",
            message="El backend no ha podido generar una salida compatible.",
            recovery="Vuelve a intentarlo más tarde.",
            request_id=request_id,
        )
    else:
        return UserFacingError(
            code="prediction_error",
            title="Error de predicción",
            message="Ocurrió un error durante la predicción.",
            recovery="Vuelve a intentarlo más tarde.",
            request_id=request_id,
        )
