"""Compact mode: 6 meta-tools instead of 293 individual tools.

Tools are split by risk level so users can allow reads but block deletes:
  komodo_read        — safe resource queries (109 ops)
  komodo_write       — create/update/rename/copy resources (68 ops)
  komodo_execute     — trigger actions: deploy, start/stop, build (48 ops)
  komodo_delete      — delete, destroy, prune (36 ops)
  komodo_admin_read  — user/permission queries (10 ops)
  komodo_admin_write — user/permission management, admin-only actions (22 ops)

Set KOMODO_COMPACT=true to enable.
"""

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


# ── Operation registry ────────────────────────────────────────────────────────
# Maps operation name -> (scope, api_endpoint, param_names, docstring)
#
# scope:        which meta-tool handles this (read/write/execute/delete/admin_read/admin_write)
# api_endpoint: actual Komodo API endpoint to call (read/write/execute)

_OPERATIONS: dict[str, tuple[str, str, list[str], str]] = {
    # ── read — General ─────────────────────────────────────────
    "GetVersion": ("read", "read", [], "Get Komodo Core version."),
    "GetCoreInfo": ("read", "read", [], "Get Komodo Core configuration info."),
    # ── read — Servers ─────────────────────────────────────────
    "ListServers": ("read", "read", ["query"], "List servers. query: optional mongo query object."),
    "ListFullServers": ("read", "read", ["query"], "List servers with full config."),
    "GetServer": ("read", "read", ["server"], "Get a specific server by id or name."),
    "GetServersSummary": ("read", "read", [], "Get summary counts for servers."),
    "GetServerState": ("read", "read", ["server"], "Get the current state of a server."),
    "GetServerActionState": ("read", "read", ["server"], "Get the action state for a server."),
    "GetSystemStats": ("read", "read", ["server"], "Get current system stats (CPU, memory, disk) for a server."),
    "GetSystemInformation": ("read", "read", ["server"], "Get system information (OS, kernel) for a server."),
    "GetHistoricalServerStats": ("read", "read", ["server", "granularity", "page"], "Get historical system stats. granularity: 15-sec, 1-min, etc."),
    "GetPeripheryVersion": ("read", "read", ["server"], "Get the Periphery agent version on a server."),
    "ListSystemProcesses": ("read", "read", ["server"], "List running system processes on a server."),
    "ListTerminals": ("read", "read", ["server", "fresh"], "List active terminals on a server."),
    # ── read — Deployments ─────────────────────────────────────
    "ListDeployments": ("read", "read", ["query"], "List deployments."),
    "ListFullDeployments": ("read", "read", ["query"], "List deployments with full config."),
    "GetDeployment": ("read", "read", ["deployment"], "Get a specific deployment by id or name."),
    "GetDeploymentsSummary": ("read", "read", [], "Get summary counts for deployments."),
    "GetDeploymentActionState": ("read", "read", ["deployment"], "Get the action state for a deployment."),
    "GetDeploymentContainer": ("read", "read", ["deployment"], "Get the container info for a deployment."),
    "GetDeploymentLog": ("read", "read", ["deployment", "tail", "timestamps"], "Get the container log for a deployment."),
    "GetDeploymentStats": ("read", "read", ["deployment"], "Get container resource stats for a deployment."),
    "InspectDeploymentContainer": ("read", "read", ["deployment"], "Inspect the Docker container of a deployment."),
    # ── read — Stacks ──────────────────────────────────────────
    "ListStacks": ("read", "read", ["query"], "List stacks."),
    "ListFullStacks": ("read", "read", ["query"], "List stacks with full config."),
    "GetStack": ("read", "read", ["stack"], "Get a specific stack by id or name."),
    "GetStacksSummary": ("read", "read", [], "Get summary counts for stacks."),
    "GetStackActionState": ("read", "read", ["stack"], "Get the action state for a stack."),
    "GetStackLog": ("read", "read", ["stack", "services", "tail", "timestamps"], "Get logs for a stack. services: list of service names."),
    "GetStackWebhooksEnabled": ("read", "read", ["stack"], "Check if webhooks are enabled for a stack."),
    "ListStackServices": ("read", "read", ["stack"], "List services in a stack."),
    "InspectStackContainer": ("read", "read", ["stack", "service"], "Inspect a specific service container in a stack."),
    "SearchStackLog": ("read", "read", ["stack", "terms", "combinator", "invert", "timestamps", "services"], "Search stack logs. combinator: And or Or."),
    # ── read — Builds ──────────────────────────────────────────
    "ListBuilds": ("read", "read", ["query"], "List builds."),
    "ListFullBuilds": ("read", "read", ["query"], "List builds with full config."),
    "GetBuild": ("read", "read", ["build"], "Get a specific build by id or name."),
    "GetBuildsSummary": ("read", "read", [], "Get summary counts for builds."),
    "GetBuildActionState": ("read", "read", ["build"], "Get the action state for a build."),
    "GetBuildMonthlyStats": ("read", "read", ["page"], "Get monthly build statistics."),
    "GetBuildWebhookEnabled": ("read", "read", ["build"], "Check if webhook is enabled for a build."),
    "ListBuildVersions": ("read", "read", ["build", "major", "minor", "patch", "limit"], "List available versions for a build."),
    # ── read — Repos ───────────────────────────────────────────
    "ListRepos": ("read", "read", ["query"], "List repos."),
    "ListFullRepos": ("read", "read", ["query"], "List repos with full config."),
    "GetRepo": ("read", "read", ["repo"], "Get a specific repo by id or name."),
    "GetReposSummary": ("read", "read", [], "Get summary counts for repos."),
    "GetRepoActionState": ("read", "read", ["repo"], "Get the action state for a repo."),
    "GetRepoWebhooksEnabled": ("read", "read", ["repo"], "Check if webhooks are enabled for a repo."),
    # ── read — Procedures ──────────────────────────────────────
    "ListProcedures": ("read", "read", ["query"], "List procedures."),
    "ListFullProcedures": ("read", "read", ["query"], "List procedures with full config."),
    "GetProcedure": ("read", "read", ["procedure"], "Get a specific procedure by id or name."),
    "GetProceduresSummary": ("read", "read", [], "Get summary counts for procedures."),
    "GetProcedureActionState": ("read", "read", ["procedure"], "Get the action state for a procedure."),
    # ── read — Actions ─────────────────────────────────────────
    "ListActions": ("read", "read", ["query"], "List actions."),
    "ListFullActions": ("read", "read", ["query"], "List actions with full config."),
    "GetAction": ("read", "read", ["action"], "Get a specific action by id or name."),
    "GetActionsSummary": ("read", "read", [], "Get summary counts for actions."),
    "GetActionActionState": ("read", "read", ["action"], "Get the action state for an action."),
    # ── read — Resource Syncs ──────────────────────────────────
    "ListResourceSyncs": ("read", "read", ["query"], "List resource syncs."),
    "ListFullResourceSyncs": ("read", "read", ["query"], "List resource syncs with full config."),
    "GetResourceSync": ("read", "read", ["sync"], "Get a specific resource sync by id or name."),
    "GetResourceSyncsSummary": ("read", "read", [], "Get summary counts for resource syncs."),
    "GetResourceSyncActionState": ("read", "read", ["sync"], "Get the action state for a resource sync."),
    "GetSyncWebhooksEnabled": ("read", "read", ["sync"], "Check if webhooks are enabled for a resource sync."),
    # ── read — Builders ────────────────────────────────────────
    "ListBuilders": ("read", "read", ["query"], "List builders."),
    "ListFullBuilders": ("read", "read", ["query"], "List builders with full config."),
    "GetBuilder": ("read", "read", ["builder"], "Get a specific builder by id or name."),
    "GetBuildersSummary": ("read", "read", [], "Get summary counts for builders."),
    # ── read — Alerters ────────────────────────────────────────
    "ListAlerters": ("read", "read", ["query"], "List alerters."),
    "ListFullAlerters": ("read", "read", ["query"], "List alerters with full config."),
    "GetAlerter": ("read", "read", ["alerter"], "Get a specific alerter by id or name."),
    "GetAlertersSummary": ("read", "read", [], "Get summary counts for alerters."),
    "GetAlert": ("read", "read", ["id"], "Get a specific alert by id."),
    # ── read — Docker ──────────────────────────────────────────
    "ListDockerContainers": ("read", "read", ["server"], "List Docker containers on a server."),
    "ListAllDockerContainers": ("read", "read", ["servers"], "List Docker containers across multiple servers. servers: list."),
    "GetDockerContainersSummary": ("read", "read", [], "Get summary counts for Docker containers."),
    "GetContainerLog": ("read", "read", ["server", "container", "tail", "timestamps"], "Get logs from a Docker container."),
    "SearchContainerLog": ("read", "read", ["server", "container", "terms", "combinator", "invert", "timestamps"], "Search Docker container logs."),
    "SearchDeploymentLog": ("read", "read", ["deployment", "terms", "combinator", "invert", "timestamps"], "Search deployment logs."),
    "InspectDockerContainer": ("read", "read", ["server", "container"], "Inspect a Docker container."),
    "ListDockerImages": ("read", "read", ["server"], "List Docker images on a server."),
    "ListDockerImageHistory": ("read", "read", ["server", "image"], "List the history of a Docker image."),
    "InspectDockerImage": ("read", "read", ["server", "image"], "Inspect a Docker image."),
    "ListDockerNetworks": ("read", "read", ["server"], "List Docker networks on a server."),
    "InspectDockerNetwork": ("read", "read", ["server", "network"], "Inspect a Docker network."),
    "ListDockerVolumes": ("read", "read", ["server"], "List Docker volumes on a server."),
    "InspectDockerVolume": ("read", "read", ["server", "volume"], "Inspect a Docker volume."),
    # ── read — Compose ─────────────────────────────────────────
    "ListComposeProjects": ("read", "read", ["server"], "List Docker Compose projects on a server."),
    # ── read — Tags, Variables, Secrets ────────────────────────
    "ListTags": ("read", "read", ["query"], "List tags."),
    "GetTag": ("read", "read", ["tag"], "Get a specific tag by id or name."),
    "ListVariables": ("read", "read", [], "List all variables."),
    "GetVariable": ("read", "read", ["name"], "Get a specific variable by name."),
    # ── read — Provider Accounts ───────────────────────────────
    "ListGitProviderAccounts": ("read", "read", ["domain", "username"], "List git provider accounts."),
    "GetGitProviderAccount": ("read", "read", ["id"], "Get a git provider account by id."),
    "ListGitProvidersFromConfig": ("read", "read", ["target"], "List git providers from Core config."),
    "ListDockerRegistryAccounts": ("read", "read", ["domain", "username"], "List Docker registry accounts."),
    "GetDockerRegistryAccount": ("read", "read", ["id"], "Get a Docker registry account by id."),
    "ListDockerRegistriesFromConfig": ("read", "read", ["target"], "List Docker registries from Core config."),
    # ── read — Updates & Alerts ────────────────────────────────
    "ListUpdates": ("read", "read", ["query", "page"], "List updates (paginated)."),
    "GetUpdate": ("read", "read", ["id"], "Get a specific update by id."),
    "ListAlerts": ("read", "read", ["query", "page"], "List alerts (paginated)."),
    # ── read — Misc ────────────────────────────────────────────
    "ListSecrets": ("read", "read", ["target"], "List available secret variable names."),
    "ListSchedules": ("read", "read", ["tags", "tag_behavior"], "List scheduled operations."),
    "GetResourceMatchingContainer": ("read", "read", ["server", "container"], "Find the Komodo resource matching a Docker container."),
    "ListCommonDeploymentExtraArgs": ("read", "read", ["query"], "List common extra args used across deployments."),
    "ListCommonBuildExtraArgs": ("read", "read", ["query"], "List common extra args used across builds."),
    "ListCommonStackExtraArgs": ("read", "read", ["query"], "List common extra args used across stacks."),
    "ListCommonStackBuildExtraArgs": ("read", "read", ["query"], "List common stack build extra args."),
    # ── read — Export ──────────────────────────────────────────
    "ExportAllResourcesToToml": ("read", "read", ["include_resources", "tags", "include_variables", "include_user_groups"], "Export all resources to TOML format."),
    "ExportResourcesToToml": ("read", "read", ["targets", "include_variables", "user_groups"], "Export specific resources to TOML."),

    # ── write — Servers ────────────────────────────────────────
    "CreateServer": ("write", "write", ["name", "config"], "Create a new server. config: server configuration object."),
    "UpdateServer": ("write", "write", ["id", "config"], "Update server configuration."),
    "RenameServer": ("write", "write", ["id", "name"], "Rename a server."),
    "CopyServer": ("write", "write", ["id", "name"], "Copy a server to a new one."),
    "CreateNetwork": ("write", "write", ["server", "name"], "Create a Docker network on a server."),
    "CreateTerminal": ("write", "write", ["server", "name", "command", "recreate"], "Create a terminal. recreate: Never, Always, or DifferentCommand."),
    # ── write — Deployments ────────────────────────────────────
    "CreateDeployment": ("write", "write", ["name", "config"], "Create a new deployment."),
    "UpdateDeployment": ("write", "write", ["id", "config"], "Update deployment configuration."),
    "RenameDeployment": ("write", "write", ["id", "name"], "Rename a deployment."),
    "CopyDeployment": ("write", "write", ["id", "name"], "Copy a deployment to a new one."),
    "CreateDeploymentFromContainer": ("write", "write", ["name", "server"], "Create a deployment from an existing container."),
    # ── write — Stacks ─────────────────────────────────────────
    "CreateStack": ("write", "write", ["name", "config"], "Create a new stack."),
    "UpdateStack": ("write", "write", ["id", "config"], "Update stack configuration."),
    "RenameStack": ("write", "write", ["id", "name"], "Rename a stack."),
    "CopyStack": ("write", "write", ["id", "name"], "Copy a stack to a new one."),
    "RefreshStackCache": ("write", "write", ["stack"], "Refresh the cached state of a stack."),
    "WriteStackFileContents": ("write", "write", ["stack", "file_path", "contents"], "Write file contents for a stack."),
    "CreateStackWebhook": ("write", "write", ["stack", "action"], "Create a webhook for a stack. action: Refresh or Deploy."),
    # ── write — Builds ─────────────────────────────────────────
    "CreateBuild": ("write", "write", ["name", "config"], "Create a new build."),
    "UpdateBuild": ("write", "write", ["id", "config"], "Update build configuration."),
    "RenameBuild": ("write", "write", ["id", "name"], "Rename a build."),
    "CopyBuild": ("write", "write", ["id", "name"], "Copy a build to a new one."),
    "RefreshBuildCache": ("write", "write", ["build"], "Refresh the cached state of a build."),
    "WriteBuildFileContents": ("write", "write", ["build", "contents"], "Write Dockerfile contents for a build."),
    "CreateBuildWebhook": ("write", "write", ["build"], "Create a webhook for a build."),
    # ── write — Repos ──────────────────────────────────────────
    "CreateRepo": ("write", "write", ["name", "config"], "Create a new repo."),
    "UpdateRepo": ("write", "write", ["id", "config"], "Update repo configuration."),
    "RenameRepo": ("write", "write", ["id", "name"], "Rename a repo."),
    "CopyRepo": ("write", "write", ["id", "name"], "Copy a repo to a new one."),
    "RefreshRepoCache": ("write", "write", ["repo"], "Refresh the cached state of a repo."),
    "CreateRepoWebhook": ("write", "write", ["repo", "action"], "Create a webhook for a repo. action: Clone, Pull, or Build."),
    # ── write — Procedures ─────────────────────────────────────
    "CreateProcedure": ("write", "write", ["name", "config"], "Create a new procedure."),
    "UpdateProcedure": ("write", "write", ["id", "config"], "Update procedure configuration."),
    "RenameProcedure": ("write", "write", ["id", "name"], "Rename a procedure."),
    "CopyProcedure": ("write", "write", ["id", "name"], "Copy a procedure to a new one."),
    # ── write — Actions ────────────────────────────────────────
    "CreateAction": ("write", "write", ["name", "config"], "Create a new action."),
    "UpdateAction": ("write", "write", ["id", "config"], "Update action configuration."),
    "RenameAction": ("write", "write", ["id", "name"], "Rename an action."),
    "CopyAction": ("write", "write", ["id", "name"], "Copy an action to a new one."),
    "CreateActionWebhook": ("write", "write", ["action"], "Create a webhook for an action."),
    # ── write — Resource Syncs ─────────────────────────────────
    "CreateResourceSync": ("write", "write", ["name", "config"], "Create a new resource sync."),
    "UpdateResourceSync": ("write", "write", ["id", "config"], "Update resource sync configuration."),
    "RenameResourceSync": ("write", "write", ["id", "name"], "Rename a resource sync."),
    "CopyResourceSync": ("write", "write", ["id", "name"], "Copy a resource sync to a new one."),
    "RefreshResourceSyncPending": ("write", "write", ["sync"], "Refresh the pending state of a resource sync."),
    "CommitSync": ("write", "write", ["sync"], "Commit pending changes for a resource sync."),
    "WriteSyncFileContents": ("write", "write", ["sync", "resource_path", "file_path", "contents"], "Write file contents for a resource sync."),
    "CreateSyncWebhook": ("write", "write", ["sync", "action"], "Create a webhook for a resource sync. action: Refresh or Sync."),
    # ── write — Builders ───────────────────────────────────────
    "CreateBuilder": ("write", "write", ["name", "config"], "Create a new builder."),
    "UpdateBuilder": ("write", "write", ["id", "config"], "Update builder configuration."),
    "RenameBuilder": ("write", "write", ["id", "name"], "Rename a builder."),
    "CopyBuilder": ("write", "write", ["id", "name"], "Copy a builder to a new one."),
    # ── write — Alerters ───────────────────────────────────────
    "CreateAlerter": ("write", "write", ["name", "config"], "Create a new alerter."),
    "UpdateAlerter": ("write", "write", ["id", "config"], "Update alerter configuration."),
    "RenameAlerter": ("write", "write", ["id", "name"], "Rename an alerter."),
    "CopyAlerter": ("write", "write", ["id", "name"], "Copy an alerter to a new one."),
    # ── write — Tags ───────────────────────────────────────────
    "CreateTag": ("write", "write", ["name", "color"], "Create a new tag. color: optional."),
    "RenameTag": ("write", "write", ["id", "name"], "Rename a tag."),
    "UpdateTagColor": ("write", "write", ["tag", "color"], "Update the color of a tag."),
    # ── write — Variables ──────────────────────────────────────
    "CreateVariable": ("write", "write", ["name", "value", "description", "is_secret"], "Create a new variable."),
    "UpdateVariableValue": ("write", "write", ["name", "value"], "Update the value of a variable."),
    "UpdateVariableDescription": ("write", "write", ["name", "description"], "Update the description of a variable."),
    "UpdateVariableIsSecret": ("write", "write", ["name", "is_secret"], "Update whether a variable is a secret."),
    # ── write — Provider Accounts ──────────────────────────────
    "CreateGitProviderAccount": ("write", "write", ["account"], "Create a git provider account. account: config object."),
    "UpdateGitProviderAccount": ("write", "write", ["id", "account"], "Update a git provider account."),
    "CreateDockerRegistryAccount": ("write", "write", ["account"], "Create a Docker registry account."),
    "UpdateDockerRegistryAccount": ("write", "write", ["id", "account"], "Update a Docker registry account."),
    # ── write — Resource Meta ──────────────────────────────────
    "UpdateResourceMeta": ("write", "write", ["target", "description", "template", "tags"], "Update resource metadata. target: {type, id}."),

    # ── execute — Deployments ──────────────────────────────────
    "Deploy": ("execute", "execute", ["deployment", "stop_signal", "stop_time"], "Deploy a deployment (pull image + recreate container)."),
    "PullDeployment": ("execute", "execute", ["deployment"], "Pull the latest image for a deployment."),
    "StartDeployment": ("execute", "execute", ["deployment"], "Start a stopped deployment."),
    "StopDeployment": ("execute", "execute", ["deployment", "signal", "time"], "Stop a running deployment."),
    "RestartDeployment": ("execute", "execute", ["deployment"], "Restart a deployment."),
    "PauseDeployment": ("execute", "execute", ["deployment"], "Pause a running deployment."),
    "UnpauseDeployment": ("execute", "execute", ["deployment"], "Unpause a paused deployment."),
    # ── execute — Stacks ───────────────────────────────────────
    "DeployStack": ("execute", "execute", ["stack", "services", "stop_time"], "Deploy a stack. services: optional list."),
    "DeployStackIfChanged": ("execute", "execute", ["stack", "stop_time"], "Deploy a stack only if its compose file changed."),
    "PullStack": ("execute", "execute", ["stack", "services"], "Pull latest images for a stack."),
    "StartStack": ("execute", "execute", ["stack", "services"], "Start a stopped stack."),
    "StopStack": ("execute", "execute", ["stack", "services", "stop_time"], "Stop a running stack."),
    "RestartStack": ("execute", "execute", ["stack", "services"], "Restart a stack."),
    "PauseStack": ("execute", "execute", ["stack", "services"], "Pause a running stack."),
    "UnpauseStack": ("execute", "execute", ["stack", "services"], "Unpause a paused stack."),
    "RunStackService": ("execute", "execute", ["stack", "service", "command", "detach"], "Run a one-off command in a stack service."),
    # ── execute — Containers ───────────────────────────────────
    "StartContainer": ("execute", "execute", ["server", "container"], "Start a Docker container on a server."),
    "StopContainer": ("execute", "execute", ["server", "container", "signal", "time"], "Stop a Docker container."),
    "RestartContainer": ("execute", "execute", ["server", "container"], "Restart a Docker container."),
    "PauseContainer": ("execute", "execute", ["server", "container"], "Pause a Docker container."),
    "UnpauseContainer": ("execute", "execute", ["server", "container"], "Unpause a Docker container."),
    "StartAllContainers": ("execute", "execute", ["server"], "Start all Docker containers on a server."),
    "StopAllContainers": ("execute", "execute", ["server"], "Stop all Docker containers on a server."),
    "RestartAllContainers": ("execute", "execute", ["server"], "Restart all Docker containers on a server."),
    "PauseAllContainers": ("execute", "execute", ["server"], "Pause all Docker containers on a server."),
    "UnpauseAllContainers": ("execute", "execute", ["server"], "Unpause all Docker containers on a server."),
    # ── execute — Builds ───────────────────────────────────────
    "RunBuild": ("execute", "execute", ["build"], "Run a build."),
    "CancelBuild": ("execute", "execute", ["build"], "Cancel a running build."),
    # ── execute — Repos ────────────────────────────────────────
    "CloneRepo": ("execute", "execute", ["repo"], "Clone a repo on its configured server."),
    "PullRepo": ("execute", "execute", ["repo"], "Pull latest changes for a repo."),
    "BuildRepo": ("execute", "execute", ["repo"], "Run the build command for a repo."),
    "CancelRepoBuild": ("execute", "execute", ["repo"], "Cancel a running repo build."),
    # ── execute — Procedures & Actions ─────────────────────────
    "RunProcedure": ("execute", "execute", ["procedure"], "Run a procedure."),
    "RunAction": ("execute", "execute", ["action", "args"], "Run an action. args: optional JSON object."),
    # ── execute — Resource Syncs ───────────────────────────────
    "RunSync": ("execute", "execute", ["sync", "resource_type", "resources"], "Run a resource sync."),
    # ── execute — Batch (non-destructive) ──────────────────────
    "BatchDeploy": ("execute", "execute", ["pattern"], "Deploy multiple deployments matching a name pattern."),
    "BatchDeployStack": ("execute", "execute", ["pattern"], "Deploy multiple stacks matching a name pattern."),
    "BatchDeployStackIfChanged": ("execute", "execute", ["pattern"], "Deploy stacks (only if changed) matching a pattern."),
    "BatchRunBuild": ("execute", "execute", ["pattern"], "Run builds matching a name pattern."),
    "BatchCloneRepo": ("execute", "execute", ["pattern"], "Clone repos matching a name pattern."),
    "BatchPullRepo": ("execute", "execute", ["pattern"], "Pull repos matching a name pattern."),
    "BatchBuildRepo": ("execute", "execute", ["pattern"], "Build repos matching a name pattern."),
    "BatchPullStack": ("execute", "execute", ["pattern"], "Pull images for stacks matching a name pattern."),
    "BatchRunAction": ("execute", "execute", ["pattern"], "Run actions matching a name pattern."),
    "BatchRunProcedure": ("execute", "execute", ["pattern"], "Run procedures matching a name pattern."),
    # ── execute — Misc ─────────────────────────────────────────
    "SendAlert": ("execute", "execute", ["level", "message", "details", "alerters"], "Send a custom alert. level: Ok, Warning, or Critical."),
    "TestAlerter": ("execute", "execute", ["alerter"], "Test an alerter by sending a test notification."),
    "Sleep": ("execute", "execute", ["duration_ms"], "Sleep for a specified duration in milliseconds."),

    # ── delete — Servers ───────────────────────────────────────
    "DeleteServer": ("delete", "write", ["id"], "Delete a server by id."),
    "DeleteTerminal": ("delete", "write", ["server", "terminal"], "Delete a terminal on a server."),
    "DeleteAllTerminals": ("delete", "write", ["server"], "Delete all terminals on a server."),
    # ── delete — Deployments ───────────────────────────────────
    "DeleteDeployment": ("delete", "write", ["id"], "Delete a deployment by id."),
    "DestroyDeployment": ("delete", "execute", ["deployment", "signal", "time"], "Destroy a deployment (stop and remove container)."),
    # ── delete — Stacks ────────────────────────────────────────
    "DeleteStack": ("delete", "write", ["id"], "Delete a stack by id."),
    "DeleteStackWebhook": ("delete", "write", ["stack", "action"], "Delete a webhook for a stack."),
    "DestroyStack": ("delete", "execute", ["stack", "services", "remove_orphans", "stop_time"], "Destroy a stack."),
    # ── delete — Builds ────────────────────────────────────────
    "DeleteBuild": ("delete", "write", ["id"], "Delete a build by id."),
    "DeleteBuildWebhook": ("delete", "write", ["build"], "Delete a webhook for a build."),
    # ── delete — Repos ─────────────────────────────────────────
    "DeleteRepo": ("delete", "write", ["id"], "Delete a repo by id."),
    "DeleteRepoWebhook": ("delete", "write", ["repo", "action"], "Delete a webhook for a repo."),
    # ── delete — Procedures ────────────────────────────────────
    "DeleteProcedure": ("delete", "write", ["id"], "Delete a procedure by id."),
    # ── delete — Actions ───────────────────────────────────────
    "DeleteAction": ("delete", "write", ["id"], "Delete an action by id."),
    "DeleteActionWebhook": ("delete", "write", ["action"], "Delete a webhook for an action."),
    # ── delete — Resource Syncs ────────────────────────────────
    "DeleteResourceSync": ("delete", "write", ["id"], "Delete a resource sync by id."),
    "DeleteSyncWebhook": ("delete", "write", ["sync", "action"], "Delete a webhook for a resource sync."),
    # ── delete — Builders ──────────────────────────────────────
    "DeleteBuilder": ("delete", "write", ["id"], "Delete a builder by id."),
    # ── delete — Alerters ──────────────────────────────────────
    "DeleteAlerter": ("delete", "write", ["id"], "Delete an alerter by id."),
    # ── delete — Tags & Variables ──────────────────────────────
    "DeleteTag": ("delete", "write", ["id"], "Delete a tag by id."),
    "DeleteVariable": ("delete", "write", ["name"], "Delete a variable by name."),
    # ── delete — Provider Accounts ─────────────────────────────
    "DeleteGitProviderAccount": ("delete", "write", ["id"], "Delete a git provider account by id."),
    "DeleteDockerRegistryAccount": ("delete", "write", ["id"], "Delete a Docker registry account by id."),
    # ── delete — Containers ────────────────────────────────────
    "DestroyContainer": ("delete", "execute", ["server", "container", "signal", "time"], "Destroy a Docker container."),
    # ── delete — Docker Cleanup ────────────────────────────────
    "PruneContainers": ("delete", "execute", ["server"], "Prune stopped containers on a server."),
    "PruneImages": ("delete", "execute", ["server"], "Prune unused images on a server."),
    "PruneNetworks": ("delete", "execute", ["server"], "Prune unused networks on a server."),
    "PruneVolumes": ("delete", "execute", ["server"], "Prune unused volumes on a server."),
    "PruneBuildx": ("delete", "execute", ["server"], "Prune buildx cache on a server."),
    "PruneDockerBuilders": ("delete", "execute", ["server"], "Prune Docker builders on a server."),
    "PruneSystem": ("delete", "execute", ["server"], "Prune all unused Docker resources on a server."),
    "DeleteImage": ("delete", "execute", ["server", "name"], "Delete a Docker image on a server."),
    "DeleteNetwork": ("delete", "execute", ["server", "name"], "Delete a Docker network on a server."),
    "DeleteVolume": ("delete", "execute", ["server", "name"], "Delete a Docker volume on a server."),
    # ── delete — Batch (destructive) ───────────────────────────
    "BatchDestroyDeployment": ("delete", "execute", ["pattern"], "Destroy deployments matching a name pattern."),
    "BatchDestroyStack": ("delete", "execute", ["pattern"], "Destroy stacks matching a name pattern."),

    # ── admin_read — Users & Permissions ───────────────────────
    "ListUsers": ("admin_read", "read", [], "List all users."),
    "FindUser": ("admin_read", "read", ["user"], "Find a user by id or username."),
    "GetUsername": ("admin_read", "read", ["user_id"], "Get username by user id."),
    "ListUserGroups": ("admin_read", "read", [], "List all user groups."),
    "GetUserGroup": ("admin_read", "read", ["user_group"], "Get a specific user group by id or name."),
    "ListPermissions": ("admin_read", "read", [], "List permissions for the calling user."),
    "ListUserTargetPermissions": ("admin_read", "read", ["user_target"], "List permissions for a user/group. user_target: {type, id}."),
    "GetPermission": ("admin_read", "read", ["target"], "Get permission on a resource target. target: {type, id}."),
    # ── admin_read — API Keys ──────────────────────────────────
    "ListApiKeys": ("admin_read", "read", [], "List API keys for the calling user."),
    "ListApiKeysForServiceUser": ("admin_read", "read", ["user"], "List API keys for a service user."),

    # ── admin_write — Users ────────────────────────────────────
    "CreateLocalUser": ("admin_write", "write", ["username", "password"], "Create a local user."),
    "CreateServiceUser": ("admin_write", "write", ["username", "description"], "Create a service user."),
    "DeleteUser": ("admin_write", "write", ["user"], "Delete a user by id or username."),
    "UpdateUserAdmin": ("admin_write", "write", ["user_id", "admin"], "Set or unset admin status for a user."),
    "UpdateUserPassword": ("admin_write", "write", ["password"], "Update the calling user's password."),
    "UpdateUserUsername": ("admin_write", "write", ["username"], "Update the calling user's username."),
    "UpdateUserBasePermissions": ("admin_write", "write", ["user_id", "enabled", "create_servers", "create_builds"], "Update base permissions for a user."),
    "UpdateServiceUserDescription": ("admin_write", "write", ["username", "description"], "Update the description of a service user."),
    "CreateApiKeyForServiceUser": ("admin_write", "write", ["user_id", "name", "expires"], "Create an API key for a service user."),
    "DeleteApiKeyForServiceUser": ("admin_write", "write", ["key"], "Delete an API key for a service user."),
    # ── admin_write — User Groups ──────────────────────────────
    "CreateUserGroup": ("admin_write", "write", ["name"], "Create a new user group."),
    "DeleteUserGroup": ("admin_write", "write", ["id"], "Delete a user group by id."),
    "RenameUserGroup": ("admin_write", "write", ["id", "name"], "Rename a user group."),
    "AddUserToUserGroup": ("admin_write", "write", ["user_group", "user"], "Add a user to a user group."),
    "RemoveUserFromUserGroup": ("admin_write", "write", ["user_group", "user"], "Remove a user from a user group."),
    "SetUsersInUserGroup": ("admin_write", "write", ["user_group", "users"], "Set exact list of users in a group. users: list."),
    "SetEveryoneUserGroup": ("admin_write", "write", ["user_group", "everyone"], "Set whether a group includes everyone."),
    # ── admin_write — Permissions ──────────────────────────────
    "UpdatePermissionOnResourceType": ("admin_write", "write", ["user_target", "resource_type", "permission"], "Update permission on a resource type."),
    "UpdatePermissionOnTarget": ("admin_write", "write", ["user_target", "resource_target", "permission"], "Update permission on a specific resource."),
    # ── admin_write — Admin-only Execute ───────────────────────
    "GlobalAutoUpdate": ("admin_write", "execute", [], "Trigger global poll for image updates. Admin only."),
    "BackupCoreDatabase": ("admin_write", "execute", [], "Backup the Komodo Core database. Admin only."),
    "ClearRepoCache": ("admin_write", "execute", [], "Clear all repos from the Core repo cache. Admin only."),
}


# ── Helpers ────────────────────────────────────────────────────────────────────

_SCOPE_NAMES = {
    "read": "komodo_read",
    "write": "komodo_write",
    "execute": "komodo_execute",
    "delete": "komodo_delete",
    "admin_read": "komodo_admin_read",
    "admin_write": "komodo_admin_write",
}


def _build_help(scope: str) -> str:
    """Build help text listing all operations for a scope."""
    lines = []
    for op, (sc, _, params, doc) in _OPERATIONS.items():
        if sc != scope:
            continue
        params_str = ", ".join(params) if params else ""
        lines.append(f"  {op}({params_str}) — {doc}")
    return f"{len(lines)} operations available:\n" + "\n".join(lines)


def _dispatch(operation: str, scope: str, params_str: str) -> str:
    """Validate scope, parse params, call API."""
    if operation not in _OPERATIONS:
        return json.dumps({
            "error": f"Unknown operation: {operation}",
            "hint": "Call with operation='help' to list available operations.",
        })

    op_scope, api_endpoint, _, _ = _OPERATIONS[operation]
    if op_scope != scope:
        return json.dumps({
            "error": f"{operation} is a {op_scope} operation. Use {_SCOPE_NAMES[op_scope]}() instead.",
        })

    parsed = json.loads(params_str) if isinstance(params_str, str) else params_str
    client = _get_client()
    result = getattr(client, api_endpoint)(operation, parsed or None)
    return _ok(result)


# ── Meta-tools ────────────────────────────────────────────────────────────────


@mcp.tool()
def komodo_read(operation: str, params: str = "{}") -> str:
    """Query Komodo resources (safe, read-only).

    Call with operation="help" to list all 109 available read operations.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_read(operation="GetServer", params='{"server": "my-server"}')
    """
    if operation == "help":
        return _build_help("read")
    return _dispatch(operation, "read", params)


@mcp.tool()
def komodo_write(operation: str, params: str = "{}") -> str:
    """Create, update, rename, or copy Komodo resources (non-destructive).

    Call with operation="help" to list all 68 available write operations.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_write(operation="CreateServer", params='{"name": "my-server", "config": {}}')
    """
    if operation == "help":
        return _build_help("write")
    return _dispatch(operation, "write", params)


@mcp.tool()
def komodo_execute(operation: str, params: str = "{}") -> str:
    """Trigger actions: deploy, start/stop, build, run procedures (non-destructive).

    Call with operation="help" to list all 48 available execute operations.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_execute(operation="Deploy", params='{"deployment": "my-app"}')
    """
    if operation == "help":
        return _build_help("execute")
    return _dispatch(operation, "execute", params)


@mcp.tool()
def komodo_delete(operation: str, params: str = "{}") -> str:
    """Delete, destroy, or prune resources (destructive, irreversible).

    Call with operation="help" to list all 36 available delete operations.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_delete(operation="DeleteServer", params='{"id": "server-id"}')
    """
    if operation == "help":
        return _build_help("delete")
    return _dispatch(operation, "delete", params)


@mcp.tool()
def komodo_admin_read(operation: str, params: str = "{}") -> str:
    """Query users, permissions, groups, and API keys (admin).

    Call with operation="help" to list all 10 available admin read operations.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_admin_read(operation="ListUsers")
    """
    if operation == "help":
        return _build_help("admin_read")
    return _dispatch(operation, "admin_read", params)


@mcp.tool()
def komodo_admin_write(operation: str, params: str = "{}") -> str:
    """Manage users, groups, permissions, and admin-only actions (restricted).

    Call with operation="help" to list all 22 available admin write operations.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_admin_write(operation="CreateServiceUser", params='{"username": "bot", "description": "CI bot"}')
    """
    if operation == "help":
        return _build_help("admin_write")
    return _dispatch(operation, "admin_write", params)
