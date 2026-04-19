class APIError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int, retry_after_seconds: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds
