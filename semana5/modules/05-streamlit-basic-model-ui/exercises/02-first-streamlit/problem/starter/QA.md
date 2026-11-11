# QA manual - Wine Streamlit

Bundle: `models/wine_quality_bundle_s4`. Comprobado ejecutando `app.py` con el motor de Streamlit. Tests: 27 en verde.

| Caso | Acción | Resultado observable | OK |
|---|---|---|---|
| 1. Arranque con bundle | Configurar `MODEL_UI_BUNDLE` y abrir la app. | Aparecen los 11 campos y el botón "Ejecutar inferencia". Mensaje "Completa el formulario…" y ninguna predicción. | ✅ |
| 2. Edición sin envío | Cambiar `alcohol` a 12,5 sin pulsar el botón. | Sigue el mensaje inicial, sin salida de predicción, y el gateway no se llama. | ✅ |
| 3. Submit válido | Pulsar "Ejecutar inferencia". | Se muestra `quality_band: acceptable`, `confidence: 0.58`, `model_version: wine-quality-rf-v1` y `preprocessing_version: wine-red-features-v1`. | ✅ |
| 4. Bundle ausente | Quitar la variable `MODEL_UI_BUNDLE`, y repetir con una ruta inexistente. | En ambos casos: error "No se pudo cargar el bundle de S4." e info "Configura MODEL_UI_BUNDLE y vuelve a ejecutar la aplicación." Sin formulario, ruta ni traceback. | ✅ |
