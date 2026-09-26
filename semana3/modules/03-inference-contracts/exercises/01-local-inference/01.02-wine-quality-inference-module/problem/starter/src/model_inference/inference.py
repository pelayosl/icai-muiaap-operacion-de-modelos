"""Carga del .joblib e inferencia sobre características preparadas."""

# Declara DEFAULT_MODEL_PATH, load_wine_quality_model() e infer_wine_quality().
# Comprueba las características del artefacto antes de llamar al clasificador.

# <0.5 pobre, 0.5-0.6 aceptable, >0.6 excelente

from pathlib import Path

import joblib

from model_inference.preprocess import FEATURE_NAMES

DEFAULT_MODEL_PATH = Path("models/wine_quality_classifier.joblib")


def load_wine_quality_model(model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    model = joblib.load(model_path)
    if not isinstance(model, dict) or "estimator" not in model:
        raise ValueError("El artefacto no contiene un clasificador compatible")
    if tuple(model.get("feature_names", ())) != FEATURE_NAMES:
        raise ValueError("feature_names no coincide con las características esperadas")
    if not model.get("model_version"):
        raise ValueError("El artefacto no contiene model_version")
    return model


def infer_wine_quality(model: dict, data_vector: list[float]) -> tuple[str, float]:
    estimator = model["estimator"]
    quality_band = str(estimator.predict([data_vector])[0])
    if quality_band not in {"needs_review", "acceptable", "excellent"}:
        raise ValueError("quality_band no es válido")
    confidence = float(max(estimator.predict_proba([data_vector])[0]))
    return quality_band, confidence
