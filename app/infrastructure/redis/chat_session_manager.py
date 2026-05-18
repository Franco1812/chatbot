import re

from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.domain.entities.chat_turn import ChatTurn

# 24 horas — TTL aplicado por RedisChatMessageHistory al persistir mensajes
DEFAULT_SESSION_TTL_SECONDS = 24 * 60 * 60


class ChatSessionManager:
    """
    Gestiona sesiones de chat en Redis usando RedisChatMessageHistory.

    El identificador de sesión en Redis es el teléfono normalizado (solo dígitos,
    incluyendo prefijo internacional), para recuperar siempre el mismo historial
    por número de teléfono.
    """

    def __init__(
        self,
        *,
        redis_url: str,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        key_prefix: str = "chat_session:",
    ) -> None:
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    @staticmethod
    def session_id_from_phone(telefono: str) -> str:
        """Normaliza el teléfono a dígitos; ese valor es el ``session_id`` en Redis."""
        digits = re.sub(r"\D", "", (telefono or "").strip())
        if len(digits) < 8 or len(digits) > 16:
            raise ValueError(
                "Teléfono inválido: se esperan entre 8 y 16 dígitos (incluye código de país)."
            )
        return digits

    def get_message_history(self, telefono: str) -> RedisChatMessageHistory:
        """
        Devuelve ``RedisChatMessageHistory`` ligado a este teléfono (mismo ``session_id``).
        TTL de sesión: 24 horas por defecto (renovado al añadir mensajes).
        """
        session_id = self.session_id_from_phone(telefono)
        return RedisChatMessageHistory(
            session_id=session_id,
            url=self._redis_url,
            key_prefix=self._key_prefix,
            ttl=self._ttl_seconds,
        )

    @staticmethod
    def turns_from_history(history: RedisChatMessageHistory) -> list[ChatTurn]:
        """Convierte mensajes almacenados en Redis a turnos de dominio (usuario / asistente)."""
        return ChatSessionManager._messages_to_turns(history.messages)

    @staticmethod
    def _messages_to_turns(messages: list[BaseMessage]) -> list[ChatTurn]:
        turns: list[ChatTurn] = []
        for m in messages:
            if isinstance(m, HumanMessage):
                text = _string_content(m.content)
                if text:
                    turns.append(ChatTurn(role="user", content=text))
            elif isinstance(m, AIMessage):
                if getattr(m, "tool_calls", None):
                    continue
                text = _string_content(m.content)
                if text:
                    turns.append(ChatTurn(role="assistant", content=text))
        return turns

    @staticmethod
    def append_exchange(
        history: RedisChatMessageHistory,
        user_text: str,
        assistant_text: str,
    ) -> None:
        """Persiste el par usuario/asistente en Redis (y refresca el TTL de la clave)."""
        history.add_message(HumanMessage(content=user_text))
        history.add_message(AIMessage(content=assistant_text))


def _string_content(content: str | list[str | dict]) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
        return "".join(parts).strip()
    return ""
