# Ejercicio 01 — Microejercicios de la clase 1

Cuatro microejercicios de 5 minutos, uno al final de cada bloque de teoría. Se
hacen sobre las demos de [`examples/`](../../../examples/README.md) y no
requieren escribir una API nueva.

Prepara el entorno una vez, desde `semana9/modules/09-api-professional`:

```bash
uv sync --locked
```

## M1 — Serialización (bloque 1)

Arranca `uv run fastapi dev examples/serialization_demo.py` y compara
`/v1/scores/leaky` con `/v1/scores/public`.

1. Anota qué campos aparecen en la primera respuesta y no en la segunda.

>Primera respuesta:
```json
{
  "band": "acceptable",
  "confidence": 0.8312377,
  "raw_score": 6.137,
  "threshold_config": "/srv/models/thresholds.yaml"
}
```

>Segunda respuesta:
```json
{
  "band": "acceptable",
  "confidence": 0.83,
  "served_at": "2026-11-14T18:16:06.067662Z",
  "note": null,
  "is_reliable": true
}
```

>Se puede ver que la primera respuesta filtra >`raw_score` y `thresholds.yaml`

2. Explica en una frase por qué `/v1/scores/filtered` tampoco los devuelve, aunque la función devuelve un `dict` con todos ellos.
>Porque utiliza un `response_model`, concretamente `PublicScore`, por lo que descarta cualquier campo que no se declare (aunque el `dict` los contenga)

3. En `/docs`, abre el esquema `PublicScore`: ¿aparece `is_reliable`?
> Sí

**Comprobación:** tu respuesta a la pregunta 2 menciona `response_model` y
qué hace con los campos que no declara.

## M2 — Errores (bloque 2)

Arranca `uv run fastapi dev examples/errors_demo.py` y envía, desde `/docs` o
con `curl`, tres peticiones a `POST /v1/scores`:

- `{"age": 30, "income": 1000}`
- `{"age": "treinta", "income": 1000}`
- `{"age": 30}`

Después llama a `GET /v1/nada` y a `GET /v1/boom`.

1. Rellena una tabla con status, `error.code` y `error.fields` de cada caso.

| Petición | Status | `error.code` | `error.fields` |
| --- | --- | --- | --- |
| `POST /v1/scores` `{"age": 30, "income": 1000}` | 200 | — (respuesta correcta: `{"score": 0.01}`) | — |
| `POST /v1/scores` `{"age": "treinta", "income": 1000}` | 422 | `validation_error` | `[{"field": "age", "message": "Input should be a valid integer, unable to parse string as an integer"}]` |
| `POST /v1/scores` `{"age": 30}` | 422 | `validation_error` | `[{"field": "income", "message": "Field required"}]` |
| `GET /v1/nada` | 404 | `not_found` | — (no se incluye la clave) |
| `GET /v1/boom` | 500 | `internal_error` | — (no se incluye la clave) |


2. ¿Qué devolvería FastAPI en el segundo caso si borraras `handle_validation`?
   Pruébalo comentando el decorador y restáuralo después.
>Respuesta
```json
{"detail":[{"type":"int_parsing","loc":["body","age"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"treinta"}]}
```
**Comprobación:** las cinco respuestas de error tienen la clave `error` en la
raíz y ninguna contiene el texto `TU_SECRETO`.

## M3 — OpenAPI (bloque 3)

Arranca `uv run fastapi dev examples/openapi_demo.py`.

1. Localiza en `/openapi.json` dónde terminan `summary`, el docstring y
   `responses` de `create_score`.
> - `summary` -> `paths./v1/scores.post.summary` (`"Calcular el score de riesgo"`).
> - Docstring -> `paths./v1/scores.post.description` (Swagger lo renderiza como Markdown).
> - `responses` del router -> `paths./v1/scores.post.responses.422` y `.503`, ambos con
>   `$ref: "#/components/schemas/ErrorResponse"`. El `200` sale del tipo de retorno
>   (`ScoringResponse`) con la descripción de `response_description`.
2. Ejecuta el ejemplo `minor` desde Swagger con «Try it out».
> Devuelve `422` porque `age: 16` incumple `ge=18`:
```json
{"detail":[{"type":"greater_than_equal","loc":["body","age"],"msg":"Input should be greater than or equal to 18","input":16,"ctx":{"ge":18}}]}
```
> (Esta demo no tiene handler propio, así que sale el formato `detail` por defecto
> de FastAPI y no el sobre `error` de `errors_demo.py`.)
3. Añade un tercer ejemplo `no_income` sin el campo `income` y comprueba que
   aparece en el desplegable.
> Añadido en `examples/openapi_demo.py`:
```python
"no_income": {"summary": "Sin ingresos: 422", "value": {"age": 30}},
```
> El desplegable muestra `valid`, `minor` y `no_income`. Al ejecutarlo devuelve `422`
> con `loc: ["body", "income"]` y `msg: "Field required"`. Me quedo con el cambio y
> adapto `test_openapi_documents_errors_and_examples` para que espere
> `{"valid", "minor", "no_income"}`.

**Comprobación:** `uv run pytest -q` sigue en verde y el desplegable muestra
tres ejemplos. Deshaz el cambio al terminar o adapta el test que cuenta los
ejemplos.

## M4 — Tests (bloque 4)

Abre [`tests/test_examples.py`](../../../tests/test_examples.py).

1. Ejecuta `uv run pytest -q` y localiza el test que usa `dependency_overrides`.
> `test_dependency_override_simulates_unavailable_model`: sustituye `get_model` por un
> modelo con `ready = False` y comprueba que la API responde `503` con
> `error.code == "model_unavailable"`.
2. Elimina temporalmente `raise_server_exceptions=False` del fixture
   `errors_client` y vuelve a ejecutar. Explica qué cambia.
> Falla `test_unexpected_error_hides_secrets` (`1 failed, 9 passed`): `TestClient`
> relanza dentro del test el `RuntimeError("password=TU_SECRETO in /etc/app.conf")` de
> `/v1/boom` en vez de devolver la respuesta `500` que vería el cliente. Viene bien
> para depurar, pero así no se puede comprobar que el handler oculta el secreto.
> Restaurado después.
3. Escribe un test nuevo que compruebe que `income: 0` devuelve `422` con
   `fields[0].field == "income"`.
> Añadido en `tests/test_examples.py`:
```python
def test_zero_income_is_rejected(errors_client: TestClient) -> None:
    response = errors_client.post("/v1/scores", json={"age": 30, "income": 0})

    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["field"] == "income"
```
> `uv run pytest -q` -> `10 passed`.

**Comprobación:** la suite vuelve a estar en verde con tu test incluido.

La [solución comentada](../solution/README.md) se comparte al final de la clase.
