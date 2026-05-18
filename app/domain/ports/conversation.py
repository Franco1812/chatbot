from typing import Protocol

from app.domain.entities.chat_turn import ChatTurn


class SalesConversationPort(Protocol):
    """Puerto: conversación con agente de ventas."""

    async def complete(self, turns: list[ChatTurn]) -> str: ...
