from contextvars import ContextVar
from typing import Any

from .client import KomodoClient
from .overrides import REQUEST_OVERRIDES, RESPONSE_OVERRIDES

# A host serving several Komodo instances in one process binds the per-request
# client here; unbound (plain CLI) falls back to the module singleton.
client_var: ContextVar[KomodoClient | None] = ContextVar("komodo_client", default=None)

_client: KomodoClient | None = None


def _get_client() -> KomodoClient:
    global _client
    if (bound := client_var.get()) is not None:
        return bound
    if _client is None:
        _client = KomodoClient()
    return _client


def _ok(data):
    if data is None:
        return {"status": "ok"}
    return data


def invoke(endpoint: str, operation: str, params: dict[str, Any] | None = None) -> Any:
    """Run a generated operation through the per-op tables in overrides.py."""
    client = _get_client()
    request = REQUEST_OVERRIDES.get(operation)
    if request is None:
        response = getattr(client, endpoint)(operation, params)
    else:
        response = request(client, operation, params)
    respond = RESPONSE_OVERRIDES.get(operation)
    return _ok(response if respond is None else respond(response))
