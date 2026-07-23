import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Request

from app.handlers.download_handler import DownloadHandler
from app.schemas.health import DownloadStartResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["download"])

_download_lock = asyncio.Lock()
_handler: DownloadHandler | None = None


def _get_handler() -> DownloadHandler:
    global _handler
    if _handler is None:
        _handler = DownloadHandler()
    return _handler


@router.post("/download-all", response_model=DownloadStartResponse)
async def start_download(background_tasks: BackgroundTasks) -> DownloadStartResponse:
    if _download_lock.locked():
        return DownloadStartResponse(started=False, message="Загрузка уже идёт")

    handler = _get_handler()
    background_tasks.add_task(_run_download, handler)
    return DownloadStartResponse(started=True)


async def _run_download(handler: DownloadHandler) -> None:
    if _download_lock.locked():
        return
    async with _download_lock:
        await handler.run()
