import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.adapters.in_memory_webhook_repository import InMemoryWebhookRepository
from app.infrastructure.config.settings import Settings
from app.infrastructure.langchain.sales_conversation_service import LangChainSalesConversationService
from app.infrastructure.redis.chat_session_manager import ChatSessionManager
from app.presentation.api.chat import router as chat_router
from app.presentation.api.health import router as health_router
from app.presentation.api.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.background_tasks = set()
    app.state.webhook_repository = InMemoryWebhookRepository()
    settings = Settings()
    key = (settings.openai_api_key or "").strip()
    app.state.sales_conversation = (
        LangChainSalesConversationService(api_key=key) if key else None
    )
    redis_url = (settings.redis_url or "").strip()
    if redis_url:
        app.state.chat_session_manager = ChatSessionManager(redis_url=redis_url)
    else:
        app.state.chat_session_manager = None
    yield
    pending = {t for t in app.state.background_tasks if not t.done()}
    for t in pending:
        t.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def create_app() -> FastAPI:
    application = FastAPI(title="Clean Architecture Webhooks", lifespan=lifespan)
    application.include_router(health_router)
    application.include_router(webhooks_router)
    application.include_router(chat_router)
    return application
