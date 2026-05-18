import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.application.use_cases.handle_whatsapp_message import HandleWhatsAppMessageUseCase
from app.infrastructure.adapters.in_memory_webhook_repository import InMemoryWebhookRepository
from app.infrastructure.adapters.json_tenant_repository import JsonTenantRepository
from app.infrastructure.config.settings import Settings
from app.infrastructure.langchain.sales_conversation_service import LangChainSalesConversationService
from app.infrastructure.redis.chat_session_manager import ChatSessionManager
from app.presentation.api.chat import router as chat_router
from app.presentation.api.health import router as health_router
from app.presentation.api.webhooks import router as webhooks_router
from app.presentation.api.whatsapp import router as whatsapp_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()

    app.state.background_tasks: set = set()
    app.state.webhook_repository = InMemoryWebhookRepository()
    app.state.webhook_verify_token = settings.webhook_verify_token

    # Redis para historial de sesiones
    redis_url = (settings.redis_url or "").strip()
    app.state.chat_session_manager = ChatSessionManager(redis_url=redis_url) if redis_url else None

    # Cargar tenants y crear una instancia del agente por tienda
    openai_key = (settings.openai_api_key or "").strip()
    tenants_path = Path(settings.tenants_file)
    tenant_runtimes: dict[str, dict] = {}

    if tenants_path.exists():
        repo = JsonTenantRepository(tenants_path)
        for tenant in repo.list_all():
            if not openai_key:
                logger.warning("Tenant %s cargado pero OPENAI_API_KEY no está configurada.", tenant.id)
                conversation = None
            else:
                conversation = LangChainSalesConversationService(
                    api_key=openai_key,
                    system_prompt=tenant.system_prompt,
                    catalog=tenant.catalog,
                )
            tenant_runtimes[tenant.phone_number_id] = {
                "tenant": tenant,
                "conversation": conversation,
            }
            logger.info("Tenant cargado: %s (phone_number_id=%s)", tenant.store_name, tenant.phone_number_id)
    else:
        logger.warning("Archivo de tenants no encontrado: %s", tenants_path)

    app.state.tenant_runtimes = tenant_runtimes

    # Use case de WhatsApp (compartido, stateless excepto por session_manager)
    app.state.handle_whatsapp_use_case = (
        HandleWhatsAppMessageUseCase(session_manager=app.state.chat_session_manager)
        if app.state.chat_session_manager
        else None
    )

    yield

    # Cancelar tareas pendientes al apagar
    pending = {t for t in app.state.background_tasks if not t.done()}
    for t in pending:
        t.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def create_app() -> FastAPI:
    application = FastAPI(title="Chatbot de Ventas — WhatsApp SaaS", lifespan=lifespan)
    application.include_router(health_router)
    application.include_router(webhooks_router)
    application.include_router(whatsapp_router)
    application.include_router(chat_router)
    return application
