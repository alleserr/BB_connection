from __future__ import annotations

from app.config import Settings
from app.models.market import AnalyzeSymbolRequest, CompareSymbolsRequest, GetRawSnapshotRequest, ScanWatchlistRequest
from app.models.snapshot import (
    CompareSummary,
    CompareSymbolsData,
    MarketSnapshot,
    ScanWatchlistData,
    TrendDirection,
    TrendStrength,
)
from app.services.bybit_client import BybitClient
from app.services.feature_service import FeatureService
from app.services.indicator_service import IndicatorService
from app.services.market_data_service import MarketDataService
from app.services.scan_service import WatchlistScoringService
from app.services.snapshot_service import SnapshotService
from app.services.validation_service import ValidationService


class AnalysisService:
    """Coordinates the end-to-end market analysis workflow."""

    def __init__(self, settings: Settings, bybit_client: BybitClient | None = None) -> None:
        self.settings = settings
        self.bybit_client = bybit_client or BybitClient(settings=settings)
        self.market_data_service = MarketDataService(settings=settings, bybit_client=self.bybit_client)
        self.validation_service = ValidationService()
        self.indicator_service = IndicatorService(settings=settings)
        self.feature_service = FeatureService()
        self.snapshot_service = SnapshotService(settings=settings)
        self.watchlist_scoring_service = WatchlistScoringService()

    def analyze_symbol(self, request: AnalyzeSymbolRequest) -> MarketSnapshot:
        market_frame = self.market_data_service.fetch_market_frame(
            symbol=request.symbol,
            timeframe=request.timeframe,
            bars_limit=request.bars_limit,
        )
        self.validation_service.validate_ohlcv(
            market_frame.dataframe,
            symbol=request.symbol,
            timeframe=request.timeframe,
            minimum_required_bars=market_frame.window.minimum_required_bars,
        )
        enriched = self.indicator_service.apply(market_frame.dataframe)
        latest = enriched.iloc[-1].to_dict()
        atr_ratio = latest.get("atr_ratio")
        features, states, flags = self.feature_service.build(
            latest_row=latest,
            atr_ratio=None if atr_ratio is None else float(atr_ratio),
        )
        return self.snapshot_service.build(
            symbol=request.symbol,
            timeframe=request.timeframe.value,
            latest_row=latest,
            requested_bars=market_frame.window.requested_bars,
            bars_used=len(enriched),
            features=features,
            states=states,
            flags=flags,
        )

    def get_raw_snapshot(self, request: GetRawSnapshotRequest) -> MarketSnapshot:
        return self.analyze_symbol(
            AnalyzeSymbolRequest(
                symbol=request.symbol,
                timeframe=request.timeframe,
            )
        )

    def compare_symbols(self, request: CompareSymbolsRequest) -> CompareSymbolsData:
        snapshots = [
            self.analyze_symbol(
                AnalyzeSymbolRequest(
                    symbol=symbol,
                    timeframe=request.timeframe,
                    bars_limit=request.bars_limit,
                )
            )
            for symbol in request.symbols
        ]
        top_trend = max(
            snapshots,
            key=lambda snapshot: (
                snapshot.states.trend_direction == TrendDirection.BULLISH,
                snapshot.states.trend_strength == TrendStrength.STRONG,
                snapshot.indicators.relative_volume,
            ),
        )
        top_volume = max(snapshots, key=lambda snapshot: snapshot.indicators.relative_volume)
        summary = CompareSummary(
            top_symbol_by_trend=top_trend.symbol if snapshots else None,
            top_symbol_by_relative_volume=top_volume.symbol if snapshots else None,
            bullish_symbols=[item.symbol for item in snapshots if item.states.trend_direction == TrendDirection.BULLISH],
            bearish_symbols=[item.symbol for item in snapshots if item.states.trend_direction == TrendDirection.BEARISH],
        )
        return CompareSymbolsData(timeframe=request.timeframe, snapshots=snapshots, summary=summary)

    def scan_watchlist(self, request: ScanWatchlistRequest) -> ScanWatchlistData:
        results = []
        for symbol in request.symbols:
            snapshot = self.analyze_symbol(
                AnalyzeSymbolRequest(
                    symbol=symbol,
                    timeframe=request.timeframe,
                    bars_limit=request.bars_limit,
                )
            )
            results.append(self.watchlist_scoring_service.score_snapshot(snapshot))
        sorted_results = sorted(results, key=lambda item: item.score, reverse=True)
        return ScanWatchlistData(
            timeframe=request.timeframe,
            scan_mode=request.scan_mode.value,
            results=sorted_results,
        )
