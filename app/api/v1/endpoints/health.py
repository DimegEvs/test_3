import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
