from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_timestamp_ms(value: str | int | float) -> pd.Timestamp:
    return pd.to_datetime(int(value), unit="ms", utc=True)


def session_key(timestamp: pd.Series) -> pd.Series:
    """Group timestamps by UTC day for the session VWAP."""

    return timestamp.dt.floor("D")
