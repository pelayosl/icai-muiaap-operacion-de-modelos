# Microejercicios — HTTP, JSON y diseño de recursos

Trabajad por parejas. No hace falta levantar ningún servicio. En el ejercicio 3
sí haréis una comprobación breve con `json.loads()` o un validador local.
Conservad las decisiones: se reutilizarán en el laboratorio de clientes.

## 1. Tres formas de pedir una predicción

Comparad estos tres casos:

A. `infer_measurements(payload)` dentro del mismo programa Python.
B. Un cliente envía `POST /runPumpModel` a otro proceso mediante HTTP.
C. Un cliente envía `POST /v1/predictions` a otro proceso mediante HTTP.

Completad la tabla:

Un proceso es un programa en ejecución. En A todo ocurre en el mismo proceso;
en B y C, el cliente se comunica con el proceso servidor.

| Caso | ¿Sale del proceso Python? | ¿Usa HTTP? | ¿La ruta nombra una acción o un recurso? |
| --- | --- | --- | --- |
| A | No, es una llamada a función dentro del mismo proceso | No | Ninguna, no hay ruta (es una función) |
| B | Sí, el cliente habla con el proceso servidor | Sí | Una acción (`runPumpModel` es un verbo) |
| C | Sí, el cliente habla con el proceso servidor | Sí | Un recurso (`predictions` es un sustantivo, la acción la indica el método `POST`) |

C es el diseño REST: la ruta nombra el recurso y el método HTTP dice qué se hace
con él. Además, `/v1` versiona el contrato.


## 2. URL, path y query

```text
http://127.0.0.1:8000/v1/predictions/pred-42?include=explanation&limit=1
```

**TODO:** marcad scheme, host, port, path y cada parámetro de query. Después
decidid dónde pondríais:

- el identificador de una predicción concreta;
- un límite de resultados;
- cuatro medidas de una bomba.

**Comprobación:** las medidas estructuradas no deberían acabar en la URL.

| Parte | Valor |
| --- | --- |
| Scheme | `http` |
| Host | `127.0.0.1` |
| Port | `8000` |
| Path | `/v1/predictions/pred-42` |
| Query: parámetro 1 | `include=explanation` |
| Query: parámetro 2 | `limit=1` |

* Identificador de una predicción concreta: en el **path**
  (`/v1/predictions/pred-42`), porque identifica el recurso.
* Límite de resultados: en la **query** (`?limit=10`), porque es una opción
  sobre cómo devolver los datos, no parte de la identidad del recurso.
* Cuatro medidas de una bomba: en el **body JSON** de un `POST`, porque son
  datos estructurados y tipados. En la URL perderían los tipos (todo es texto),
  tendrían límite de longitud y quedarían registradas en logs e historiales.

## 3. JSON y Python

```python
{"machine_id": "pump-017", "ready": True, "comment": None, "axes": (1, 2)}
```

**TODO:** convertid esta expresión Python a JSON interoperable. Investigad las
formas JSON de booleano, nulo y colección. Comprobad el resultado con un
validador local o `json.loads()`.

```json
{"machine_id": "pump-017", "ready": true, "comment": null, "axes": [1, 2]}
```

| Python | JSON |
| --- | --- |
| `True` / `False` | `true` / `false` |
| `None` | `null` |
| tupla `(1, 2)` o lista `[1, 2]` | array `[1, 2]` (JSON no tiene tuplas) |
| `"texto"` o `'texto'` | solo `"texto"` (comillas dobles obligatorias) |

Comprobación:

```python
>>> import json
>>> json.loads('{"machine_id": "pump-017", "ready": true, "comment": null, "axes": [1, 2]}')
{'machine_id': 'pump-017', 'ready': True, 'comment': None, 'axes': [1, 2]}
```

Al volver a Python, el array se lee como lista, no como tupla: el viaje de ida
y vuelta no conserva el tipo exacto.

## 4. Cuatro estados HTTP esenciales

Para cada caso, elegid solo entre `200`, `400`, `422` y `503`. Escribid el
código y una razón de una frase.

1. Predicción correcta y devuelta: código `200`; razón: el resultado es el adecuado y la petición ha resultado exitosa, `200 == "OK"`.
2. Texto truncado o que no es JSON: código `400`; razón: el texto es inválido, y el código `400` se utiliza en situaciones de mala sintaxis.
3. JSON válido, pero `vibration_mm_s` es la cadena `"alta"`: código `422`;
   razón: el mensaje es sintácticamente correcto, pero semánticamente inválido ya que `vibration_mm_s` no espera un string.
4. Petición correcta, pero el modelo no está disponible temporalmente: código
   `503`; razón: es un problema del servidor, el error `503` indica precisamente eso (service unavailable).

## 5. Crear y consultar una predicción

Completad estas plantillas:

```text
Crear una predicción:    [POST] /v1/predictions
Consultar la predicción: [GET] /v1/predictions/pred-42
```

¿Dónde van las mediciones: en el path, en la query o en el body JSON?
* En el body JSON, porque son datos estructurados

¿Dónde va `pred-42`?
* En el path, tal y como indiqué en el endpoint de consultar la predicción

¿Qué podría pasar si se repite dos veces la creación?
* Podría crear dos predicciones distintas, `POST` no es idempotente ni seguro.

¿Consultar dos veces debería cambiar el estado del servidor?
* No, `GET` nunca debería de cambiar el estado del servidor, ya que es idempotente y seguro.

- **segura:** está pensada solo para leer, sin cambiar el estado del servidor;
- **idempotente:** repetirla tiene el mismo efecto esperado que ejecutarla una
  sola vez.

Aplicad ambos términos a crear y consultar una predicción.

| Operación | ¿Segura? | ¿Idempotente? |
| --- | --- | --- |
| Crear (`POST /v1/predictions`) | No, crea un recurso nuevo | No, repetirla puede crear un duplicado |
| Consultar (`GET /v1/predictions/pred-42`) | Sí, solo lee | Sí, repetirla no cambia nada |

Consecuencia para el cliente: un `GET` que falla por timeout se puede reintentar
sin riesgo. Un `POST` no se debe reintentar a ciegas, porque si la primera
petición sí llegó al servidor, el reintento crearía una segunda predicción.
