from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error with a stable machine-readable payload."""

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class ConfigurationError(AppError):
    """Raised when configuration is invalid."""


class InputError(AppError):
    """Raised when a tool request is invalid."""


class DataFetchError(AppError):
    """Raised when market data cannot be fetched from Bybit."""


class MarketValidationError(AppError):
    """Raised when OHLCV data is invalid."""


class IndicatorCalculationError(AppError):
    """Raised when indicator calculations fail."""


class SnapshotBuildError(AppError):
    """Raised when the snapshot cannot be serialized."""

