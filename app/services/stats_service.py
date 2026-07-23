import logging
from collections import Counter
from pathlib import Path

from app.config import settings
from app.schemas.state import FileDigitStats, StatsModel

logger = logging.getLogger(__name__)

DIGITS = {str(d): 0 for d in range(10)}


class StatsService:
    @staticmethod
    def compute(download_dir: Path | None = None) -> StatsModel:
        if download_dir is None:
            download_dir = settings.download_path
        files = list(download_dir.glob("*.txt"))

        overall_counter: Counter = Counter()
        file_stats: list[FileDigitStats] = []

        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                logger.warning("Не удалось прочитать %s, пропуск", fp.name)
                continue

            file_digits = DIGITS.copy()
            for ch in text:
                if ch.isdigit():
                    overall_counter[ch] += 1
                    file_digits[ch] += 1

            file_stats.append(FileDigitStats(
                file_name=fp.name,
                digit_counts=dict(file_digits),
            ))

        digit_counts = {d: overall_counter.get(d, 0) for d in DIGITS}

        return StatsModel(
            total_files=len(files),
            digit_counts=digit_counts,
            file_stats=file_stats,
        )
