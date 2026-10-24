from fastapi import APIRouter, Depends

from app.schemas.chat import ChatEntrada, ChatSalida
from app.services.llm import get_llm
from app.services.orquestador import responder

router = APIRouter()


# TODO: POST /chat (entrada ChatEntrada, salida ChatSalida). Recibe el LLM con Depends(get_llm)
@router.post("/chat")
def chat(
    entrada: ChatEntrada,
    llm = Depends(get_llm) # (Dependency Injection) Evitamos que el router
                           # cree los recursos, se delega a los servicios.
    ) -> ChatSalida:
    return responder(entrada.mensajes, llm)