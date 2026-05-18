from collections.abc import MutableMapping
from uuid import UUID

from app.domain.entities.webhook_event import WebhookEvent
from app.domain.ports.webhook_repository import WebhookRepositoryPort


class InMemoryWebhookRepository(WebhookRepositoryPort):
    """Adaptador de persistencia en memoria (útil para desarrollo y tests)."""

    def __init__(self) -> None:
        self._by_correlation: MutableMapping[UUID, WebhookEvent] = {}

    async def save(self, event: WebhookEvent) -> None:
        self._by_correlation[event.correlation_id] = event

    async def get_by_correlation_id(self, correlation_id: UUID) -> WebhookEvent | None:
        return self._by_correlation.get(correlation_id)
