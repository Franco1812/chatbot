import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.application.use_cases.chat_with_sales_agent import ChatWithSalesAgentUseCase
from app.presentation.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """Endpoint de prueba: simula el flujo de WhatsApp sin pasar por Meta."""
    runtime = request.app.state.tenant_runtimes.get(body.phone_number_id)
    if runtime is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tienda con phone_number_id '{body.phone_number_id}' no encontrada.",
        )
    session_manager = request.app.state.chat_session_manager
    if session_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="REDIS_URL no configurada; se requiere Redis para el historial de sesión.",
        )
    use_case = ChatWithSalesAgentUseCase(
        conversation=runtime["conversation"],
        session_manager=session_manager,
    )
    try:
        reply = await use_case.execute(body.telefono, body.mensaje)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ChatResponse(reply=reply)
