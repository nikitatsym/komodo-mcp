# komodo-mcp

MCP server for [Komodo](https://komo.do/) — full API coverage for autonomous AI agents.

**293 tools** covering every Komodo Core operation: servers, deployments, stacks, builds, repos, procedures, actions, resource syncs, Docker management, users, permissions, and more. Compact mode available (6 meta-tools).

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

## Configuration

| Variable | Description |
|----------|-------------|
| `KOMODO_URL` | Base URL of your Komodo Core instance |
| `KOMODO_API_KEY` | API key for authentication |
| `KOMODO_API_SECRET` | API secret for authentication |
| `KOMODO_COMPACT` | Set to `true` for compact mode (3 meta-tools instead of 293) |

## Getting API Credentials

1. Open your Komodo dashboard
2. Go to **Settings → API Keys**
3. Create a new API key (or create a Service User first)
4. Copy the **Key** and **Secret**

## Compact Mode

If you have many MCP servers and want to reduce total tool count, set `KOMODO_COMPACT=true`. Instead of 293 individual tools, it exposes 6 meta-tools split by risk level, with built-in help discovery:

| Tool | Scope | Ops |
|------|-------|-----|
| `komodo_read` | Safe resource queries | 109 |
| `komodo_write` | Create/update/rename/copy (non-destructive) | 68 |
| `komodo_execute` | Deploy, start/stop, build (actions) | 48 |
| `komodo_delete` | Delete, destroy, prune (destructive) | 36 |
| `komodo_admin_read` | User/permission queries | 10 |
| `komodo_admin_write` | User/permission management, admin-only | 22 |

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

### Read (119 tools)
Query servers, deployments, stacks, builds, repos, procedures, actions, resource syncs, builders, alerters, Docker containers/images/networks/volumes, tags, variables, users, permissions, updates, alerts, and more.

### Write (108 tools)
Create, update, delete, rename, and copy all resource types. Manage webhooks, variables, tags, users, user groups, permissions, and provider accounts.

### Execute (66 tools)
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
