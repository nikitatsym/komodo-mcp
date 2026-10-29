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


@pytest.mark.parametrize(
    ("group_name", "operation", "present", "absent"),
    [
        (
            "komodo_read",
            "UpdatesWait",
            ["update_id: str", "failed_only?: bool = True", "log_tail?: int = 100"],
            ["update_id?"],
        ),
        (
            "komodo_execute",
            "RunStackService",
            ["stack: str", "service: str", "no_tty?: bool"],
            ["stack?", "service?", " = None"],
        ),
    ],
)
def test_registered_help_marks_optional_params_and_defaults(group_name, operation, present, absent):
    result = asyncio.run(server.mcp.call_tool(group_name, {"operation": "help"}))
    content = result.content[0]
    assert isinstance(content, TextContent)
    line = next(
        line.strip()
        for line in content.text.splitlines()
        if line.strip().startswith(f"{operation}(")
    )
    for fragment in present:
        assert fragment in line
    for fragment in absent:
        assert fragment not in line
    assert "ctx" not in line


def test_registered_help_filters_by_search():
    result = asyncio.run(
        server.mcp.call_tool("komodo_read", {"operation": "help", "params": {"search": "log"}})
    )
    content = result.content[0]
    assert isinstance(content, TextContent)
    header, *lines = content.text.splitlines()
    matched, total = (int(n) for n in header.split(" operations")[0].split(" of "))
    assert header.endswith(" operations in komodo_read matching 'log'.")
    assert 0 < matched < total == len(server._group_ops["komodo_read"])
    listed = [line.strip().split("(")[0] for line in lines if line.startswith("  ")]
    assert "GetContainerLog" in listed
    assert "GetServer" not in listed
    assert len(listed) == matched


@pytest.mark.parametrize(
    ("default", "expected"),
    [
        (inspect.Parameter.empty, "value"),
        (None, "value?"),
        (False, "value? = False"),
        (0, "value? = 0"),
        ("default", "value? = 'default'"),
    ],
)
def test_untyped_help_params_keep_optional_markers_and_defaults(default, expected):
    assert server._format_param("value", None, default) == expected
