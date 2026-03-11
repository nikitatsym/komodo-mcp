from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    komodo_url: str = ""
    komodo_api_key: str = ""
    komodo_api_secret: str = ""
    komodo_compact: bool = False


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def _reset_settings() -> None:
    """Force re-read from env. Used by tests."""
    global _settings
    _settings = None
