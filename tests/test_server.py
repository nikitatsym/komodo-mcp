"""Unit tests for server-side registration invariants."""

import inspect

import pytest

from komodo_mcp import server, tools
from komodo_mcp.registry import Group


def test_group_docs_resolve_operation_placeholders():
    groups = [
        obj
        for _, obj in inspect.getmembers(tools, lambda o: isinstance(o, Group))
        if obj.name in server._group_ops
    ]
    assert len(groups) == len(server._group_ops)
    for group in groups:
        rendered = server._render_group_doc(
            group.name, group.doc, server._group_ops[group.name]
        )
        assert "$" not in rendered, f"{group.name} doc left a placeholder unrendered"


def test_render_group_doc_rejects_unknown_placeholder():
    with pytest.raises(RuntimeError, match="NoSuchOp"):
        server._render_group_doc(
            "komodo_read",
            'Example: komodo_read(operation="$NoSuchOp")',
            {"GetServer": None},
        )


def test_render_group_doc_rejects_hardcoded_operation():
    with pytest.raises(RuntimeError, match="hardcodes"):
        server._render_group_doc(
            "komodo_read",
            'Example: komodo_read(operation="GetServer")',
            {"GetServer": None},
        )

    with pytest.raises(RuntimeError, match="hardcodes"):
        server._render_group_doc(
            "komodo_read",
            'Example: komodo_read(operation = "GetServer")',
            {"GetServer": None},
        )


def test_render_group_doc_resolves_meta_and_keeps_generic_form():
    rendered = server._render_group_doc(
        "komodo_read", 'operation="$help" or operation="<OpName>"', {}
    )
    assert rendered == 'operation="help" or operation="<OpName>"'
