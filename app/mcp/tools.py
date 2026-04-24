from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.config import Settings
from app.exceptions import AppError, InputError
from app.models.market import AnalyzeSymbolRequest, CompareSymbolsRequest, GetRawSnapshotRequest, ScanWatchlistRequest
from app.models.snapshot import ErrorPayload, ToolErrorResponse
from app.services.analysis_service import AnalysisService

LOGGER = logging.getLogger(__name__)


class ToolHandlers:
    """Thin adapters between MCP tool calls and the analysis service."""

    def __init__(self, settings: Settings, analysis_service: AnalysisService | None = None) -> None:
        self.settings = settings
        self.analysis_service = analysis_service or AnalysisService(settings=settings)

    def analyze_symbol(self, symbol: str, timeframe: str, bars_limit: int | None = None) -> dict[str, Any]:
        return self._execute(
            AnalyzeSymbolRequest,
            self.analysis_service.analyze_symbol,
            {"symbol": symbol, "timeframe": timeframe, "bars_limit": bars_limit},
        )

    def compare_symbols(self, symbols: list[str], timeframe: str, bars_limit: int | None = None) -> dict[str, Any]:
        return self._execute(
            CompareSymbolsRequest,
            self.analysis_service.compare_symbols,
            {"symbols": symbols, "timeframe": timeframe, "bars_limit": bars_limit},
        )

    def scan_watchlist(
        self,
        symbols: list[str],
        timeframe: str,
        scan_mode: str = "balanced",
        bars_limit: int | None = None,
    ) -> dict[str, Any]:
        if scan_mode != "balanced":
            return self._error_response(
                InputError(
                    "unsupported_scan_mode",
                    "Only the balanced scan mode is supported in the MVP",
                    details={"received_scan_mode": scan_mode, "supported_scan_mode": "balanced"},
                )
            )
        return self._execute(
            ScanWatchlistRequest,
            self.analysis_service.scan_watchlist,
            {
                "symbols": symbols,
                "timeframe": timeframe,
                "scan_mode": scan_mode,
                "bars_limit": bars_limit,
            },
        )

    def get_raw_snapshot(self, symbol: str, timeframe: str) -> dict[str, Any]:
        return self._execute(
            GetRawSnapshotRequest,
            self.analysis_service.get_raw_snapshot,
            {"symbol": symbol, "timeframe": timeframe},
        )

    def _execute(self, request_model: Any, operation: Any, payload: dict[str, Any]) -> dict[str, Any]:
        LOGGER.info("Handling MCP request", extra={"operation": operation.__name__, "payload": payload})
        try:
            validated_request = request_model.model_validate(payload)
            data = operation(validated_request)
            return {"status": "ok", "data": data.model_dump(mode="json")}
        except ValidationError as exc:
            return self._error_response(
                InputError(
                    "INVALID_INPUT",
                    "Request parameters are invalid",
                    details={"errors": exc.errors(include_url=False)},
                )
            )
        except AppError as exc:
            return self._error_response(exc)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return self._error_response(
                AppError(
                    "UNEXPECTED_ERROR",
                    "An unexpected internal error occurred",
                    details={"reason": str(exc)},
                )
            )

    @staticmethod
    def _error_response(exc: AppError) -> dict[str, Any]:
        return ToolErrorResponse(
            error=ErrorPayload(code=exc.error_code, message=exc.message, details=exc.details)
        ).model_dump(mode="json")
