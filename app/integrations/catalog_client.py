from __future__ import annotations

import asyncio
import io
import logging
import os
import zipfile
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DownloadState:
    total_attempted: int = 0
    total_downloaded: int = 0
    total_marked: int = 0
    requests_made: int = 0
    errors: int = 0
    status: str = "idle"
    error_message: str = ""


class CatalogClient:
    def __init__(self, state: DownloadState) -> None:
        self.base_url = settings.api_base_url.rstrip("/")
        self._headers = {"X-Candidate-Id": settings.candidate_id}
        self._state = state
        self._semaphore = asyncio.Semaphore(3)

    async def fetch_names(self) -> list[str]:
        async with self._semaphore:
            return await self._request("GET", "/api/files/names")

    async def download_files(self, file_names: list[str]) -> int:
        async with self._semaphore:
            content = await self._request(
                "POST",
                "/api/files/download",
                json={"file_names": file_names},
                expect_json=False,
            )
            if content is None:
                return 0
            return self._extract_zip(content)

    async def mark_downloaded(self, file_names: list[str]) -> Optional[dict]:
        async with self._semaphore:
            return await self._request(
                "POST",
                "/api/files/downloaded",
                json={"file_names": file_names},
            )

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        expect_json: bool = True,
    ):
        url = f"{self.base_url}{path}"
        self._state.requests_made += 1

        while True:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    if method == "GET":
                        resp = await client.get(url, headers=self._headers)
                    else:
                        resp = await client.post(url, headers=self._headers, json=json)

                    if resp.status_code == 200:
                        logger.debug("%s %s — 200", method, path)
                        return resp.json() if expect_json else resp.content

                    if resp.status_code in (429, 403):
                        retry_after = self._parse_retry_after(resp.headers.get("Retry-After", "5"))
                        self._state.status = "retrying"
                        self._state.error_message = f"{resp.status_code}, жду {retry_after}с"
                        logger.warning("Лимит API, жду %sс", retry_after)
                        await asyncio.sleep(retry_after)
                        continue

                    if resp.status_code == 404:
                        logger.warning("404 на %s", path)
                        self._state.errors += 1
                        return None

                    resp.raise_for_status()

            except httpx.TimeoutException:
                logger.warning("Таймаут на %s, повтор через 5с", path)
                await asyncio.sleep(5)
                continue
            except httpx.HTTPStatusError as exc:
                logger.error("HTTP ошибка %s: %s", path, exc)
                self._state.errors += 1
                raise

    def _extract_zip(self, content: bytes) -> int:
        count = 0
        download_dir = settings.download_path
        os.makedirs(download_dir, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for name in zf.namelist():
                zf.extract(name, download_dir)
                count += 1
        logger.info("Извлечено %d файлов", count)
        return count

    @staticmethod
    def _parse_retry_after(value: str) -> int:
        try:
            return max(1, int(value))
        except (ValueError, TypeError):
            return 5
