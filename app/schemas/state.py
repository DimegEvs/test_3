from pydantic import BaseModel, Field


class FileDigitStats(BaseModel):
    file_name: str
    digit_counts: dict[str, int]


class StatsModel(BaseModel):
    total_files: int = 0
    digit_counts: dict[str, int] = Field(default_factory=dict)
    file_stats: list[FileDigitStats] = Field(default_factory=list)


class StateResponse(BaseModel):
    status: str = "idle"
    total_attempted: int = 0
    total_downloaded: int = 0
    total_marked: int = 0
    requests_made: int = 0
    errors: int = 0
    error_message: str = ""
    stats: StatsModel | None = None
