from __future__ import annotations

import argparse
import json

from app.config import get_settings
from app.logging_setup import configure_logging
from app.mcp.server import run_server
from app.mcp.tools import ToolHandlers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bybit spot analytics MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Run one analysis request locally")
    analyze_parser.add_argument("--symbol", required=True)
    analyze_parser.add_argument("--timeframe", required=True, choices=["5m", "15m", "1h", "4h"])
    analyze_parser.add_argument("--bars-limit", type=int, default=None)

    serve_parser = subparsers.add_parser("serve-mcp", help="Run the MCP HTTP server")
    serve_parser.add_argument("--host", default=None)
    serve_parser.add_argument("--port", type=int, default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    if args.command == "serve-mcp":
        if args.host is not None:
            settings.mcp_host = args.host
        if args.port is not None:
            settings.mcp_port = args.port

    configure_logging(settings)

    if args.command == "analyze":
        handlers = ToolHandlers(settings=settings)
        response = handlers.analyze_symbol(
            symbol=args.symbol,
            timeframe=args.timeframe,
            bars_limit=args.bars_limit,
        )
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return

    if args.command == "serve-mcp":
        run_server(settings=settings)


if __name__ == "__main__":
    main()
