"""Liveness and readiness endpoints.

Live outside `/api/v1` on purpose: they report process health, not a domain
resource, so they should stay at stable URLs across API versions.

Two endpoints, not one: an orchestrator restarts the container when liveness
fails, and only stops routing traffic to it when readiness fails. So only
readiness may depend on the database — otherwise a network blip to PostgreSQL
would restart a perfectly healthy process.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.version,
        environment=settings.environment,
    )


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness probe")
def ready(db: Annotated[Session, Depends(get_db)], response: Response) -> ReadinessResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # The cause goes to the log, not the body: a probe only needs the status,
        # and an unauthenticated endpoint should not describe the database.
        logger.exception("Readiness check failed: database unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="unavailable")
    return ReadinessResponse(status="ok")
