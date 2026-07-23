import logging
from collections import Counter
from pathlib import Path

from app.config import settings
from app.schemas.state import StatsModel

logger = logging.getLogger(__name__)


class StatsService:
    @staticmethod
    def compute(download_dir: Path | None = None) -> StatsModel:
        if download_dir is None:
            download_dir = settings.download_path
        files = list(download_dir.glob("*.txt"))

        total_chars = 0
        total_lines = 0
        word_counter: Counter = Counter()

        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                logger.warning("Не удалось прочитать %s, пропуск", fp.name)
                continue

            total_chars += len(text)
            total_lines += text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            words = text.split()
            word_counter.update(words)

        total_words = sum(word_counter.values())
        unique_words = len(word_counter)
        top_words = word_counter.most_common(20)

        return StatsModel(
            total_files=len(files),
            total_chars=total_chars,
            total_lines=total_lines,
            total_words=total_words,
            unique_words=unique_words,
            top_words=top_words,
        )
