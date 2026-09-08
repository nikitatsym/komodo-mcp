"""Unit tests for server-side registration invariants."""

import asyncio
import inspect
import json

import pytest
from mcp.types import TextContent

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


def test_registered_tools_return_compact_json():
    registered_tools = server.mcp._tool_manager.list_tools()
    assert all(tool.fn_metadata.output_schema is None for tool in registered_tools)

    result = asyncio.run(
        server.mcp.call_tool("komodo_read", {"operation": "not-an-operation"})
    )
    assert result.structured_content is None
    assert len(result.content) == 1
    content = result.content[0]
    assert isinstance(content, TextContent)
    assert "\n" not in content.text
    assert json.loads(content.text) == {
        "error": (
            "Unknown operation: not-an-operation. "
            'Use operation="help" to list available operations.'
        )
    }
