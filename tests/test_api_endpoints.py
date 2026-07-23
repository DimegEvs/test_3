import io
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def api_client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_get_health_returns_ok(self, api_client: TestClient):
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data


class TestStateEndpoint:
    def test_get_state_idle(self, api_client: TestClient):
        with patch("app.api.v1.endpoints.state._get_handler") as mock_get_handler:
            mock_handler = MagicMock()
            mock_handler.state.status = "idle"
            mock_handler.state.total_attempted = 0
            mock_handler.state.total_downloaded = 0
            mock_handler.state.total_marked = 0
            mock_handler.state.requests_made = 0
            mock_handler.state.errors = 0
            mock_handler.state.error_message = ""
            mock_get_handler.return_value = mock_handler

            with patch("app.api.v1.endpoints.state.settings") as mock_settings:
                mock_path = MagicMock()
                mock_path.exists.return_value = False
                mock_settings.download_path = mock_path

                response = api_client.get("/api/state")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "idle"
        assert data["stats"] is None

    def test_get_state_with_stats(self, api_client: TestClient):
        with patch("app.api.v1.endpoints.state._get_handler") as mock_get_handler:
            mock_handler = MagicMock()
            mock_handler.state.status = "done"
            mock_handler.state.total_attempted = 10
            mock_handler.state.total_downloaded = 8
            mock_handler.state.total_marked = 5
            mock_handler.state.requests_made = 4
            mock_handler.state.errors = 1
            mock_handler.state.error_message = ""
            mock_get_handler.return_value = mock_handler

            with patch("app.api.v1.endpoints.state.settings") as mock_settings:
                mock_path = MagicMock()
                mock_path.exists.return_value = True
                mock_settings.download_path = mock_path

                from app.schemas.state import StatsModel
                with patch("app.api.v1.endpoints.state.StatsService") as mock_stats:
                    mock_stats.compute.return_value = StatsModel(
                        total_files=10,
                        digit_counts={str(d): d for d in range(10)},
                        file_stats=[],
                    )

                    response = api_client.get("/api/state")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["total_attempted"] == 10
        assert data["total_downloaded"] == 8
        assert data["total_marked"] == 5
        assert data["requests_made"] == 4
        assert data["errors"] == 1


class TestFilesEndpoints:
    def test_get_file_names_empty(self, api_client: TestClient):
        with patch("app.api.v1.endpoints.files.settings") as mock_settings:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_settings.download_path = mock_path

            response = api_client.get("/api/files/names")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_file_names_returns_sorted_txt(self, api_client: TestClient, tmp_path: Path):
        (tmp_path / "b.txt").write_text("")
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "c.csv").write_text("")

        with patch("app.api.v1.endpoints.files.settings") as mock_settings:
            mock_settings.download_path = tmp_path

            response = api_client.get("/api/files/names")

        assert response.status_code == 200
        assert response.json() == ["a.txt", "b.txt"]

    def test_download_files_creates_zip(self, api_client: TestClient, tmp_path: Path):
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")

        with patch("app.api.v1.endpoints.files.settings") as mock_settings:
            mock_settings.download_path = tmp_path

            response = api_client.post(
                "/api/files/download",
                json={"file_names": ["a.txt", "b.txt"]},
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "attachment" in response.headers["content-disposition"]

        zf = zipfile.ZipFile(io.BytesIO(response.content))
        names = zf.namelist()
        assert "a.txt" in names
        assert "b.txt" in names

    def test_download_files_not_found_returns_404(self, api_client: TestClient, tmp_path: Path):
        with patch("app.api.v1.endpoints.files.settings") as mock_settings:
            mock_settings.download_path = tmp_path

            response = api_client.post(
                "/api/files/download",
                json={"file_names": ["missing.txt"]},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "No requested files found"

    def test_download_files_partial_found(self, api_client: TestClient, tmp_path: Path):
        (tmp_path / "x.txt").write_text("data")

        with patch("app.api.v1.endpoints.files.settings") as mock_settings:
            mock_settings.download_path = tmp_path

            response = api_client.post(
                "/api/files/download",
                json={"file_names": ["x.txt", "missing.txt"]},
            )

        assert response.status_code == 200
        zf = zipfile.ZipFile(io.BytesIO(response.content))
        assert zf.namelist() == ["x.txt"]

    def test_mark_downloaded_counts_existing(self, api_client: TestClient, tmp_path: Path):
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")

        with patch("app.api.v1.endpoints.files.settings") as mock_settings:
            mock_settings.download_path = tmp_path

            response = api_client.post(
                "/api/files/downloaded",
                json={"file_names": ["a.txt", "b.txt", "c.txt"]},
            )

        assert response.status_code == 200
        assert response.json()["marked_now"] == 2

    def test_mark_downloaded_none_found(self, api_client: TestClient, tmp_path: Path):
        with patch("app.api.v1.endpoints.files.settings") as mock_settings:
            mock_settings.download_path = tmp_path

            response = api_client.post(
                "/api/files/downloaded",
                json={"file_names": ["x.txt", "y.txt"]},
            )

        assert response.status_code == 200
        assert response.json()["marked_now"] == 0


class TestDownloadEndpoint:
    def test_start_download_idle(self, api_client: TestClient):
        with patch("app.api.v1.endpoints.download._run_download", side_effect=lambda h: None):
            response = api_client.post("/api/download-all")
        assert response.status_code == 200
        data = response.json()
        assert data["started"] is True

    def test_start_download_already_running(self, api_client: TestClient):
        import app.api.v1.endpoints.download as download_mod
        with patch.object(download_mod._download_lock, "locked", return_value=True):
            response = api_client.post("/api/download-all")
        assert response.status_code == 200
        data = response.json()
        assert data["started"] is False
        assert "идёт" in data["message"]


class TestFrontend:
    def test_serve_frontend_404_when_missing(self, api_client: TestClient):
        with patch("pathlib.Path.exists", return_value=False):
            response = api_client.get("/")
        assert response.status_code == 404
        assert response.json()["detail"] == "Frontend not found"
