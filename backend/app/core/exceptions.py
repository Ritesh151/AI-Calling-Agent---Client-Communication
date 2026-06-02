from __future__ import annotations

from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str = "An error occurred",
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=404, details=details)


class ValidationException(AppException):
    def __init__(
        self,
        message: str = "Validation error",
        error_code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=422, details=details)


class AuthenticationException(AppException):
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=401, details=details)


class AuthorizationException(AppException):
    def __init__(
        self,
        message: str = "Permission denied",
        error_code: str = "AUTHORIZATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=403, details=details)


class DatabaseException(AppException):
    def __init__(
        self,
        message: str = "Database error occurred",
        error_code: str = "DATABASE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=500, details=details)


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Resource already exists",
        error_code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=409, details=details)


class RateLimitException(AppException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, error_code=error_code, status_code=429, details=details)
