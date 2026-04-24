from __future__ import annotations

from app.models.snapshot import PriceVsVWAPState, TrendDirection, TrendStrength, VolumeState
from app.services.feature_service import FeatureService


def test_feature_service_builds_states_and_flags():
    latest_row = {
        "close": 105.0,
        "ema20": 100.0,
        "ema50": 98.0,
        "ema200": 95.0,
        "rsi14": 62.0,
        "relative_volume": 1.4,
        "distance_to_vwap_pct": 0.25,
    }
    service = FeatureService()

    features, states, flags = service.build(latest_row=latest_row, atr_ratio=1.1)

    assert features.price_above_ema20 is True
    assert states.trend_direction == TrendDirection.BULLISH
    assert states.trend_strength == TrendStrength.STRONG
    assert states.volume_state == VolumeState.ELEVATED
    assert states.price_vs_vwap_state == PriceVsVWAPState.NEAR
    assert "trend_continuation" in flags.setup_flags
