import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = client_instance
        yield client_instance


@pytest.fixture
def tmp_download_dir(tmp_path: Path):
    d = tmp_path / "downloads"
    d.mkdir()
    return d
