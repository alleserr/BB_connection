from __future__ import annotations

from app.exceptions import DataFetchError
from app.models.market import Timeframe
from app.services.bybit_client import BybitClient


def test_get_klines_normalizes_and_sorts_rows(settings, sample_kline_payload):
    from tests.conftest import FakeResponse, FakeSession

    session = FakeSession(FakeResponse(status_code=200, payload=sample_kline_payload))
    client = BybitClient(settings=settings, session=session)

    frame = client.get_klines(symbol="BTCUSDT", timeframe=Timeframe.H1, limit=300)

    assert list(frame.columns[:6]) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert frame["timestamp"].is_monotonic_increasing
    assert frame["close"].dtype.kind == "f"
    assert session.calls[0]["params"]["category"] == "spot"
    assert session.calls[0]["params"]["interval"] == "60"


def test_get_klines_surfaces_region_block_as_structured_error(settings):
    from tests.conftest import FakeResponse, FakeSession

    session = FakeSession(
        FakeResponse(
            status_code=403,
            payload={"retCode": 0},
            text="{ error:The Amazon CloudFront distribution is configured to block access from your country }",
        )
    )
    client = BybitClient(settings=settings, session=session)

    try:
        client.get_klines(symbol="BTCUSDT", timeframe=Timeframe.H1, limit=300)
    except DataFetchError as exc:
        assert exc.error_code == "BYBIT_ACCESS_FORBIDDEN"
        assert exc.details["http_status"] == 403
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("Expected DataFetchError to be raised")
