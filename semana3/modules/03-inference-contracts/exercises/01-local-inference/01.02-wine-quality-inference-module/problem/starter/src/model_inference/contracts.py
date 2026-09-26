"""TODO: contratos de entrada y salida de la inferencia."""

# Implementa WineQualityRequest y WineQualityPrediction con Pydantic.
# Revisa los campos de assets/inference_samples.csv y prohíbe columnas extra.

from pydantic import BaseModel, ConfigDict, Field

class WineQualityRequest(BaseModel):
    fixed_acidity: float = Field(..., ge=0, le=20, description="Fixed acidity of the wine")
    volatile_acidity: float = Field(..., ge=0, le=2, description="Volatile acidity of the wine")
    citric_acid: float = Field(..., ge=0, le=2, description="Citric acid content of the wine")
    residual_sugar: float = Field(..., ge=0, le=20, description="Residual sugar content of the wine")
    chlorides: float = Field(..., ge=0,le=1, description="Chloride content of the wine")
    free_sulfur_dioxide: float = Field(..., ge=0, le=100, description="Free sulfur dioxide content of the wine")
    total_sulfur_dioxide: float = Field(..., ge=0, le=300, description="Total sulfur dioxide content of the wine")
    density: float = Field(..., ge=0, le=1.01, description="Density of the wine")
    ph: float = Field(..., ge=0, le=4.5, description="pH level of the wine")
    sulphates: float = Field(..., ge=0, le=3, description="Sulphate content of the wine")
    alcohol: float = Field(..., ge=0, le=20, description="Alcohol content of the wine")
    
    model_config = ConfigDict(extra="forbid")

class WineQualityPrediction(BaseModel):
    sample_id: str = Field(..., description="Unique identifier for the wine sample")
    quality_band: str = Field(..., description="Predicted quality of the wine")
    confidence: float = Field(..., ge=0, le=1, description="Confidence of the prediction")
    model_version: str = Field(..., description="Version of the model used for prediction")
    preprocessing_version: str = Field(..., description="Version of the preprocessing used for prediction")

    model_config = ConfigDict(extra="forbid")