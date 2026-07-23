import logging

from fastapi import APIRouter

from app.api.v1.endpoints.download import _get_handler
from app.config import settings
from app.schemas.state import StateResponse
from app.services import StatsService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["state"])


@router.get("/state", response_model=StateResponse)
async def get_state() -> StateResponse:
    handler = _get_handler()
    s = handler.state

    stats = None
    download_path = settings.download_path
    if download_path.exists():
        stats = StatsService.compute(download_path)

    return StateResponse(
        status=s.status,
        total_attempted=s.total_attempted,
        total_downloaded=s.total_downloaded,
        total_marked=s.total_marked,
        requests_made=s.requests_made,
        errors=s.errors,
        error_message=s.error_message,
        stats=stats,
    )
