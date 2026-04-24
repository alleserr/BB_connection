from __future__ import annotations

from app.exceptions import DataFetchError, MarketValidationError
from app.models.market import AnalyzeSymbolRequest, Timeframe
from app.services.analysis_service import AnalysisService


class StubBybitClient:
    def __init__(self, frame):
        self.frame = frame

    def get_klines(self, symbol: str, timeframe: Timeframe, limit: int):
        return self.frame.copy()


class EmptyBybitClient:
    def get_klines(self, symbol: str, timeframe: Timeframe, limit: int):
        raise DataFetchError("EMPTY_API_RESPONSE", "Bybit returned an empty candle list", details={"symbol": symbol})


def test_analysis_service_runs_successfully(settings, sample_ohlcv_frame):
    service = AnalysisService(settings=settings, bybit_client=StubBybitClient(sample_ohlcv_frame))

    snapshot = service.analyze_symbol(AnalyzeSymbolRequest(symbol="BTCUSDT", timeframe="1h", bars_limit=300))

    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.states.trend_direction in {"bullish", "neutral", "bearish"}


def test_analysis_service_raises_on_insufficient_data(settings, sample_ohlcv_frame):
    too_short = sample_ohlcv_frame.head(100)
    service = AnalysisService(settings=settings, bybit_client=StubBybitClient(too_short))

    try:
        service.analyze_symbol(AnalyzeSymbolRequest(symbol="BTCUSDT", timeframe="1h", bars_limit=100))
    except MarketValidationError as exc:
        assert exc.error_code == "INSUFFICIENT_DATA"
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected MarketValidationError")


def test_no_fake_analytics_when_market_data_fails(settings):
    service = AnalysisService(settings=settings, bybit_client=EmptyBybitClient())

    try:
        service.analyze_symbol(AnalyzeSymbolRequest(symbol="BTCUSDT", timeframe="1h"))
    except DataFetchError as exc:
        assert exc.error_code == "EMPTY_API_RESPONSE"
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected DataFetchError")
