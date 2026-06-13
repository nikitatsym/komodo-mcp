"""Unit tests for the update waiters (`updates_wait` + start/poll/cancel).

Komodo's RPC client posts {"type": op, "params": ...} to /read; the mock
handler scripts responses per operation type. Blocking tests patch
`asyncio.sleep` to a no-op; non-blocking tests run real (tiny) sleeps so
the background task gets actual event-loop turns.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

import komodo_mcp._helpers as helpers_mod
import komodo_mcp.tools as tools_mod
from komodo_mcp.client import KomodoClient, KomodoError
from komodo_mcp.config import _reset_settings
from komodo_mcp.wait_registry import WAIT_REGISTRY

UPDATE_ID = "65a1b2c3d4e5f6a7b8c9d0e1"


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    monkeypatch.setenv("KOMODO_URL", "https://komodo.example.com")
    monkeypatch.setenv("KOMODO_API_KEY", "k")
    monkeypatch.setenv("KOMODO_API_SECRET", "s")
    _reset_settings()
    helpers_mod._client = None
    WAIT_REGISTRY.clear()
    yield
    WAIT_REGISTRY.clear()
    helpers_mod._client = None
    _reset_settings()


@pytest.fixture
def instant_sleep(monkeypatch):
    async def _instant(_secs):
        return None
    monkeypatch.setattr(asyncio, "sleep", _instant)


def _seed(handler) -> KomodoClient:
    client = KomodoClient(transport=httpx.MockTransport(handler))
    helpers_mod._client = client
    return client


def _update(status: str, success: bool = True, logs: list | None = None) -> dict:
    return {
        "_id": {"$oid": UPDATE_ID},
        "operation": "RunBuild",
        "status": status,
        "success": success,
        "target": {"type": "Build", "id": "b1"},
        "start_ts": 1765600000000,
        "logs": logs or [],
    }


def _stage(stage: str, success: bool, stdout: str = "", stderr: str = "") -> dict:
    return {
        "stage": stage, "command": f"run {stage}", "success": success,
        "stdout": stdout, "stderr": stderr,
    }


def _make_handler(scripts: dict[str, list]):
    """Scripts keyed by RPC operation type; the last item repeats forever."""
    def handler(req: httpx.Request) -> httpx.Response:
        op = json.loads(req.content)["type"]
        script = scripts.get(op)
        if not script:
            return httpx.Response(404, json={"error": f"no script for {op}"})
        item = script.pop(0) if len(script) > 1 else script[0]
        status, payload = item
        return httpx.Response(status, json=payload)
    return handler


# ── updates_wait (blocking) ──────────────────────────────────────────────────


class TestUpdatesWait:
    def test_reaches_complete_after_polls(self, instant_sleep):
        scripts = {"GetUpdate": [
            (200, _update("Queued")),
            (200, _update("InProgress")),
            (200, _update("Complete", success=True,
                          logs=[_stage("build", True, stdout="ok")])),
        ]}
        _seed(_make_handler(scripts))
        result = asyncio.run(tools_mod.updates_wait(
            update_id=UPDATE_ID, timeout=60.0, interval=0.01,
        ))
        assert result["terminated"] is True
        assert result["status"] == "Complete"
        assert result["success"] is True
        assert result["polls"] == 3
        # failed_only=True and everything succeeded -> no logs attached.
        assert result["logs"] == []
        # Snapshot meta carries stage successes without stdout.
        assert result["update"]["stages"] == [{"stage": "build", "success": True}]

    def test_failed_update_attaches_failed_stage_logs(self, instant_sleep):
        boom = "\n".join(f"line{i}" for i in range(10)) + "\nERROR: boom"
        scripts = {"GetUpdate": [
            (200, _update("InProgress")),
            (200, _update("Complete", success=False, logs=[
                _stage("pull", True, stdout="pulled"),
                _stage("build", False, stderr=boom),
            ])),
        ]}
        _seed(_make_handler(scripts))
        result = asyncio.run(tools_mod.updates_wait(
            update_id=UPDATE_ID, timeout=60.0, interval=0.01, log_tail=3,
        ))
        assert result["success"] is False
        assert len(result["logs"]) == 1  # failed_only drops the passing stage
        entry = result["logs"][0]
        assert entry["stage"] == "build"
        assert "ERROR: boom" in entry["stderr"]
        assert "lines truncated" in entry["stderr"]

    def test_timeout_returns_partial(self, instant_sleep):
        scripts = {"GetUpdate": [(200, _update("InProgress"))]}
        _seed(_make_handler(scripts))
        result = asyncio.run(tools_mod.updates_wait(
            update_id=UPDATE_ID, timeout=0.05, interval=0.02,
        ))
        assert result["terminated"] is False
        assert result["timed_out"] is True
        assert result["status"] == "InProgress"
        assert "logs" not in result

    def test_transient_blip_tolerated_and_budget_raises(self, instant_sleep):
        scripts = {"GetUpdate": [
            (200, _update("InProgress")),
            (502, {"error": "bad gateway"}),
            (200, _update("Complete")),
        ]}
        _seed(_make_handler(scripts))
        result = asyncio.run(tools_mod.updates_wait(
            update_id=UPDATE_ID, timeout=60.0, interval=0.01,
        ))
        assert result["terminated"] is True
        assert result["poll_failures"] == 1
        assert "502" in result["last_poll_error"]

        scripts = {"GetUpdate": [
            (200, _update("InProgress")),
            (502, {"error": "bad gateway"}),  # repeats forever
        ]}
        _seed(_make_handler(scripts))
        with pytest.raises(KomodoError, match="502"):
            asyncio.run(tools_mod.updates_wait(
                update_id=UPDATE_ID, timeout=60.0, interval=0.01,
                max_poll_failures=2,
            ))

    def test_fatal_4xx_raises_immediately(self, instant_sleep):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(200, json=_update("InProgress"))
            return httpx.Response(400, json={"error": "unknown update"})

        _seed(handler)
        with pytest.raises(KomodoError, match="400"):
            asyncio.run(tools_mod.updates_wait(
                update_id=UPDATE_ID, timeout=60.0, interval=0.01,
                max_poll_failures=5,
            ))
        assert calls["n"] == 2

    def test_rejects_bad_params(self):
        _seed(_make_handler({}))
        with pytest.raises(ValueError, match="interval must be > 0"):
            asyncio.run(tools_mod.updates_wait(update_id=UPDATE_ID, interval=0))
        with pytest.raises(ValueError, match="max_poll_failures must be >= 1"):
            asyncio.run(tools_mod.updates_wait(update_id=UPDATE_ID, max_poll_failures=0))


# ── start / poll / cancel ────────────────────────────────────────────────────


class TestWaitStartPoll:
    def test_terminal_on_first_poll(self):
        scripts = {"GetUpdate": [(200, _update("Complete", success=True))]}
        _seed(_make_handler(scripts))
        snap = asyncio.run(tools_mod.updates_wait_start(
            update_id=UPDATE_ID, interval=0.01,
        ))
        assert snap["terminated"] is True
        assert snap["status"] == "Complete"
        assert snap["success"] is True
        assert snap["wait_id"].startswith("wu-")
        assert snap["update_id"] == UPDATE_ID
        assert WAIT_REGISTRY.get(snap["wait_id"]).task is None

    def test_max_block_waits_for_terminal(self):
        scripts = {"GetUpdate": [
            (200, _update("InProgress")),
            (200, _update("Complete", success=True)),
        ]}
        _seed(_make_handler(scripts))

        async def flow():
            start = await tools_mod.updates_wait_start(
                update_id=UPDATE_ID, interval=0.01,
            )
            poll = await tools_mod.updates_wait_poll(start["wait_id"], max_block=5.0)
            return start, poll

        start, poll = asyncio.run(flow())
        assert start["status"] == "InProgress"
        assert poll["terminated"] is True
        assert poll["status"] == "Complete"
        statuses = [t["to"] for t in poll["transitions"]]
        assert statuses == ["InProgress", "Complete"]

    def test_cancel_and_max_lifetime(self):
        scripts = {"GetUpdate": [(200, _update("InProgress"))]}
        _seed(_make_handler(scripts))

        async def flow():
            start = await tools_mod.updates_wait_start(
                update_id=UPDATE_ID, interval=0.01,
            )
            cancelled = await tools_mod.updates_wait_cancel(start["wait_id"])

            start2 = await tools_mod.updates_wait_start(
                update_id=UPDATE_ID, interval=0.01, max_lifetime=0.05,
            )
            expired = await tools_mod.updates_wait_poll(start2["wait_id"], max_block=5.0)
            return cancelled, expired

        cancelled, expired = asyncio.run(flow())
        assert cancelled["error"] == "cancelled"
        assert expired["timed_out"] is True
        assert "max_lifetime" in expired["error"]

    def test_waits_list_and_unknown_id(self):
        scripts = {"GetUpdate": [(200, _update("Complete"))]}
        _seed(_make_handler(scripts))

        async def flow():
            await tools_mod.updates_wait_start(update_id=UPDATE_ID, interval=0.01)
            return tools_mod.waits_list(), tools_mod.waits_list(terminated=False)

        all_waits, in_flight = asyncio.run(flow())
        assert len(all_waits) == 1
        assert all_waits[0]["update_id"] == UPDATE_ID
        assert in_flight == []
        with pytest.raises(ValueError, match="Unknown wait_id"):
            asyncio.run(tools_mod.updates_wait_poll("wu-nope"))


# ── dispatch through the async meta-tool path ────────────────────────────────


class TestDispatch:
    def test_async_op_through_dispatch_and_ctx_rejected(self):
        scripts = {"GetUpdate": [(200, _update("Complete", success=True))]}
        _seed(_make_handler(scripts))
        from komodo_mcp import server

        async def flow():
            coro = server._dispatch(
                "UpdatesWaitStart", "komodo_read",
                {"update_id": UPDATE_ID, "interval": 0.01},
            )
            assert asyncio.iscoroutine(coro)
            return await coro

        snap = asyncio.run(flow())
        assert snap["status"] == "Complete"

        with pytest.raises(ValueError, match="Unknown parameters.*ctx"):
            server._dispatch(
                "UpdatesWait", "komodo_read",
                {"update_id": UPDATE_ID, "ctx": "evil"},
            )

    def test_help_hides_ctx(self):
        _seed(_make_handler({}))
        from komodo_mcp import server
        help_text = server._build_help("komodo_read")
        line = next(
            ln for ln in help_text.splitlines() if ln.strip().startswith("UpdatesWait(")
        )
        assert "ctx" not in line
        assert "update_id" in line
