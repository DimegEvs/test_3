from app.schemas.health import HealthResponse, DownloadStartResponse
from app.schemas.state import FileDigitStats, StatsModel, StateResponse


class TestHealthResponse:
    def test_create(self):
        r = HealthResponse(status="ok", version="1.0.0", timestamp="2024-01-01T00:00:00")
        assert r.status == "ok"
        assert r.version == "1.0.0"
        assert r.timestamp == "2024-01-01T00:00:00"


class TestDownloadStartResponse:
    def test_started_true(self):
        r = DownloadStartResponse(started=True)
        assert r.started is True
        assert r.message == ""

    def test_started_false_with_message(self):
        r = DownloadStartResponse(started=False, message="Already running")
        assert r.started is False
        assert r.message == "Already running"


class TestFileDigitStats:
    def test_create(self):
        s = FileDigitStats(file_name="test.txt", digit_counts={"1": 5, "2": 3})
        assert s.file_name == "test.txt"
        assert s.digit_counts == {"1": 5, "2": 3}


class TestStatsModel:
    def test_defaults(self):
        s = StatsModel()
        assert s.total_files == 0
        assert s.digit_counts == {}
        assert s.file_stats == []

    def test_with_data(self):
        file_stat = FileDigitStats(file_name="a.txt", digit_counts={"0": 1})
        s = StatsModel(total_files=2, digit_counts={"0": 5, "1": 3}, file_stats=[file_stat])
        assert s.total_files == 2
        assert s.digit_counts == {"0": 5, "1": 3}
        assert len(s.file_stats) == 1

    def test_serialization(self):
        file_stat = FileDigitStats(file_name="a.txt", digit_counts={"0": 1})
        s = StatsModel(total_files=1, digit_counts={"0": 1}, file_stats=[file_stat])
        d = s.model_dump()
        assert d["total_files"] == 1
        assert d["digit_counts"] == {"0": 1}


class TestStateResponse:
    def test_defaults(self):
        s = StateResponse()
        assert s.status == "idle"
        assert s.total_attempted == 0
        assert s.total_downloaded == 0
        assert s.total_marked == 0
        assert s.requests_made == 0
        assert s.errors == 0
        assert s.error_message == ""
        assert s.stats is None

    def test_with_stats(self):
        stats = StatsModel(total_files=3, digit_counts={"1": 10})
        s = StateResponse(status="done", total_downloaded=5, stats=stats)
        assert s.status == "done"
        assert s.stats.total_files == 3
