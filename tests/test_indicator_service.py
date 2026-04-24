from __future__ import annotations

import pandas as pd

from app.services.indicator_service import IndicatorService


def test_indicator_service_adds_required_columns(settings, sample_ohlcv_frame):
    service = IndicatorService(settings=settings)

    enriched = service.apply(sample_ohlcv_frame)

    for column in ["ema20", "ema50", "ema200", "rsi14", "atr14", "relative_volume", "vwap", "distance_to_vwap_pct"]:
        assert column in enriched.columns
        assert pd.notna(enriched.iloc[-1][column])


def test_rsi_hits_extremes_for_one_way_price_action(settings, sample_ohlcv_frame):
    service = IndicatorService(settings=settings)
    rising = sample_ohlcv_frame.copy()
    rising["close"] = range(1, len(rising) + 1)
    rising["open"] = rising["close"]
    rising["high"] = rising["close"] + 1
    rising["low"] = rising["close"] - 1

    falling = rising.iloc[::-1].reset_index(drop=True).copy()

    rising_result = service.apply(rising)
    falling_result = service.apply(falling)

    assert rising_result.iloc[-1]["rsi14"] == 100.0
    assert falling_result.iloc[-1]["rsi14"] == 0.0


def test_atr_stays_positive(settings, sample_ohlcv_frame):
    service = IndicatorService(settings=settings)

    enriched = service.apply(sample_ohlcv_frame)

    assert enriched.iloc[-1]["atr14"] > 0
