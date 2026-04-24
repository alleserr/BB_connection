from __future__ import annotations

import pandas as pd


REQUIRED_OHLCV_COLUMNS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

NUMERIC_COLUMNS = ["open", "high", "low", "close", "volume", "turnover"]


def ensure_numeric_columns(frame: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    result = frame.copy()
    for column in columns or NUMERIC_COLUMNS:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result
