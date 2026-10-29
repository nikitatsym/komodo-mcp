"""Unit tests for `_build_help` — render, search filter, cross-group hint.

Seeds a couple of synthetic ops into `_group_ops` so we exercise the help
renderer without relying on the full tools.py registration.
"""

from __future__ import annotations

import pytest

from komodo_mcp import server
from komodo_mcp.server import _build_help


@pytest.fixture(autouse=True)
def _isolate_state():
    """Snapshot and restore module-level help state so tests don't leak."""
    saved_ops = dict(server._group_ops)
    saved_all = dict(server._all_grouped)
    server._group_ops.clear()
    server._all_grouped.clear()
    yield
    server._group_ops.clear()
    server._all_grouped.clear()
    server._group_ops.update(saved_ops)
    server._all_grouped.update(saved_all)


def _seed(group_to_fns: dict[str, dict[str, callable]]) -> None:
    """Install ops into the help registry."""
    for group_name, fns in group_to_fns.items():
        server._group_ops[group_name] = dict(fns)
        for pascal in fns:
            server._all_grouped[pascal] = group_name


def get_container_log(server: str, container: str, tail: int = 50):
    """GetContainerLog."""


def list_stacks():
    """ListStacks."""


def list_variables():
    """ListVariables."""


def deploy_stack(stack: str):
    """DeployStack."""


def get_stack_log(stack: str):
    """GetStackLog."""


class TestHelpFlat:
    def test_full_listing_no_args(self):
        _seed({"komodo_read": {"GetContainerLog": get_container_log, "ListStacks": list_stacks}})
        out = _build_help("komodo_read")
        assert out.startswith("2 operations available:\n")
        assert "GetContainerLog(server: str, container: str, tail?: int = 50) — " in out
        assert "ListStacks() — ListStacks." in out


class TestHelpSearch:
    def test_search_filters_in_local_group(self):
        _seed({"komodo_read": {"GetContainerLog": get_container_log, "ListStacks": list_stacks}})
        out = _build_help("komodo_read", search="log")
        assert "GetContainerLog" in out
        assert "ListStacks" not in out
        assert out.startswith("1 of 2 operations in komodo_read matching 'log'.\n")

    def test_search_case_insensitive(self):
        _seed({"komodo_read": {"GetContainerLog": get_container_log}})
        out = _build_help("komodo_read", search="LOG")
        assert "GetContainerLog" in out

    def test_search_matches_annotation(self):
        """Help shows the ANNOTATIONS entry, so its words find the op."""
        _seed({"komodo_read": {"ListVariables": list_variables, "ListStacks": list_stacks}})
        out = _build_help("komodo_read", search="masked")
        assert "ListVariables" in out
        assert "ListStacks" not in out

    def test_empty_search_lists_everything(self):
        _seed({"komodo_read": {"GetContainerLog": get_container_log, "ListStacks": list_stacks}})
        assert _build_help("komodo_read", search="") == _build_help("komodo_read")

    def test_search_no_match_in_local_group(self):
        _seed({"komodo_read": {"GetContainerLog": get_container_log}})
        out = _build_help("komodo_read", search="qwerty")
        assert out == (
            "No ops in komodo_read matching 'qwerty'. "
            "Call operation='help' (no params) to list all ops."
        )

    def test_search_cross_group_hint(self):
        """When local search is empty but other groups have a match, the
        renderer surfaces a 'Found in other groups' pointer so the agent
        learns where the op actually lives."""
        _seed({
            "komodo_read": {"ListStacks": list_stacks},
            "komodo_execute": {"DeployStack": deploy_stack},
        })
        out = _build_help("komodo_read", search="deploy")
        assert out == (
            "No ops in komodo_read matching 'deploy'. "
            "Found in other groups: komodo_execute: DeployStack"
        )

    def test_search_with_matches_and_cross_group_appended(self):
        """Local matches AND cross-group hits both render — local block on
        top, 'Also matching in other groups' appended."""
        _seed({
            "komodo_read": {"ListStacks": list_stacks, "GetStackLog": get_stack_log},
            "komodo_execute": {"DeployStack": deploy_stack},
        })
        out = _build_help("komodo_read", search="stack")
        header, *body = out.split("\n")
        assert header == "2 of 2 operations in komodo_read matching 'stack'."
        assert body[-1] == "Also matching in other groups: komodo_execute: DeployStack"

    def test_search_without_cross_group_hits_has_no_hint(self):
        _seed({
            "komodo_read": {"ListStacks": list_stacks},
            "komodo_execute": {"DeployStack": deploy_stack},
        })
        out = _build_help("komodo_read", search="list")
        assert "ListStacks" in out
        assert "Also matching in other groups" not in out
