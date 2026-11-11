# Práctica 8 - Chatbot de riesgo (FastAPI + LLM + modelo)

```
app/
  main.py               crea la API y registra los routers
  config.py             ajustes (ruta del modelo)
  routers/              endpoints: health.py, predict.py, chat.py
  schemas/              contratos Pydantic: prestamo.py, chat.py
  services/             logica: modelo.py, orquestador.py, llm.py
frontend/               app.py (Streamlit) y logo.png
models/                 modelo_impago.joblib
scripts/                entrenar_modelo.py (regenera el joblib)
tests/                  tests con pytest
pyproject.toml
```

## Arrancar

```
uv sync
uv run uvicorn app.main:app --port 8000        # backend
uv run streamlit run frontend/app.py           # frontend (otra terminal)
uv run pytest                                  # tests
```

Sin configurar nada usa un LLM simulado. Para un LLM real (LiteLLM), por ejemplo Azure OpenAI:

```
export LLM_MODEL=azure/<nombre-del-deployment>
export AZURE_API_KEY=...
export AZURE_API_BASE=https://<recurso>.openai.azure.com
export AZURE_API_VERSION=...
```

## Arrancar con Docker (extra opcional)

```
docker compose up -d --build
```

- `api`: FastAPI en http://localhost:8000 (imagen con las dependencias de `uv.lock`).
- `streamlit`: frontend en http://localhost:8501; llega a la API por la red de compose (`API_URL=http://api:8000`) y espera a que `api` esté sana (`/health`).

Sin `LLM_MODEL` usa el LLM simulado. Las variables `LLM_MODEL` y `AZURE_*` del entorno se pasan a `api`. Para pararlo: `docker compose down`.
