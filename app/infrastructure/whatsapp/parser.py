from dataclasses import dataclass


@dataclass
class IncomingWhatsAppMessage:
    phone_number_id: str
    from_phone: str
    message_id: str
    text: str


def parse_whatsapp_webhook(payload: dict) -> list[IncomingWhatsAppMessage]:
    """Extrae mensajes de texto del payload que envía Meta al webhook."""
    results: list[IncomingWhatsAppMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id", "")
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                text = msg.get("text", {}).get("body", "").strip()
                if not text:
                    continue
                results.append(
                    IncomingWhatsAppMessage(
                        phone_number_id=phone_number_id,
                        from_phone=msg.get("from", ""),
                        message_id=msg.get("id", ""),
                        text=text,
                    )
                )
    return results
