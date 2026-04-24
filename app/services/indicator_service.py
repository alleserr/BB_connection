from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import Settings
from app.exceptions import IndicatorCalculationError
from app.utils.time_utils import session_key


class IndicatorService:
    """Computes the fixed MVP indicator set in a transparent way."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def apply(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()

        close = result["close"]
        high = result["high"]
        low = result["low"]
        volume = result["volume"]

        result["ema20"] = self._ema(close, 20)
        result["ema50"] = self._ema(close, 50)
        result["ema200"] = self._ema(close, 200)
        result["rsi14"] = self._rsi(close, self.settings.rsi_window)
        result["atr14"] = self._atr(high, low, close, self.settings.atr_window)
        result["relative_volume"] = self._relative_volume(volume, self.settings.relative_volume_window)
        result["vwap"] = self._session_vwap(result)
        result["distance_to_vwap_pct"] = np.where(
            result["vwap"] != 0,
            ((close - result["vwap"]) / result["vwap"]) * 100.0,
            np.nan,
        )
        result["atr_ratio"] = result["atr14"] / result["atr14"].rolling(window=50, min_periods=10).median()

        latest = result.iloc[-1]
        required_fields = [
            "ema20",
            "ema50",
            "ema200",
            "rsi14",
            "atr14",
            "relative_volume",
            "vwap",
            "distance_to_vwap_pct",
        ]
        missing_fields = [field for field in required_fields if pd.isna(latest[field])]
        if missing_fields:
            raise IndicatorCalculationError(
                "INDICATOR_VALUES_MISSING",
                "Indicator calculation produced incomplete values",
                details={"missing_fields": missing_fields},
            )
        return result

    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False, min_periods=span).mean()

    @staticmethod
    def _rsi(series: pd.Series, window: int) -> pd.Series:
        delta = series.diff()
        gains = delta.clip(lower=0.0)
        losses = -delta.clip(upper=0.0)
        average_gain = gains.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        average_loss = losses.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        relative_strength = average_gain / average_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + relative_strength))
        rsi = rsi.mask((average_loss == 0) & average_gain.notna(), 100.0)
        rsi = rsi.mask((average_gain == 0) & average_loss.notna(), 0.0)
        rsi = rsi.mask((average_gain == 0) & (average_loss == 0), 50.0)
        return rsi

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> pd.Series:
        previous_close = close.shift(1)
        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()

    @staticmethod
    def _relative_volume(volume: pd.Series, window: int) -> pd.Series:
        baseline = volume.shift(1).rolling(window=window, min_periods=window).mean().replace(0, np.nan)
        return volume / baseline

    @staticmethod
    def _session_vwap(frame: pd.DataFrame) -> pd.Series:
        typical_price = (frame["high"] + frame["low"] + frame["close"]) / 3.0
        session = session_key(frame["timestamp"])
        volume_price = typical_price * frame["volume"]
        cumulative_volume_price = volume_price.groupby(session).cumsum()
        cumulative_volume = frame["volume"].groupby(session).cumsum().replace(0, np.nan)
        return cumulative_volume_price / cumulative_volume
