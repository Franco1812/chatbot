from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WebhookIngestRequest(BaseModel):
    """Entrada HTTP validada con Pydantic v2."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    source: str = Field(..., min_length=1, max_length=128, examples=["stripe"])
    event_type: str = Field(..., min_length=1, max_length=256, examples=["payment_intent.succeeded"])
    data: dict[str, Any] = Field(default_factory=dict)


class WebhookIngestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    correlation_id: UUID
    accepted: bool = True
    message: str = "accepted for async processing"
