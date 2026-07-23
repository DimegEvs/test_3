import logging

from app.integrations.catalog_client import CatalogClient, DownloadState
from app.services import StatsService

logger = logging.getLogger(__name__)


class DownloadHandler:
    def __init__(self) -> None:
        self._state = DownloadState()

    @property
    def state(self) -> DownloadState:
        return self._state

    async def run(self) -> DownloadState:
        client = CatalogClient(self._state)
        self._state.status = "running"
        self._state.error_message = ""
        self._state.total_attempted = 0
        self._state.total_downloaded = 0
        self._state.total_marked = 0
        self._state.requests_made = 0
        self._state.errors = 0
        processed: set[str] = set()

        try:
            while True:
                names = await client.fetch_names()
                if names is None:
                    continue

                new_names = [n for n in names if n not in processed]
                if not new_names:
                    self._state.status = "done"
                    return self._state

                self._state.total_attempted += len(new_names)
                processed.update(new_names)

                for i in range(0, len(new_names), 3):
                    batch = new_names[i : i + 3]
                    try:
                        extracted = await client.download_files(batch)
                        self._state.total_downloaded += extracted or 0
                    except Exception:
                        self._state.errors += 1

                try:
                    result = await client.mark_downloaded(new_names)
                    if result:
                        self._state.total_marked += result.get("marked_now", 0)
                except Exception:
                    pass

                stats = StatsService.compute()
                logger.info(
                    "Прогресс: скачано=%d, отмечено=%d, файлов на диске=%d",
                    self._state.total_downloaded,
                    self._state.total_marked,
                    stats.total_files,
                )

        except Exception as exc:
            self._state.status = "error"
            self._state.error_message = str(exc)
            logger.exception("Ошибка загрузки")

        return self._state
