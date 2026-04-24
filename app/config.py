from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.exceptions import ConfigurationError


class Settings(BaseModel):
    """Runtime configuration loaded from environment variables."""

    model_config = ConfigDict(extra="forbid")

    bybit_api_key: str | None = None
    bybit_api_secret: str | None = None
    bybit_base_url: str = "https://api.bybit.com"
    default_bars_limit: int = 300
    max_bars_limit: int = 1000
    ema_warmup_bars: int = 20
    relative_volume_window: int = 20
    rsi_window: int = 14
    atr_window: int = 14
    log_level: str = "INFO"
    use_testnet: bool = False
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000
    mcp_public_base_url: str | None = None
    cloudflare_tunnel_enabled: bool = False
    market_category: str = "spot"
    vwap_variant: str = "session_utc"
    request_timeout_seconds: float = 20.0

    @property
    def effective_bybit_base_url(self) -> str:
        if self.use_testnet and self.bybit_base_url == "https://api.bybit.com":
            return "https://api-testnet.bybit.com"
        return self.bybit_base_url.rstrip("/")

    @property
    def minimum_required_bars(self) -> int:
        longest_lookback = max(200, self.relative_volume_window, self.rsi_window, self.atr_window)
        return longest_lookback + self.ema_warmup_bars

    @field_validator("default_bars_limit", "max_bars_limit")
    @classmethod
    def _validate_positive_bars(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than zero")
        return value

    @field_validator("mcp_port")
    @classmethod
    def _validate_port(cls, value: int) -> int:
        if not 0 < value < 65536:
            raise ValueError("must be a valid TCP port")
        return value

    @field_validator("market_category")
    @classmethod
    def _validate_market_category(cls, value: str) -> str:
        if value != "spot":
            raise ValueError("MVP supports only the spot market category")
        return value

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> "Settings":
        if env_file is not None:
            load_dotenv(env_file, override=False)
        else:
            load_dotenv(override=False)

        raw = {
            "bybit_api_key": os.getenv("BYBIT_API_KEY") or None,
            "bybit_api_secret": os.getenv("BYBIT_API_SECRET") or None,
            "bybit_base_url": os.getenv("BYBIT_BASE_URL", "https://api.bybit.com"),
            "default_bars_limit": os.getenv("DEFAULT_BARS_LIMIT", 300),
            "max_bars_limit": os.getenv("MAX_BARS_LIMIT", 1000),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "use_testnet": os.getenv("USE_TESTNET", "false"),
            "mcp_host": os.getenv("MCP_HOST", "127.0.0.1"),
            "mcp_port": os.getenv("MCP_PORT", 8000),
            "mcp_public_base_url": os.getenv("MCP_PUBLIC_BASE_URL") or None,
            "cloudflare_tunnel_enabled": os.getenv("CLOUDFLARE_TUNNEL_ENABLED", "false"),
        }
        try:
            return cls.model_validate(raw)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise ConfigurationError(
                "CONFIGURATION_ERROR",
                "Failed to load application settings",
                details={"reason": str(exc)},
            ) from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()

