"""Komodo MCP server — auto-discovery, grouping, and dispatch."""

import functools
import inspect
import re
import string
import types
import typing
from urllib.parse import urlsplit, urlunsplit

import httpx
from mcp.server.mcpserver import Context, MCPServer

from . import tools as _tools_module
from .annotations import ANNOTATIONS
from .client import KomodoError
from .registry import ROOT

mcp = MCPServer("komodo")

# Functions may declare a `ctx` parameter to receive the live MCP Context
# (progress / log notifications). It is injected by `_coerce_call` and
# excluded from param validation and help - callers can't pass it.
_CTX_PARAM = "ctx"

_URL_RE = re.compile(r"[a-z][a-z0-9+.-]*://[^\s'\"<>]+", re.IGNORECASE)
_RELATIVE_QUERY_RE = re.compile(r"/[^\s?,'\"<>]*\?[^ \t\r\n,'\"<>]*")
_SECRET_VALUE_RE = re.compile(
    r"""(?ix)
    (["']?(?:authorization|token|api[_-]?key|secret|password|credential|dsn)
    ["']?\s*[:=]\s*)
    (?:["'][^"']*["']|\[[^\]]*\]|\{[^}]*\}|[^,\s}]+)
    """
)
_AUTHORIZATION_RE = re.compile(
    r"(?i)(authorization\s*[:=]\s*)(?:bearer|basic)\s+[^\s,;]+"
)


def _redact_error_text(value: object) -> str:
    """Remove credentials and query values from an error string."""
    text = str(value)

    def _redact_url(match: re.Match[str]) -> str:
        try:
            parts = urlsplit(match.group())
            host = parts.hostname
            if host is None:
                return "<redacted-url>"
            if ":" in host:
                host = f"[{host}]"
            try:
                port = parts.port
            except ValueError:
                port = None
            netloc = f"{host}:{port}" if port is not None else host
            return urlunsplit((parts.scheme, netloc, parts.path, "", ""))
        except ValueError:
            return "<redacted-url>"

    text = _URL_RE.sub(_redact_url, text)
    text = _RELATIVE_QUERY_RE.sub(lambda match: match.group().split("?", 1)[0], text)
    text = _AUTHORIZATION_RE.sub(r"\1<redacted>", text)
    return _SECRET_VALUE_RE.sub(r"\1<redacted>", text)


def _error_result(exc: ValueError | KomodoError | httpx.RequestError) -> dict[str, str]:
    if isinstance(exc, httpx.RequestError):
        try:
            request = exc.request
        except RuntimeError:
            request = None
        method = request.method if request is not None else "REQUEST"
        path = request.url.path if request is not None else "<unknown path>"
        cause = _redact_error_text(exc) or "request failed"
        return {
            "error": (
                f"Komodo transport failure: {method} {path}: "
                f"{type(exc).__name__}: {cause}"
            )
        }
    return {"error": _redact_error_text(exc)}


def _safe_root(fn):
    """Serialize expected failures for a ROOT tool, which has no meta-tool seam.

    ROOT ops come from the generated sync surface, so the wrapper stays sync -
    MCP classifies tools with `iscoroutinefunction` and an awaitable wrapper
    would move the blocking HTTP call onto the event loop.
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ValueError, KomodoError) as exc:
            return _error_result(exc)
        except httpx.RequestError as exc:
            return _error_result(exc)

    return wrapped


# ── Helpers ──────────────────────────────────────────────────────────────────


def _to_pascal(name: str) -> str:
    """get_server → GetServer"""
    return "".join(w.capitalize() for w in name.split("_"))


def _parse_bool(val, default: bool) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("1", "true", "yes")
    return bool(val)


def _is_bool_hint(hint) -> bool:
    """Check if a type hint is bool or Optional[bool]."""
    if hint is bool:
        return True
    args = typing.get_args(hint)
    return bool in args if args else False


def _get_literal_values(hint) -> list[str] | None:
    """Extract Literal values from a type hint (including Optional[Literal[...]])."""
    if hint is None:
        return None
    origin = typing.get_origin(hint)
    if origin is typing.Literal:
        return [str(v) for v in typing.get_args(hint)]
    # Optional[Literal[...]] = Union[Literal[...], None]
    if origin is typing.Union:
        for arg in typing.get_args(hint):
            if typing.get_origin(arg) is typing.Literal:
                return [str(v) for v in typing.get_args(arg)]
    return None


def _unwrap_optional(hint):
    """Unwrap Optional[X] or X | None to X."""
    origin = typing.get_origin(hint)
    if origin is typing.Union or isinstance(hint, types.UnionType):
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return hint


def _format_param(name: str, hint) -> str:
    """Format a parameter with type info for help text."""
    if hint is None:
        return name
    lit_vals = _get_literal_values(hint)
    if lit_vals:
        return f"{name}: {'|'.join(lit_vals)}"
    inner = _unwrap_optional(hint)
    origin = typing.get_origin(inner)
    if origin is list:
        type_args = typing.get_args(inner)
        if type_args and hasattr(type_args[0], "__name__"):
            return f"{name}: list[{type_args[0].__name__}]"
        return f"{name}: list"
    if inner is str:
        return f"{name}: str"
    if inner is int:
        return f"{name}: int"
    if inner is bool:
        return f"{name}: bool"
    if inner is dict:
        return f"{name}: dict"
    return name


def _coerce_call(fn, params: dict, ctx: Context | None = None):
    """Coerce JSON-parsed params to match function signature, then call fn.

    When the target function declares a `ctx` parameter, the live MCP
    Context (when present) is injected after validation; `ctx` is never a
    valid caller-supplied param. Async functions return their coroutine
    as-is - the meta-tool awaits it.
    """
    sig = inspect.signature(fn)
    parameters = tuple(sig.parameters.items())
    accepts_kwargs = any(
        param.kind is inspect.Parameter.VAR_KEYWORD
        for _, param in parameters
    )
    valid = {
        name
        for name, param in parameters
        if name != _CTX_PARAM
        and param.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    }
    unknown = set(params) - valid
    if unknown and not accepts_kwargs:
        raise ValueError(
            f"Unknown parameters: {sorted(unknown)}. "
            f"Valid: {sorted(valid)}"
        )
    missing = [
        name
        for name, param in parameters
        if name != _CTX_PARAM
        and param.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        and param.default is inspect.Parameter.empty
        and name not in params
    ]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    hints = typing.get_type_hints(fn, include_extras=True)
    kwargs = {}
    for name, param in parameters:
        if name not in valid or name not in params:
            continue
        val = params[name]
        hint = hints.get(name)
        # Validate Literal values
        lit_vals = _get_literal_values(hint)
        if lit_vals and val not in lit_vals:
            raise ValueError(
                f"Invalid value {val!r} for {name}. "
                f"Accepted: {', '.join(lit_vals)}"
            )
        if hint and _is_bool_hint(hint) and not isinstance(val, bool):
            default = param.default
            if default is inspect.Parameter.empty or default is None:
                default = False
            val = _parse_bool(val, default)
        kwargs[name] = val
    if accepts_kwargs:
        kwargs.update({name: value for name, value in params.items() if name not in valid})
    if _CTX_PARAM in sig.parameters:
        kwargs[_CTX_PARAM] = ctx
    return fn(**kwargs)


async def _await_result(result):
    try:
        return await result
    except (ValueError, KomodoError) as exc:
        return _error_result(exc)
    except httpx.RequestError as exc:
        return _error_result(exc)


# ── Module-level state (populated by _register_tools) ────────────────────────

_group_ops: dict[str, dict] = {}    # {group_name: {PascalName: fn}}
_all_grouped: dict[str, str] = {}   # {PascalName: group_name}


def _build_help(group_name: str) -> str:
    """Build help text from operation functions in a group."""
    ops = _group_ops[group_name]
    lines = []
    for pascal_name, fn in ops.items():
        sig = inspect.signature(fn)
        hints = typing.get_type_hints(fn, include_extras=True)
        parts = [
            _format_param(p, hints.get(p))
            for p in sig.parameters if p != _CTX_PARAM
        ]
        desc = ANNOTATIONS.get(pascal_name, f"{pascal_name}.")
        lines.append(f"  {pascal_name}({', '.join(parts)}) — {desc}")
    return f"{len(lines)} operations available:\n" + "\n".join(lines)


def _dispatch(operation: str, group_name: str, params: dict, ctx: Context | None = None):
    """Dispatch an operation call and serialize expected service failures.

    Async waiter operations remain coroutines for direct callers; their
    execution errors are converted when the registered meta-tool awaits them.
    """
    try:
        ops = _group_ops[group_name]
        if operation not in ops:
            if operation in _all_grouped:
                correct = _all_grouped[operation]
                return {
                    "error": f"{operation} belongs to {correct}. "
                    f"Use {correct}() instead."
                }
            return {
                "error": f"Unknown operation: {operation}. "
                "Use operation=\"help\" to list available operations."
            }
        result = _coerce_call(ops[operation], params, ctx)
    except (ValueError, KomodoError) as exc:
        return _error_result(exc)
    except httpx.RequestError as exc:
        return _error_result(exc)
    if inspect.iscoroutine(result):
        return _await_result(result)
    return result


# ── Registration ─────────────────────────────────────────────────────────


_HARDCODED_OPERATION = re.compile(r"""\boperation\s*=\s*["'](?![$<])""")


def _render_group_doc(group_name: str, doc: str, ops: dict) -> str:
    """Resolve $OpName placeholders in a group doc against the registered operations.

    Examples are hand-written while operation names come from the generated
    Komodo API surface; rendering the names from the registry keeps the two from
    drifting apart, and an unresolved placeholder aborts startup. A hardcoded
    operation name is rejected outright; `<...>` stays available for deliberately
    generic placeholders.
    """
    if _HARDCODED_OPERATION.search(doc):
        raise RuntimeError(
            f"{group_name} doc hardcodes an operation name; use the $OpName form"
        )
    names = {name: name for name in ops} | {"help": "help"}
    try:
        return string.Template(doc).substitute(names)
    except (KeyError, ValueError) as exc:
        raise RuntimeError(
            f"{group_name} doc references an unknown operation placeholder: {exc}"
        ) from exc


def _register_tools():
    """Discover @_op-decorated functions, validate, and register as MCP tools."""
    groups: dict[str, tuple] = {}  # {group_name: (Group, {snake_name: fn})}

    for name, fn in inspect.getmembers(_tools_module, inspect.isfunction):
        if name.startswith("_"):
            continue
        if not hasattr(fn, "_mcp_group"):
            continue
        assert fn.__doc__, f"Missing docstring for {name}"
        group = fn._mcp_group
        if group is ROOT:
            mcp.tool()(_safe_root(fn))
        else:
            if group.name not in groups:
                groups[group.name] = (group, {})
            groups[group.name][1][name] = fn

    # Build operation maps and register meta-tools
    for group_name, (group, fns) in groups.items():
        ops = {_to_pascal(n): fn for n, fn in fns.items()}
        _group_ops[group_name] = ops
        doc = _render_group_doc(group_name, group.doc, ops)
        for pascal_name in ops:
            _all_grouped[pascal_name] = group_name

        def _make_tool(gname, gdoc):
            # Async by design so tools that need the MCP Context (progress /
            # log) can `await ctx.report_progress(...)` inside their dispatch
            # path; sync ops still work - we only await actual coroutines.
            # `params` defaults to None (NOT `{}`): a mutable default would
            # be shared across every call of the meta-tool.
            async def tool_fn(
                operation: str,
                params: dict | None = None,
                ctx: Context | None = None,
            ):
                params = params or {}
                if operation == "help":
                    return _build_help(gname)
                result = _dispatch(operation, gname, params, ctx)
                if inspect.iscoroutine(result):
                    result = await result
                return result
            tool_fn.__name__ = gname
            tool_fn.__qualname__ = gname
            tool_fn.__doc__ = gdoc
            return tool_fn

        mcp.tool()(_make_tool(group_name, doc))


_register_tools()
