from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class DownloadStartResponse(BaseModel):
    started: bool
    message: str | None = None
