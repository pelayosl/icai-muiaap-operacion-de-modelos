# QA manual - Churn Streamlit (Clase 01)

Tests unitarios: 13 en verde

| Caso | Acción | Resultado observable | OK |
|---|---|---|---|
| 1. Arranque | Abrir la app. | Título "¿Qué cliente podría darse de baja?", caption con el aviso de score no calibrado y un formulario con 4 widgets (2 sliders, 1 number_input, 1 checkbox) y el botón "Calcular riesgo". Sin resultado. | ✅ |
| 2. Edición sin envío | Cambiar antigüedad a 2, gasto a 95 y llamadas a 4, sin pulsar el botón. | No aparece ningún resultado ni mensaje; `predict()` no se ejecuta. | ✅ |
| 3. Submit válido | Pulsar "Calcular riesgo" con ese perfil. | Aviso "Baja probable", "Score de riesgo: 0.95" y la explicación de la regla (base: +0,25; antigüedad inferior a 6 meses: +0,30; gasto mensual de al menos 80 €: +0,20; tres o más llamadas de soporte: +0,25; sin contrato anual: +0,10. Score acotado: 0,95; umbral de decisión: 0,50. No es una probabilidad calibrada.). | ✅ |
| 4. Resultado actualizado | Cambiar a 36 meses, 35 €, 0 llamadas, contrato anual, y enviar de nuevo. | Al enviar, el resultado anterior se sustituye por "Permanencia probable", "Score de riesgo: 0.05" y su nueva explicación. | ✅ |

## Puente a Wine

Se conserva el patrón: formulario único -> `form_submit_button` como frontera -> una sola llamada al predictor inyectado -> render del resultado o mensaje de error fijo. Solo cambian los campos y el contrato de inferencia.
