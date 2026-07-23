import io
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.integrations.catalog_client import CatalogClient, DownloadState


class TestDownloadState:
    def test_defaults(self):
        s = DownloadState()
        assert s.total_attempted == 0
        assert s.total_downloaded == 0
        assert s.total_marked == 0
        assert s.requests_made == 0
        assert s.errors == 0
        assert s.status == "idle"
        assert s.error_message == ""

    def test_mutable_fields(self):
        s = DownloadState()
        s.status = "running"
        s.errors = 3
        assert s.status == "running"
        assert s.errors == 3


class TestParseRetryAfter:
    def test_valid_int(self):
        assert CatalogClient._parse_retry_after("10") == 10

    def test_negative_clamps_to_1(self):
        assert CatalogClient._parse_retry_after("-5") == 1

    def test_zero_clamps_to_1(self):
        assert CatalogClient._parse_retry_after("0") == 1

    def test_invalid_string_returns_5(self):
        assert CatalogClient._parse_retry_after("abc") == 5

    def test_empty_string_returns_5(self):
        assert CatalogClient._parse_retry_after("") == 5

    def test_none_returns_5(self):
        assert CatalogClient._parse_retry_after(None) == 5

    def test_float_string_truncates(self):
        assert CatalogClient._parse_retry_after("3.14") == 5


class TestExtractZip:
    def test_extracts_files(self, tmp_download_dir):
        state = DownloadState()
        client = CatalogClient(state)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("a.txt", "hello")
            zf.writestr("b.txt", "world")
        content = buf.getvalue()

        with patch("app.integrations.catalog_client.settings") as mock_settings:
            mock_settings.download_path = tmp_download_dir
            count = client._extract_zip(content)

        assert count == 2
        assert (tmp_download_dir / "a.txt").exists()
        assert (tmp_download_dir / "b.txt").exists()

    def test_empty_zip_returns_zero(self, tmp_download_dir):
        state = DownloadState()
        client = CatalogClient(state)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            pass
        content = buf.getvalue()

        with patch("app.integrations.catalog_client.settings") as mock_settings:
            mock_settings.download_path = tmp_download_dir
            count = client._extract_zip(content)

        assert count == 0


class TestFetchNames:
    @pytest.mark.asyncio
    async def test_returns_names(self):
        state = DownloadState()
        client = CatalogClient(state)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = ["file1.txt", "file2.txt"]

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await client.fetch_names()

        assert result == ["file1.txt", "file2.txt"]
        assert state.requests_made == 1


class TestDownloadFiles:
    @pytest.mark.asyncio
    async def test_downloads_and_extracts(self, tmp_download_dir):
        state = DownloadState()
        client = CatalogClient(state)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("x.txt", "content")
        zip_content = buf.getvalue()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = zip_content

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with patch("app.integrations.catalog_client.settings") as mock_settings:
                mock_settings.download_path = tmp_download_dir
                result = await client.download_files(["x.txt"])

        assert result == 1
        assert state.requests_made == 1

    @pytest.mark.asyncio
    async def test_returns_zero_when_content_none(self):
        state = DownloadState()
        client = CatalogClient(state)

        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await client.download_files(["missing.txt"])

        assert result == 0
        assert state.errors == 1


class TestMarkDownloaded:
    @pytest.mark.asyncio
    async def test_marks_downloaded(self):
        state = DownloadState()
        client = CatalogClient(state)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"marked_now": 3}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await client.mark_downloaded(["a.txt", "b.txt", "c.txt"])

        assert result == {"marked_now": 3}
        assert state.requests_made == 1


class TestRequestRetry:
    @pytest.mark.asyncio
    async def test_retries_on_429(self):
        state = DownloadState()
        client = CatalogClient(state)

        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "1"}

        success = MagicMock()
        success.status_code = 200
        success.json.return_value = ["a.txt"]

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [rate_limited, success]
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await client.fetch_names()

        assert result == ["a.txt"]
        assert state.status == "retrying"
        assert "429" in state.error_message

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self):
        state = DownloadState()
        client = CatalogClient(state)

        success = MagicMock()
        success.status_code = 200
        success.json.return_value = ["a.txt"]

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [
                httpx.TimeoutException("timeout"),
                success,
            ]
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await client.fetch_names()

        assert result == ["a.txt"]

    @pytest.mark.asyncio
    async def test_handles_403(self):
        state = DownloadState()
        client = CatalogClient(state)

        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_resp
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await client.fetch_names()

        assert state.status == "error"
        assert state.errors == 2

    @pytest.mark.asyncio
    async def test_http_status_error_propagates(self):
        state = DownloadState()
        client = CatalogClient(state)

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_resp
        )

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__.return_value = mock_client
            with pytest.raises(httpx.HTTPStatusError):
                await client.fetch_names()
