from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.market import Timeframe


class TrendDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class TrendStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class RSIState(str, Enum):
    OVERSOLD = "oversold"
    NEUTRAL = "neutral"
    STRONG = "strong"
    OVERBOUGHT = "overbought"


class ATRState(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class VolumeState(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    ELEVATED = "elevated"


class PriceVsVWAPState(str, Enum):
    BELOW = "below"
    NEAR = "near"
    ABOVE = "above"
    EXTENDED_ABOVE = "extended_above"
    EXTENDED_BELOW = "extended_below"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IndicatorSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    ema20: float
    ema50: float
    ema200: float
    rsi14: float
    atr14: float
    vwap: float
    distance_to_vwap_pct: float
    relative_volume: float


class FeatureSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    price_above_ema20: bool
    price_above_ema50: bool
    price_above_ema200: bool
    ema20_above_ema50: bool
    ema50_above_ema200: bool


class StateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    trend_direction: TrendDirection
    trend_strength: TrendStrength
    rsi_state: RSIState
    atr_state: ATRState
    volume_state: VolumeState
    price_vs_vwap_state: PriceVsVWAPState


class FlagSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    setup_flags: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class SnapshotMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bars_requested: int
    bars_used: int
    data_source: str = "bybit"
    market_category: str = "spot"
    validation_passed: bool = True
    vwap_variant: str = "session_utc"


class MarketSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    symbol: str
    timeframe: Timeframe
    as_of: datetime
    price: float
    indicators: IndicatorSnapshot
    features: FeatureSnapshot
    states: StateSnapshot
    flags: FlagSnapshot
    meta: SnapshotMeta


class ErrorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ToolErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "error"
    error: ErrorPayload


class CompareSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    top_symbol_by_trend: str | None = None
    top_symbol_by_relative_volume: str | None = None
    bullish_symbols: list[str] = Field(default_factory=list)
    bearish_symbols: list[str] = Field(default_factory=list)


class CompareSymbolsData(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    timeframe: Timeframe
    snapshots: list[MarketSnapshot]
    summary: CompareSummary


class ScanResult(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    symbol: str
    score: int
    priority: Priority
    flags: list[str] = Field(default_factory=list)
    snapshot: MarketSnapshot


class ScanWatchlistData(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    timeframe: Timeframe
    scan_mode: str
    results: list[ScanResult]


class ToolSuccessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    data: dict[str, Any]
