from __future__ import annotations

import pandas as pd

from app.exceptions import MarketValidationError
from app.models.market import Timeframe, ValidationReport
from app.utils.dataframe_utils import REQUIRED_OHLCV_COLUMNS


class ValidationService:
    """Validates normalized OHLCV data before any analytics are computed."""

    def validate_ohlcv(
        self,
        frame: pd.DataFrame,
        *,
        symbol: str,
        timeframe: Timeframe,
        minimum_required_bars: int,
    ) -> ValidationReport:
        if frame.empty:
            raise MarketValidationError(
                "EMPTY_DATA",
                "No OHLCV data was returned",
                details={"symbol": symbol, "timeframe": timeframe.value},
            )

        if len(frame) < minimum_required_bars:
            raise MarketValidationError(
                "INSUFFICIENT_DATA",
                "Not enough candles to compute the required indicators",
                details={
                    "symbol": symbol,
                    "timeframe": timeframe.value,
                    "required_bars": minimum_required_bars,
                    "received_bars": len(frame),
                },
            )

        missing_columns = [column for column in REQUIRED_OHLCV_COLUMNS if column not in frame.columns]
        if missing_columns:
            raise MarketValidationError(
                "MISSING_COLUMNS",
                "Required OHLCV columns are missing",
                details={"missing_columns": missing_columns},
            )

        if frame[REQUIRED_OHLCV_COLUMNS].isnull().any().any():
            raise MarketValidationError(
                "NULL_VALUES",
                "OHLCV data contains null values",
                details={"symbol": symbol, "timeframe": timeframe.value},
            )

        if not frame["timestamp"].is_monotonic_increasing:
            raise MarketValidationError(
                "UNSORTED_TIMESTAMPS",
                "Timestamps must be sorted in ascending order",
                details={"symbol": symbol, "timeframe": timeframe.value},
            )

        if frame["timestamp"].duplicated().any():
            raise MarketValidationError(
                "DUPLICATE_TIMESTAMPS",
                "Duplicate candle timestamps were detected",
                details={"symbol": symbol, "timeframe": timeframe.value},
            )

        numeric_columns = ["open", "high", "low", "close", "volume"]
        for column in numeric_columns:
            if not pd.api.types.is_numeric_dtype(frame[column]):
                raise MarketValidationError(
                    "INVALID_COLUMN_TYPE",
                    "OHLCV columns must be numeric",
                    details={"column": column},
                )

        if (frame["high"] < frame["low"]).any():
            raise MarketValidationError(
                "INVALID_HIGH_LOW",
                "Every candle must satisfy high >= low",
                details={"symbol": symbol, "timeframe": timeframe.value},
            )

        open_out_of_range = (frame["open"] < frame["low"]) | (frame["open"] > frame["high"])
        close_out_of_range = (frame["close"] < frame["low"]) | (frame["close"] > frame["high"])
        if open_out_of_range.any() or close_out_of_range.any():
            raise MarketValidationError(
                "INVALID_OPEN_CLOSE_RANGE",
                "Open and close must stay inside each candle range",
                details={"symbol": symbol, "timeframe": timeframe.value},
            )

        if (frame["volume"] < 0).any():
            raise MarketValidationError(
                "NEGATIVE_VOLUME",
                "Volume cannot be negative",
                details={"symbol": symbol, "timeframe": timeframe.value},
            )

        deltas = frame["timestamp"].diff().dropna()
        if not deltas.empty:
            expected_delta = pd.Timedelta(timeframe.duration)
            if not (deltas == expected_delta).all():
                raise MarketValidationError(
                    "INVALID_TIMEFRAME_STEP",
                    "Candle spacing does not match the requested timeframe",
                    details={
                        "symbol": symbol,
                        "timeframe": timeframe.value,
                        "expected_step": str(expected_delta),
                    },
                )

        return ValidationReport(
            rows=len(frame),
            start_timestamp=frame["timestamp"].iloc[0],
            end_timestamp=frame["timestamp"].iloc[-1],
            timeframe=timeframe,
        )
