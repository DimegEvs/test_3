from pathlib import Path
from unittest.mock import MagicMock, patch

from app.core.logging_config import setup_logging


def test_setup_logging_creates_dir():
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger, \
         patch("app.core.logging_config.logging.StreamHandler") as mock_stream, \
         patch("app.core.logging_config.RotatingFileHandler") as mock_file:
        mock_root = MagicMock()
        mock_httpx = MagicMock()
        mock_httpcore = MagicMock()
        mock_get_logger.side_effect = lambda name=None: {
            None: mock_root,
            "httpx": mock_httpx,
            "httpcore": mock_httpcore,
        }.get(name, MagicMock())

        log_dir = Path("/tmp/test_logs")
        path_mock = MagicMock()
        log_dir_mock = MagicMock(spec=Path)
        log_dir_mock.__truediv__.return_value = path_mock
        log_dir_mock.mkdir = MagicMock()

        with patch("pathlib.Path.mkdir"):
            setup_logging(log_dir, debug=True)

        mock_root.setLevel.assert_called_once()
        mock_httpx.setLevel.assert_called_once()
        mock_httpcore.setLevel.assert_called_once()


def test_setup_logging_production_mode():
    with patch("app.core.logging_config.logging.getLogger") as mock_get_logger, \
         patch("app.core.logging_config.logging.StreamHandler") as mock_stream, \
         patch("app.core.logging_config.RotatingFileHandler") as mock_file:
        mock_root = MagicMock()
        mock_httpx = MagicMock()
        mock_httpcore = MagicMock()
        mock_get_logger.side_effect = lambda name=None: {
            None: mock_root,
            "httpx": mock_httpx,
            "httpcore": mock_httpcore,
        }.get(name, MagicMock())

        import logging
        log_dir = Path("/tmp/test_logs")
        with patch("pathlib.Path.mkdir"):
            setup_logging(log_dir, debug=False)

        args, _ = mock_root.setLevel.call_args
        assert args[0] == logging.INFO
