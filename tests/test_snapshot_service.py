from __future__ import annotations

from app.models.snapshot import FeatureSnapshot, FlagSnapshot, StateSnapshot
from app.services.snapshot_service import SnapshotService


def test_snapshot_service_builds_market_snapshot(settings):
    service = SnapshotService(settings=settings)
    latest_row = {
        "timestamp": "2026-04-23T18:00:00Z",
        "close": 105.0,
        "ema20": 100.0,
        "ema50": 98.0,
        "ema200": 95.0,
        "rsi14": 62.0,
        "atr14": 3.5,
        "vwap": 103.0,
        "distance_to_vwap_pct": 1.94,
        "relative_volume": 1.25,
    }

    snapshot = service.build(
        symbol="BTCUSDT",
        timeframe="1h",
        latest_row=latest_row,
        requested_bars=300,
        bars_used=300,
        features=FeatureSnapshot(
            price_above_ema20=True,
            price_above_ema50=True,
            price_above_ema200=True,
            ema20_above_ema50=True,
            ema50_above_ema200=True,
        ),
        states=StateSnapshot(
            trend_direction="bullish",
            trend_strength="strong",
            rsi_state="strong",
            atr_state="normal",
            volume_state="elevated",
            price_vs_vwap_state="above",
        ),
        flags=FlagSnapshot(setup_flags=["trend_continuation"], risk_flags=[]),
    )

    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.meta.vwap_variant == "session_utc"
    assert snapshot.indicators.vwap == 103.0
