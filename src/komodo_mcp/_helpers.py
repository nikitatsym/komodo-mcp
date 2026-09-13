from contextvars import ContextVar

from .client import KomodoClient

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
