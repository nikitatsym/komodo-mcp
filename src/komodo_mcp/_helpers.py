import json
from .client import KomodoClient

_client: KomodoClient | None = None


def _get_client() -> KomodoClient:
    global _client
    if _client is None:
        _client = KomodoClient()
    return _client


def _ok(data) -> str:
    if data is None:
        return json.dumps({"status": "ok"})
    return json.dumps(data, indent=2, ensure_ascii=False)
