FROM python:3.12-slim

# uv para instalar exactamente lo que fija uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# 1) Dependencias primero: esta capa se cachea mientras no cambie el lock
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

# 2) Código y modelo
COPY app ./app
COPY frontend ./frontend
COPY models ./models

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
