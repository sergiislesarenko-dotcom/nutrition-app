from fastapi import HTTPException


class AppError(HTTPException):
    """Application-level HTTP error with an optional machine-readable code."""

    def __init__(self, status_code: int, detail: str, code: str | None = None) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
