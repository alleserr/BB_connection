from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import pytest

from app.config import Settings


@pytest.fixture()
def settings() -> Settings:
    return Settings()


@pytest.fixture()
def sample_ohlcv_frame() -> pd.DataFrame:
    periods = 300
    timestamps = pd.date_range("2026-04-20 00:00:00+00:00", periods=periods, freq="1h")
    close = np.linspace(100.0, 160.0, periods) + np.sin(np.linspace(0, 8 * math.pi, periods))
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close - 0.5,
            "high": close + 1.5,
            "low": close - 1.5,
            "close": close,
            "volume": np.linspace(1000.0, 1800.0, periods) + 50 * np.cos(np.linspace(0, 4 * math.pi, periods)),
        }
    )
    frame["turnover"] = frame["close"] * frame["volume"]
    frame["symbol"] = "BTCUSDT"
    frame["timeframe"] = "1h"
    return frame


@pytest.fixture()
def sample_kline_payload(sample_ohlcv_frame: pd.DataFrame) -> dict[str, Any]:
    reversed_rows = []
    for row in sample_ohlcv_frame.iloc[::-1].itertuples(index=False):
        reversed_rows.append(
            [
                str(int(row.timestamp.timestamp() * 1000)),
                f"{row.open:.4f}",
                f"{row.high:.4f}",
                f"{row.low:.4f}",
                f"{row.close:.4f}",
                f"{row.volume:.4f}",
                f"{row.turnover:.4f}",
            ]
        )
    return {
        "retCode": 0,
        "retMsg": "OK",
        "result": {"category": "spot", "symbol": "BTCUSDT", "list": reversed_rows},
        "retExtInfo": {},
        "time": 0,
    }


@dataclass
class FakeResponse:
    status_code: int
    payload: dict[str, Any] | None = None
    text: str = ""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code} error")

    def json(self) -> dict[str, Any]:
        if self.payload is None:
            raise ValueError("no json")
        return self.payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.response
