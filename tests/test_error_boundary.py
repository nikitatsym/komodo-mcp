from __future__ import annotations

import asyncio

import httpx
import pytest

from komodo_mcp import _generated, server
from komodo_mcp.client import KomodoError


def _raise(exc: Exception):
    raise exc


def _registered(name: str):
    return server.mcp._tool_manager._tools[name].fn


def test_dispatch_returns_contextual_api_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "_coerce_call",
        lambda *_args: _raise(KomodoError(404, "read", "ListServers", {"detail": "missing"})),
    )

    result = server._dispatch("ListServers", "komodo_read", {})

    assert result == {"error": "Komodo API 404 read ListServers: {'detail': 'missing'}"}


def test_dispatch_redacts_async_waiter_transport_query_values(monkeypatch):
    request = httpx.Request("POST", "https://komodo.example/read?api_key=secret")

    async def failing_waiter():
        raise httpx.ConnectError("connection refused", request=request)

    monkeypatch.setattr(server, "_coerce_call", lambda *_args: failing_waiter())

    result = asyncio.run(server._dispatch("UpdatesWait", "komodo_read", {}))

    assert "Komodo transport failure: POST /read: ConnectError" in result["error"]
    assert "secret" not in result["error"]
    assert "api_key=" not in result["error"]


def test_dispatch_returns_missing_parameter_error():
    result = server._dispatch("UpdatesWait", "komodo_read", {})

    assert result["error"] == "Missing required parameters: ['update_id']"


def test_dispatch_propagates_programming_error(monkeypatch):
    monkeypatch.setattr(
        server, "_coerce_call", lambda *_args: _raise(AttributeError("programming error"))
    )

    with pytest.raises(AttributeError):
        server._dispatch("ListServers", "komodo_read", {})


def test_deferred_waiter_cancellation_propagates(monkeypatch):
    """CancelledError is a BaseException: the await-time guard must not eat it."""

    async def hanging_waiter():
        await asyncio.sleep(3600)

    monkeypatch.setattr(server, "_coerce_call", lambda *_args: hanging_waiter())

    async def flow():
        task = asyncio.ensure_future(server._dispatch("UpdatesWait", "komodo_read", {}))
        await asyncio.sleep(0)
        task.cancel()
        await task

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(flow())


def test_registered_root_returns_contextual_api_error(monkeypatch):
    class BrokenClient:
        def read(self, *_args, **_kwargs):
            raise KomodoError(503, "read", "GetVersion", {"detail": "unavailable"})

    monkeypatch.setattr(_generated, "_get_client", lambda: BrokenClient())

    result = _registered("get_version")()

    assert result == {"error": "Komodo API 503 read GetVersion: {'detail': 'unavailable'}"}


def test_registered_root_redacts_transport_query_values(monkeypatch):
    request = httpx.Request("POST", "https://komodo.example/read?api_key=secret")

    class DownClient:
        def read(self, *_args, **_kwargs):
            raise httpx.ConnectError("connection refused", request=request)

    monkeypatch.setattr(_generated, "_get_client", lambda: DownClient())

    result = _registered("get_version")()

    assert "Komodo transport failure: POST /read: ConnectError" in result["error"]
    assert "secret" not in result["error"]
    assert "api_key=" not in result["error"]


def test_registered_root_preserves_success_shape(monkeypatch):
    class OkClient:
        def read(self, *_args, **_kwargs):
            return {"version": "1.19.4"}

    monkeypatch.setattr(_generated, "_get_client", lambda: OkClient())

    assert _registered("get_version")() == {"version": "1.19.4"}


def test_error_text_redacts_secret_fields():
    """Container values are redacted whole: a partial match would leave the
    tail of a list or nested dict in the reported error."""
    text = server._redact_error_text(
        {"password": ["too short", "p@ssw0rd"], "api_secret": "zzz", "detail": "keep me"}
    )

    assert "p@ssw0rd" not in text
    assert "zzz" not in text
    assert "keep me" in text
