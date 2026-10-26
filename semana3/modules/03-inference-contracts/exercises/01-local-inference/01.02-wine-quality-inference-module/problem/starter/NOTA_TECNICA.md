# Nota técnica - módulo local de inferencia (S3)

Módulo que lee un CSV de muestras de vino, valida cada fila, construye el vector de entrada en el orden del entrenamiento, aplica el modelo preentrenado y escribe un CSV con las predicciones.

```
CSV → contracts (validación) → preprocess (vector) → inference (modelo) → CSV de salida
```

## Responsabilidad de cada módulo

- **`contracts.py`**: define los contratos de entrada y salida con Pydantic. `WineQualityRequest` exige las 11 features como float dentro de su rango y rechaza campos adicionales (`extra="forbid"`). `WineQualityPrediction` valida la salida: `sample_id` no vacío, `confidence` entre 0 y 1 y las dos versiones. No lee ficheros ni conoce el modelo.
- **`preprocess.py`**: define `FEATURE_NAMES` y `PREPROCESSING_VERSION`, y transforma una solicitud ya validada en el vector de 11 valores en ese orden. No lee el CSV ni incluye `sample_id`.
- **`inference.py`**: carga el `.joblib` y comprueba, antes de usarlo, que contiene `estimator` con `predict` y `predict_proba`, que `feature_names` coincide con `FEATURE_NAMES` y que existe `model_version`. Después obtiene la categoría y su probabilidad, y verifica que la categoría es una de las esperadas.
- **`predict_file.py`**: CLI que orquesta el flujo: lee el CSV, valida todas las filas, preprocesa, infiere y escribe la salida. Cualquier error se muestra por `stderr` y el comando devuelve código 2. No carga el joblib directamente ni transforma features.

## Decisiones de diseño

1. **Escritura atómica de la salida.** Primero se validan todas las filas y las predicciones se acumulan en memoria. Después el CSV se escribe en un fichero temporal y se renombra al destino con `os.replace`. De este modo, si alguna fila es inválida o falla la escritura, no queda un fichero de salida parcial.

2. **Validación del artefacto antes de predecir.** El orden de las features forma parte del contrato: un artefacto con las mismas 11 columnas en otro orden produciría predicciones incorrectas sin lanzar ningún error. Por ejemplo, al intercambiar `density` y `alcohol`, `red-003` pasa de `acceptable` a `needs_review`. Por eso el cargador compara `feature_names` con `FEATURE_NAMES` (definido una sola vez en `preprocess.py`) y comprueba la interfaz mínima del estimador antes de llamar a `predict`.

## Otras consideraciones

- Los rangos de `WineQualityRequest` coinciden con la tabla del lienzo de la clase 1 (por ejemplo, `density` 0.98–1.01, `ph` 2.5–4.5 y `alcohol` 5–20).
- `preprocessing_version` se define como constante en `preprocess.py`, junto a la transformación que describe. Así, al modificar el preprocesado, la versión que debe actualizarse está en el mismo fichero, y cada predicción de salida indica con qué versión se generó.
