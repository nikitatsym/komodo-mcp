from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from .client import KomodoClient

mcp = FastMCP("komodo")
_client: KomodoClient | None = None


def _get_client() -> KomodoClient:
    global _client
    if _client is None:
        _client = KomodoClient()
    return _client


def _ok(data) -> str:
    if data is None:
        return json.dumps({"status": "ok"})
    return json.dumps(data, indent=2, ensure_ascii=False)


def _parse_json(value: str | dict | list | None):
    """Accept a JSON string, dict, or list; return the parsed value as-is."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


# ══════════════════════════════════════════════════════════════════════════════
#  READ — General
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_version() -> str:
    """Get Komodo Core version."""
    return _ok(_get_client().read("GetVersion"))


@mcp.tool()
def get_core_info() -> str:
    """Get Komodo Core configuration info (title, monitoring interval, webhook base URL, etc.)."""
    return _ok(_get_client().read("GetCoreInfo"))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Servers
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_servers(query: str | dict | None = None) -> str:
    """List servers. Optionally filter by mongo query (JSON string)."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListServers", params or None))


@mcp.tool()
def list_full_servers(query: str | dict | None = None) -> str:
    """List servers with full config. Optionally filter by mongo query (JSON string)."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullServers", params or None))


@mcp.tool()
def get_server(server: str) -> str:
    """Get a specific server by id or name."""
    return _ok(_get_client().read("GetServer", {"server": server}))


@mcp.tool()
def get_servers_summary() -> str:
    """Get summary counts for servers (total, healthy, warning, unhealthy, disabled)."""
    return _ok(_get_client().read("GetServersSummary"))


@mcp.tool()
def get_server_state(server: str) -> str:
    """Get the current state of a server."""
    return _ok(_get_client().read("GetServerState", {"server": server}))


@mcp.tool()
def get_server_action_state(server: str) -> str:
    """Get the action state for a server."""
    return _ok(_get_client().read("GetServerActionState", {"server": server}))


@mcp.tool()
def get_system_stats(server: str) -> str:
    """Get current system stats (CPU, memory, disk) for a server."""
    return _ok(_get_client().read("GetSystemStats", {"server": server}))


@mcp.tool()
def get_system_information(server: str) -> str:
    """Get system information (OS, kernel, architecture) for a server."""
    return _ok(_get_client().read("GetSystemInformation", {"server": server}))


@mcp.tool()
def get_historical_server_stats(server: str, granularity: str = "15-sec", page: int = 0) -> str:
    """Get historical system stats for a server. Granularity: 15-sec, 1-min, 5-min, 15-min, 1-hr, etc."""
    return _ok(_get_client().read("GetHistoricalServerStats", {
        "server": server,
        "granularity": granularity,
        "page": page,
    }))


@mcp.tool()
def get_periphery_version(server: str) -> str:
    """Get the Periphery agent version on a server."""
    return _ok(_get_client().read("GetPeripheryVersion", {"server": server}))


@mcp.tool()
def list_system_processes(server: str) -> str:
    """List running system processes on a server."""
    return _ok(_get_client().read("ListSystemProcesses", {"server": server}))


@mcp.tool()
def list_terminals(server: str, fresh: bool = False) -> str:
    """List active terminals on a server."""
    return _ok(_get_client().read("ListTerminals", {"server": server, "fresh": fresh}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Deployments
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_deployments(query: str | dict | None = None) -> str:
    """List deployments. Optionally filter by mongo query (JSON string)."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListDeployments", params or None))


@mcp.tool()
def list_full_deployments(query: str | dict | None = None) -> str:
    """List deployments with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullDeployments", params or None))


@mcp.tool()
def get_deployment(deployment: str) -> str:
    """Get a specific deployment by id or name."""
    return _ok(_get_client().read("GetDeployment", {"deployment": deployment}))


@mcp.tool()
def get_deployments_summary() -> str:
    """Get summary counts for deployments (total, running, stopped, not_deployed, unhealthy, unknown)."""
    return _ok(_get_client().read("GetDeploymentsSummary"))


@mcp.tool()
def get_deployment_action_state(deployment: str) -> str:
    """Get the action state for a deployment."""
    return _ok(_get_client().read("GetDeploymentActionState", {"deployment": deployment}))


@mcp.tool()
def get_deployment_container(deployment: str) -> str:
    """Get the container info for a deployment."""
    return _ok(_get_client().read("GetDeploymentContainer", {"deployment": deployment}))


@mcp.tool()
def get_deployment_log(deployment: str, tail: int = 100, timestamps: bool = False) -> str:
    """Get the container log for a deployment."""
    return _ok(_get_client().read("GetDeploymentLog", {
        "deployment": deployment,
        "tail": tail,
        "timestamps": timestamps,
    }))


@mcp.tool()
def get_deployment_stats(deployment: str) -> str:
    """Get container resource stats (CPU, memory) for a deployment."""
    return _ok(_get_client().read("GetDeploymentStats", {"deployment": deployment}))


@mcp.tool()
def inspect_deployment_container(deployment: str) -> str:
    """Inspect the Docker container of a deployment (full docker inspect output)."""
    return _ok(_get_client().read("InspectDeploymentContainer", {"deployment": deployment}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Stacks
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_stacks(query: str | dict | None = None) -> str:
    """List stacks. Optionally filter by mongo query (JSON string)."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListStacks", params or None))


@mcp.tool()
def list_full_stacks(query: str | dict | None = None) -> str:
    """List stacks with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullStacks", params or None))


@mcp.tool()
def get_stack(stack: str) -> str:
    """Get a specific stack by id or name."""
    return _ok(_get_client().read("GetStack", {"stack": stack}))


@mcp.tool()
def get_stacks_summary() -> str:
    """Get summary counts for stacks."""
    return _ok(_get_client().read("GetStacksSummary"))


@mcp.tool()
def get_stack_action_state(stack: str) -> str:
    """Get the action state for a stack."""
    return _ok(_get_client().read("GetStackActionState", {"stack": stack}))


@mcp.tool()
def get_stack_log(
    stack: str,
    tail: int = 100,
    timestamps: bool = False,
    services: str | None = None,
) -> str:
    """Get logs for a stack. Optionally filter by comma-separated service names."""
    params: dict = {"stack": stack, "tail": tail, "timestamps": timestamps, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    return _ok(_get_client().read("GetStackLog", params))


@mcp.tool()
def get_stack_webhooks_enabled(stack: str) -> str:
    """Check if webhooks are enabled for a stack."""
    return _ok(_get_client().read("GetStackWebhooksEnabled", {"stack": stack}))


@mcp.tool()
def list_stack_services(stack: str) -> str:
    """List services in a stack."""
    return _ok(_get_client().read("ListStackServices", {"stack": stack}))


@mcp.tool()
def inspect_stack_container(stack: str, service: str) -> str:
    """Inspect a specific service container in a stack."""
    return _ok(_get_client().read("InspectStackContainer", {"stack": stack, "service": service}))


@mcp.tool()
def search_stack_log(
    stack: str,
    terms: str,
    combinator: str = "Or",
    invert: bool = False,
    timestamps: bool = False,
    services: str | None = None,
) -> str:
    """Search stack logs. terms: comma-separated search terms. combinator: 'And' or 'Or'."""
    params: dict = {
        "stack": stack,
        "terms": [t.strip() for t in terms.split(",")],
        "combinator": combinator,
        "invert": invert,
        "timestamps": timestamps,
        "services": [],
    }
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    return _ok(_get_client().read("SearchStackLog", params))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Builds
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_builds(query: str | dict | None = None) -> str:
    """List builds."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListBuilds", params or None))


@mcp.tool()
def list_full_builds(query: str | dict | None = None) -> str:
    """List builds with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullBuilds", params or None))


@mcp.tool()
def get_build(build: str) -> str:
    """Get a specific build by id or name."""
    return _ok(_get_client().read("GetBuild", {"build": build}))


@mcp.tool()
def get_builds_summary() -> str:
    """Get summary counts for builds."""
    return _ok(_get_client().read("GetBuildsSummary"))


@mcp.tool()
def get_build_action_state(build: str) -> str:
    """Get the action state for a build."""
    return _ok(_get_client().read("GetBuildActionState", {"build": build}))


@mcp.tool()
def get_build_monthly_stats(page: int = 0) -> str:
    """Get monthly build statistics."""
    return _ok(_get_client().read("GetBuildMonthlyStats", {"page": page}))


@mcp.tool()
def get_build_webhook_enabled(build: str) -> str:
    """Check if webhook is enabled for a build."""
    return _ok(_get_client().read("GetBuildWebhookEnabled", {"build": build}))


@mcp.tool()
def list_build_versions(
    build: str,
    major: int | None = None,
    minor: int | None = None,
    patch: int | None = None,
    limit: int | None = None,
) -> str:
    """List available versions for a build. Optionally filter by version components."""
    params: dict = {"build": build}
    if major is not None:
        params["major"] = major
    if minor is not None:
        params["minor"] = minor
    if patch is not None:
        params["patch"] = patch
    if limit is not None:
        params["limit"] = limit
    return _ok(_get_client().read("ListBuildVersions", params))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Repos
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_repos(query: str | dict | None = None) -> str:
    """List repos."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListRepos", params or None))


@mcp.tool()
def list_full_repos(query: str | dict | None = None) -> str:
    """List repos with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullRepos", params or None))


@mcp.tool()
def get_repo(repo: str) -> str:
    """Get a specific repo by id or name."""
    return _ok(_get_client().read("GetRepo", {"repo": repo}))


@mcp.tool()
def get_repos_summary() -> str:
    """Get summary counts for repos."""
    return _ok(_get_client().read("GetReposSummary"))


@mcp.tool()
def get_repo_action_state(repo: str) -> str:
    """Get the action state for a repo."""
    return _ok(_get_client().read("GetRepoActionState", {"repo": repo}))


@mcp.tool()
def get_repo_webhooks_enabled(repo: str) -> str:
    """Check if webhooks are enabled for a repo."""
    return _ok(_get_client().read("GetRepoWebhooksEnabled", {"repo": repo}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Procedures
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_procedures(query: str | dict | None = None) -> str:
    """List procedures."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListProcedures", params or None))


@mcp.tool()
def list_full_procedures(query: str | dict | None = None) -> str:
    """List procedures with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullProcedures", params or None))


@mcp.tool()
def get_procedure(procedure: str) -> str:
    """Get a specific procedure by id or name."""
    return _ok(_get_client().read("GetProcedure", {"procedure": procedure}))


@mcp.tool()
def get_procedures_summary() -> str:
    """Get summary counts for procedures."""
    return _ok(_get_client().read("GetProceduresSummary"))


@mcp.tool()
def get_procedure_action_state(procedure: str) -> str:
    """Get the action state for a procedure."""
    return _ok(_get_client().read("GetProcedureActionState", {"procedure": procedure}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Actions
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_actions(query: str | dict | None = None) -> str:
    """List actions."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListActions", params or None))


@mcp.tool()
def list_full_actions(query: str | dict | None = None) -> str:
    """List actions with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullActions", params or None))


@mcp.tool()
def get_action(action: str) -> str:
    """Get a specific action by id or name."""
    return _ok(_get_client().read("GetAction", {"action": action}))


@mcp.tool()
def get_actions_summary() -> str:
    """Get summary counts for actions."""
    return _ok(_get_client().read("GetActionsSummary"))


@mcp.tool()
def get_action_action_state(action: str) -> str:
    """Get the action state for an action."""
    return _ok(_get_client().read("GetActionActionState", {"action": action}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Resource Syncs
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_resource_syncs(query: str | dict | None = None) -> str:
    """List resource syncs."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListResourceSyncs", params or None))


@mcp.tool()
def list_full_resource_syncs(query: str | dict | None = None) -> str:
    """List resource syncs with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullResourceSyncs", params or None))


@mcp.tool()
def get_resource_sync(sync: str) -> str:
    """Get a specific resource sync by id or name."""
    return _ok(_get_client().read("GetResourceSync", {"sync": sync}))


@mcp.tool()
def get_resource_syncs_summary() -> str:
    """Get summary counts for resource syncs."""
    return _ok(_get_client().read("GetResourceSyncsSummary"))


@mcp.tool()
def get_resource_sync_action_state(sync: str) -> str:
    """Get the action state for a resource sync."""
    return _ok(_get_client().read("GetResourceSyncActionState", {"sync": sync}))


@mcp.tool()
def get_sync_webhooks_enabled(sync: str) -> str:
    """Check if webhooks are enabled for a resource sync."""
    return _ok(_get_client().read("GetSyncWebhooksEnabled", {"sync": sync}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Builders
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_builders(query: str | dict | None = None) -> str:
    """List builders."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListBuilders", params or None))


@mcp.tool()
def list_full_builders(query: str | dict | None = None) -> str:
    """List builders with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullBuilders", params or None))


@mcp.tool()
def get_builder(builder: str) -> str:
    """Get a specific builder by id or name."""
    return _ok(_get_client().read("GetBuilder", {"builder": builder}))


@mcp.tool()
def get_builders_summary() -> str:
    """Get summary counts for builders."""
    return _ok(_get_client().read("GetBuildersSummary"))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Alerters
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_alerters(query: str | dict | None = None) -> str:
    """List alerters."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListAlerters", params or None))


@mcp.tool()
def list_full_alerters(query: str | dict | None = None) -> str:
    """List alerters with full config."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListFullAlerters", params or None))


@mcp.tool()
def get_alerter(alerter: str) -> str:
    """Get a specific alerter by id or name."""
    return _ok(_get_client().read("GetAlerter", {"alerter": alerter}))


@mcp.tool()
def get_alerters_summary() -> str:
    """Get summary counts for alerters."""
    return _ok(_get_client().read("GetAlertersSummary"))


@mcp.tool()
def get_alert(id: str) -> str:
    """Get a specific alert by id."""
    return _ok(_get_client().read("GetAlert", {"id": id}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Docker
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_docker_containers(server: str) -> str:
    """List Docker containers on a server."""
    return _ok(_get_client().read("ListDockerContainers", {"server": server}))


@mcp.tool()
def list_all_docker_containers(servers: str | None = None) -> str:
    """List Docker containers across multiple servers. servers: comma-separated server ids/names."""
    params: dict = {"servers": []}
    if servers is not None:
        params["servers"] = [s.strip() for s in servers.split(",")]
    return _ok(_get_client().read("ListAllDockerContainers", params))


@mcp.tool()
def get_docker_containers_summary() -> str:
    """Get summary counts for Docker containers across all servers."""
    return _ok(_get_client().read("GetDockerContainersSummary"))


@mcp.tool()
def get_container_log(server: str, container: str, tail: int = 100, timestamps: bool = False) -> str:
    """Get logs from a Docker container."""
    return _ok(_get_client().read("GetContainerLog", {
        "server": server,
        "container": container,
        "tail": tail,
        "timestamps": timestamps,
    }))


@mcp.tool()
def search_container_log(
    server: str,
    container: str,
    terms: str,
    combinator: str = "Or",
    invert: bool = False,
    timestamps: bool = False,
) -> str:
    """Search Docker container logs. terms: comma-separated search terms. combinator: 'And' or 'Or'."""
    return _ok(_get_client().read("SearchContainerLog", {
        "server": server,
        "container": container,
        "terms": [t.strip() for t in terms.split(",")],
        "combinator": combinator,
        "invert": invert,
        "timestamps": timestamps,
    }))


@mcp.tool()
def search_deployment_log(
    deployment: str,
    terms: str,
    combinator: str = "Or",
    invert: bool = False,
    timestamps: bool = False,
) -> str:
    """Search deployment logs. terms: comma-separated search terms. combinator: 'And' or 'Or'."""
    return _ok(_get_client().read("SearchDeploymentLog", {
        "deployment": deployment,
        "terms": [t.strip() for t in terms.split(",")],
        "combinator": combinator,
        "invert": invert,
        "timestamps": timestamps,
    }))


@mcp.tool()
def inspect_docker_container(server: str, container: str) -> str:
    """Inspect a Docker container (full docker inspect output)."""
    return _ok(_get_client().read("InspectDockerContainer", {"server": server, "container": container}))


@mcp.tool()
def list_docker_images(server: str) -> str:
    """List Docker images on a server."""
    return _ok(_get_client().read("ListDockerImages", {"server": server}))


@mcp.tool()
def list_docker_image_history(server: str, image: str) -> str:
    """List the history of a Docker image."""
    return _ok(_get_client().read("ListDockerImageHistory", {"server": server, "image": image}))


@mcp.tool()
def inspect_docker_image(server: str, image: str) -> str:
    """Inspect a Docker image."""
    return _ok(_get_client().read("InspectDockerImage", {"server": server, "image": image}))


@mcp.tool()
def list_docker_networks(server: str) -> str:
    """List Docker networks on a server."""
    return _ok(_get_client().read("ListDockerNetworks", {"server": server}))


@mcp.tool()
def inspect_docker_network(server: str, network: str) -> str:
    """Inspect a Docker network."""
    return _ok(_get_client().read("InspectDockerNetwork", {"server": server, "network": network}))


@mcp.tool()
def list_docker_volumes(server: str) -> str:
    """List Docker volumes on a server."""
    return _ok(_get_client().read("ListDockerVolumes", {"server": server}))


@mcp.tool()
def inspect_docker_volume(server: str, volume: str) -> str:
    """Inspect a Docker volume."""
    return _ok(_get_client().read("InspectDockerVolume", {"server": server, "volume": volume}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Compose
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_compose_projects(server: str) -> str:
    """List Docker Compose projects on a server."""
    return _ok(_get_client().read("ListComposeProjects", {"server": server}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Tags, Variables, Secrets
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_tags(query: str | dict | None = None) -> str:
    """List tags. Optionally filter by mongo query (JSON string)."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListTags", params or None))


@mcp.tool()
def get_tag(tag: str) -> str:
    """Get a specific tag by id or name."""
    return _ok(_get_client().read("GetTag", {"tag": tag}))


@mcp.tool()
def list_variables() -> str:
    """List all variables."""
    return _ok(_get_client().read("ListVariables"))


@mcp.tool()
def get_variable(name: str) -> str:
    """Get a specific variable by name."""
    return _ok(_get_client().read("GetVariable", {"name": name}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Users & Permissions
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_users() -> str:
    """List all users."""
    return _ok(_get_client().read("ListUsers"))


@mcp.tool()
def find_user(user: str) -> str:
    """Find a user by id or username."""
    return _ok(_get_client().read("FindUser", {"user": user}))


@mcp.tool()
def get_username(user_id: str) -> str:
    """Get username by user id."""
    return _ok(_get_client().read("GetUsername", {"user_id": user_id}))


@mcp.tool()
def list_user_groups() -> str:
    """List all user groups."""
    return _ok(_get_client().read("ListUserGroups"))


@mcp.tool()
def get_user_group(user_group: str) -> str:
    """Get a specific user group by id or name."""
    return _ok(_get_client().read("GetUserGroup", {"user_group": user_group}))


@mcp.tool()
def list_permissions() -> str:
    """List permissions for the calling user."""
    return _ok(_get_client().read("ListPermissions"))


@mcp.tool()
def list_user_target_permissions(user_target: str | dict) -> str:
    """List permissions for a specific user or user group. Pass as JSON: {"type": "User", "id": "..."}."""
    return _ok(_get_client().read("ListUserTargetPermissions", {"user_target": _parse_json(user_target)}))


@mcp.tool()
def get_permission(target: str | dict) -> str:
    """Get permission on a resource target. Pass target as JSON: {"type": "Server", "id": "..."}."""
    return _ok(_get_client().read("GetPermission", {"target": _parse_json(target)}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — API Keys
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_api_keys() -> str:
    """List API keys for the calling user."""
    return _ok(_get_client().read("ListApiKeys"))


@mcp.tool()
def list_api_keys_for_service_user(user: str) -> str:
    """List API keys for a service user."""
    return _ok(_get_client().read("ListApiKeysForServiceUser", {"user": user}))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Provider Accounts
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_git_provider_accounts(
    domain: str | None = None,
    username: str | None = None,
) -> str:
    """List git provider accounts. Optionally filter by domain and/or username."""
    params: dict = {}
    if domain is not None:
        params["domain"] = domain
    if username is not None:
        params["username"] = username
    return _ok(_get_client().read("ListGitProviderAccounts", params or None))


@mcp.tool()
def get_git_provider_account(id: str) -> str:
    """Get a git provider account by id."""
    return _ok(_get_client().read("GetGitProviderAccount", {"id": id}))


@mcp.tool()
def list_git_providers_from_config(target: str | dict | None = None) -> str:
    """List git providers from Core config. Optionally pass target as JSON."""
    params: dict = {}
    if target is not None:
        params["target"] = _parse_json(target)
    return _ok(_get_client().read("ListGitProvidersFromConfig", params or None))


@mcp.tool()
def list_docker_registry_accounts(
    domain: str | None = None,
    username: str | None = None,
) -> str:
    """List Docker registry accounts. Optionally filter by domain and/or username."""
    params: dict = {}
    if domain is not None:
        params["domain"] = domain
    if username is not None:
        params["username"] = username
    return _ok(_get_client().read("ListDockerRegistryAccounts", params or None))


@mcp.tool()
def get_docker_registry_account(id: str) -> str:
    """Get a Docker registry account by id."""
    return _ok(_get_client().read("GetDockerRegistryAccount", {"id": id}))


@mcp.tool()
def list_docker_registries_from_config(target: str | dict | None = None) -> str:
    """List Docker registries from Core config. Optionally pass target as JSON."""
    params: dict = {}
    if target is not None:
        params["target"] = _parse_json(target)
    return _ok(_get_client().read("ListDockerRegistriesFromConfig", params or None))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Updates & Alerts
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_updates(page: int = 0, query: str | dict | None = None) -> str:
    """List updates (paginated). Optionally filter by mongo query (JSON string)."""
    params: dict = {"page": page}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListUpdates", params))


@mcp.tool()
def get_update(id: str) -> str:
    """Get a specific update by id."""
    return _ok(_get_client().read("GetUpdate", {"id": id}))


@mcp.tool()
def list_alerts(page: int = 0, query: str | dict | None = None) -> str:
    """List alerts (paginated). Optionally filter by mongo query (JSON string)."""
    params: dict = {"page": page}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListAlerts", params))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Misc
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_secrets(target: str | dict | None = None) -> str:
    """List available secret variable names. Optionally pass target as JSON."""
    params: dict = {}
    if target is not None:
        params["target"] = _parse_json(target)
    return _ok(_get_client().read("ListSecrets", params or None))


@mcp.tool()
def list_schedules(tags: str | None = None) -> str:
    """List scheduled operations. Optionally filter by comma-separated tag ids/names."""
    params: dict = {"tags": [], "tag_behavior": "All"}
    if tags is not None:
        params["tags"] = [t.strip() for t in tags.split(",")]
    return _ok(_get_client().read("ListSchedules", params))


@mcp.tool()
def get_resource_matching_container(server: str, container: str) -> str:
    """Find the Komodo resource that matches a Docker container."""
    return _ok(_get_client().read("GetResourceMatchingContainer", {"server": server, "container": container}))


@mcp.tool()
def list_common_deployment_extra_args(query: str | dict | None = None) -> str:
    """List common extra args used across deployments."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListCommonDeploymentExtraArgs", params or None))


@mcp.tool()
def list_common_build_extra_args(query: str | dict | None = None) -> str:
    """List common extra args used across builds."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListCommonBuildExtraArgs", params or None))


@mcp.tool()
def list_common_stack_extra_args(query: str | dict | None = None) -> str:
    """List common extra args used across stacks."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListCommonStackExtraArgs", params or None))


@mcp.tool()
def list_common_stack_build_extra_args(query: str | dict | None = None) -> str:
    """List common stack build extra args."""
    params: dict = {}
    if query is not None:
        params["query"] = _parse_json(query)
    return _ok(_get_client().read("ListCommonStackBuildExtraArgs", params or None))


# ══════════════════════════════════════════════════════════════════════════════
#  READ — Export
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def export_all_resources_to_toml(
    include_resources: bool = True,
    include_variables: bool = True,
    include_user_groups: bool = True,
    tags: str | None = None,
) -> str:
    """Export all resources to TOML format. Optionally filter by comma-separated tag ids."""
    params: dict = {
        "include_resources": include_resources,
        "include_variables": include_variables,
        "include_user_groups": include_user_groups,
        "tags": [],
    }
    if tags is not None:
        params["tags"] = [t.strip() for t in tags.split(",")]
    return _ok(_get_client().read("ExportAllResourcesToToml", params))


@mcp.tool()
def export_resources_to_toml(
    targets: str | list,
    include_variables: bool = True,
    user_groups: str | None = None,
) -> str:
    """Export specific resources to TOML. targets: JSON array of resource targets. user_groups: comma-separated."""
    params: dict = {
        "targets": _parse_json(targets),
        "include_variables": include_variables,
        "user_groups": [],
    }
    if user_groups is not None:
        params["user_groups"] = [g.strip() for g in user_groups.split(",")]
    return _ok(_get_client().read("ExportResourcesToToml", params))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Servers
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_server(name: str, config: str | dict | None = None) -> str:
    """Create a new server. config: optional JSON string with server configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateServer", params))


@mcp.tool()
def update_server(id: str, config: str | dict) -> str:
    """Update server configuration. config: JSON string with partial server config."""
    return _ok(_get_client().write("UpdateServer", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_server(id: str) -> str:
    """Delete a server by id."""
    return _ok(_get_client().write("DeleteServer", {"id": id}))


@mcp.tool()
def rename_server(id: str, name: str) -> str:
    """Rename a server."""
    return _ok(_get_client().write("RenameServer", {"id": id, "name": name}))


@mcp.tool()
def copy_server(id: str, name: str) -> str:
    """Copy a server to a new one with a different name."""
    return _ok(_get_client().write("CopyServer", {"id": id, "name": name}))


@mcp.tool()
def create_network(server: str, name: str) -> str:
    """Create a Docker network on a server."""
    return _ok(_get_client().write("CreateNetwork", {"server": server, "name": name}))


@mcp.tool()
def create_terminal(server: str, name: str, command: str, recreate: str = "Never") -> str:
    """Create a terminal on a server. recreate: Never, Always, or DifferentCommand."""
    return _ok(_get_client().write("CreateTerminal", {
        "server": server,
        "name": name,
        "command": command,
        "recreate": recreate,
    }))


@mcp.tool()
def delete_terminal(server: str, terminal: str) -> str:
    """Delete a terminal on a server."""
    return _ok(_get_client().write("DeleteTerminal", {"server": server, "terminal": terminal}))


@mcp.tool()
def delete_all_terminals(server: str) -> str:
    """Delete all terminals on a server."""
    return _ok(_get_client().write("DeleteAllTerminals", {"server": server}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Deployments
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_deployment(name: str, config: str | dict | None = None) -> str:
    """Create a new deployment. config: optional JSON string with deployment configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateDeployment", params))


@mcp.tool()
def update_deployment(id: str, config: str | dict) -> str:
    """Update deployment configuration. config: JSON string with partial deployment config."""
    return _ok(_get_client().write("UpdateDeployment", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_deployment(id: str) -> str:
    """Delete a deployment by id."""
    return _ok(_get_client().write("DeleteDeployment", {"id": id}))


@mcp.tool()
def rename_deployment(id: str, name: str) -> str:
    """Rename a deployment."""
    return _ok(_get_client().write("RenameDeployment", {"id": id, "name": name}))


@mcp.tool()
def copy_deployment(id: str, name: str) -> str:
    """Copy a deployment to a new one with a different name."""
    return _ok(_get_client().write("CopyDeployment", {"id": id, "name": name}))


@mcp.tool()
def create_deployment_from_container(name: str, server: str) -> str:
    """Create a deployment from an existing container on a server."""
    return _ok(_get_client().write("CreateDeploymentFromContainer", {"name": name, "server": server}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Stacks
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_stack(name: str, config: str | dict | None = None) -> str:
    """Create a new stack. config: optional JSON string with stack configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateStack", params))


@mcp.tool()
def update_stack(id: str, config: str | dict) -> str:
    """Update stack configuration. config: JSON string with partial stack config."""
    return _ok(_get_client().write("UpdateStack", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_stack(id: str) -> str:
    """Delete a stack by id."""
    return _ok(_get_client().write("DeleteStack", {"id": id}))


@mcp.tool()
def rename_stack(id: str, name: str) -> str:
    """Rename a stack."""
    return _ok(_get_client().write("RenameStack", {"id": id, "name": name}))


@mcp.tool()
def copy_stack(id: str, name: str) -> str:
    """Copy a stack to a new one with a different name."""
    return _ok(_get_client().write("CopyStack", {"id": id, "name": name}))


@mcp.tool()
def refresh_stack_cache(stack: str) -> str:
    """Refresh the cached state of a stack."""
    return _ok(_get_client().write("RefreshStackCache", {"stack": stack}))


@mcp.tool()
def write_stack_file_contents(stack: str, file_path: str, contents: str) -> str:
    """Write file contents for a stack (e.g. docker-compose.yml)."""
    return _ok(_get_client().write("WriteStackFileContents", {
        "stack": stack,
        "file_path": file_path,
        "contents": contents,
    }))


@mcp.tool()
def create_stack_webhook(stack: str, action: str = "Deploy") -> str:
    """Create a webhook for a stack. action: Refresh or Deploy."""
    return _ok(_get_client().write("CreateStackWebhook", {"stack": stack, "action": action}))


@mcp.tool()
def delete_stack_webhook(stack: str, action: str = "Deploy") -> str:
    """Delete a webhook for a stack. action: Refresh or Deploy."""
    return _ok(_get_client().write("DeleteStackWebhook", {"stack": stack, "action": action}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Builds
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_build(name: str, config: str | dict | None = None) -> str:
    """Create a new build. config: optional JSON string with build configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateBuild", params))


@mcp.tool()
def update_build(id: str, config: str | dict) -> str:
    """Update build configuration. config: JSON string with partial build config."""
    return _ok(_get_client().write("UpdateBuild", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_build(id: str) -> str:
    """Delete a build by id."""
    return _ok(_get_client().write("DeleteBuild", {"id": id}))


@mcp.tool()
def rename_build(id: str, name: str) -> str:
    """Rename a build."""
    return _ok(_get_client().write("RenameBuild", {"id": id, "name": name}))


@mcp.tool()
def copy_build(id: str, name: str) -> str:
    """Copy a build to a new one with a different name."""
    return _ok(_get_client().write("CopyBuild", {"id": id, "name": name}))


@mcp.tool()
def refresh_build_cache(build: str) -> str:
    """Refresh the cached state of a build."""
    return _ok(_get_client().write("RefreshBuildCache", {"build": build}))


@mcp.tool()
def write_build_file_contents(build: str, contents: str) -> str:
    """Write Dockerfile contents for a build."""
    return _ok(_get_client().write("WriteBuildFileContents", {"build": build, "contents": contents}))


@mcp.tool()
def create_build_webhook(build: str) -> str:
    """Create a webhook for a build."""
    return _ok(_get_client().write("CreateBuildWebhook", {"build": build}))


@mcp.tool()
def delete_build_webhook(build: str) -> str:
    """Delete a webhook for a build."""
    return _ok(_get_client().write("DeleteBuildWebhook", {"build": build}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Repos
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_repo(name: str, config: str | dict | None = None) -> str:
    """Create a new repo. config: optional JSON string with repo configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateRepo", params))


@mcp.tool()
def update_repo(id: str, config: str | dict) -> str:
    """Update repo configuration. config: JSON string with partial repo config."""
    return _ok(_get_client().write("UpdateRepo", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_repo(id: str) -> str:
    """Delete a repo by id."""
    return _ok(_get_client().write("DeleteRepo", {"id": id}))


@mcp.tool()
def rename_repo(id: str, name: str) -> str:
    """Rename a repo."""
    return _ok(_get_client().write("RenameRepo", {"id": id, "name": name}))


@mcp.tool()
def copy_repo(id: str, name: str) -> str:
    """Copy a repo to a new one with a different name."""
    return _ok(_get_client().write("CopyRepo", {"id": id, "name": name}))


@mcp.tool()
def refresh_repo_cache(repo: str) -> str:
    """Refresh the cached state of a repo."""
    return _ok(_get_client().write("RefreshRepoCache", {"repo": repo}))


@mcp.tool()
def create_repo_webhook(repo: str, action: str = "Pull") -> str:
    """Create a webhook for a repo. action: Clone, Pull, or Build."""
    return _ok(_get_client().write("CreateRepoWebhook", {"repo": repo, "action": action}))


@mcp.tool()
def delete_repo_webhook(repo: str, action: str = "Pull") -> str:
    """Delete a webhook for a repo. action: Clone, Pull, or Build."""
    return _ok(_get_client().write("DeleteRepoWebhook", {"repo": repo, "action": action}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Procedures
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_procedure(name: str, config: str | dict | None = None) -> str:
    """Create a new procedure. config: optional JSON string with procedure configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateProcedure", params))


@mcp.tool()
def update_procedure(id: str, config: str | dict) -> str:
    """Update procedure configuration. config: JSON string with partial procedure config."""
    return _ok(_get_client().write("UpdateProcedure", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_procedure(id: str) -> str:
    """Delete a procedure by id."""
    return _ok(_get_client().write("DeleteProcedure", {"id": id}))


@mcp.tool()
def rename_procedure(id: str, name: str) -> str:
    """Rename a procedure."""
    return _ok(_get_client().write("RenameProcedure", {"id": id, "name": name}))


@mcp.tool()
def copy_procedure(id: str, name: str) -> str:
    """Copy a procedure to a new one with a different name."""
    return _ok(_get_client().write("CopyProcedure", {"id": id, "name": name}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Actions
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_action(name: str, config: str | dict | None = None) -> str:
    """Create a new action. config: optional JSON string with action configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateAction", params))


@mcp.tool()
def update_action(id: str, config: str | dict) -> str:
    """Update action configuration. config: JSON string with partial action config."""
    return _ok(_get_client().write("UpdateAction", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_action(id: str) -> str:
    """Delete an action by id."""
    return _ok(_get_client().write("DeleteAction", {"id": id}))


@mcp.tool()
def rename_action(id: str, name: str) -> str:
    """Rename an action."""
    return _ok(_get_client().write("RenameAction", {"id": id, "name": name}))


@mcp.tool()
def copy_action(id: str, name: str) -> str:
    """Copy an action to a new one with a different name."""
    return _ok(_get_client().write("CopyAction", {"id": id, "name": name}))


@mcp.tool()
def create_action_webhook(action: str) -> str:
    """Create a webhook for an action."""
    return _ok(_get_client().write("CreateActionWebhook", {"action": action}))


@mcp.tool()
def delete_action_webhook(action: str) -> str:
    """Delete a webhook for an action."""
    return _ok(_get_client().write("DeleteActionWebhook", {"action": action}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Resource Syncs
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_resource_sync(name: str, config: str | dict | None = None) -> str:
    """Create a new resource sync. config: optional JSON string with sync configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateResourceSync", params))


@mcp.tool()
def update_resource_sync(id: str, config: str | dict) -> str:
    """Update resource sync configuration. config: JSON string with partial sync config."""
    return _ok(_get_client().write("UpdateResourceSync", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_resource_sync(id: str) -> str:
    """Delete a resource sync by id."""
    return _ok(_get_client().write("DeleteResourceSync", {"id": id}))


@mcp.tool()
def rename_resource_sync(id: str, name: str) -> str:
    """Rename a resource sync."""
    return _ok(_get_client().write("RenameResourceSync", {"id": id, "name": name}))


@mcp.tool()
def copy_resource_sync(id: str, name: str) -> str:
    """Copy a resource sync to a new one with a different name."""
    return _ok(_get_client().write("CopyResourceSync", {"id": id, "name": name}))


@mcp.tool()
def refresh_resource_sync_pending(sync: str) -> str:
    """Refresh the pending state of a resource sync."""
    return _ok(_get_client().write("RefreshResourceSyncPending", {"sync": sync}))


@mcp.tool()
def commit_sync(sync: str) -> str:
    """Commit pending changes for a resource sync."""
    return _ok(_get_client().write("CommitSync", {"sync": sync}))


@mcp.tool()
def write_sync_file_contents(sync: str, resource_path: str, file_path: str, contents: str) -> str:
    """Write file contents for a resource sync."""
    return _ok(_get_client().write("WriteSyncFileContents", {
        "sync": sync,
        "resource_path": resource_path,
        "file_path": file_path,
        "contents": contents,
    }))


@mcp.tool()
def create_sync_webhook(sync: str, action: str = "Sync") -> str:
    """Create a webhook for a resource sync. action: Refresh or Sync."""
    return _ok(_get_client().write("CreateSyncWebhook", {"sync": sync, "action": action}))


@mcp.tool()
def delete_sync_webhook(sync: str, action: str = "Sync") -> str:
    """Delete a webhook for a resource sync. action: Refresh or Sync."""
    return _ok(_get_client().write("DeleteSyncWebhook", {"sync": sync, "action": action}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Builders
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_builder(name: str, config: str | dict | None = None) -> str:
    """Create a new builder. config: optional JSON string with builder configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateBuilder", params))


@mcp.tool()
def update_builder(id: str, config: str | dict) -> str:
    """Update builder configuration. config: JSON string with partial builder config."""
    return _ok(_get_client().write("UpdateBuilder", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_builder(id: str) -> str:
    """Delete a builder by id."""
    return _ok(_get_client().write("DeleteBuilder", {"id": id}))


@mcp.tool()
def rename_builder(id: str, name: str) -> str:
    """Rename a builder."""
    return _ok(_get_client().write("RenameBuilder", {"id": id, "name": name}))


@mcp.tool()
def copy_builder(id: str, name: str) -> str:
    """Copy a builder to a new one with a different name."""
    return _ok(_get_client().write("CopyBuilder", {"id": id, "name": name}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Alerters
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_alerter(name: str, config: str | dict | None = None) -> str:
    """Create a new alerter. config: optional JSON string with alerter configuration."""
    params: dict = {"name": name, "config": {}}
    if config is not None:
        params["config"] = _parse_json(config)
    return _ok(_get_client().write("CreateAlerter", params))


@mcp.tool()
def update_alerter(id: str, config: str | dict) -> str:
    """Update alerter configuration. config: JSON string with partial alerter config."""
    return _ok(_get_client().write("UpdateAlerter", {"id": id, "config": _parse_json(config)}))


@mcp.tool()
def delete_alerter(id: str) -> str:
    """Delete an alerter by id."""
    return _ok(_get_client().write("DeleteAlerter", {"id": id}))


@mcp.tool()
def rename_alerter(id: str, name: str) -> str:
    """Rename an alerter."""
    return _ok(_get_client().write("RenameAlerter", {"id": id, "name": name}))


@mcp.tool()
def copy_alerter(id: str, name: str) -> str:
    """Copy an alerter to a new one with a different name."""
    return _ok(_get_client().write("CopyAlerter", {"id": id, "name": name}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Tags
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_tag(name: str, color: str | None = None) -> str:
    """Create a new tag. color: optional hex color or named color."""
    params: dict = {"name": name}
    if color is not None:
        params["color"] = color
    return _ok(_get_client().write("CreateTag", params))


@mcp.tool()
def delete_tag(id: str) -> str:
    """Delete a tag by id."""
    return _ok(_get_client().write("DeleteTag", {"id": id}))


@mcp.tool()
def rename_tag(id: str, name: str) -> str:
    """Rename a tag."""
    return _ok(_get_client().write("RenameTag", {"id": id, "name": name}))


@mcp.tool()
def update_tag_color(tag: str, color: str) -> str:
    """Update the color of a tag."""
    return _ok(_get_client().write("UpdateTagColor", {"tag": tag, "color": color}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Variables
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_variable(
    name: str,
    value: str,
    description: str = "",
    is_secret: bool = False,
) -> str:
    """Create a new variable."""
    return _ok(_get_client().write("CreateVariable", {
        "name": name,
        "value": value,
        "description": description,
        "is_secret": is_secret,
    }))


@mcp.tool()
def delete_variable(name: str) -> str:
    """Delete a variable by name."""
    return _ok(_get_client().write("DeleteVariable", {"name": name}))


@mcp.tool()
def update_variable_value(name: str, value: str) -> str:
    """Update the value of a variable."""
    return _ok(_get_client().write("UpdateVariableValue", {"name": name, "value": value}))


@mcp.tool()
def update_variable_description(name: str, description: str) -> str:
    """Update the description of a variable."""
    return _ok(_get_client().write("UpdateVariableDescription", {"name": name, "description": description}))


@mcp.tool()
def update_variable_is_secret(name: str, is_secret: bool) -> str:
    """Update whether a variable is a secret."""
    return _ok(_get_client().write("UpdateVariableIsSecret", {"name": name, "is_secret": is_secret}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Users
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_local_user(username: str, password: str) -> str:
    """Create a local user."""
    return _ok(_get_client().write("CreateLocalUser", {"username": username, "password": password}))


@mcp.tool()
def create_service_user(username: str, description: str = "") -> str:
    """Create a service user for API automation."""
    return _ok(_get_client().write("CreateServiceUser", {"username": username, "description": description}))


@mcp.tool()
def delete_user(user: str) -> str:
    """Delete a user by id or username."""
    return _ok(_get_client().write("DeleteUser", {"user": user}))


@mcp.tool()
def update_user_admin(user_id: str, admin: bool) -> str:
    """Set or unset admin status for a user."""
    return _ok(_get_client().write("UpdateUserAdmin", {"user_id": user_id, "admin": admin}))


@mcp.tool()
def update_user_password(password: str) -> str:
    """Update the calling user's password."""
    return _ok(_get_client().write("UpdateUserPassword", {"password": password}))


@mcp.tool()
def update_user_username(username: str) -> str:
    """Update the calling user's username."""
    return _ok(_get_client().write("UpdateUserUsername", {"username": username}))


@mcp.tool()
def update_user_base_permissions(
    user_id: str,
    enabled: bool | None = None,
    create_servers: bool | None = None,
    create_builds: bool | None = None,
) -> str:
    """Update base permissions for a user."""
    params: dict = {"user_id": user_id}
    if enabled is not None:
        params["enabled"] = enabled
    if create_servers is not None:
        params["create_servers"] = create_servers
    if create_builds is not None:
        params["create_builds"] = create_builds
    return _ok(_get_client().write("UpdateUserBasePermissions", params))


@mcp.tool()
def update_service_user_description(username: str, description: str) -> str:
    """Update the description of a service user."""
    return _ok(_get_client().write("UpdateServiceUserDescription", {
        "username": username,
        "description": description,
    }))


@mcp.tool()
def create_api_key_for_service_user(user_id: str, name: str, expires: int = 0) -> str:
    """Create an API key for a service user. expires: unix timestamp (0 = never)."""
    return _ok(_get_client().write("CreateApiKeyForServiceUser", {
        "user_id": user_id,
        "name": name,
        "expires": expires,
    }))


@mcp.tool()
def delete_api_key_for_service_user(key: str) -> str:
    """Delete an API key for a service user."""
    return _ok(_get_client().write("DeleteApiKeyForServiceUser", {"key": key}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — User Groups
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_user_group(name: str) -> str:
    """Create a new user group."""
    return _ok(_get_client().write("CreateUserGroup", {"name": name}))


@mcp.tool()
def delete_user_group(id: str) -> str:
    """Delete a user group by id."""
    return _ok(_get_client().write("DeleteUserGroup", {"id": id}))


@mcp.tool()
def rename_user_group(id: str, name: str) -> str:
    """Rename a user group."""
    return _ok(_get_client().write("RenameUserGroup", {"id": id, "name": name}))


@mcp.tool()
def add_user_to_user_group(user_group: str, user: str) -> str:
    """Add a user to a user group."""
    return _ok(_get_client().write("AddUserToUserGroup", {"user_group": user_group, "user": user}))


@mcp.tool()
def remove_user_from_user_group(user_group: str, user: str) -> str:
    """Remove a user from a user group."""
    return _ok(_get_client().write("RemoveUserFromUserGroup", {"user_group": user_group, "user": user}))


@mcp.tool()
def set_users_in_user_group(user_group: str, users: str) -> str:
    """Set the exact list of users in a user group. users: comma-separated user ids."""
    return _ok(_get_client().write("SetUsersInUserGroup", {
        "user_group": user_group,
        "users": [u.strip() for u in users.split(",")],
    }))


@mcp.tool()
def set_everyone_user_group(user_group: str, everyone: bool) -> str:
    """Set whether a user group includes everyone."""
    return _ok(_get_client().write("SetEveryoneUserGroup", {"user_group": user_group, "everyone": everyone}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Permissions
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def update_permission_on_resource_type(
    user_target: str | dict,
    resource_type: str,
    permission: str | dict,
) -> str:
    """Update permission on a resource type. user_target/permission: JSON strings."""
    return _ok(_get_client().write("UpdatePermissionOnResourceType", {
        "user_target": _parse_json(user_target),
        "resource_type": resource_type,
        "permission": _parse_json(permission),
    }))


@mcp.tool()
def update_permission_on_target(
    user_target: str | dict,
    resource_target: str | dict,
    permission: str | dict,
) -> str:
    """Update permission on a specific resource. user_target/resource_target/permission: JSON strings."""
    return _ok(_get_client().write("UpdatePermissionOnTarget", {
        "user_target": _parse_json(user_target),
        "resource_target": _parse_json(resource_target),
        "permission": _parse_json(permission),
    }))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Provider Accounts
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_git_provider_account(account: str | dict) -> str:
    """Create a git provider account. account: JSON string with account config."""
    return _ok(_get_client().write("CreateGitProviderAccount", {"account": _parse_json(account)}))


@mcp.tool()
def update_git_provider_account(id: str, account: str | dict) -> str:
    """Update a git provider account. account: JSON string with partial account config."""
    return _ok(_get_client().write("UpdateGitProviderAccount", {"id": id, "account": _parse_json(account)}))


@mcp.tool()
def delete_git_provider_account(id: str) -> str:
    """Delete a git provider account by id."""
    return _ok(_get_client().write("DeleteGitProviderAccount", {"id": id}))


@mcp.tool()
def create_docker_registry_account(account: str | dict) -> str:
    """Create a Docker registry account. account: JSON string with account config."""
    return _ok(_get_client().write("CreateDockerRegistryAccount", {"account": _parse_json(account)}))


@mcp.tool()
def update_docker_registry_account(id: str, account: str | dict) -> str:
    """Update a Docker registry account. account: JSON string with partial account config."""
    return _ok(_get_client().write("UpdateDockerRegistryAccount", {"id": id, "account": _parse_json(account)}))


@mcp.tool()
def delete_docker_registry_account(id: str) -> str:
    """Delete a Docker registry account by id."""
    return _ok(_get_client().write("DeleteDockerRegistryAccount", {"id": id}))


# ══════════════════════════════════════════════════════════════════════════════
#  WRITE — Resource Meta
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def update_resource_meta(
    target: str | dict,
    description: str | None = None,
    template: bool | None = None,
    tags: str | None = None,
) -> str:
    """Update resource metadata. target: JSON string. tags: comma-separated tag ids."""
    params: dict = {"target": _parse_json(target)}
    if description is not None:
        params["description"] = description
    if template is not None:
        params["template"] = template
    if tags is not None:
        params["tags"] = [t.strip() for t in tags.split(",")]
    return _ok(_get_client().write("UpdateResourceMeta", params))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Deployments
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def deploy(
    deployment: str,
    stop_signal: str | None = None,
    stop_time: int | None = None,
) -> str:
    """Deploy a deployment (pull image + recreate container)."""
    params: dict = {"deployment": deployment}
    if stop_signal is not None:
        params["stop_signal"] = stop_signal
    if stop_time is not None:
        params["stop_time"] = stop_time
    return _ok(_get_client().execute("Deploy", params))


@mcp.tool()
def pull_deployment(deployment: str) -> str:
    """Pull the latest image for a deployment."""
    return _ok(_get_client().execute("PullDeployment", {"deployment": deployment}))


@mcp.tool()
def start_deployment(deployment: str) -> str:
    """Start a stopped deployment."""
    return _ok(_get_client().execute("StartDeployment", {"deployment": deployment}))


@mcp.tool()
def stop_deployment(
    deployment: str,
    signal: str | None = None,
    time: int | None = None,
) -> str:
    """Stop a running deployment."""
    params: dict = {"deployment": deployment}
    if signal is not None:
        params["signal"] = signal
    if time is not None:
        params["time"] = time
    return _ok(_get_client().execute("StopDeployment", params))


@mcp.tool()
def restart_deployment(deployment: str) -> str:
    """Restart a deployment."""
    return _ok(_get_client().execute("RestartDeployment", {"deployment": deployment}))


@mcp.tool()
def pause_deployment(deployment: str) -> str:
    """Pause a running deployment."""
    return _ok(_get_client().execute("PauseDeployment", {"deployment": deployment}))


@mcp.tool()
def unpause_deployment(deployment: str) -> str:
    """Unpause a paused deployment."""
    return _ok(_get_client().execute("UnpauseDeployment", {"deployment": deployment}))


@mcp.tool()
def destroy_deployment(
    deployment: str,
    signal: str | None = None,
    time: int | None = None,
) -> str:
    """Destroy a deployment (stop and remove container)."""
    params: dict = {"deployment": deployment}
    if signal is not None:
        params["signal"] = signal
    if time is not None:
        params["time"] = time
    return _ok(_get_client().execute("DestroyDeployment", params))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Stacks
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def deploy_stack(
    stack: str,
    services: str | None = None,
    stop_time: int | None = None,
) -> str:
    """Deploy a stack. services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    if stop_time is not None:
        params["stop_time"] = stop_time
    return _ok(_get_client().execute("DeployStack", params))


@mcp.tool()
def deploy_stack_if_changed(stack: str, stop_time: int | None = None) -> str:
    """Deploy a stack only if its compose file has changed."""
    params: dict = {"stack": stack}
    if stop_time is not None:
        params["stop_time"] = stop_time
    return _ok(_get_client().execute("DeployStackIfChanged", params))


@mcp.tool()
def pull_stack(stack: str, services: str | None = None) -> str:
    """Pull latest images for a stack. services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    return _ok(_get_client().execute("PullStack", params))


@mcp.tool()
def start_stack(stack: str, services: str | None = None) -> str:
    """Start a stopped stack. services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    return _ok(_get_client().execute("StartStack", params))


@mcp.tool()
def stop_stack(
    stack: str,
    services: str | None = None,
    stop_time: int | None = None,
) -> str:
    """Stop a running stack. services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    if stop_time is not None:
        params["stop_time"] = stop_time
    return _ok(_get_client().execute("StopStack", params))


@mcp.tool()
def restart_stack(stack: str, services: str | None = None) -> str:
    """Restart a stack. services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    return _ok(_get_client().execute("RestartStack", params))


@mcp.tool()
def pause_stack(stack: str, services: str | None = None) -> str:
    """Pause a running stack. services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    return _ok(_get_client().execute("PauseStack", params))


@mcp.tool()
def unpause_stack(stack: str, services: str | None = None) -> str:
    """Unpause a paused stack. services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": []}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    return _ok(_get_client().execute("UnpauseStack", params))


@mcp.tool()
def destroy_stack(
    stack: str,
    services: str | None = None,
    remove_orphans: bool = False,
    stop_time: int | None = None,
) -> str:
    """Destroy a stack (stop and remove containers). services: optional comma-separated service names."""
    params: dict = {"stack": stack, "services": [], "remove_orphans": remove_orphans}
    if services is not None:
        params["services"] = [s.strip() for s in services.split(",")]
    if stop_time is not None:
        params["stop_time"] = stop_time
    return _ok(_get_client().execute("DestroyStack", params))


@mcp.tool()
def run_stack_service(
    stack: str,
    service: str,
    command: str | None = None,
    detach: bool | None = None,
) -> str:
    """Run a one-off command in a stack service. command: optional shell command."""
    params: dict = {"stack": stack, "service": service}
    if command is not None:
        params["command"] = command.split()
    if detach is not None:
        params["detach"] = detach
    return _ok(_get_client().execute("RunStackService", params))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Containers
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def start_container(server: str, container: str) -> str:
    """Start a Docker container on a server."""
    return _ok(_get_client().execute("StartContainer", {"server": server, "container": container}))


@mcp.tool()
def stop_container(
    server: str,
    container: str,
    signal: str | None = None,
    time: int | None = None,
) -> str:
    """Stop a Docker container on a server."""
    params: dict = {"server": server, "container": container}
    if signal is not None:
        params["signal"] = signal
    if time is not None:
        params["time"] = time
    return _ok(_get_client().execute("StopContainer", params))


@mcp.tool()
def restart_container(server: str, container: str) -> str:
    """Restart a Docker container on a server."""
    return _ok(_get_client().execute("RestartContainer", {"server": server, "container": container}))


@mcp.tool()
def pause_container(server: str, container: str) -> str:
    """Pause a Docker container on a server."""
    return _ok(_get_client().execute("PauseContainer", {"server": server, "container": container}))


@mcp.tool()
def unpause_container(server: str, container: str) -> str:
    """Unpause a Docker container on a server."""
    return _ok(_get_client().execute("UnpauseContainer", {"server": server, "container": container}))


@mcp.tool()
def destroy_container(
    server: str,
    container: str,
    signal: str | None = None,
    time: int | None = None,
) -> str:
    """Destroy a Docker container on a server (stop and remove)."""
    params: dict = {"server": server, "container": container}
    if signal is not None:
        params["signal"] = signal
    if time is not None:
        params["time"] = time
    return _ok(_get_client().execute("DestroyContainer", params))


@mcp.tool()
def start_all_containers(server: str) -> str:
    """Start all Docker containers on a server."""
    return _ok(_get_client().execute("StartAllContainers", {"server": server}))


@mcp.tool()
def stop_all_containers(server: str) -> str:
    """Stop all Docker containers on a server."""
    return _ok(_get_client().execute("StopAllContainers", {"server": server}))


@mcp.tool()
def restart_all_containers(server: str) -> str:
    """Restart all Docker containers on a server."""
    return _ok(_get_client().execute("RestartAllContainers", {"server": server}))


@mcp.tool()
def pause_all_containers(server: str) -> str:
    """Pause all Docker containers on a server."""
    return _ok(_get_client().execute("PauseAllContainers", {"server": server}))


@mcp.tool()
def unpause_all_containers(server: str) -> str:
    """Unpause all Docker containers on a server."""
    return _ok(_get_client().execute("UnpauseAllContainers", {"server": server}))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Builds
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def run_build(build: str) -> str:
    """Run a build."""
    return _ok(_get_client().execute("RunBuild", {"build": build}))


@mcp.tool()
def cancel_build(build: str) -> str:
    """Cancel a running build."""
    return _ok(_get_client().execute("CancelBuild", {"build": build}))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Repos
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def clone_repo(repo: str) -> str:
    """Clone a repo on its configured server."""
    return _ok(_get_client().execute("CloneRepo", {"repo": repo}))


@mcp.tool()
def pull_repo(repo: str) -> str:
    """Pull latest changes for a repo."""
    return _ok(_get_client().execute("PullRepo", {"repo": repo}))


@mcp.tool()
def build_repo(repo: str) -> str:
    """Run the build command for a repo."""
    return _ok(_get_client().execute("BuildRepo", {"repo": repo}))


@mcp.tool()
def cancel_repo_build(repo: str) -> str:
    """Cancel a running repo build."""
    return _ok(_get_client().execute("CancelRepoBuild", {"repo": repo}))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Procedures & Actions
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def run_procedure(procedure: str) -> str:
    """Run a procedure."""
    return _ok(_get_client().execute("RunProcedure", {"procedure": procedure}))


@mcp.tool()
def run_action(action: str, args: str | dict | None = None) -> str:
    """Run an action. args: optional JSON object with arguments."""
    params: dict = {"action": action}
    if args is not None:
        params["args"] = _parse_json(args)
    return _ok(_get_client().execute("RunAction", params))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Resource Syncs
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def run_sync(
    sync: str,
    resource_type: str | None = None,
    resources: str | None = None,
) -> str:
    """Run a resource sync. resource_type: optional type filter. resources: optional comma-separated ids/names."""
    params: dict = {"sync": sync}
    if resource_type is not None:
        params["resource_type"] = resource_type
    if resources is not None:
        params["resources"] = [r.strip() for r in resources.split(",")]
    return _ok(_get_client().execute("RunSync", params))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Docker Cleanup
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def prune_containers(server: str) -> str:
    """Prune stopped containers on a server."""
    return _ok(_get_client().execute("PruneContainers", {"server": server}))


@mcp.tool()
def prune_images(server: str) -> str:
    """Prune unused images on a server."""
    return _ok(_get_client().execute("PruneImages", {"server": server}))


@mcp.tool()
def prune_networks(server: str) -> str:
    """Prune unused networks on a server."""
    return _ok(_get_client().execute("PruneNetworks", {"server": server}))


@mcp.tool()
def prune_volumes(server: str) -> str:
    """Prune unused volumes on a server."""
    return _ok(_get_client().execute("PruneVolumes", {"server": server}))


@mcp.tool()
def prune_buildx(server: str) -> str:
    """Prune buildx cache on a server."""
    return _ok(_get_client().execute("PruneBuildx", {"server": server}))


@mcp.tool()
def prune_docker_builders(server: str) -> str:
    """Prune Docker builders on a server."""
    return _ok(_get_client().execute("PruneDockerBuilders", {"server": server}))


@mcp.tool()
def prune_system(server: str) -> str:
    """Prune all unused Docker resources on a server (containers, images, networks, volumes)."""
    return _ok(_get_client().execute("PruneSystem", {"server": server}))


@mcp.tool()
def delete_image(server: str, name: str) -> str:
    """Delete a Docker image on a server."""
    return _ok(_get_client().execute("DeleteImage", {"server": server, "name": name}))


@mcp.tool()
def delete_network(server: str, name: str) -> str:
    """Delete a Docker network on a server."""
    return _ok(_get_client().execute("DeleteNetwork", {"server": server, "name": name}))


@mcp.tool()
def delete_volume(server: str, name: str) -> str:
    """Delete a Docker volume on a server."""
    return _ok(_get_client().execute("DeleteVolume", {"server": server, "name": name}))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Batch Operations
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def batch_deploy(pattern: str) -> str:
    """Deploy multiple deployments matching a name pattern."""
    return _ok(_get_client().execute("BatchDeploy", {"pattern": pattern}))


@mcp.tool()
def batch_deploy_stack(pattern: str) -> str:
    """Deploy multiple stacks matching a name pattern."""
    return _ok(_get_client().execute("BatchDeployStack", {"pattern": pattern}))


@mcp.tool()
def batch_deploy_stack_if_changed(pattern: str) -> str:
    """Deploy multiple stacks (only if changed) matching a name pattern."""
    return _ok(_get_client().execute("BatchDeployStackIfChanged", {"pattern": pattern}))


@mcp.tool()
def batch_destroy_deployment(pattern: str) -> str:
    """Destroy multiple deployments matching a name pattern."""
    return _ok(_get_client().execute("BatchDestroyDeployment", {"pattern": pattern}))


@mcp.tool()
def batch_destroy_stack(pattern: str) -> str:
    """Destroy multiple stacks matching a name pattern."""
    return _ok(_get_client().execute("BatchDestroyStack", {"pattern": pattern}))


@mcp.tool()
def batch_run_build(pattern: str) -> str:
    """Run multiple builds matching a name pattern."""
    return _ok(_get_client().execute("BatchRunBuild", {"pattern": pattern}))


@mcp.tool()
def batch_clone_repo(pattern: str) -> str:
    """Clone multiple repos matching a name pattern."""
    return _ok(_get_client().execute("BatchCloneRepo", {"pattern": pattern}))


@mcp.tool()
def batch_pull_repo(pattern: str) -> str:
    """Pull multiple repos matching a name pattern."""
    return _ok(_get_client().execute("BatchPullRepo", {"pattern": pattern}))


@mcp.tool()
def batch_build_repo(pattern: str) -> str:
    """Build multiple repos matching a name pattern."""
    return _ok(_get_client().execute("BatchBuildRepo", {"pattern": pattern}))


@mcp.tool()
def batch_pull_stack(pattern: str) -> str:
    """Pull images for multiple stacks matching a name pattern."""
    return _ok(_get_client().execute("BatchPullStack", {"pattern": pattern}))


@mcp.tool()
def batch_run_action(pattern: str) -> str:
    """Run multiple actions matching a name pattern."""
    return _ok(_get_client().execute("BatchRunAction", {"pattern": pattern}))


@mcp.tool()
def batch_run_procedure(pattern: str) -> str:
    """Run multiple procedures matching a name pattern."""
    return _ok(_get_client().execute("BatchRunProcedure", {"pattern": pattern}))


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTE — Misc
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def send_alert(
    level: str,
    message: str,
    details: str = "",
    alerters: str | None = None,
) -> str:
    """Send a custom alert. level: Ok, Warning, or Critical. alerters: comma-separated alerter ids/names."""
    params: dict = {
        "level": level,
        "message": message,
        "details": details,
        "alerters": [],
    }
    if alerters is not None:
        params["alerters"] = [a.strip() for a in alerters.split(",")]
    return _ok(_get_client().execute("SendAlert", params))


@mcp.tool()
def test_alerter(alerter: str) -> str:
    """Test an alerter by sending a test notification."""
    return _ok(_get_client().execute("TestAlerter", {"alerter": alerter}))


@mcp.tool()
def global_auto_update() -> str:
    """Trigger a global poll for image updates on stacks/deployments with auto_update enabled. Admin only."""
    return _ok(_get_client().execute("GlobalAutoUpdate"))


@mcp.tool()
def backup_core_database() -> str:
    """Backup the Komodo Core database. Admin only."""
    return _ok(_get_client().execute("BackupCoreDatabase"))


@mcp.tool()
def clear_repo_cache() -> str:
    """Clear all repos from the Core repo cache. Admin only."""
    return _ok(_get_client().execute("ClearRepoCache"))


@mcp.tool()
def sleep(duration_ms: int) -> str:
    """Sleep for a specified duration in milliseconds."""
    return _ok(_get_client().execute("Sleep", {"duration_ms": duration_ms}))
