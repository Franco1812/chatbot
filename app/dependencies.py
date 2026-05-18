from fastapi import HTTPException, Request, status

from app.application.use_cases.process_webhook import ProcessWebhookUseCase


def get_process_webhook_use_case(request: Request) -> ProcessWebhookUseCase:
    return ProcessWebhookUseCase(repository=request.app.state.webhook_repository)
