# Nota de compatibilidad - Wine Quality API 1.1.0

Los cambios de esta semana son compatibles con los clientes de S7, porque el contrato público no cambia.

Las rutas siguen siendo `POST /v1/predictions` y `GET /health`, y la entrada acepta los mismos campos.


La respuesta mantiene los cuatro campos de la predicción, ahora con `confidence` redondeado a dos decimales y `served_at` en UTC con sufijo `Z`.

Ya no sale `raw_score`, pero nunca formó parte del contrato, así que ningún cliente debería depender de él.

Los errores pasan de `{"detail": ...}` al sobre de S7 con `code`, `message`, `fields` y `request_id`, que es lo que el contrato ya prometía. Por eso la versión sube de 1.0.0 a 1.1.0 (versión menor).

Sí rompería a los clientes renombrar o quitar un campo de la respuesta, cambiar un `error.code` o añadir un campo obligatorio en la entrada. Un cambio así lo publicaría como 2.0.0 en una ruta nueva `/v2/predictions`, y mantendría `/v1` funcionando durante un tiempo y avisaría de la fecha en la que deja de estar disponible.
