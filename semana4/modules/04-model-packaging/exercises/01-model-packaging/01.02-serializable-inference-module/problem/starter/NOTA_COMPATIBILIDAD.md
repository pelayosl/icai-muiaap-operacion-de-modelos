# Nota de compatibilidad - bundle serializado (S4)

El bundle separa el estimador de los metadatos que permiten decidir si es compatible con el módulo de inferencia:

```
models/wine_quality_bundle/
|__ manifest.json   # contrato legible: versiones, features, etiquetas y tipo de estimador
|__ model.joblib    # estimador serializado
```

`load_model_bundle()` valida primero que existen los dos ficheros y que `manifest.json` cumple `ArtifactManifest` (sin campos desconocidos, con `schema_version`, `preprocessing_version`, `feature_names` y `output_labels` iguales a los del código). Solo después deserializa `model.joblib` y comprueba que el estimador tiene `predict`/`predict_proba` y que su tipo coincide con `estimator_type`.

## Cambios que deben bloquearse

1. **Cambio en el orden de `feature_names`.** Si el manifiesto declara las 11 features en otro orden (por ejemplo, con `density` y `alcohol` intercambiadas), el modelo seguiría recibiendo un vector de 11 valores y predeciría sin error, pero con las features mal asignadas. En la semana 3 se comprobó con el modelo real que este cambio hace que `red-003` pase de `acceptable` a `needs_review`. Por eso se rechaza al validar el manifiesto, antes de cargar el estimador (`feature_names no coincide`).

2. **Cambio en `preprocessing_version`.** El estimador se entrenó con una transformación concreta (`wine-red-features-v1`). Si el bundle declara otra versión, el vector que construye `preprocess.py` puede no ser el que espera el modelo, aunque tenga la misma forma. Como no hay forma de detectarlo a partir de las predicciones, se rechaza al validar el manifiesto (`preprocessing_version no coincide`) y no se llega a escribir ningún CSV.

Otros cambios bloqueados: un `schema_version` distinto, campos desconocidos en el manifiesto, un manifiesto corrupto, un estimador sin `predict`/`predict_proba` o de un tipo distinto al declarado, y una etiqueta de salida que no esté en `output_labels`.

## Generación del bundle

El bundle se genera a partir del payload legado de la semana 3 (diccionario con `estimator`, `feature_names` y `model_version`) usando las funciones del propio módulo:

```python
legacy = joblib.load("<ruta>/wine_quality_classifier.joblib")
estimator = legacy["estimator"]
save_model_bundle(
    Path("models/wine_quality_bundle"),
    estimator,
    create_manifest(estimator, legacy["model_version"]),
)
```

La carpeta `models/` está ignorada por git, por lo que el binario no se sube al repositorio.
