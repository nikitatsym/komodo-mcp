"""Unit tests for pydantic-settings config."""

import os

import pytest

from komodo_mcp.config import Settings, _reset_settings, get_settings


@pytest.fixture(autouse=True)
def _clean_settings():
    """Reset settings before and after each test."""
    _reset_settings()
    yield
    _reset_settings()


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.komodo_url == ""
        assert s.komodo_api_key == ""
        assert s.komodo_api_secret == ""
        assert s.komodo_compact is False

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("KOMODO_URL", "https://komodo.example.com")
        monkeypatch.setenv("KOMODO_API_KEY", "key123")
        monkeypatch.setenv("KOMODO_API_SECRET", "secret456")
        monkeypatch.setenv("KOMODO_COMPACT", "true")
        s = Settings()
        assert s.komodo_url == "https://komodo.example.com"
        assert s.komodo_api_key == "key123"
        assert s.komodo_api_secret == "secret456"
        assert s.komodo_compact is True

    def test_compact_bool_parsing(self, monkeypatch):
        for val in ("1", "True", "YES", "true"):
            monkeypatch.setenv("KOMODO_COMPACT", val)
            assert Settings().komodo_compact is True

        for val in ("0", "False", "no", "false"):
            monkeypatch.setenv("KOMODO_COMPACT", val)
            assert Settings().komodo_compact is False


class TestGetSettings:
    def test_lazy_singleton(self, monkeypatch):
        monkeypatch.setenv("KOMODO_URL", "https://first.com")
        s1 = get_settings()
        assert s1.komodo_url == "https://first.com"

        monkeypatch.setenv("KOMODO_URL", "https://second.com")
        s2 = get_settings()
        assert s2 is s1  # same instance, not re-read

    def test_reset_forces_reread(self, monkeypatch):
        monkeypatch.setenv("KOMODO_URL", "https://first.com")
        s1 = get_settings()

        monkeypatch.setenv("KOMODO_URL", "https://second.com")
        _reset_settings()
        s2 = get_settings()
        assert s2.komodo_url == "https://second.com"
        assert s2 is not s1
