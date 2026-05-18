import asyncio

from app.domain.entities.chat_turn import ChatTurn
from app.domain.ports.conversation import SalesConversationPort
from app.infrastructure.redis.chat_session_manager import ChatSessionManager


class ChatWithSalesAgentUseCase:
    def __init__(
        self,
        conversation: SalesConversationPort,
        session_manager: ChatSessionManager,
    ) -> None:
        self._conversation = conversation
        self._session_manager = session_manager

    async def execute(self, telefono: str, mensaje: str) -> str:
        if not mensaje.strip():
            raise ValueError("El mensaje no puede estar vacío.")

        history = self._session_manager.get_message_history(telefono)
        turns = self._session_manager.turns_from_history(history)
        turns.append(ChatTurn(role="user", content=mensaje.strip()))

        reply = await self._conversation.complete(turns)

        await asyncio.to_thread(
            ChatSessionManager.append_exchange,
            history,
            mensaje.strip(),
            reply,
        )
        return reply
