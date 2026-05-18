from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Endpoint de prueba directo. En producción el flujo pasa por WhatsApp."""

    phone_number_id: str = Field(
        ...,
        description="ID del número WA de la tienda (identifica el tenant).",
        examples=["123456789012345"],
    )
    telefono: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="Teléfono del usuario. Se usa como clave de sesión en Redis.",
        examples=["+34600111222"],
    )
    mensaje: str = Field(..., min_length=1, max_length=32_000, description="Nuevo mensaje del usuario.")


class ChatResponse(BaseModel):
    reply: str
