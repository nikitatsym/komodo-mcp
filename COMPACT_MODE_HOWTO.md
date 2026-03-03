# Compact Mode for MCP Servers

MCP servers wrapping rich APIs easily reach 100-300+ tools. This bloats LLM context, hits client tool-count limits, and makes per-tool permissions useless. Compact mode collapses N tools into ~6 meta-tools grouped by risk level, with built-in discovery via `path="help"`.

## Architecture

```
N individual tools  →  6 meta-tools (CRUD + admin read/write)
```

Split by HTTP method + admin scope. Users can allow reads but block deletes.

| Tool | HTTP | Admin? | Signature |
|---|---|---|---|
| `svc_read` | GET | no | `(path, params)` |
| `svc_create` | POST | no | `(path, params)` |
| `svc_update` | PUT/PATCH | no | `(method, path, params)` |
| `svc_delete` | DELETE | no | `(path, params)` |
| `svc_admin_read` | GET | yes | `(path, params)` |
| `svc_admin_write` | POST/PUT/PATCH/DELETE | yes | `(method, path, params)` |

`update` and `admin_write` take an explicit `method` because they cover multiple HTTP methods. The rest don't -- the method is always unambiguous (GET, POST, or DELETE).

For RPC APIs, replace HTTP scoping with semantic: `read`, `write`, `execute`, `delete`, `admin_read`, `admin_write`. See `komodo-mcp/src/komodo_mcp/server_compact.py` for a working 6-tool implementation with this exact split.

## How it looks to the LLM

`params` is always a JSON string (query params for GET, request body for POST/PUT/PATCH). Every tool supports `path="help"` to list its endpoints.

```
svc_read("help")                              → shows all GET endpoints
svc_read("/repos/owner/repo")                 → get a repository
svc_read("/repos/owner/repo/issues", '{"state":"open","page":2}')
svc_create("/user/repos", '{"name":"new-repo","auto_init":true}')
svc_update("PATCH", "/repos/owner/repo", '{"description":"updated"}')
svc_delete("/repos/owner/repo")
svc_admin_read("/admin/users")
svc_admin_write("POST", "/admin/users", '{"username":"new","email":"a@b.c","password":"..."}')
```

## File structure

```
src/your_package/
    __init__.py         # picks server or server_compact based on env var
    server.py           # normal mode: N individual @mcp.tool() functions
    server_compact.py   # compact mode: 6 meta-tools, own mcp = FastMCP() instance
    client.py           # shared API client (used by both modes)
```

`server_compact.py` must create its own `mcp = FastMCP("name")` -- it's a separate server, not an extension of `server.py`. It imports `server.py` only for validation (checking that every tool has a corresponding endpoint mapping).

## Key components

**Endpoint registry** -- single source of truth, categorized dict:
```python
_ENDPOINTS = {
    "Repositories": {
        "get_repo":    ("GET",    "/repos/{owner}/{repo}"),
        "create_repo": ("POST",   "/user/repos"),
        "delete_repo": ("DELETE", "/repos/{owner}/{repo}"),
    },
    "Admin": {
        "admin_list_users": ("GET", "/admin/users"),
    },
}
```

**Import-time validation** -- cross-check against `server.py` tools, fail loudly on drift:
```python
from . import server as _srv
_FLAT = {name: ep for ops in _ENDPOINTS.values() for name, ep in ops.items()}
missing = set(_srv.mcp._tool_manager._tools) - set(_FLAT)
if missing:
    raise RuntimeError(f"Missing endpoint mapping: {sorted(missing)}")
```

**Filtered help builder** -- one function, filter via predicate:
```python
def _build_help(header, filter_fn):
    for category, ops in _ENDPOINTS.items():
        matching = [(n, m, p) for n, (m, p) in ops.items() if filter_fn(m, p)]
        ...

_HELP_READ = _build_help("svc_read -- GET endpoints", lambda m, p: m == "GET" and not p.startswith("/admin/"))
_HELP_DELETE = _build_help("svc_delete -- DELETE endpoints", lambda m, p: m == "DELETE" and not p.startswith("/admin/"))
# ... 4 more
```

**Shared dispatch** -- all request logic in one place, tools are thin wrappers:
```python
def _dispatch(method, path, params_str):
    p = json.loads(params_str) if params_str.strip() else {}
    if method == "GET":    return _ok(client.get(path, params=p or None))
    if method == "POST":   return _ok(client.post(path, json=p))
    if method == "DELETE":  return _ok(client.delete(path))
    ...

@mcp.tool()
def svc_read(path: str, params: str = "{}") -> str:
    """Read from API (GET). path='help' lists endpoints."""
    if path.lower() == "help":       return _HELP_READ
    if path.startswith("/admin/"):   return json.dumps({"error": "Use svc_admin_read"})
    return _dispatch("GET", path, params)
```

## Mode switching

Use env var, **not** CLI flag (FastMCP owns `sys.argv` and will break on unknown flags):

```python
# __init__.py
if os.environ.get("SVC_COMPACT", "").lower() in ("1", "true", "yes"):
    from .server_compact import mcp
else:
    from .server import mcp
```

MCP client config to enable compact mode:
```json
{
  "mcpServers": {
    "my-service": {
      "command": "uvx",
      "args": ["my-mcp-package"],
      "env": {
        "SVC_URL": "https://example.com",
        "SVC_TOKEN": "...",
        "SVC_COMPACT": "true"
      }
    }
  }
}
```

## Verification

```python
from your_package.server_compact import mcp
assert len(mcp._tool_manager._tools) == 6
# Sum of endpoints across all 6 helps == total (e.g. 293)
```

## Principles

1. **Scopes = risk levels.** Read is safe, delete is dangerous, admin is restricted.
2. **One `_dispatch`, thin tools.** Tools only validate scope and delegate.
3. **One `_build_help(filter_fn)`.** No copy-pasted help per tool.
4. **Fail-fast validation.** Cross-check registries at import time.
5. **Helpful scope errors.** Wrong tool? Return error naming the right one -- LLM self-corrects.
6. **Env var, not CLI flag.** FastMCP owns argv. Env vars work in all MCP client configs.
