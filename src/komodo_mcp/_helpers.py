from .client import KomodoClient

_client: KomodoClient | None = None


def _get_client() -> KomodoClient:
    global _client
    if _client is None:
        _client = KomodoClient()
    return _client


def _ok(data):
    if data is None:
        return {"status": "ok"}
    return data
