from __future__ import annotations

from app.config import Settings
from app.mcp.tools import ToolHandlers
from app.models.market import AnalyzeSymbolRequest, Timeframe
from app.models.snapshot import FeatureSnapshot, FlagSnapshot, MarketSnapshot, SnapshotMeta, StateSnapshot


def build_snapshot(symbol: str = "BTCUSDT") -> MarketSnapshot:
    return MarketSnapshot(
        symbol=symbol,
        timeframe=Timeframe.H1,
        as_of="2026-04-23T18:00:00Z",
        price=105.0,
        indicators={
            "ema20": 100.0,
            "ema50": 98.0,
            "ema200": 95.0,
            "rsi14": 62.0,
            "atr14": 3.5,
            "vwap": 103.0,
            "distance_to_vwap_pct": 1.94,
            "relative_volume": 1.2,
        },
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
        meta=SnapshotMeta(bars_requested=300, bars_used=300),
    )


class StubAnalysisService:
    def analyze_symbol(self, request: AnalyzeSymbolRequest) -> MarketSnapshot:
        return build_snapshot(symbol=request.symbol)

    def compare_symbols(self, request):
        return {"timeframe": request.timeframe.value, "snapshots": [build_snapshot(symbol=s) for s in request.symbols], "summary": {}}

    def get_raw_snapshot(self, request):
        return build_snapshot(symbol=request.symbol)

    def scan_watchlist(self, request):
        return {"timeframe": request.timeframe.value, "scan_mode": request.scan_mode.value, "results": []}


def test_analyze_symbol_returns_wrapped_success():
    handlers = ToolHandlers(settings=Settings(), analysis_service=StubAnalysisService())

    result = handlers.analyze_symbol(symbol="btcusdt", timeframe="1h")

    assert result["status"] == "ok"
    assert result["data"]["symbol"] == "BTCUSDT"


def test_analyze_symbol_rejects_invalid_input():
    handlers = ToolHandlers(settings=Settings(), analysis_service=StubAnalysisService())

    result = handlers.analyze_symbol(symbol="BTCUSDT", timeframe="10m")

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_scan_watchlist_rejects_unsupported_scan_mode():
    handlers = ToolHandlers(settings=Settings(), analysis_service=StubAnalysisService())

    result = handlers.scan_watchlist(symbols=["BTCUSDT"], timeframe="1h", scan_mode="momentum")

    assert result["status"] == "error"
    assert result["error"]["code"] == "unsupported_scan_mode"
