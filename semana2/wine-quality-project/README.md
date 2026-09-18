# Assignment 2.2 -> Wine Quality

Proyecto reproducible para entrenar un modelo de clasificación sobre el dataset Wine Quality.

## Rama de trabajo

La práctica se realizó en una rama independiente de `main`:

```bash
git switch -c feature/s2-wine-project
```

## Instalación
Desde la raíz del repositorio se inicializó el proyecto con uv:

```bash
uv init --package --vcs none --name wine-quality semana2/wine-quality-project
cd semana2/wine-quality-project
```

Se instalaron las dependencias de ejecución:

```bash
uv add pandas scikit-learn
```

Y las dependencias de desarrollo:

```bash
uv add --dev pytest ruff
```

Finalmente, se generó el archivo de bloqueo y se sincronizó el entorno:

```bash
uv lock
uv sync --locked
```

## Estructura

```
wine-quality-project/
├── data/
│   └── raw/
│       └── WineQT.csv
├── src/
│   └── wine_quality/
│       ├── __init__.py
│       └── train.py
├── tests/
│   └── test_train.py
├── pyproject.toml
├── uv.lock
└── README.md
```
Adicionalmente, tanto /tests como /wine_quality cuentan con un archivo __init__.py.

## Migración

Los archivos iniciales se copiaron a los siguientes destinos:

```
WineQT.csv → data/raw/WineQT.csv
train.py → src/wine_quality/train.py
test_train.py → tests/test_train.py
```

También se ajustaron las rutas del dataset y los imports para adaptarlos a la estructura src.

El import utilizado en los tests es:

```bash
from src.wine_quality.train import FEATURES, load_dataset, train_and_evaluate
```

## Ejecución del entrenamiento
El entrenamiento se ejecuta como módulo del paquete:

```bash
uv run python -m wine_quality.train
```
## Comprobaciones
Para ejecutar los tests:

```bash
uv run pytest
```

Para comprobar la calidad del código:
```bash
uv run ruff check .
uv run ruff format --check .
```

La instalación puede verificarse usando exclusivamente las dependencias bloqueadas:

```bash
uv sync --locked
```


