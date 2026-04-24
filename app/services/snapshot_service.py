from __future__ import annotations

import math
from typing import Any

from app.config import Settings
from app.exceptions import SnapshotBuildError
from app.models.snapshot import (
    FeatureSnapshot,
    FlagSnapshot,
    IndicatorSnapshot,
    MarketSnapshot,
    SnapshotMeta,
    StateSnapshot,
)


class SnapshotService:
    """Builds a stable typed snapshot from the enriched market data."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build(
        self,
        *,
        symbol: str,
        timeframe: str,
        latest_row: dict[str, Any],
        requested_bars: int,
        bars_used: int,
        features: FeatureSnapshot,
        states: StateSnapshot,
        flags: FlagSnapshot,
    ) -> MarketSnapshot:
        try:
            snapshot = MarketSnapshot(
                symbol=symbol,
                timeframe=timeframe,
                as_of=latest_row["timestamp"],
                price=self._safe_float(latest_row["close"]),
                indicators=IndicatorSnapshot(
                    ema20=self._safe_float(latest_row["ema20"]),
                    ema50=self._safe_float(latest_row["ema50"]),
                    ema200=self._safe_float(latest_row["ema200"]),
                    rsi14=self._safe_float(latest_row["rsi14"]),
                    atr14=self._safe_float(latest_row["atr14"]),
                    vwap=self._safe_float(latest_row["vwap"]),
                    distance_to_vwap_pct=self._safe_float(latest_row["distance_to_vwap_pct"]),
                    relative_volume=self._safe_float(latest_row["relative_volume"]),
                ),
                features=features,
                states=states,
                flags=flags,
                meta=SnapshotMeta(
                    bars_requested=requested_bars,
                    bars_used=bars_used,
                    validation_passed=True,
                    vwap_variant=self.settings.vwap_variant,
                ),
            )
        except Exception as exc:
            raise SnapshotBuildError(
                "SNAPSHOT_SERIALIZATION_ERROR",
                "Failed to serialize the market snapshot",
                details={"reason": str(exc)},
            ) from exc
        return snapshot

    @staticmethod
    def _safe_float(value: Any) -> float:
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            raise ValueError("numeric snapshot fields must be finite")
        return number

