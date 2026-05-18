import json
import uuid
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# Inventario simulado (sustituir por API real en otro adaptador)
_MOCK_STOCK: dict[str, int] = {
    "SKU-001": 120,
    "SKU-002": 0,
    "SKU-DEMO": 50,
}


class ConsultarStockInput(BaseModel):
    """Argumentos validados con Pydantic v2 para la herramienta consultar_stock."""

    sku: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Identificador del producto en almacén (ej. SKU-001).",
    )
    cantidad_solicitada: int = Field(
        default=1,
        ge=1,
        le=10_000,
        description="Unidades que el cliente desea comprar.",
    )


class CrearOrdenPagoInput(BaseModel):
    """Argumentos validados con Pydantic v2 para la herramienta crear_orden_pago."""

    sku: str = Field(..., min_length=1, max_length=64, description="SKU incluido en la orden.")
    cantidad: int = Field(..., ge=1, le=10_000, description="Unidades a cobrar.")
    metodo_pago: str = Field(
        ...,
        min_length=2,
        max_length=32,
        description="Método de pago acordado (ej. tarjeta, transferencia, bizum).",
    )
    email_cliente: str | None = Field(
        default=None,
        max_length=254,
        description="Email del cliente para el comprobante (opcional).",
    )


def _consultar_stock(sku: str, cantidad_solicitada: int) -> str:
    sku_key = sku.strip().upper()
    disponibles = _MOCK_STOCK.get(sku_key)
    if disponibles is None:
        payload: dict[str, Any] = {
            "sku": sku_key,
            "encontrado": False,
            "mensaje": "SKU no catalogado. Pregunta al cliente por otro código o ofrece alternativas.",
        }
    else:
        suficiente = disponibles >= cantidad_solicitada
        payload = {
            "sku": sku_key,
            "encontrado": True,
            "unidades_disponibles": disponibles,
            "cantidad_solicitada": cantidad_solicitada,
            "puede_servir": suficiente,
            "mensaje": "Stock suficiente." if suficiente else "Stock insuficiente; propón cantidad menor o reserva.",
        }
    return json.dumps(payload, ensure_ascii=False)


def _crear_orden_pago(sku: str, cantidad: int, metodo_pago: str, email_cliente: str | None) -> str:
    sku_key = sku.strip().upper()
    disponibles = _MOCK_STOCK.get(sku_key)
    if disponibles is None:
        return json.dumps(
            {
                "ok": False,
                "error": "SKU desconocido; usa consultar_stock antes de crear la orden.",
            },
            ensure_ascii=False,
        )
    if disponibles < cantidad:
        return json.dumps(
            {
                "ok": False,
                "error": "No hay stock suficiente para esta cantidad.",
                "unidades_disponibles": disponibles,
            },
            ensure_ascii=False,
        )
    orden_id = str(uuid.uuid4())
    return json.dumps(
        {
            "ok": True,
            "orden_id": orden_id,
            "sku": sku_key,
            "cantidad": cantidad,
            "metodo_pago": metodo_pago,
            "email_cliente": email_cliente,
            "mensaje": "Orden registrada; confirma al cliente total y plazo de entrega.",
        },
        ensure_ascii=False,
    )


def build_sales_tools() -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            name="consultar_stock",
            description=(
                "Consulta disponibilidad en almacén para un SKU y una cantidad. "
                "Úsala cuando el cliente pregunte por existencias, tallas, unidades o si hay producto."
            ),
            func=_consultar_stock,
            args_schema=ConsultarStockInput,
        ),
        StructuredTool.from_function(
            name="crear_orden_pago",
            description=(
                "Crea una orden de pago/venta cuando el cliente confirme compra, cantidad y método de pago. "
                "Antes conviene haber consultado stock si había dudas de disponibilidad."
            ),
            func=_crear_orden_pago,
            args_schema=CrearOrdenPagoInput,
        ),
    ]
