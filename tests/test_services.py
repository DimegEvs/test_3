from pathlib import Path
from unittest.mock import patch

import pytest

from app.schemas.state import StatsModel
from app.services.file_service import FileService
from app.services.stats_service import StatsService


class TestFileService:
    def test_ensure_download_dir_creates(self, tmp_path: Path):
        d = tmp_path / "new_downloads"
        with patch("app.services.file_service.settings") as mock_settings:
            mock_settings.download_path = d
            result = FileService.ensure_download_dir()

        assert result == d
        assert d.exists()


class TestStatsService:
    def test_empty_dir_returns_zero(self, tmp_path: Path):
        result = StatsService.compute(download_dir=tmp_path)
        assert isinstance(result, StatsModel)
        assert result.total_files == 0
        assert result.digit_counts == {str(d): 0 for d in range(10)}
        assert result.file_stats == []

    def test_counts_digits_correctly(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("a1b2c3", encoding="utf-8")
        (tmp_path / "b.txt").write_text("hello 42 world", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        assert result.total_files == 2
        assert result.digit_counts["1"] == 1
        assert result.digit_counts["2"] == 2
        assert result.digit_counts["3"] == 1
        assert result.digit_counts["4"] == 1

        names = {f.file_name for f in result.file_stats}
        assert names == {"a.txt", "b.txt"}

    def test_skips_non_txt_files(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("123", encoding="utf-8")
        (tmp_path / "b.csv").write_text("4,5,6", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        assert result.total_files == 1

    def test_digit_counts_include_all_digits(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("1", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        assert len(result.digit_counts) == 10
        assert result.digit_counts["1"] == 1
        assert result.digit_counts["0"] == 0

    def test_file_stats_include_all_digits(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("5", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        fs = result.file_stats[0]
        assert len(fs.digit_counts) == 10
        assert fs.digit_counts["5"] == 1
        assert fs.digit_counts["0"] == 0

    def test_skips_unreadable_files(self, tmp_path: Path):
        (tmp_path / "a.txt").write_bytes(b"\xff\xfe\x00\x01")
        (tmp_path / "b.txt").write_text("123", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        assert result.total_files == 2
        assert result.digit_counts["1"] == 1

    def test_aggregates_digits_across_files(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("11", encoding="utf-8")
        (tmp_path / "b.txt").write_text("12", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        assert result.digit_counts["1"] == 3
        assert result.digit_counts["2"] == 1

    def test_file_stat_digit_counts_per_file(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("111", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        fs = result.file_stats[0]
        assert fs.file_name == "a.txt"
        assert fs.digit_counts["1"] == 3

    def test_non_digit_characters_ignored(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("abc!@#", encoding="utf-8")

        result = StatsService.compute(download_dir=tmp_path)

        assert result.digit_counts["0"] == 0
        assert all(v == 0 for v in result.digit_counts.values())
