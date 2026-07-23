from pathlib import Path

from app.config import settings


class FileService:
    @staticmethod
    def ensure_download_dir() -> Path:
        path = settings.download_path
        path.mkdir(parents=True, exist_ok=True)
        return path
