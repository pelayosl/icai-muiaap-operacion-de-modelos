"""Puntos de extensión del taller de serialización."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

import joblib
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from model_packaging.contracts import (
    QualityBand,
    WineQualityPrediction,
    WineQualityRequest,
)
from model_packaging.preprocess import (
    FEATURE_NAMES,
    PREPROCESSING_VERSION,
    preprocess_wine_request,
)

ARTIFACT_SCHEMA_VERSION = "wine-quality-bundle-v1"
DEFAULT_BUNDLE_PATH = Path("models/wine_quality_bundle")
MANIFEST_FILENAME = "manifest.json"
MODEL_FILENAME = "model.joblib"
OUTPUT_LABELS: tuple[QualityBand, ...] = (
    "needs_review",
    "acceptable",
    "excellent",
)


@runtime_checkable  # Necesario para poder usar isinstance() con el Protocol
class WineQualityEstimator(Protocol):
    """Interfaz mínima que debe cumplir el estimador cargado."""

    def predict(self, features: list[list[float]]) -> Sequence[str]:
        """Devuelve una etiqueta por fila."""

    def predict_proba(self, features: list[list[float]]) -> Sequence[Sequence[float]]:
        """Devuelve probabilidades por fila."""


class ArtifactManifest(BaseModel):
    """Declara y valida los metadatos del bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    model_version: str = Field(min_length=1)
    preprocessing_version: str = Field(min_length=1)
    feature_names: tuple[str, ...] = Field(min_length=1)
    output_labels: tuple[QualityBand, ...]
    estimator_type: str = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod  # Se pone classmethod porque no hay constructor
    def validate_schema_version(cls, v: str) -> str:
        if v != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version no coincide: {v} != {ARTIFACT_SCHEMA_VERSION}"
            )
        return v

    @field_validator("preprocessing_version")
    @classmethod
    def validate_preprocessing_version(cls, v: str) -> str:
        if v != PREPROCESSING_VERSION:
            raise ValueError(
                f"preprocessing_version no coincide: {v} != {PREPROCESSING_VERSION}"
            )
        return v

    @field_validator("feature_names")
    @classmethod
    def validate_feature_names(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if v != FEATURE_NAMES:
            raise ValueError(f"feature_names no coincide: {v} != {FEATURE_NAMES}")
        return v

    @field_validator("output_labels")
    @classmethod
    def validate_output_labels(
        cls, v: tuple[QualityBand, ...]
    ) -> tuple[QualityBand, ...]:
        if v != OUTPUT_LABELS:
            raise ValueError(f"output_labels no coincide: {v} != {OUTPUT_LABELS}")
        return v


@dataclass(frozen=True)
class LoadedModelBundle:
    """Bundle cargado; no modificar esta interfaz pública."""

    estimator: WineQualityEstimator
    manifest: ArtifactManifest


def _check_estimator(estimator: object, manifest: ArtifactManifest) -> None:
    """Comprueba la interfaz mínima y que el tipo coincide con el manifiesto."""

    if not isinstance(estimator, WineQualityEstimator):
        raise ValueError(
            "El estimador no cumple la interfaz mínima (predict/predict_proba): "
            f"{type(estimator).__name__}"
        )
    if type(estimator).__name__ != manifest.estimator_type:
        raise ValueError(
            f"estimator_type no coincide: {type(estimator).__name__} "
            f"!= {manifest.estimator_type}"
        )


def create_manifest(
    estimator: WineQualityEstimator, model_version: str
) -> ArtifactManifest:
    return ArtifactManifest(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        model_version=model_version,
        preprocessing_version=PREPROCESSING_VERSION,
        feature_names=FEATURE_NAMES,
        output_labels=OUTPUT_LABELS,
        estimator_type=type(estimator).__name__,
    )


def save_model_bundle(
    bundle_path: Path,
    estimator: WineQualityEstimator,
    manifest: ArtifactManifest | None = None,
) -> ArtifactManifest:
    """Escribe manifest.json y model.joblib de forma segura."""

    if manifest is None:
        manifest = create_manifest(estimator, model_version="unknown")

    # Se valida antes de escribir nada para no dejar un bundle a medias.
    _check_estimator(estimator, manifest)

    bundle_path.mkdir(parents=True, exist_ok=True)
    (bundle_path / MANIFEST_FILENAME).write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    joblib.dump(estimator, bundle_path / MODEL_FILENAME)

    return manifest


def load_model_bundle(bundle_path: Path) -> LoadedModelBundle:
    """Valida el manifiesto antes de cargar el estimador."""

    manifest_path = bundle_path / MANIFEST_FILENAME
    model_path = bundle_path / MODEL_FILENAME

    if not manifest_path.exists():
        raise ValueError(f"El manifiesto no existe: {manifest_path}")
    if not model_path.exists():
        raise ValueError(f"El modelo no existe: {model_path}")

    # Validamos el manifiesto antes de deserializar el estimador
    try:
        manifest = ArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except ValidationError as error:
        raise ValueError(f"Manifiesto incompatible: {error}") from error

    estimator = joblib.load(model_path)
    _check_estimator(estimator, manifest)

    return LoadedModelBundle(estimator=estimator, manifest=manifest)


def infer_wine_quality(
    bundle: LoadedModelBundle,
    request: WineQualityRequest,
) -> WineQualityPrediction:
    """Preprocesa, invoca el estimador y valida la respuesta."""

    vector = preprocess_wine_request(request).as_vector()
    quality_band = str(bundle.estimator.predict([vector])[0])
    if quality_band not in bundle.manifest.output_labels:
        raise ValueError(
            f"quality_band no permitida por el manifiesto: {quality_band!r}"
        )

    # Uso max porque randomforest devuelve tres probabilidades en este caso
    # (una por cada QualityBand), y nos interesa la más alta (la probabilidad
    # asociada con la predicción producida por estimator.predict)
    confidence = float(max(bundle.estimator.predict_proba([vector])[0]))

    return WineQualityPrediction(
        quality_band=quality_band,
        confidence=confidence,
        model_version=bundle.manifest.model_version,
        preprocessing_version=bundle.manifest.preprocessing_version,
    )
