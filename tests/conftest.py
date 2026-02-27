"""Test infrastructure: Docker Compose Komodo instance + MCP agent simulator."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

from komodo_mcp.server import mcp

COMPOSE_DIR = Path(__file__).parent
KOMODO_URL = "http://localhost:9120"
PASSKEY = "test-passkey"


# ── Docker Compose lifecycle ──────────────────────────────────────────────────


def _compose(*args: str):
    subprocess.run(
        ["docker", "compose", *args],
        cwd=COMPOSE_DIR,
        check=True,
        capture_output=True,
    )


def _wait_for_komodo(timeout: int = 120):
    """Poll Komodo Core until it's ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.post(
                f"{KOMODO_URL}/auth/local/login",
                json={"username": "admin", "password": PASSKEY},
                timeout=5,
            )
            if r.status_code < 500:
                return
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError("Komodo Core did not start in time")


def _create_api_key() -> tuple[str, str]:
    """Login and create an API key, return (key, secret)."""
    # Login with local auth
    r = httpx.post(
        f"{KOMODO_URL}/auth/local/login",
        json={"username": "admin", "password": PASSKEY},
        timeout=10,
    )
    r.raise_for_status()
    token = r.json().get("token") or r.cookies.get("komodo_token")

    # Create a service user + API key via the write endpoint
    headers = {"Authorization": f"Bearer {token}"}

    # First try to create a service user
    r = httpx.post(
        f"{KOMODO_URL}/write",
        json={"type": "CreateServiceUser", "params": {
            "username": "test-agent",
            "description": "Test agent for integration tests",
        }},
        headers=headers,
        timeout=10,
    )

    # Get the service user to find their id
    r = httpx.post(
        f"{KOMODO_URL}/read",
        json={"type": "FindUser", "params": {"user": "test-agent"}},
        headers=headers,
        timeout=10,
    )
    r.raise_for_status()
    user_id = r.json().get("id", "")

    # Make the service user an admin
    httpx.post(
        f"{KOMODO_URL}/write",
        json={"type": "UpdateUserAdmin", "params": {"user_id": user_id, "admin": True}},
        headers=headers,
        timeout=10,
    )

    # Create API key for the service user
    r = httpx.post(
        f"{KOMODO_URL}/write",
        json={"type": "CreateApiKeyForServiceUser", "params": {
            "user_id": user_id,
            "name": "test-key",
            "expires": 0,
        }},
        headers=headers,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    return data["key"], data["secret"]


# ── Agent simulator ───────────────────────────────────────────────────────────


class AgentSimulator:
    """Simulates an MCP agent calling tools by name."""

    def __init__(self):
        self.call_log: list[dict] = []
        self._tools: dict[str, Any] = {}
        for tool in mcp._tool_manager._tools.values():
            self._tools[tool.name] = tool.fn

    def call(self, tool_name: str, **kwargs) -> Any:
        """Call an MCP tool by name and return parsed result."""
        fn = self._tools.get(tool_name)
        if fn is None:
            raise ValueError(f"Unknown tool: {tool_name}. Available: {sorted(self._tools.keys())}")

        result_str = fn(**kwargs)
        self.call_log.append({"tool": tool_name, "kwargs": kwargs, "result": result_str})

        try:
            return json.loads(result_str)
        except (json.JSONDecodeError, TypeError):
            return result_str

    def call_raw(self, tool_name: str, **kwargs) -> str:
        """Call an MCP tool and return raw string result."""
        fn = self._tools.get(tool_name)
        if fn is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        result_str = fn(**kwargs)
        self.call_log.append({"tool": tool_name, "kwargs": kwargs, "result": result_str})
        return result_str

    @property
    def total_calls(self) -> int:
        return len(self.call_log)

    @property
    def unique_tools_used(self) -> set[str]:
        return {e["tool"] for e in self.call_log}

    def print_log(self):
        for i, entry in enumerate(self.call_log):
            print(f"\n[{i}] {entry['tool']}({entry['kwargs']})")
            result = entry["result"]
            if len(str(result)) > 200:
                print(f"  => {str(result)[:200]}...")
            else:
                print(f"  => {result}")


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def komodo_instance():
    """Start Komodo via Docker Compose, yield the URL, then tear down."""
    _compose("up", "-d")
    try:
        _wait_for_komodo()
        yield KOMODO_URL
    finally:
        _compose("down", "-v")


@pytest.fixture(scope="session")
def api_credentials(komodo_instance):
    """Create service user and return (api_key, api_secret)."""
    return _create_api_key()


@pytest.fixture(scope="session")
def configure_env(komodo_instance, api_credentials):
    """Set environment variables for KomodoClient."""
    import os

    api_key, api_secret = api_credentials
    os.environ["KOMODO_URL"] = komodo_instance
    os.environ["KOMODO_API_KEY"] = api_key
    os.environ["KOMODO_API_SECRET"] = api_secret

    import komodo_mcp.server as srv
    srv._client = None
    yield
    srv._client = None


@pytest.fixture(scope="session")
def agent(configure_env) -> AgentSimulator:
    """Return an AgentSimulator connected to the test Komodo instance."""
    return AgentSimulator()
