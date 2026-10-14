"""Carga del .joblib e inferencia sobre características preparadas."""

from pathlib import Path

import joblib

from model_inference.preprocess import FEATURE_NAMES

DEFAULT_MODEL_PATH = Path("models/wine_quality_classifier.joblib")

QUALITY_BANDS = frozenset({"needs_review", "acceptable", "excellent"})


def load_wine_quality_model(model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    model = joblib.load(model_path)
    if not isinstance(model, dict) or "estimator" not in model:
        raise ValueError("El artefacto no contiene un clasificador compatible")
    estimator = model["estimator"]
    for method in ("predict", "predict_proba"):
        if not callable(getattr(estimator, method, None)):
            raise ValueError(
                f"El artefacto no contiene un clasificador compatible: falta {method}()"
            )
    if tuple(model.get("feature_names", ())) != FEATURE_NAMES:
        raise ValueError("feature_names no coincide con las características esperadas")
    if not model.get("model_version"):
        raise ValueError("El artefacto no contiene model_version")
    return model


def infer_wine_quality(model: dict, data_vector: list[float]) -> tuple[str, float]:
    estimator = model["estimator"]
    quality_band = str(estimator.predict([data_vector])[0])
    if quality_band not in QUALITY_BANDS:
        raise ValueError(f"quality_band no es válido: {quality_band!r}")
    confidence = float(max(estimator.predict_proba([data_vector])[0]))
    return quality_band, confidence
