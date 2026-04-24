from __future__ import annotations

from datetime import timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Timeframe(str, Enum):
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"

    @property
    def bybit_interval(self) -> str:
        return {
            Timeframe.M5: "5",
            Timeframe.M15: "15",
            Timeframe.H1: "60",
            Timeframe.H4: "240",
        }[self]

    @property
    def duration(self) -> timedelta:
        return {
            Timeframe.M5: timedelta(minutes=5),
            Timeframe.M15: timedelta(minutes=15),
            Timeframe.H1: timedelta(hours=1),
            Timeframe.H4: timedelta(hours=4),
        }[self]


class ScanMode(str, Enum):
    BALANCED = "balanced"


class BaseRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def normalize_symbol(value: str) -> str:
        return value.strip().upper()


class AnalyzeSymbolRequest(BaseRequestModel):
    symbol: str
    timeframe: Timeframe
    bars_limit: int | None = Field(default=None, ge=1)

    @field_validator("symbol")
    @classmethod
    def _normalize_symbol(cls, value: str) -> str:
        normalized = cls.normalize_symbol(value)
        if not normalized:
            raise ValueError("symbol must not be empty")
        return normalized


class CompareSymbolsRequest(BaseRequestModel):
    symbols: list[str] = Field(min_length=2)
    timeframe: Timeframe
    bars_limit: int | None = Field(default=None, ge=1)

    @field_validator("symbols")
    @classmethod
    def _normalize_symbols(cls, values: list[str]) -> list[str]:
        normalized = [cls.normalize_symbol(value) for value in values]
        if len(set(normalized)) != len(normalized):
            raise ValueError("symbols must be unique")
        return normalized


class ScanWatchlistRequest(BaseRequestModel):
    symbols: list[str] = Field(min_length=1)
    timeframe: Timeframe
    scan_mode: ScanMode = ScanMode.BALANCED
    bars_limit: int | None = Field(default=None, ge=1)

    @field_validator("symbols")
    @classmethod
    def _normalize_symbols(cls, values: list[str]) -> list[str]:
        normalized = [cls.normalize_symbol(value) for value in values]
        if len(set(normalized)) != len(normalized):
            raise ValueError("symbols must be unique")
        return normalized


class GetRawSnapshotRequest(BaseRequestModel):
    symbol: str
    timeframe: Timeframe

    @field_validator("symbol")
    @classmethod
    def _normalize_symbol(cls, value: str) -> str:
        normalized = cls.normalize_symbol(value)
        if not normalized:
            raise ValueError("symbol must not be empty")
        return normalized


class MarketDataWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested_bars: int
    fetch_bars: int
    minimum_required_bars: int


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: int
    start_timestamp: Any
    end_timestamp: Any
    timeframe: Timeframe
