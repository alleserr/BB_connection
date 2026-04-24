from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import requests

from app.config import Settings
from app.exceptions import DataFetchError
from app.models.market import Timeframe
from app.utils.dataframe_utils import ensure_numeric_columns
from app.utils.time_utils import normalize_timestamp_ms

LOGGER = logging.getLogger(__name__)


class BybitClient:
    """Thin REST client for Bybit market data."""

    def __init__(self, settings: Settings, session: requests.Session | None = None) -> None:
        self.settings = settings
        self.session = session or requests.Session()

    def get_klines(self, symbol: str, timeframe: Timeframe, limit: int) -> pd.DataFrame:
        url = f"{self.settings.effective_bybit_base_url}/v5/market/kline"
        params = {
            "category": self.settings.market_category,
            "symbol": symbol,
            "interval": timeframe.bybit_interval,
            "limit": limit,
        }
        LOGGER.info("Requesting Bybit klines", extra={"symbol": symbol, "timeframe": timeframe.value, "limit": limit})
        try:
            response = self.session.get(url, params=params, timeout=self.settings.request_timeout_seconds)
        except requests.RequestException as exc:
            raise DataFetchError(
                "BYBIT_API_UNAVAILABLE",
                "Failed to fetch market data from Bybit",
                details={"symbol": symbol, "timeframe": timeframe.value, "reason": str(exc)},
            ) from exc

        if response.status_code == 403:
            raise DataFetchError(
                "BYBIT_ACCESS_FORBIDDEN",
                "Bybit rejected the request. This often means the current IP or region is blocked by Bybit.",
                details={
                    "symbol": symbol,
                    "timeframe": timeframe.value,
                    "base_url": self.settings.effective_bybit_base_url,
                    "http_status": response.status_code,
                    "response_text": response.text[:300],
                },
            )

        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise DataFetchError(
                "BYBIT_API_UNAVAILABLE",
                "Failed to fetch market data from Bybit",
                details={"symbol": symbol, "timeframe": timeframe.value, "reason": str(exc)},
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise DataFetchError(
                "BYBIT_INVALID_JSON",
                "Bybit returned a non-JSON response",
                details={"symbol": symbol, "timeframe": timeframe.value},
            ) from exc

        if payload.get("retCode") != 0:
            raise DataFetchError(
                "BYBIT_API_ERROR",
                payload.get("retMsg", "Bybit returned an error"),
                details={
                    "symbol": symbol,
                    "timeframe": timeframe.value,
                    "ret_code": payload.get("retCode"),
                },
            )

        rows = payload.get("result", {}).get("list") or []
        if not rows:
            raise DataFetchError(
                "EMPTY_API_RESPONSE",
                "Bybit returned an empty candle list",
                details={"symbol": symbol, "timeframe": timeframe.value, "limit": limit},
            )

        return self._normalize_kline_rows(rows, symbol=symbol, timeframe=timeframe)

    def _normalize_kline_rows(
        self,
        rows: list[list[Any]],
        *,
        symbol: str,
        timeframe: Timeframe,
    ) -> pd.DataFrame:
        normalized_rows = [
            {
                "timestamp": normalize_timestamp_ms(row[0]),
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
                "turnover": row[6],
                "symbol": symbol,
                "timeframe": timeframe.value,
            }
            for row in rows
        ]
        frame = pd.DataFrame(normalized_rows)
        frame = ensure_numeric_columns(frame)
        frame = frame.sort_values("timestamp").reset_index(drop=True)
        return frame
