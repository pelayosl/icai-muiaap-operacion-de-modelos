import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir
from app.services.llm import LLMSimulado

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


# TODO: definir_tool() -> dict con la definicion de la tool, sacando "parameters" de PrestamoEntrada
def definir_tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": "Calcula la probabilidad de impago de un prestamo y devuelve decision",
            "parameters": PrestamoEntrada.model_json_schema(),
        }
    }
    
# TODO: ejecutar_tool(nombre, argumentos_json) -> dict con "ok" True/False
#       (tool desconocida, JSON roto, datos invalidos o campos inventados -> ok False con el error)

def ejecutar_tool(nombre, argumentos_json) -> dict:
    try:
        PrestamoEntrada.model_validate_json(argumentos_json)
    except ValueError:
        return {"ok": False}

    if(nombre != NOMBRE_TOOL):
        return {"ok": False}
    
    return {"ok": True}

# TODO: responder(mensajes, llm) -> ChatSalida, con el bucle LLM -> tool -> LLM (maximo MAX_VUELTAS)

def responder(mensajes: list, llm: LLMSimulado) -> ChatSalida:
    historial = []
    historial.append({"role": "system", "content": SISTEMA})

    for i in range(MAX_VUELTAS):
        historial.extend(mensajes)
        respuesta_llm = llm.completar(historial, [definir_tool()])
        if respuesta_llm.get("role") == "assistant" and respuesta_llm.get("content"):
            return ChatSalida(respuesta=respuesta_llm["content"])
        elif respuesta_llm.get("role") == "assistant" and respuesta_llm.get("tool_calls"):
            tool_call = respuesta_llm["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            resultado_tool = ejecutar_tool(tool_name, tool_args)
            mensajes.append({"role": "tool", "content": json.dumps(resultado_tool)})
        else:
            break
    return ChatSalida(respuesta="No he podido responder a tu solicitud. Por favor, inténtalo de nuevo más tarde.")
