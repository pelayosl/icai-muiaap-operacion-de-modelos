# Wine Quality S5 02 - ejecución y límites

## Bundle

La app solo funciona con un bundle de S4 real. La ruta de `MODEL_UI_BUNDLE` debe ser un directorio (no el `.joblib`) con:

- `manifest.json`
- `model.joblib`

El bundle no se publica en el repositorio (`models/` está en `.gitignore`).

## Arranque

Desde `semana5/modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/problem/starter`:

```powershell
uv sync
$env:MODEL_UI_BUNDLE = 'models/wine_quality_bundle_s4'
uv run python -m pytest -q
uv run ruff check app.py src tests
uv run ruff format --check app.py src tests
uv run --with 'streamlit>=1.40,<2.0' streamlit run app.py
```

Sin `MODEL_UI_BUNDLE` o con un bundle inválido, la app muestra un error seguro con la instrucción de configurarlo, sin rutas ni traceback.

## Límites (se abordan en S6)

- Sin `session_state`: no se conserva el estado entre interacciones.
- Sin caché: el bundle se recarga en cada rerun.
- Sin FSM, telemetría ni persistencia.
