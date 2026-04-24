from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.config import Settings
from app.exceptions import InputError
from app.models.market import MarketDataWindow, Timeframe
from app.services.bybit_client import BybitClient


@dataclass(frozen=True)
class MarketFrame:
    dataframe: pd.DataFrame
    window: MarketDataWindow


class MarketDataService:
    """Determines the candle window to fetch and retrieves market data."""

    def __init__(self, settings: Settings, bybit_client: BybitClient) -> None:
        self.settings = settings
        self.bybit_client = bybit_client

    def resolve_window(self, bars_limit: int | None) -> MarketDataWindow:
        requested_bars = bars_limit or self.settings.default_bars_limit
        if requested_bars > self.settings.max_bars_limit:
            raise InputError(
                "BARS_LIMIT_TOO_LARGE",
                "bars_limit exceeds MAX_BARS_LIMIT",
                details={
                    "requested_bars": requested_bars,
                    "max_bars_limit": self.settings.max_bars_limit,
                },
            )
        fetch_bars = max(requested_bars, self.settings.minimum_required_bars)
        if fetch_bars > self.settings.max_bars_limit:
            raise InputError(
                "BARS_LIMIT_UNABLE_TO_SATISFY_INDICATORS",
                "Configured MAX_BARS_LIMIT is smaller than the minimum required indicator window",
                details={
                    "requested_bars": requested_bars,
                    "required_bars": self.settings.minimum_required_bars,
                    "max_bars_limit": self.settings.max_bars_limit,
                },
            )
        return MarketDataWindow(
            requested_bars=requested_bars,
            fetch_bars=fetch_bars,
            minimum_required_bars=self.settings.minimum_required_bars,
        )

    def fetch_market_frame(self, symbol: str, timeframe: Timeframe, bars_limit: int | None) -> MarketFrame:
        window = self.resolve_window(bars_limit)
        frame = self.bybit_client.get_klines(symbol=symbol, timeframe=timeframe, limit=window.fetch_bars)
        return MarketFrame(dataframe=frame, window=window)
