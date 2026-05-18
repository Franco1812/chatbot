import json
import uuid
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.domain.entities.tenant import CatalogItem


class ConsultarStockInput(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64, description="Identificador del producto (ej. SKU-001).")
    cantidad_solicitada: int = Field(default=1, ge=1, le=10_000, description="Unidades que el cliente desea comprar.")


class CrearOrdenPagoInput(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64, description="SKU incluido en la orden.")
    cantidad: int = Field(..., ge=1, le=10_000, description="Unidades a cobrar.")
    metodo_pago: str = Field(..., min_length=2, max_length=32, description="Método de pago acordado.")
    email_cliente: str | None = Field(default=None, max_length=254, description="Email del cliente (opcional).")


def build_sales_tools(catalog: dict[str, CatalogItem]) -> list[StructuredTool]:
    def _consultar_stock(sku: str, cantidad_solicitada: int) -> str:
        sku_key = sku.strip().upper()
        item = catalog.get(sku_key)
        if item is None:
            payload: dict[str, Any] = {
                "sku": sku_key,
                "encontrado": False,
                "mensaje": "SKU no catalogado. Pregunta al cliente por otro código o ofrece alternativas.",
            }
        else:
            suficiente = item.stock >= cantidad_solicitada
            payload = {
                "sku": sku_key,
                "encontrado": True,
                "nombre": item.name,
                "unidades_disponibles": item.stock,
                "cantidad_solicitada": cantidad_solicitada,
                "puede_servir": suficiente,
                "mensaje": "Stock suficiente." if suficiente else "Stock insuficiente; propón cantidad menor o reserva.",
            }
        return json.dumps(payload, ensure_ascii=False)

    def _crear_orden_pago(sku: str, cantidad: int, metodo_pago: str, email_cliente: str | None) -> str:
        sku_key = sku.strip().upper()
        item = catalog.get(sku_key)
        if item is None:
            return json.dumps(
                {"ok": False, "error": "SKU desconocido; usa consultar_stock antes de crear la orden."},
                ensure_ascii=False,
            )
        if item.stock < cantidad:
            return json.dumps(
                {"ok": False, "error": "No hay stock suficiente.", "unidades_disponibles": item.stock},
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "ok": True,
                "orden_id": str(uuid.uuid4()),
                "sku": sku_key,
                "nombre": item.name,
                "cantidad": cantidad,
                "metodo_pago": metodo_pago,
                "email_cliente": email_cliente,
                "mensaje": "Orden registrada; confirma al cliente total y plazo de entrega.",
            },
            ensure_ascii=False,
        )

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
