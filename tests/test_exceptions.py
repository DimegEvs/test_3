import pytest

from app.core.exceptions import AppException, CatalogAPIError, DownloadInProgressError


class TestAppException:
    def test_default_detail_and_status(self):
        exc = AppException()
        assert exc.status_code == 500
        assert exc.detail == "Internal server error"
        assert str(exc) == "Internal server error"

    def test_custom_detail(self):
        exc = AppException(detail="Custom error")
        assert exc.status_code == 500
        assert exc.detail == "Custom error"
        assert str(exc) == "Custom error"

    def test_is_exception_subclass(self):
        assert issubclass(AppException, Exception)


class TestCatalogAPIError:
    def test_default_values(self):
        exc = CatalogAPIError()
        assert exc.status_code == 502
        assert exc.detail == "External catalog API error"

    def test_custom_detail(self):
        exc = CatalogAPIError(detail="Connection refused")
        assert exc.status_code == 502
        assert exc.detail == "Connection refused"

    def test_inherits_app_exception(self):
        assert issubclass(CatalogAPIError, AppException)


class TestDownloadInProgressError:
    def test_default_values(self):
        exc = DownloadInProgressError()
        assert exc.status_code == 409
        assert exc.detail == "Download is already in progress"

    def test_inherits_app_exception(self):
        assert issubclass(DownloadInProgressError, AppException)
