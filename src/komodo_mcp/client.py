from __future__ import annotations

import os

import httpx


class KomodoError(Exception):
    """Komodo API error with full context."""

    def __init__(self, status: int, endpoint: str, operation: str, body):
        self.status = status
        self.endpoint = endpoint
        self.operation = operation
        self.body = body
        super().__init__(f"Komodo API {status} {endpoint} {operation}: {body}")


class KomodoClient:
    """RPC client for Komodo Core API.

    All Komodo operations are POST requests with JSON body:
        {"type": "OperationName", "params": {...}}

    Three endpoints:
        /read    — read data
        /write   — create/update/delete resources
        /execute — trigger actions (deploy, build, start/stop, etc.)
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        self._base = (base_url or os.environ["KOMODO_URL"]).rstrip("/")
        self._http = httpx.Client(
            headers={
                "X-Api-Key": api_key or os.environ["KOMODO_API_KEY"],
                "X-Api-Secret": api_secret or os.environ["KOMODO_API_SECRET"],
            },
            timeout=30.0,
        )

    def _call(self, endpoint: str, operation: str, params: dict | None = None):
        """Send RPC request and return parsed response."""
        r = self._http.post(
            f"{self._base}/{endpoint}",
            json={"type": operation, "params": params or {}},
        )
        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = r.text
            raise KomodoError(r.status_code, endpoint, operation, body)
        if not r.content:
            return None
        return r.json()

    def read(self, operation: str, params: dict | None = None):
        """Read operation (query data)."""
        return self._call("read", operation, params)

    def write(self, operation: str, params: dict | None = None):
        """Write operation (create/update/delete resources)."""
        return self._call("write", operation, params)

    def execute(self, operation: str, params: dict | None = None):
        """Execute operation (trigger actions)."""
        return self._call("execute", operation, params)
