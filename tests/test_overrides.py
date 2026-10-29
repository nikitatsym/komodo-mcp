"""Hand-written operations and the per-op tables in overrides.py.

Requests go through `server._dispatch` (group check, param coercion,
`_helpers.invoke`) to a KomodoClient on an httpx.MockTransport that answers
per operation type and records what Komodo was sent.
"""

from __future__ import annotations

import asyncio
import json
import tomllib
from pathlib import Path

import httpx
import pytest

import komodo_mcp._helpers as helpers_mod
from komodo_mcp import _generated, server, tools
from komodo_mcp.client import KomodoClient
from komodo_mcp.config import _reset_settings

HAND_WRITTEN = json.loads(
    (Path(__file__).parent.parent / "codegen" / "hand_written.json").read_text()
)

SECRET = {"name": "DB_PASSWORD", "value": "hunter22", "is_secret": True}
MASKED = SECRET | {"value": "########"}
PLAIN = {"name": "DOMAIN", "value": "example.com", "description": "site", "is_secret": False}
ACCOUNT = {"domain": "git.example.com", "username": "bot", "token": "tok-123"}


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    monkeypatch.setenv("KOMODO_URL", "https://komodo.example.com")
    monkeypatch.setenv("KOMODO_API_KEY", "k")
    monkeypatch.setenv("KOMODO_API_SECRET", "s")
    _reset_settings()
    helpers_mod._client = None
    yield
    helpers_mod._client = None
    _reset_settings()


def _seed(responses: dict) -> list[tuple[str, dict]]:
    calls: list[tuple[str, dict]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append((body["type"], body["params"]))
        return httpx.Response(200, json=responses[body["type"]])

    helpers_mod._client = KomodoClient(transport=httpx.MockTransport(handler))
    return calls


@pytest.mark.parametrize("operation", sorted(HAND_WRITTEN))
def test_hand_written_operation_is_served_by_tools(operation):
    snake = tools._to_snake(operation)
    assert not hasattr(_generated, snake), "regenerate: codegen still emits it"
    fn = getattr(tools, snake)
    assert fn.__module__ == tools.__name__
    assert hasattr(fn, "_mcp_group")


def test_list_variables_masks_only_secret_values():
    _seed({"ListVariables": [SECRET, PLAIN]})

    assert asyncio.run(server._dispatch("ListVariables", "komodo_read", {})) == [MASKED, PLAIN]


@pytest.mark.parametrize(
    ("group", "operation", "params"),
    [
        ("komodo_read", "GetVariable", {"name": "DB_PASSWORD"}),
        ("komodo_write", "CreateVariable", {"name": "DB_PASSWORD", "value": "hunter22"}),
        ("komodo_write", "UpdateVariableValue", {"name": "DB_PASSWORD", "value": "hunter22"}),
        ("komodo_write", "UpdateVariableDescription", {"name": "DB_PASSWORD", "description": "d"}),
        ("komodo_write", "UpdateVariableIsSecret", {"name": "DB_PASSWORD", "is_secret": True}),
        ("komodo_delete", "DeleteVariable", {"name": "DB_PASSWORD"}),
    ],
)
def test_variable_responses_mask_secret_value(group, operation, params):
    _seed({operation: SECRET})

    assert asyncio.run(server._dispatch(operation, group, params)) == MASKED


@pytest.mark.parametrize(
    ("group", "operation", "params"),
    [
        ("komodo_write", "CreateGitProviderAccount", {"account": ACCOUNT}),
        ("komodo_write", "UpdateGitProviderAccount", {"id": "a1", "account": ACCOUNT}),
        ("komodo_delete", "DeleteGitProviderAccount", {"id": "a1"}),
        ("komodo_write", "CreateDockerRegistryAccount", {"account": ACCOUNT}),
        ("komodo_write", "UpdateDockerRegistryAccount", {"id": "a1", "account": ACCOUNT}),
        ("komodo_delete", "DeleteDockerRegistryAccount", {"id": "a1"}),
    ],
)
def test_account_write_responses_mask_token(group, operation, params):
    _seed({operation: ACCOUNT})

    assert asyncio.run(server._dispatch(operation, group, params)) == ACCOUNT | {"token": "#######"}


@pytest.mark.parametrize(
    "operation",
    [
        "RevealVariable",
        "ListGitProviderAccounts",
        "GetGitProviderAccount",
        "ListDockerRegistryAccounts",
        "GetDockerRegistryAccount",
    ],
)
def test_unmasked_reads_live_in_admin_read(operation):
    assert asyncio.run(server._dispatch(operation, "komodo_read", {})) == {
        "error": f"{operation} belongs to komodo_admin_read. Use komodo_admin_read() instead."
    }


def test_admin_reads_return_secrets_unmasked():
    _seed({"GetVariable": SECRET, "ListGitProviderAccounts": [ACCOUNT]})

    assert asyncio.run(
        server._dispatch("RevealVariable", "komodo_admin_read", {"name": "DB_PASSWORD"})
    ) == SECRET
    assert asyncio.run(
        server._dispatch("ListGitProviderAccounts", "komodo_admin_read", {})
    ) == [ACCOUNT]


def test_export_appends_masked_variables_that_komodo_was_not_asked_for():
    calls = _seed({
        "ExportAllResourcesToToml": {"toml": '[[server]]\nname = "local"'},
        "ListVariables": [SECRET, PLAIN],
    })

    result = asyncio.run(server._dispatch(
        "ExportAllResourcesToToml",
        "komodo_read",
        {"include_resources": True, "include_variables": True},
    ))

    assert calls[0] == ("ExportAllResourcesToToml", {"include_resources": True})
    assert tomllib.loads(result["toml"]) == {
        "server": [{"name": "local"}],
        "variable": [
            {"name": "DB_PASSWORD", "value": "########", "is_secret": True},
            {"name": "DOMAIN", "value": "example.com", "description": "site", "is_secret": False},
        ],
    }


def test_export_of_variables_only_starts_with_the_first_block():
    _seed({"ExportResourcesToToml": {"toml": ""}, "ListVariables": [PLAIN]})

    result = asyncio.run(
        server._dispatch("ExportResourcesToToml", "komodo_read", {"include_variables": True})
    )

    assert result["toml"].startswith("[[variable]]\n")


def test_export_without_variables_passes_komodo_toml_through():
    calls = _seed({"ExportResourcesToToml": {"toml": "[[stack]]\nname = \"web\""}})

    result = asyncio.run(
        server._dispatch("ExportResourcesToToml", "komodo_read", {"user_groups": ["ops"]})
    )

    assert calls == [("ExportResourcesToToml", {"user_groups": ["ops"]})]
    assert result == {"toml": "[[stack]]\nname = \"web\""}


def test_exported_variable_strings_round_trip_through_toml():
    awkward = 'say "hi" \\ path\nnext\ttab\x7fdel\x01ctl é 😀'
    _seed({
        "ExportResourcesToToml": {"toml": ""},
        "ListVariables": [PLAIN | {"value": awkward, "description": awkward}],
    })

    result = asyncio.run(
        server._dispatch("ExportResourcesToToml", "komodo_read", {"include_variables": True})
    )

    variable = tomllib.loads(result["toml"])["variable"][0]
    assert (variable["value"], variable["description"]) == (awkward, awkward)
