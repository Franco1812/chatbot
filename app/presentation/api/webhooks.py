import asyncio
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, status

from app.application.use_cases.process_webhook import ProcessWebhookUseCase
from app.dependencies import get_process_webhook_use_case
from app.domain.entities.webhook_event import WebhookEvent, WebhookEventStatus
from app.presentation.schemas.webhook import WebhookIngestRequest, WebhookIngestResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _schedule_webhook_processing(
    request: Request,
    correlation_id: UUID,
    body: WebhookIngestRequest,
    use_case: ProcessWebhookUseCase,
) -> None:
    event = WebhookEvent(
        correlation_id=correlation_id,
        source=body.source,
        event_type=body.event_type,
        payload={"data": body.data, "raw_model_dump": body.model_dump()},
        status=WebhookEventStatus.RECEIVED,
    )

    async def _run() -> None:
        await use_case.execute(event)

    task = asyncio.create_task(_run(), name=f"webhook:{correlation_id}")
    request.app.state.background_tasks.add(task)

    def _discard(t: asyncio.Task[None]) -> None:
        request.app.state.background_tasks.discard(t)
        try:
            t.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Tarea de webhook finalizó con error")

    task.add_done_callback(_discard)


@router.post(
    "/ingest",
    response_model=WebhookIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_webhook(
    request: Request,
    body: WebhookIngestRequest,
    use_case: ProcessWebhookUseCase = Depends(get_process_webhook_use_case),
) -> WebhookIngestResponse:
    correlation_id = uuid4()
    _schedule_webhook_processing(request, correlation_id, body, use_case)
    return WebhookIngestResponse(correlation_id=correlation_id)
