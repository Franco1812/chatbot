from typing import Protocol
from uuid import UUID

from app.domain.entities.webhook_event import WebhookEvent


class WebhookRepositoryPort(Protocol):
    """Puerto de salida: persistencia de eventos de webhook (implementado en infraestructura)."""

    async def save(self, event: WebhookEvent) -> None: ...

    async def get_by_correlation_id(self, correlation_id: UUID) -> WebhookEvent | None: ...
