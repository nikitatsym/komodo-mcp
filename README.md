# komodo-mcp

MCP server for [Komodo](https://komo.do/), built for autonomous AI agents.

Servers, deployments, stacks, builds, repos, procedures, actions, resource syncs, Docker management, users, permissions, and more — one tool per operation, or compact mode with risk-graded meta-tools.

**Long-running waiters**: every execute op returns an Update; `UpdatesWait` blocks until it completes, `UpdatesWaitStart` / `UpdatesWaitPoll(max_block=...)` / `UpdatesWaitCancel` + `WaitsList` keep the agent responsive. Waits tolerate transient API errors (`max_poll_failures`), self-terminate after `max_lifetime` (default 2h), and live in `komodo_read` - they only ever read. Stage logs default to failed stages only (`failed_only=True`); `logs_omitted` counts the hidden ones.

## Quick Start

Add to your MCP client config:

```json
{
  "mcpServers": {
    "komodo": {
      "command": "uvx",
      "args": ["--refresh", "--extra-index-url",
        "https://nikitatsym.github.io/komodo-mcp/simple",
        "komodo-mcp"],
      "env": {
        "KOMODO_URL": "https://komodo.example.com",
        "KOMODO_API_KEY": "your-api-key",
        "KOMODO_API_SECRET": "your-api-secret"
      }
    }
  }
}
```

Or use the [interactive config generator](https://nikitatsym.github.io/komodo-mcp/).

### HTTP

`komodo-mcp --http` serves streamable HTTP at `http://127.0.0.1:8000/mcp` (`--host`, `--port`) instead of stdio, same environment variables. No authentication: put a gateway in front.

The package can also be imported: `mcp`, `Settings`, the client class, and `client_var` (a `ContextVar` the host sets per request) let one process serve several instances.

## Configuration

| Variable | Description |
|----------|-------------|
| `KOMODO_URL` | Base URL of your Komodo Core instance |
| `KOMODO_API_KEY` | API key for authentication |
| `KOMODO_API_SECRET` | API secret for authentication |
| `KOMODO_COMPACT` | Set to `true` for compact mode (risk-graded meta-tools instead of one tool per operation) |

## Getting API Credentials

1. Open your Komodo dashboard
2. Go to **Settings → API Keys**
3. Create a new API key (or create a Service User first)
4. Copy the **Key** and **Secret**

## Compact Mode

If you have many MCP servers and want to reduce total tool count, set `KOMODO_COMPACT=true`. Instead of one tool per operation, it exposes meta-tools split by risk level, with built-in help discovery:

| Tool | Scope |
|------|-------|
| `komodo_read` | Safe resource queries; secret values masked |
| `komodo_write` | Create/update/rename/copy (non-destructive) |
| `komodo_execute` | Deploy, start/stop, build (actions) |
| `komodo_delete` | Delete, destroy, prune (destructive) |
| `komodo_admin_read` | Users, permissions, groups, API keys, provider accounts, secret values |
| `komodo_admin_write` | User/permission management, admin-only |

```json
{
  "mcpServers": {
    "komodo": {
      "command": "uvx",
      "args": ["--refresh", "--extra-index-url",
        "https://nikitatsym.github.io/komodo-mcp/simple",
        "komodo-mcp"],
      "env": {
        "KOMODO_URL": "https://komodo.example.com",
        "KOMODO_API_KEY": "your-api-key",
        "KOMODO_API_SECRET": "your-api-secret",
        "KOMODO_COMPACT": "true"
      }
    }
  }
}
```

The LLM calls any tool with `operation="help"` to discover available operations, then calls with the specific operation name and params JSON. Users can selectively allow safe tools (read) while blocking destructive ones (delete, admin).

## Tools Overview

### Read
Query servers, deployments, stacks, builds, repos, procedures, actions, resource syncs, builders, alerters, Docker containers/images/networks/volumes, tags, variables, users, permissions, updates, alerts, and more.

Variable and provider-account operations mask secret variable values and tokens (`#` per character, as Komodo shows them to non-admins) in every group except `komodo_admin_read`, where `RevealVariable` and the provider-account reads return them. TOML exports mask secret variables too, so applying such an export through a sync overwrites them with the mask. This guards against accidental exposure, not against an agent with an admin API key: container inspection (`Env` with interpolated secrets), resource configs, and logs are returned as Komodo sends them.

### Write
Create, update, delete, rename, and copy all resource types. Manage webhooks, variables, tags, users, user groups, permissions, and provider accounts.

### Execute
Deploy, start, stop, restart, pause, unpause, and destroy deployments and stacks. Run builds, clone/pull repos, execute procedures and actions, sync resources. Docker cleanup (prune). Batch operations. Send alerts, backup database.

## Running Tests

```bash
# Start test infrastructure
docker compose -f tests/docker-compose.yml up -d

# Run integration tests
uv run pytest tests/ -v

# Tear down
docker compose -f tests/docker-compose.yml down -v
```

## License

MIT
