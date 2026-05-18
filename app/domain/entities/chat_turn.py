from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    """Un turno de conversación (usuario o asistente)."""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=32_000)
