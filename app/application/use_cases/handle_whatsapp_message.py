import asyncio
import logging

from app.domain.entities.chat_turn import ChatTurn
from app.domain.entities.tenant import Tenant
from app.domain.ports.conversation import SalesConversationPort
from app.infrastructure.redis.chat_session_manager import ChatSessionManager
from app.infrastructure.whatsapp.client import send_whatsapp_text

logger = logging.getLogger(__name__)


class HandleWhatsAppMessageUseCase:
    def __init__(self, session_manager: ChatSessionManager) -> None:
        self._session_manager = session_manager

    async def execute(
        self,
        *,
        tenant: Tenant,
        conversation: SalesConversationPort,
        from_phone: str,
        text: str,
    ) -> None:
        history = self._session_manager.get_message_history(from_phone)
        turns = self._session_manager.turns_from_history(history)
        turns.append(ChatTurn(role="user", content=text))

        reply = await conversation.complete(turns)

        await asyncio.to_thread(ChatSessionManager.append_exchange, history, text, reply)

        await send_whatsapp_text(
            phone_number_id=tenant.phone_number_id,
            waba_token=tenant.waba_token,
            to=from_phone,
            text=reply,
        )
