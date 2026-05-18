from fastapi import HTTPException, Request, status

from app.application.use_cases.chat_with_sales_agent import ChatWithSalesAgentUseCase
from app.application.use_cases.process_webhook import ProcessWebhookUseCase


def get_process_webhook_use_case(request: Request) -> ProcessWebhookUseCase:
    repository = request.app.state.webhook_repository
    return ProcessWebhookUseCase(repository=repository)


def get_chat_with_sales_agent_use_case(request: Request) -> ChatWithSalesAgentUseCase:
    conversation = getattr(request.app.state, "sales_conversation", None)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY no configurada; define la variable de entorno para usar /chat.",
        )
    session_manager = getattr(request.app.state, "chat_session_manager", None)
    if session_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="REDIS_URL no configurada; se requiere Redis para el historial de sesión.",
        )
    return ChatWithSalesAgentUseCase(
        conversation=conversation,
        session_manager=session_manager,
    )
