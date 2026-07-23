class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class CatalogAPIError(AppException):
    status_code: int = 502
    detail: str = "External catalog API error"


class DownloadInProgressError(AppException):
    status_code: int = 409
    detail: str = "Download is already in progress"
