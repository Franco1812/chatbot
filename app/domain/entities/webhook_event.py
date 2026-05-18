from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class WebhookEventStatus(StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass(slots=True)
class WebhookEvent:
    """Entidad de dominio: evento entrante desde un proveedor externo."""

    correlation_id: UUID
    source: str
    event_type: str
    payload: dict
    status: WebhookEventStatus = WebhookEventStatus.RECEIVED
    id: UUID = field(default_factory=uuid4)
    received_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None
