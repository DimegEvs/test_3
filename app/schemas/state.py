from pydantic import BaseModel, Field


class FileDigitStats(BaseModel):
    file_name: str
    digit_counts: dict[str, int]


class StatsModel(BaseModel):
    total_files: int = 0
    digit_counts: dict[str, int] = Field(default_factory=dict)
    file_stats: list[FileDigitStats] = Field(default_factory=list)


class StateResponse(BaseModel):
    status: str
    total_attempted: int
    total_downloaded: int
    total_marked: int
    requests_made: int
    errors: int
    error_message: str
    stats: StatsModel | None = None
