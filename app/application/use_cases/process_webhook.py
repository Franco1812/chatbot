import logging
from uuid import UUID

from app.domain.entities.webhook_event import WebhookEvent, WebhookEventStatus
from app.domain.ports.webhook_repository import WebhookRepositoryPort

logger = logging.getLogger(__name__)


class ProcessWebhookUseCase:
    """Orquesta el procesamiento de un webhook tras ser aceptado por la capa HTTP."""

    def __init__(self, repository: WebhookRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, event: WebhookEvent) -> None:
        correlation = event.correlation_id
        try:
            event.status = WebhookEventStatus.PROCESSING
            await self._repository.save(event)
            await self._handle_side_effects(event)
            event.status = WebhookEventStatus.PROCESSED
            await self._repository.save(event)
            logger.info("Webhook procesado: correlation_id=%s", correlation)
        except Exception:
            logger.exception("Fallo al procesar webhook: correlation_id=%s", correlation)
            event.status = WebhookEventStatus.FAILED
            await self._repository.save(event)
            raise

    async def _handle_side_effects(self, event: WebhookEvent) -> None:
        """Sustituir por integraciones reales (colas, HTTP downstream, etc.)."""
        _ = event.event_type, event.payload
