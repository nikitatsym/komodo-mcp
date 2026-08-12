"""Unit tests for server-side registration invariants."""

import inspect

import pytest

from komodo_mcp import server, tools
from komodo_mcp.registry import Group


def test_group_doc_examples_name_registered_operations():
    groups = [
        obj
        for _, obj in inspect.getmembers(tools, lambda o: isinstance(o, Group))
        if obj.name in server._group_ops
    ]
    assert len(groups) == len(server._group_ops)
    for group in groups:
        for name in server._EXAMPLE_OPERATION.findall(group.doc):
            if name == "help":
                continue
            assert name in server._group_ops[group.name], (
                f"{group.name} example names {name!r}, which it does not expose"
            )


def test_doc_example_validation_rejects_unknown_operation():
    with pytest.raises(RuntimeError, match="NoSuchOp"):
        server._validate_doc_examples(
            "komodo_read",
            'Example: komodo_read(operation="NoSuchOp")',
            {"GetServer": None},
        )

    server._validate_doc_examples("komodo_read", 'operation="help"', {})
