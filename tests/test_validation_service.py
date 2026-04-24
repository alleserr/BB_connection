from __future__ import annotations

from app.exceptions import MarketValidationError
from app.models.market import Timeframe
from app.services.validation_service import ValidationService


def test_validate_ohlcv_accepts_valid_frame(sample_ohlcv_frame):
    service = ValidationService()

    report = service.validate_ohlcv(
        sample_ohlcv_frame,
        symbol="BTCUSDT",
        timeframe=Timeframe.H1,
        minimum_required_bars=220,
    )

    assert report.rows == len(sample_ohlcv_frame)
    assert report.timeframe == Timeframe.H1


def test_validate_ohlcv_rejects_unsorted_timestamps(sample_ohlcv_frame):
    service = ValidationService()
    broken = sample_ohlcv_frame.iloc[::-1].reset_index(drop=True)

    try:
        service.validate_ohlcv(
            broken,
            symbol="BTCUSDT",
            timeframe=Timeframe.H1,
            minimum_required_bars=220,
        )
    except MarketValidationError as exc:
        assert exc.error_code == "UNSORTED_TIMESTAMPS"
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected MarketValidationError")

