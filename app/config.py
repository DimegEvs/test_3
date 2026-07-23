from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Catalog Downloader"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: str = "http://localhost:8000"

    candidate_id: str = "my-candidate"

    download_dir: str = "downloaded"
    log_dir: str = "storage/logs"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def download_path(self) -> Path:
        return Path(self.download_dir)

    @property
    def log_path(self) -> Path:
        return Path(self.log_dir)


settings = Settings()
