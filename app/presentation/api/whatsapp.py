import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.infrastructure.whatsapp.parser import parse_whatsapp_webhook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])


@router.get("/")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
) -> int:
    """Meta llama a este endpoint para verificar que el webhook es nuestro."""
    if hub_mode == "subscribe" and hub_verify_token == request.app.state.webhook_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token de verificación inválido.")


@router.post("/", status_code=status.HTTP_200_OK)
async def receive_message(request: Request, body: dict[str, Any]) -> dict[str, str]:
    """Recibe mensajes entrantes de WhatsApp y los despacha al agente de ventas."""
    messages = parse_whatsapp_webhook(body)
    tenant_runtimes: dict = request.app.state.tenant_runtimes
    use_case = request.app.state.handle_whatsapp_use_case

    for msg in messages:
        runtime = tenant_runtimes.get(msg.phone_number_id)
        if runtime is None:
            logger.warning("Webhook para phone_number_id desconocido: %s", msg.phone_number_id)
            continue

        task = asyncio.create_task(
            use_case.execute(
                tenant=runtime["tenant"],
                conversation=runtime["conversation"],
                from_phone=msg.from_phone,
                text=msg.text,
            ),
            name=f"wa:{msg.message_id}",
        )
        request.app.state.background_tasks.add(task)

        def _discard(t: asyncio.Task, mid: str = msg.message_id) -> None:
            request.app.state.background_tasks.discard(t)
            try:
                t.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Error procesando mensaje WA %s", mid)

        task.add_done_callback(_discard)

    return {"status": "ok"}
