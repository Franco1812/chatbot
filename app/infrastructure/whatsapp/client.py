import logging

import httpx

logger = logging.getLogger(__name__)

_WA_API_VERSION = "v20.0"
_WA_BASE_URL = f"https://graph.facebook.com/{_WA_API_VERSION}"


async def send_whatsapp_text(
    *,
    phone_number_id: str,
    waba_token: str,
    to: str,
    text: str,
) -> None:
    url = f"{_WA_BASE_URL}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {waba_token}", "Content-Type": "application/json"}
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=body, headers=headers)
        response.raise_for_status()
        logger.info("Mensaje WA enviado a %s via phone_number_id=%s", to, phone_number_id)
