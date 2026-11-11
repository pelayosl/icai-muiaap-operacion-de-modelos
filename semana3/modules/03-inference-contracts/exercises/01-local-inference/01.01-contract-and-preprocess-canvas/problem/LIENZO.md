# Lienzo S3 - contrato y preprocesado (vino)

Especificación previa a la clase 02. El modelo ya está entrenado, en este documento se establece qué datos entran, en qué orden se presentan al modelo y qué salida se devuelve.

## 1. Clasificación de piezas

- **Datos de entrenamiento**: muestras de vino con las 11 features y la etiqueta `quality`, ya empleadas durante el entrenamiento. El módulo de inferencia no las utiliza.
- **Artefacto**: diccionario con `estimator` (RandomForest), `feature_names` (orden de las features en el entrenamiento) y `model_version`. El módulo lo carga, pero debe comprobar su estructura antes de utilizarlo.
- **Datos nuevos**: `sample_id` y las 11 features, sin etiqueta, ya que es precisamente lo que se pretende predecir. Deben validarse antes de llegar al modelo.

`sample_id` identifica cada solicitud y acompaña a la predicción, pero no forma parte del vector de entrada al modelo.

## 2. Campos de entrada

Todos los campos son de tipo float y obligatorios. Ninguno admite valores ausentes ni columnas adicionales.

| campo | unidad | rango |
|---|---|---|
| fixed_acidity | g/dm³ | 0 - 20 |
| volatile_acidity | g/dm³ | 0 - 2 |
| citric_acid | g/dm³ | 0 - 2 |
| residual_sugar | g/dm³ | 0 - 20 |
| chlorides | g/dm³ | 0 - 1 |
| free_sulfur_dioxide | mg/dm³ | 0 - 100 |
| total_sulfur_dioxide | mg/dm³ | 0 - 300 |
| density | g/cm³ | 0.98 - 1.01 |
| ph | adimensional | 2.5 - 4.5 |
| sulphates | g/dm³ | 0 - 3 |
| alcohol | % vol | 5 - 20 |

`sample_id`: str, no puede estar vacío.

## 3. Orden del vector

El orden de referencia es el de `feature_names` en el artefacto, no el de las columnas del CSV:

```
fixed_acidity, volatile_acidity, citric_acid, residual_sugar, chlorides,
free_sulfur_dioxide, total_sulfur_dioxide, density, ph, sulphates, alcohol
```

red-001 → `[7.4, 0.7, 0.0, 1.9, 0.076, 11.0, 34.0, 0.9978, 3.51, 0.56, 9.4]`

**Justificación.** Intercambiar dos predictores (como puede ser `density` y `alcohol`) puede producir predicciones incorrectas silenciosamente, porque ambos son de tipo float y por ende le llegan al modelo como valores válidos, sin embargo el modelo interpretará que los valores que le llegan corresponden con el orden que tiene asignado.

## 4. Flujo

```
CSV → solicitud (validación con Pydantic) → preprocesado (vector ordenado, sin sample_id) → artefacto (cargado y validado) → predicción → CSV de salida
```

El CSV de salida se escribe al final y únicamente si todas las filas son válidas. En caso contrario, no se genera ningún fichero.

## 5. Salida

Una fila por muestra con los siguientes campos:
- `sample_id`
- `quality_band`: needs_review / acceptable / excellent
- `confidence`: valor entre 0 y 1. Corresponde a la probabilidad asignada por el modelo a la clase predicha.
- `model_version`: se obtiene del artefacto.
- `preprocessing_version`: la define el módulo de preprocesado.

## 6. Casos de fallo

| caso | ejemplo | etapa de rechazo | motivo |
|---|---|---|---|
| fila válida | red-001 sin modificar | no se rechaza | cumple el contrato |
| columna desconocida | red-001 + `unexpected_field` | validación de la entrada, antes del preprocesado | no se admiten campos adicionales; su presencia indica un cambio en el esquema de los datos |
| valor fuera de rango | red-001 con `ph=99` | validación de la entrada | el pH debe estar entre 2.5 y 4.5 |
| segunda fila inválida | red-001 válida + red-002 con `alcohol=invalid` | validación de la entrada | no debe generarse un CSV parcial que contenga solo red-001 |
| artefacto con otro orden | `feature_names` en orden inverso | carga del modelo, antes de `predict` | de lo contrario se produciría el error descrito en el apartado 3 |

En todos los casos de error, el comando finaliza con código 2, indica el campo o la muestra que ha provocado el fallo y no crea el fichero de salida.

## 7. Criterios de aceptación

1. `uv run python -m model_inference.predict_file --input assets/inference_samples.csv --output .tmp/wine_predictions.csv` genera 5 filas con las columnas `sample_id, quality_band, confidence, model_version, preprocessing_version`.
2. Ante cualquier fila inválida, el comando devuelve código 2 y no se crea el fichero de salida.
3. El vector respeta el orden de `FEATURE_NAMES` y excluye `sample_id`. Un artefacto con `feature_names` distinto, o sin `predict`/`predict_proba`, se rechaza antes de realizar la predicción.
