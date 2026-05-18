from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.chat_with_sales_agent import ChatWithSalesAgentUseCase
from app.dependencies import get_chat_with_sales_agent_use_case
from app.presentation.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    use_case: ChatWithSalesAgentUseCase = Depends(get_chat_with_sales_agent_use_case),
) -> ChatResponse:
    try:
        reply = await use_case.execute(body.telefono, body.mensaje)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ChatResponse(reply=reply)
