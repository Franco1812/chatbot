import logging
from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.domain.entities.chat_turn import ChatTurn
from app.domain.entities.tenant import CatalogItem
from app.domain.ports.conversation import SalesConversationPort

logger = logging.getLogger(__name__)


class LangChainSalesConversationService(SalesConversationPort):
    def __init__(
        self,
        *,
        api_key: str,
        system_prompt: str,
        catalog: dict[str, CatalogItem],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        tool_executor: Callable[[BaseTool, dict], str] | None = None,
    ) -> None:
        self._system_prompt = system_prompt
        self._llm = ChatOpenAI(model=model, api_key=api_key, temperature=temperature)
        self._tools = self._build_tools(catalog)
        self._tool_by_name = {t.name: t for t in self._tools}
        self._llm_with_tools = self._llm.bind_tools(self._tools)
        self._tool_executor = tool_executor or self._default_tool_invoke
        self._max_tool_rounds = 8

    @staticmethod
    def _build_tools(catalog: dict[str, CatalogItem]) -> list[BaseTool]:
        from app.infrastructure.langchain.sales_tools import build_sales_tools
        return build_sales_tools(catalog)

    @staticmethod
    def _default_tool_invoke(tool: BaseTool, args: dict) -> str:
        return tool.invoke(args)

    @staticmethod
    def _turns_to_lc_messages(turns: list[ChatTurn]) -> list[BaseMessage]:
        out: list[BaseMessage] = []
        for t in turns:
            if t.role == "user":
                out.append(HumanMessage(content=t.content))
            else:
                out.append(AIMessage(content=t.content))
        return out

    async def complete(self, turns: list[ChatTurn]) -> str:
        llm_messages: list[BaseMessage] = [SystemMessage(content=self._system_prompt)]
        llm_messages.extend(self._turns_to_lc_messages(turns))

        for _ in range(self._max_tool_rounds):
            ai = await self._llm_with_tools.ainvoke(llm_messages)
            if not isinstance(ai, AIMessage):
                ai = AIMessage(content=str(getattr(ai, "content", ai)))
            llm_messages.append(ai)

            tool_calls = getattr(ai, "tool_calls", None) or []
            if not tool_calls:
                text = (str(ai.content) if ai.content is not None else "").strip()
                return text or "(Sin respuesta textual del modelo.)"

            for call in tool_calls:
                name = call["name"]
                args = call.get("args") or {}
                tool_call_id = call["id"]
                tool = self._tool_by_name.get(name)
                if tool is None:
                    logger.warning("Tool desconocida solicitada por el modelo: %s", name)
                    payload = f'{{"error": "herramienta desconocida: {name}"}}'
                    llm_messages.append(ToolMessage(content=payload, tool_call_id=tool_call_id, name=name))
                    continue
                try:
                    result = self._tool_executor(tool, args)
                except Exception:
                    logger.exception("Error ejecutando herramienta %s", name)
                    result = '{"ok": false, "error": "fallo interno al ejecutar la herramienta"}'
                llm_messages.append(ToolMessage(content=result, tool_call_id=tool_call_id, name=name))

        logger.warning("Límite de rondas de herramientas alcanzado")
        final = await self._llm.ainvoke(llm_messages)
        content = getattr(final, "content", "") or ""
        return str(content).strip() or "No pude completar la operación; intenta de nuevo."
