from pydantic import BaseModel, Field


class StatsModel(BaseModel):
    total_files: int = 0
    total_chars: int = 0
    total_lines: int = 0
    total_words: int = 0
    unique_words: int = 0
    top_words: list[tuple[str, int]] = Field(default_factory=list)


class StateResponse(BaseModel):
    status: str
    total_attempted: int
    total_downloaded: int
    total_marked: int
    requests_made: int
    errors: int
    error_message: str
    stats: StatsModel | None = None
