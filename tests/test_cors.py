from unittest.mock import MagicMock, patch

from fastapi import FastAPI

from app.core.cors import setup_cors


@patch("app.core.cors.settings")
def test_setup_cors_calls_add_middleware(mock_settings):
    mock_settings.cors_origins_list = ["http://localhost:8000", "https://example.com"]

    app = MagicMock(spec=FastAPI)
    setup_cors(app)

    app.add_middleware.assert_called_once()
    call_args, call_kwargs = app.add_middleware.call_args

    from fastapi.middleware.cors import CORSMiddleware
    assert call_args[0] == CORSMiddleware
    assert call_kwargs["allow_origins"] == ["http://localhost:8000", "https://example.com"]
    assert call_kwargs["allow_credentials"] is True
    assert call_kwargs["allow_methods"] == ["*"]
    assert call_kwargs["allow_headers"] == ["*"]
