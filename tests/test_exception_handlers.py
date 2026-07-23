from unittest.mock import MagicMock

from fastapi import FastAPI, Request

from app.core.exceptions import AppException, CatalogAPIError, DownloadInProgressError
from app.core.exception_handlers import register_exception_handlers


def _get_handler_fn(app_mock, index: int):
    """Extract the handler function registered at given index."""
    register_call = app_mock.exception_handler.call_args_list[index]
    exc_type = register_call[0][0]
    handler_call = app_mock.exception_handler.return_value.call_args_list[index]
    handler_fn = handler_call[0][0]
    return exc_type, handler_fn


def test_app_exception_handler_returns_json():
    app = MagicMock(spec=FastAPI)
    register_exception_handlers(app)

    exc_type, handler_fn = _get_handler_fn(app, 0)
    assert exc_type is AppException

    request = MagicMock(spec=Request)
    request.url.path = "/test"

    exc = CatalogAPIError(detail="API unavailable")
    import asyncio
    response = asyncio.run(handler_fn(request, exc))

    assert response.status_code == 502
    import json
    body = json.loads(response.body)
    assert body["detail"] == "API unavailable"
    assert body["status_code"] == 502


def test_unhandled_exception_handler_returns_500():
    app = MagicMock(spec=FastAPI)
    register_exception_handlers(app)

    exc_type, handler_fn = _get_handler_fn(app, 1)
    assert exc_type is Exception

    request = MagicMock(spec=Request)
    request.url.path = "/test"

    exc = ValueError("unexpected")
    import asyncio
    response = asyncio.run(handler_fn(request, exc))

    assert response.status_code == 500
    import json
    body = json.loads(response.body)
    assert body["detail"] == "Internal server error"
    assert body["status_code"] == 500


def test_app_exception_accepts_subclasses():
    app = MagicMock(spec=FastAPI)
    register_exception_handlers(app)

    exc_type, handler_fn = _get_handler_fn(app, 0)
    assert exc_type is AppException

    request = MagicMock(spec=Request)
    request.url.path = "/test"

    exc = DownloadInProgressError()
    import asyncio
    response = asyncio.run(handler_fn(request, exc))

    assert response.status_code == 409
