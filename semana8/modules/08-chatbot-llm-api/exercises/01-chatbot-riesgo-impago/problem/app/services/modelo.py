import joblib

from app.config import MODEL_PATH
from app.schemas.prestamo import PrediccionSalida

# Orden en el que el modelo espera las variables
VARIABLES = [
    "edad",
    "ingresos_mensuales",
    "importe_prestamo",
    "plazo_meses",
    "antiguedad_laboral_anios",
    "impagos_previos",
]

# TODO: cargar el modelo joblib una sola vez, al importar el modulo
# TODO: funcion decidir(probabilidad) -> "aprobar", "revisar" o "rechazar" (umbrales en el enunciado)
def decidir(probabilidad: float) -> str:
    if probabilidad < 0.2:
        return "aprobar"
    if probabilidad < 0.5:
        return "revisar"
    return "rechazar"

# TODO: funcion predecir(entrada) -> PrediccionSalida, usando VARIABLES para ordenar los valores
def predecir(entrada):
    model = joblib.load(MODEL_PATH)
    input_values = [getattr(entrada, var) for var in VARIABLES]

    if len(input_values) != len(VARIABLES):
        raise ValueError(f"Se esperaban {len(VARIABLES)} variables, pero se recibieron {len(input_values)}")

    probabilidad_impago = model.predict_proba([input_values])[0][1]
    decision = decidir(probabilidad_impago)

    return PrediccionSalida(probabilidad_impago=probabilidad_impago, decision=decision)

