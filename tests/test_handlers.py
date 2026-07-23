from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.handlers.download_handler import DownloadHandler
from app.integrations.catalog_client import DownloadState


class TestDownloadHandler:
    def test_initial_state(self):
        h = DownloadHandler()
        assert isinstance(h.state, DownloadState)
        assert h.state.status == "idle"

    def test_state_property_returns_same_object(self):
        h = DownloadHandler()
        assert h.state is h._state

    @pytest.mark.asyncio
    async def test_run_completes_when_no_new_names(self):
        h = DownloadHandler()
        h._state.status = "idle"

        with patch.object(h, "_state", wraps=h._state) as wrapped_state:
            with patch("app.handlers.download_handler.CatalogClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client.fetch_names = AsyncMock(return_value=["a.txt"])
                mock_client.download_files = AsyncMock(return_value=1)
                mock_client.mark_downloaded = AsyncMock(return_value={"marked_now": 1})
                mock_client_cls.return_value = mock_client

                with patch("app.handlers.download_handler.StatsService") as mock_stats:
                    mock_stats.compute.return_value = MagicMock(total_files=10)

                    result = await h.run()

        assert result.status == "done"
        assert result.total_attempted == 1
        assert result.total_downloaded == 1
        assert result.total_marked == 1

    @pytest.mark.asyncio
    async def test_run_multiple_batches(self):
        h = DownloadHandler()

        with patch("app.handlers.download_handler.CatalogClient") as mock_client_cls:
            mock_client = MagicMock()

            fetch_results = [
                ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"],
                [],
            ]
            mock_client.fetch_names = AsyncMock(side_effect=fetch_results)
            mock_client.download_files = AsyncMock(return_value=2)
            mock_client.mark_downloaded = AsyncMock(return_value={"marked_now": 4})

            mock_client_cls.return_value = mock_client

            with patch("app.handlers.download_handler.StatsService") as mock_stats:
                mock_stats.compute.return_value = MagicMock(total_files=0)

                result = await h.run()

        assert result.status == "done"
        assert result.total_attempted == 5

    @pytest.mark.asyncio
    async def test_run_handles_download_errors(self):
        h = DownloadHandler()

        with patch("app.handlers.download_handler.CatalogClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.fetch_names = AsyncMock(return_value=["a.txt", "b.txt"])
            mock_client.download_files = AsyncMock(side_effect=Exception("Download failed"))
            mock_client.mark_downloaded = AsyncMock(return_value={"marked_now": 0})

            mock_client_cls.return_value = mock_client

            with patch("app.handlers.download_handler.StatsService") as mock_stats:
                mock_stats.compute.return_value = MagicMock(total_files=0)

                result = await h.run()

        assert result.errors > 0

    @pytest.mark.asyncio
    async def test_run_handles_mark_errors(self):
        h = DownloadHandler()

        with patch("app.handlers.download_handler.CatalogClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.fetch_names = AsyncMock(return_value=["a.txt"])
            mock_client.download_files = AsyncMock(return_value=1)
            mock_client.mark_downloaded = AsyncMock(side_effect=Exception("Mark failed"))

            mock_client_cls.return_value = mock_client

            with patch("app.handlers.download_handler.StatsService") as mock_stats:
                mock_stats.compute.return_value = MagicMock(total_files=10)

                result = await h.run()

        assert result.status == "done"
        assert result.total_downloaded == 1

    @pytest.mark.asyncio
    async def test_run_handles_fetch_names_none(self):
        h = DownloadHandler()

        with patch("app.handlers.download_handler.CatalogClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.fetch_names = AsyncMock(side_effect=[None, ["a.txt"], []])
            mock_client.download_files = AsyncMock(return_value=1)
            mock_client.mark_downloaded = AsyncMock(return_value={"marked_now": 1})

            mock_client_cls.return_value = mock_client

            with patch("app.handlers.download_handler.StatsService") as mock_stats:
                mock_stats.compute.return_value = MagicMock(total_files=10)

                result = await h.run()

        assert result.status == "done"

    @pytest.mark.asyncio
    async def test_run_catches_unhandled_exceptions(self):
        h = DownloadHandler()

        with patch("app.handlers.download_handler.CatalogClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.fetch_names = AsyncMock(side_effect=RuntimeError("Boom"))

            mock_client_cls.return_value = mock_client

            result = await h.run()

        assert result.status == "error"
        assert "Boom" in result.error_message

    @pytest.mark.asyncio
    async def test_run_resets_state_on_start(self):
        h = DownloadHandler()
        h._state.status = "error"
        h._state.errors = 99
        h._state.error_message = "old error"

        with patch("app.handlers.download_handler.CatalogClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.fetch_names = AsyncMock(return_value=[])
            mock_client_cls.return_value = mock_client

            result = await h.run()

        assert result.errors == 0
        assert result.error_message == ""
        assert result.status == "done"
