# Ampliación posterior a la clase 1 — consumir una API de predicción

Este laboratorio es una **ampliación posterior a la clase 1** o assignment;
**no es la clase 2**. La clase 2 continúa el proyecto Wine Quality en
[`03-wine-http-gateway`](../../03-wine-http-gateway/README.md).

## Objetivo

Consumir una API local ya preparada con curl y Python. Postman queda como
ampliación opcional. No abras ni modifiques el servidor: el trabajo está en el
lado cliente.

## 0. Arranque y salud

Desde la raíz del módulo:

```text
uv run python examples/pump-maintenance-api/server.py
```

En otra terminal ejecuta el `GET /health` de la [guía curl](../../../examples/curl/README.md).

**Comprobación:** obtienes `200`, `status: ok`, `model_status: ready` y un
`request_id`.

```bash
>> curl.exe -i "$baseUrl/health"
HTTP/1.1 200 OK
Server: S7LocalAPI/1.0 Python/3.12.14
Date: Wed, 11 Nov 2026 10:56:04 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 153
X-Request-Id: req_94b66edba470
```

## 1. Observar el contrato con curl

Ejecuta el POST válido y el inválido ya preparados.

**TODO 1:** registra método, path, `Content-Type`, status, `request_id` y el
campo rechazado. Explica por qué el segundo caso es `422`, no `400`.
> El caso inválido es 422 por un error de semántica (no se cumple el contrato de entrada para el JSON)


| Caso | Método | Path | Content-Type respuesta | Status | request_id | Campo rechazado |
| --- | --- | --- | --- | --- | --- | --- |
| Salud | `GET` | `/health` | `application/json; charset=utf-8` | `200 OK` | `req_7f35161bb633` | — |
| POST válido | `POST` | `/v1/predictions` | `application/json; charset=utf-8` | `200 OK` | `req_daf0fdf775c7` | — |
| POST inválido | `POST` | `/v1/predictions` | `application/json; charset=utf-8` | `422 Unprocessable Entity` | `req_c6c4968a27fc` | `measurements.vibration_mm_s` |

Las peticiones `POST` se envían con `Content-Type: application/json` y
`Accept: application/json`.

**GET /health**:
```text
$ curl -i "$BASE_URL/health"
HTTP/1.1 200 OK
Server: S7LocalAPI/1.0 Python/3.12.14
Date: Wed, 11 Nov 2026 13:51:17 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 153
X-Request-Id: req_7f35161bb633

{"status": "ok", "service": "pump-maintenance-prediction", "model_status": "ready", "model_version": "pump-risk-1.0.0", "request_id": "req_7f35161bb633"}
```

**POST VÁLIDO**:
```text
$ curl -i -X POST "$BASE_URL/v1/predictions" -H "Accept: application/json" -H "Content-Type: application/json" --data-binary @examples/pump-maintenance-api/samples/prediction-valid.json
HTTP/1.1 200 OK
Server: S7LocalAPI/1.0 Python/3.12.14
Date: Wed, 11 Nov 2026 13:51:17 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 165
X-Request-Id: req_daf0fdf775c7

{"machine_id": "pump-017", "prediction": {"label": "maintenance_required", "risk_score": 0.85}, "model_version": "pump-risk-1.0.0", "request_id": "req_daf0fdf775c7"}
```

**POST INVÁLIDO**:
```text
$ curl -i -X POST "$BASE_URL/v1/predictions" -H "Accept: application/json" -H "Content-Type: application/json" --data-binary @examples/pump-maintenance-api/samples/prediction-invalid.json
HTTP/1.1 422 Unprocessable Entity
Server: S7LocalAPI/1.0 Python/3.12.14
Date: Wed, 11 Nov 2026 13:51:17 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 218
X-Request-Id: req_c6c4968a27fc

{"error": {"code": "validation_error", "message": "JSON is valid but violates the input contract", "fields": [{"field": "measurements.vibration_mm_s", "message": "must be a number"}]}, "request_id": "req_c6c4968a27fc"}
```

**Comprobación:** no confundas `maintenance_required` con un error HTTP; el
primer status sigue siendo `200`.

## 2. Ampliación opcional con Postman

Completa el [ejercicio Postman](../../../examples/postman/README.md). La
colección sirve para comprobar el resultado, pero reconstruye al menos una
petición manualmente.

**TODO 2 opcional:** prepara una tabla de evidencia con salud, éxito y
validación.

## 3. Completar el cliente Python

Trabaja en `starter/client.py` y ejecuta:

```text
uv run python -m unittest discover -s exercises/02-api-client-lab/problem/starter -p "test_*.py" -v
```

Los cinco tests empiezan en rojo por el `NotImplementedError` intencional.

**TODO 3 — petición:** usa `session.post()` con:

- URL terminada en `/v1/predictions`;
- `json=payload`, no `data=str(payload)`;
- `headers={"Accept": "application/json"}`;
- `timeout=timeout`.

Esto es necesario para serializar correctamente el cuerpo, expresar el formato
esperado y limitar la espera. Comprueba que pasa el test de argumentos.

**TODO 4 — status:** llama a `response.raise_for_status()`. Convierte
`requests.HTTPError` en `PredictionClientError` conservando el código. Esto
evita tratar un `422` como una predicción. Comprueba el test de error HTTP.

**TODO 5 — transporte:** captura `requests.Timeout` y
`requests.ConnectionError` antes del error genérico. Devuelve mensajes que
permitan decidir entre reintentar o revisar la URL. Comprueba los tests de
timeout y conexión.

**TODO 6 — respuesta:** usa `response.json()` y rechaza una respuesta de éxito
que no sea un objeto JSON. Comprueba el test de contrato de salida.

## Evidencia final

- cinco tests verdes;
- salida de un `200` y un `422`;
- una frase que explique por qué no conviene reintentar ciegamente un POST;
- ningún cambio en la API de caja negra.

### Cinco tests verdes

```text
$ uv run python -m unittest discover -s exercises/02-api-client-lab/problem/starter -p "test_*.py" -v
test_converts_connection_error (test_client.ClientExerciseTest.test_converts_connection_error) ... ok
test_converts_http_error_and_preserves_status (test_client.ClientExerciseTest.test_converts_http_error_and_preserves_status) ... ok
test_converts_timeout (test_client.ClientExerciseTest.test_converts_timeout) ... ok
test_rejects_success_json_that_is_not_an_object (test_client.ClientExerciseTest.test_rejects_success_json_that_is_not_an_object) ... ok
test_sends_json_accept_and_timeout (test_client.ClientExerciseTest.test_sends_json_accept_and_timeout) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.002s

OK
```

### Salida de un `200` y un `422`

Están en el apartado 1: el POST válido devuelve `200 OK` (`req_daf0fdf775c7`)
y el inválido `422 Unprocessable Entity` (`req_c6c4968a27fc`), con
`measurements.vibration_mm_s` como campo rechazado.

### Por qué no reintentar ciegamente un POST

> `POST /v1/predictions` no es idempotente: si hay un timeout, el cliente no
> sabe si el servidor llegó a procesar la petición, y reintentarla sin más
> podría crear una segunda predicción duplicada; además, un `422` no se arregla
> reintentando, porque el error está en los datos enviados.

### API de caja negra sin cambios

`examples/pump-maintenance-api/` no tiene cambios respecto a `main`
(`git diff main -- semana7/modules/07-http-rest-clients/examples` vacío).
