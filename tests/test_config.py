from unittest.mock import patch

from app.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.app_name == "Catalog Downloader"
        assert s.app_version == "1.0.0"
        assert s.debug is True
        assert s.host == "0.0.0.0"
        assert s.port == 8000
        assert s.candidate_id == "my-candidate"
        assert s.download_dir == "downloaded"
        assert s.log_dir == "storage/logs"

    def test_cors_origins_list_single(self):
        s = Settings(cors_origins="http://localhost:8000")
        assert s.cors_origins_list == ["http://localhost:8000"]

    def test_cors_origins_list_multiple(self):
        s = Settings(cors_origins="http://localhost:8000, https://example.com")
        assert s.cors_origins_list == ["http://localhost:8000", "https://example.com"]

    def test_cors_origins_list_empty(self):
        s = Settings(cors_origins="")
        assert s.cors_origins_list == []

    def test_cors_origins_list_strips_whitespace(self):
        s = Settings(cors_origins=" http://a.com , https://b.com ")
        assert s.cors_origins_list == ["http://a.com", "https://b.com"]

    def test_download_path(self):
        s = Settings(download_dir="my_downloads")
        from pathlib import Path
        assert s.download_path == Path("my_downloads")

    def test_log_path(self):
        s = Settings(log_dir="my_logs")
        from pathlib import Path
        assert s.log_path == Path("my_logs")

    def test_extra_fields_ignored(self):
        s = Settings(app_name="test", unknown_field=123)
        assert s.app_name == "test"

    def test_case_insensitive_setting(self):
        s = Settings(app_name="FromEnv")
        assert s.app_name == "FromEnv"
