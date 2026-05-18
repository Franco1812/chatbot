from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """El historial se carga y guarda en Redis por ``telefono`` (session_id normalizado a dígitos)."""

    telefono: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="Teléfono del usuario (ej. +34 600 111 222). Se usa como clave de sesión en Redis.",
        examples=["+34600111222"],
    )
    mensaje: str = Field(..., min_length=1, max_length=32_000, description="Nuevo mensaje del usuario.")


class ChatResponse(BaseModel):
    reply: str
