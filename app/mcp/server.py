from __future__ import annotations
from typing import Any
from urllib.parse import urlparse

from starlette.responses import JSONResponse

from app.config import Settings, get_settings
from app.mcp.tools import ToolHandlers


def _build_transport_security(settings: Settings) -> Any:
    from mcp.server.transport_security import TransportSecuritySettings

    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]

    if settings.mcp_public_base_url:
        parsed = urlparse(settings.mcp_public_base_url)
        if parsed.hostname:
            allowed_hosts.append(parsed.hostname)
            allowed_hosts.append(f"{parsed.hostname}:*")
            origin = f"{parsed.scheme}://{parsed.netloc}"
            allowed_origins.append(origin)
            if parsed.hostname and parsed.scheme:
                allowed_origins.append(f"{parsed.scheme}://{parsed.hostname}:*")

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def create_mcp_server(settings: Settings | None = None) -> Any:
    """Create a FastMCP server without coupling business logic to the SDK."""

    resolved_settings = settings or get_settings()
    from mcp.server.fastmcp import FastMCP

    handlers = ToolHandlers(settings=resolved_settings)
    mcp = FastMCP(
        name="Bybit Spot Analytics",
        instructions=(
            "Use these tools to fetch real Bybit spot candles, validate them, compute indicators, "
            "and return typed market snapshots. Do not invent missing data."
        ),
        stateless_http=True,
        json_response=True,
        transport_security=_build_transport_security(resolved_settings),
    )
    mcp.settings.host = resolved_settings.mcp_host
    mcp.settings.port = resolved_settings.mcp_port
    mcp.settings.streamable_http_path = "/mcp"

    @mcp.tool()
    def analyze_symbol(symbol: str, timeframe: str, bars_limit: int | None = None) -> dict[str, Any]:
        """Analyze one Bybit spot symbol on one timeframe."""

        return handlers.analyze_symbol(symbol=symbol, timeframe=timeframe, bars_limit=bars_limit)

    @mcp.tool()
    def compare_symbols(symbols: list[str], timeframe: str, bars_limit: int | None = None) -> dict[str, Any]:
        """Compare several Bybit spot symbols on the same timeframe."""

        return handlers.compare_symbols(symbols=symbols, timeframe=timeframe, bars_limit=bars_limit)

    @mcp.tool()
    def scan_watchlist(
        symbols: list[str],
        timeframe: str,
        scan_mode: str = "balanced",
        bars_limit: int | None = None,
    ) -> dict[str, Any]:
        """Run the transparent balanced watchlist scan for a list of symbols."""

        return handlers.scan_watchlist(
            symbols=symbols,
            timeframe=timeframe,
            scan_mode=scan_mode,
            bars_limit=bars_limit,
        )

    @mcp.tool()
    def get_raw_snapshot(symbol: str, timeframe: str) -> dict[str, Any]:
        """Return the raw technical snapshot without extra aggregation."""

        return handlers.get_raw_snapshot(symbol=symbol, timeframe=timeframe)

    @mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def healthcheck(_request: Any) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "bybit-spot-analytics"})

    return mcp


def build_asgi_app(settings: Settings | None = None) -> Any:
    resolved_settings = settings or get_settings()
    mcp = create_mcp_server(settings=resolved_settings)
    return mcp.streamable_http_app()


def run_server(settings: Settings | None = None) -> None:
    resolved_settings = settings or get_settings()
    import uvicorn

    uvicorn.run(
        build_asgi_app(resolved_settings),
        host=resolved_settings.mcp_host,
        port=resolved_settings.mcp_port,
        log_level=resolved_settings.log_level.lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
