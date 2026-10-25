"""Per-operation deltas for generated operations, applied by `_helpers.invoke`.

Keys are Komodo operation names. `REQUEST_OVERRIDES[op](client, op, params)`
replaces the Komodo call and returns its response; `RESPONSE_OVERRIDES[op]`
rewrites the response. An operation that needs a different signature is not a
delta: list it in codegen/hand_written.json and write it in tools.py.

Secret values are masked the way Komodo masks them for non-admin callers.
Only komodo_admin_read (RevealVariable, provider-account reads) returns them.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .client import KomodoClient


def _mask(value: str) -> str:
    return "#" * len(value)


def _mask_variable(variable: dict) -> dict:
    if not variable["is_secret"]:
        return variable
    return variable | {"value": _mask(variable["value"])}


def _mask_variables(variables: list[dict]) -> list[dict]:
    return [_mask_variable(variable) for variable in variables]


def _mask_token(account: dict) -> dict:
    return account | {"token": _mask(account["token"])}


_TOML_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _toml_string(value: str) -> str:
    """TOML basic string: control characters and DEL must be escaped."""
    out = []
    for ch in value:
        if ch in _TOML_ESCAPES:
            out.append(_TOML_ESCAPES[ch])
        elif ch < " " or ch == "\x7f":
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _variable_toml(variable: dict) -> str:
    # Komodo omits an empty description from JSON, and its export skips empty strings.
    fields = {"description": variable.get("description", ""), "value": variable["value"]}
    lines = ["[[variable]]", f"name = {_toml_string(variable['name'])}"]
    lines += [f"{key} = {_toml_string(text)}" for key, text in fields.items() if text]
    lines.append(f"is_secret = {'true' if variable['is_secret'] else 'false'}")
    return "\n".join(lines)


# Komodo's separator between exported blocks.
_TOML_BLOCK_SEPARATOR = "\n\n##\n\n"


def _export_with_masked_variables(
    client: KomodoClient, operation: str, params: dict | None
) -> dict:
    """Export without Komodo's variables, then append them masked.

    Komodo puts variables before user groups; here they come last, which TOML
    does not distinguish.
    """
    params = dict(params or {})
    include_variables = params.pop("include_variables", False)
    response = client.read(operation, params or None)
    if not include_variables:
        return response
    blocks = [_variable_toml(v) for v in _mask_variables(client.read("ListVariables"))]
    parts = [response["toml"]] if response["toml"] else []
    response["toml"] = _TOML_BLOCK_SEPARATOR.join(parts + blocks)
    return response


REQUEST_OVERRIDES: dict[str, Callable[[KomodoClient, str, dict | None], Any]] = {
    "ExportAllResourcesToToml": _export_with_masked_variables,
    "ExportResourcesToToml": _export_with_masked_variables,
}

RESPONSE_OVERRIDES: dict[str, Callable[[Any], Any]] = {
    "ListVariables": _mask_variables,
    "GetVariable": _mask_variable,
    "CreateVariable": _mask_variable,
    "UpdateVariableValue": _mask_variable,
    "UpdateVariableDescription": _mask_variable,
    "UpdateVariableIsSecret": _mask_variable,
    "DeleteVariable": _mask_variable,
    "CreateGitProviderAccount": _mask_token,
    "UpdateGitProviderAccount": _mask_token,
    "DeleteGitProviderAccount": _mask_token,
    "CreateDockerRegistryAccount": _mask_token,
    "UpdateDockerRegistryAccount": _mask_token,
    "DeleteDockerRegistryAccount": _mask_token,
}
