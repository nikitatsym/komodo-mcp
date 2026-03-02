"""Compact mode: 3 meta-tools instead of 293 individual tools.

Usage: komodo-mcp --compact
"""

from __future__ import annotations

import json
from typing import Optional

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
# Maps operation name -> (endpoint, param_names, docstring)
# This is the single source of truth for all 293 operations.

_OPERATIONS: dict[str, tuple[str, list[str], str]] = {
    # ── Read — General ────────────────────────────────────────
    "GetVersion": ("read", [], "Get Komodo Core version."),
    "GetCoreInfo": ("read", [], "Get Komodo Core configuration info."),
    # ── Read — Servers ────────────────────────────────────────
    "ListServers": ("read", ["query"], "List servers. query: optional mongo query object."),
    "ListFullServers": ("read", ["query"], "List servers with full config."),
    "GetServer": ("read", ["server"], "Get a specific server by id or name."),
    "GetServersSummary": ("read", [], "Get summary counts for servers."),
    "GetServerState": ("read", ["server"], "Get the current state of a server."),
    "GetServerActionState": ("read", ["server"], "Get the action state for a server."),
    "GetSystemStats": ("read", ["server"], "Get current system stats (CPU, memory, disk) for a server."),
    "GetSystemInformation": ("read", ["server"], "Get system information (OS, kernel) for a server."),
    "GetHistoricalServerStats": ("read", ["server", "granularity", "page"], "Get historical system stats. granularity: 15-sec, 1-min, etc."),
    "GetPeripheryVersion": ("read", ["server"], "Get the Periphery agent version on a server."),
    "ListSystemProcesses": ("read", ["server"], "List running system processes on a server."),
    "ListTerminals": ("read", ["server", "fresh"], "List active terminals on a server."),
    # ── Read — Deployments ────────────────────────────────────
    "ListDeployments": ("read", ["query"], "List deployments."),
    "ListFullDeployments": ("read", ["query"], "List deployments with full config."),
    "GetDeployment": ("read", ["deployment"], "Get a specific deployment by id or name."),
    "GetDeploymentsSummary": ("read", [], "Get summary counts for deployments."),
    "GetDeploymentActionState": ("read", ["deployment"], "Get the action state for a deployment."),
    "GetDeploymentContainer": ("read", ["deployment"], "Get the container info for a deployment."),
    "GetDeploymentLog": ("read", ["deployment", "tail", "timestamps"], "Get the container log for a deployment."),
    "GetDeploymentStats": ("read", ["deployment"], "Get container resource stats for a deployment."),
    "InspectDeploymentContainer": ("read", ["deployment"], "Inspect the Docker container of a deployment."),
    # ── Read — Stacks ─────────────────────────────────────────
    "ListStacks": ("read", ["query"], "List stacks."),
    "ListFullStacks": ("read", ["query"], "List stacks with full config."),
    "GetStack": ("read", ["stack"], "Get a specific stack by id or name."),
    "GetStacksSummary": ("read", [], "Get summary counts for stacks."),
    "GetStackActionState": ("read", ["stack"], "Get the action state for a stack."),
    "GetStackLog": ("read", ["stack", "services", "tail", "timestamps"], "Get logs for a stack. services: list of service names."),
    "GetStackWebhooksEnabled": ("read", ["stack"], "Check if webhooks are enabled for a stack."),
    "ListStackServices": ("read", ["stack"], "List services in a stack."),
    "InspectStackContainer": ("read", ["stack", "service"], "Inspect a specific service container in a stack."),
    "SearchStackLog": ("read", ["stack", "terms", "combinator", "invert", "timestamps", "services"], "Search stack logs. combinator: And or Or."),
    # ── Read — Builds ─────────────────────────────────────────
    "ListBuilds": ("read", ["query"], "List builds."),
    "ListFullBuilds": ("read", ["query"], "List builds with full config."),
    "GetBuild": ("read", ["build"], "Get a specific build by id or name."),
    "GetBuildsSummary": ("read", [], "Get summary counts for builds."),
    "GetBuildActionState": ("read", ["build"], "Get the action state for a build."),
    "GetBuildMonthlyStats": ("read", ["page"], "Get monthly build statistics."),
    "GetBuildWebhookEnabled": ("read", ["build"], "Check if webhook is enabled for a build."),
    "ListBuildVersions": ("read", ["build", "major", "minor", "patch", "limit"], "List available versions for a build."),
    # ── Read — Repos ──────────────────────────────────────────
    "ListRepos": ("read", ["query"], "List repos."),
    "ListFullRepos": ("read", ["query"], "List repos with full config."),
    "GetRepo": ("read", ["repo"], "Get a specific repo by id or name."),
    "GetReposSummary": ("read", [], "Get summary counts for repos."),
    "GetRepoActionState": ("read", ["repo"], "Get the action state for a repo."),
    "GetRepoWebhooksEnabled": ("read", ["repo"], "Check if webhooks are enabled for a repo."),
    # ── Read — Procedures ─────────────────────────────────────
    "ListProcedures": ("read", ["query"], "List procedures."),
    "ListFullProcedures": ("read", ["query"], "List procedures with full config."),
    "GetProcedure": ("read", ["procedure"], "Get a specific procedure by id or name."),
    "GetProceduresSummary": ("read", [], "Get summary counts for procedures."),
    "GetProcedureActionState": ("read", ["procedure"], "Get the action state for a procedure."),
    # ── Read — Actions ────────────────────────────────────────
    "ListActions": ("read", ["query"], "List actions."),
    "ListFullActions": ("read", ["query"], "List actions with full config."),
    "GetAction": ("read", ["action"], "Get a specific action by id or name."),
    "GetActionsSummary": ("read", [], "Get summary counts for actions."),
    "GetActionActionState": ("read", ["action"], "Get the action state for an action."),
    # ── Read — Resource Syncs ─────────────────────────────────
    "ListResourceSyncs": ("read", ["query"], "List resource syncs."),
    "ListFullResourceSyncs": ("read", ["query"], "List resource syncs with full config."),
    "GetResourceSync": ("read", ["sync"], "Get a specific resource sync by id or name."),
    "GetResourceSyncsSummary": ("read", [], "Get summary counts for resource syncs."),
    "GetResourceSyncActionState": ("read", ["sync"], "Get the action state for a resource sync."),
    "GetSyncWebhooksEnabled": ("read", ["sync"], "Check if webhooks are enabled for a resource sync."),
    # ── Read — Builders ───────────────────────────────────────
    "ListBuilders": ("read", ["query"], "List builders."),
    "ListFullBuilders": ("read", ["query"], "List builders with full config."),
    "GetBuilder": ("read", ["builder"], "Get a specific builder by id or name."),
    "GetBuildersSummary": ("read", [], "Get summary counts for builders."),
    # ── Read — Alerters ───────────────────────────────────────
    "ListAlerters": ("read", ["query"], "List alerters."),
    "ListFullAlerters": ("read", ["query"], "List alerters with full config."),
    "GetAlerter": ("read", ["alerter"], "Get a specific alerter by id or name."),
    "GetAlertersSummary": ("read", [], "Get summary counts for alerters."),
    "GetAlert": ("read", ["id"], "Get a specific alert by id."),
    # ── Read — Docker ─────────────────────────────────────────
    "ListDockerContainers": ("read", ["server"], "List Docker containers on a server."),
    "ListAllDockerContainers": ("read", ["servers"], "List Docker containers across multiple servers. servers: list."),
    "GetDockerContainersSummary": ("read", [], "Get summary counts for Docker containers."),
    "GetContainerLog": ("read", ["server", "container", "tail", "timestamps"], "Get logs from a Docker container."),
    "SearchContainerLog": ("read", ["server", "container", "terms", "combinator", "invert", "timestamps"], "Search Docker container logs."),
    "SearchDeploymentLog": ("read", ["deployment", "terms", "combinator", "invert", "timestamps"], "Search deployment logs."),
    "InspectDockerContainer": ("read", ["server", "container"], "Inspect a Docker container."),
    "ListDockerImages": ("read", ["server"], "List Docker images on a server."),
    "ListDockerImageHistory": ("read", ["server", "image"], "List the history of a Docker image."),
    "InspectDockerImage": ("read", ["server", "image"], "Inspect a Docker image."),
    "ListDockerNetworks": ("read", ["server"], "List Docker networks on a server."),
    "InspectDockerNetwork": ("read", ["server", "network"], "Inspect a Docker network."),
    "ListDockerVolumes": ("read", ["server"], "List Docker volumes on a server."),
    "InspectDockerVolume": ("read", ["server", "volume"], "Inspect a Docker volume."),
    # ── Read — Compose ────────────────────────────────────────
    "ListComposeProjects": ("read", ["server"], "List Docker Compose projects on a server."),
    # ── Read — Tags, Variables, Secrets ───────────────────────
    "ListTags": ("read", ["query"], "List tags."),
    "GetTag": ("read", ["tag"], "Get a specific tag by id or name."),
    "ListVariables": ("read", [], "List all variables."),
    "GetVariable": ("read", ["name"], "Get a specific variable by name."),
    # ── Read — Users & Permissions ────────────────────────────
    "ListUsers": ("read", [], "List all users."),
    "FindUser": ("read", ["user"], "Find a user by id or username."),
    "GetUsername": ("read", ["user_id"], "Get username by user id."),
    "ListUserGroups": ("read", [], "List all user groups."),
    "GetUserGroup": ("read", ["user_group"], "Get a specific user group by id or name."),
    "ListPermissions": ("read", [], "List permissions for the calling user."),
    "ListUserTargetPermissions": ("read", ["user_target"], "List permissions for a user/group. user_target: {type, id}."),
    "GetPermission": ("read", ["target"], "Get permission on a resource target. target: {type, id}."),
    # ── Read — API Keys ───────────────────────────────────────
    "ListApiKeys": ("read", [], "List API keys for the calling user."),
    "ListApiKeysForServiceUser": ("read", ["user"], "List API keys for a service user."),
    # ── Read — Provider Accounts ──────────────────────────────
    "ListGitProviderAccounts": ("read", ["domain", "username"], "List git provider accounts."),
    "GetGitProviderAccount": ("read", ["id"], "Get a git provider account by id."),
    "ListGitProvidersFromConfig": ("read", ["target"], "List git providers from Core config."),
    "ListDockerRegistryAccounts": ("read", ["domain", "username"], "List Docker registry accounts."),
    "GetDockerRegistryAccount": ("read", ["id"], "Get a Docker registry account by id."),
    "ListDockerRegistriesFromConfig": ("read", ["target"], "List Docker registries from Core config."),
    # ── Read — Updates & Alerts ───────────────────────────────
    "ListUpdates": ("read", ["query", "page"], "List updates (paginated)."),
    "GetUpdate": ("read", ["id"], "Get a specific update by id."),
    "ListAlerts": ("read", ["query", "page"], "List alerts (paginated)."),
    # ── Read — Misc ───────────────────────────────────────────
    "ListSecrets": ("read", ["target"], "List available secret variable names."),
    "ListSchedules": ("read", ["tags", "tag_behavior"], "List scheduled operations."),
    "GetResourceMatchingContainer": ("read", ["server", "container"], "Find the Komodo resource matching a Docker container."),
    "ListCommonDeploymentExtraArgs": ("read", ["query"], "List common extra args used across deployments."),
    "ListCommonBuildExtraArgs": ("read", ["query"], "List common extra args used across builds."),
    "ListCommonStackExtraArgs": ("read", ["query"], "List common extra args used across stacks."),
    "ListCommonStackBuildExtraArgs": ("read", ["query"], "List common stack build extra args."),
    # ── Read — Export ─────────────────────────────────────────
    "ExportAllResourcesToToml": ("read", ["include_resources", "tags", "include_variables", "include_user_groups"], "Export all resources to TOML format."),
    "ExportResourcesToToml": ("read", ["targets", "include_variables", "user_groups"], "Export specific resources to TOML."),

    # ── Write — Servers ───────────────────────────────────────
    "CreateServer": ("write", ["name", "config"], "Create a new server. config: server configuration object."),
    "UpdateServer": ("write", ["id", "config"], "Update server configuration."),
    "DeleteServer": ("write", ["id"], "Delete a server by id."),
    "RenameServer": ("write", ["id", "name"], "Rename a server."),
    "CopyServer": ("write", ["id", "name"], "Copy a server to a new one."),
    "CreateNetwork": ("write", ["server", "name"], "Create a Docker network on a server."),
    "CreateTerminal": ("write", ["server", "name", "command", "recreate"], "Create a terminal. recreate: Never, Always, or DifferentCommand."),
    "DeleteTerminal": ("write", ["server", "terminal"], "Delete a terminal on a server."),
    "DeleteAllTerminals": ("write", ["server"], "Delete all terminals on a server."),
    # ── Write — Deployments ───────────────────────────────────
    "CreateDeployment": ("write", ["name", "config"], "Create a new deployment."),
    "UpdateDeployment": ("write", ["id", "config"], "Update deployment configuration."),
    "DeleteDeployment": ("write", ["id"], "Delete a deployment by id."),
    "RenameDeployment": ("write", ["id", "name"], "Rename a deployment."),
    "CopyDeployment": ("write", ["id", "name"], "Copy a deployment to a new one."),
    "CreateDeploymentFromContainer": ("write", ["name", "server"], "Create a deployment from an existing container."),
    # ── Write — Stacks ────────────────────────────────────────
    "CreateStack": ("write", ["name", "config"], "Create a new stack."),
    "UpdateStack": ("write", ["id", "config"], "Update stack configuration."),
    "DeleteStack": ("write", ["id"], "Delete a stack by id."),
    "RenameStack": ("write", ["id", "name"], "Rename a stack."),
    "CopyStack": ("write", ["id", "name"], "Copy a stack to a new one."),
    "RefreshStackCache": ("write", ["stack"], "Refresh the cached state of a stack."),
    "WriteStackFileContents": ("write", ["stack", "file_path", "contents"], "Write file contents for a stack."),
    "CreateStackWebhook": ("write", ["stack", "action"], "Create a webhook for a stack. action: Refresh or Deploy."),
    "DeleteStackWebhook": ("write", ["stack", "action"], "Delete a webhook for a stack."),
    # ── Write — Builds ────────────────────────────────────────
    "CreateBuild": ("write", ["name", "config"], "Create a new build."),
    "UpdateBuild": ("write", ["id", "config"], "Update build configuration."),
    "DeleteBuild": ("write", ["id"], "Delete a build by id."),
    "RenameBuild": ("write", ["id", "name"], "Rename a build."),
    "CopyBuild": ("write", ["id", "name"], "Copy a build to a new one."),
    "RefreshBuildCache": ("write", ["build"], "Refresh the cached state of a build."),
    "WriteBuildFileContents": ("write", ["build", "contents"], "Write Dockerfile contents for a build."),
    "CreateBuildWebhook": ("write", ["build"], "Create a webhook for a build."),
    "DeleteBuildWebhook": ("write", ["build"], "Delete a webhook for a build."),
    # ── Write — Repos ─────────────────────────────────────────
    "CreateRepo": ("write", ["name", "config"], "Create a new repo."),
    "UpdateRepo": ("write", ["id", "config"], "Update repo configuration."),
    "DeleteRepo": ("write", ["id"], "Delete a repo by id."),
    "RenameRepo": ("write", ["id", "name"], "Rename a repo."),
    "CopyRepo": ("write", ["id", "name"], "Copy a repo to a new one."),
    "RefreshRepoCache": ("write", ["repo"], "Refresh the cached state of a repo."),
    "CreateRepoWebhook": ("write", ["repo", "action"], "Create a webhook for a repo. action: Clone, Pull, or Build."),
    "DeleteRepoWebhook": ("write", ["repo", "action"], "Delete a webhook for a repo."),
    # ── Write — Procedures ────────────────────────────────────
    "CreateProcedure": ("write", ["name", "config"], "Create a new procedure."),
    "UpdateProcedure": ("write", ["id", "config"], "Update procedure configuration."),
    "DeleteProcedure": ("write", ["id"], "Delete a procedure by id."),
    "RenameProcedure": ("write", ["id", "name"], "Rename a procedure."),
    "CopyProcedure": ("write", ["id", "name"], "Copy a procedure to a new one."),
    # ── Write — Actions ───────────────────────────────────────
    "CreateAction": ("write", ["name", "config"], "Create a new action."),
    "UpdateAction": ("write", ["id", "config"], "Update action configuration."),
    "DeleteAction": ("write", ["id"], "Delete an action by id."),
    "RenameAction": ("write", ["id", "name"], "Rename an action."),
    "CopyAction": ("write", ["id", "name"], "Copy an action to a new one."),
    "CreateActionWebhook": ("write", ["action"], "Create a webhook for an action."),
    "DeleteActionWebhook": ("write", ["action"], "Delete a webhook for an action."),
    # ── Write — Resource Syncs ────────────────────────────────
    "CreateResourceSync": ("write", ["name", "config"], "Create a new resource sync."),
    "UpdateResourceSync": ("write", ["id", "config"], "Update resource sync configuration."),
    "DeleteResourceSync": ("write", ["id"], "Delete a resource sync by id."),
    "RenameResourceSync": ("write", ["id", "name"], "Rename a resource sync."),
    "CopyResourceSync": ("write", ["id", "name"], "Copy a resource sync to a new one."),
    "RefreshResourceSyncPending": ("write", ["sync"], "Refresh the pending state of a resource sync."),
    "CommitSync": ("write", ["sync"], "Commit pending changes for a resource sync."),
    "WriteSyncFileContents": ("write", ["sync", "resource_path", "file_path", "contents"], "Write file contents for a resource sync."),
    "CreateSyncWebhook": ("write", ["sync", "action"], "Create a webhook for a resource sync. action: Refresh or Sync."),
    "DeleteSyncWebhook": ("write", ["sync", "action"], "Delete a webhook for a resource sync."),
    # ── Write — Builders ──────────────────────────────────────
    "CreateBuilder": ("write", ["name", "config"], "Create a new builder."),
    "UpdateBuilder": ("write", ["id", "config"], "Update builder configuration."),
    "DeleteBuilder": ("write", ["id"], "Delete a builder by id."),
    "RenameBuilder": ("write", ["id", "name"], "Rename a builder."),
    "CopyBuilder": ("write", ["id", "name"], "Copy a builder to a new one."),
    # ── Write — Alerters ──────────────────────────────────────
    "CreateAlerter": ("write", ["name", "config"], "Create a new alerter."),
    "UpdateAlerter": ("write", ["id", "config"], "Update alerter configuration."),
    "DeleteAlerter": ("write", ["id"], "Delete an alerter by id."),
    "RenameAlerter": ("write", ["id", "name"], "Rename an alerter."),
    "CopyAlerter": ("write", ["id", "name"], "Copy an alerter to a new one."),
    # ── Write — Tags ──────────────────────────────────────────
    "CreateTag": ("write", ["name", "color"], "Create a new tag. color: optional."),
    "DeleteTag": ("write", ["id"], "Delete a tag by id."),
    "RenameTag": ("write", ["id", "name"], "Rename a tag."),
    "UpdateTagColor": ("write", ["tag", "color"], "Update the color of a tag."),
    # ── Write — Variables ─────────────────────────────────────
    "CreateVariable": ("write", ["name", "value", "description", "is_secret"], "Create a new variable."),
    "DeleteVariable": ("write", ["name"], "Delete a variable by name."),
    "UpdateVariableValue": ("write", ["name", "value"], "Update the value of a variable."),
    "UpdateVariableDescription": ("write", ["name", "description"], "Update the description of a variable."),
    "UpdateVariableIsSecret": ("write", ["name", "is_secret"], "Update whether a variable is a secret."),
    # ── Write — Users ─────────────────────────────────────────
    "CreateLocalUser": ("write", ["username", "password"], "Create a local user."),
    "CreateServiceUser": ("write", ["username", "description"], "Create a service user."),
    "DeleteUser": ("write", ["user"], "Delete a user by id or username."),
    "UpdateUserAdmin": ("write", ["user_id", "admin"], "Set or unset admin status for a user."),
    "UpdateUserPassword": ("write", ["password"], "Update the calling user's password."),
    "UpdateUserUsername": ("write", ["username"], "Update the calling user's username."),
    "UpdateUserBasePermissions": ("write", ["user_id", "enabled", "create_servers", "create_builds"], "Update base permissions for a user."),
    "UpdateServiceUserDescription": ("write", ["username", "description"], "Update the description of a service user."),
    "CreateApiKeyForServiceUser": ("write", ["user_id", "name", "expires"], "Create an API key for a service user."),
    "DeleteApiKeyForServiceUser": ("write", ["key"], "Delete an API key for a service user."),
    # ── Write — User Groups ───────────────────────────────────
    "CreateUserGroup": ("write", ["name"], "Create a new user group."),
    "DeleteUserGroup": ("write", ["id"], "Delete a user group by id."),
    "RenameUserGroup": ("write", ["id", "name"], "Rename a user group."),
    "AddUserToUserGroup": ("write", ["user_group", "user"], "Add a user to a user group."),
    "RemoveUserFromUserGroup": ("write", ["user_group", "user"], "Remove a user from a user group."),
    "SetUsersInUserGroup": ("write", ["user_group", "users"], "Set exact list of users in a group. users: list."),
    "SetEveryoneUserGroup": ("write", ["user_group", "everyone"], "Set whether a group includes everyone."),
    # ── Write — Permissions ───────────────────────────────────
    "UpdatePermissionOnResourceType": ("write", ["user_target", "resource_type", "permission"], "Update permission on a resource type."),
    "UpdatePermissionOnTarget": ("write", ["user_target", "resource_target", "permission"], "Update permission on a specific resource."),
    # ── Write — Provider Accounts ─────────────────────────────
    "CreateGitProviderAccount": ("write", ["account"], "Create a git provider account. account: config object."),
    "UpdateGitProviderAccount": ("write", ["id", "account"], "Update a git provider account."),
    "DeleteGitProviderAccount": ("write", ["id"], "Delete a git provider account by id."),
    "CreateDockerRegistryAccount": ("write", ["account"], "Create a Docker registry account."),
    "UpdateDockerRegistryAccount": ("write", ["id", "account"], "Update a Docker registry account."),
    "DeleteDockerRegistryAccount": ("write", ["id"], "Delete a Docker registry account by id."),
    # ── Write — Resource Meta ─────────────────────────────────
    "UpdateResourceMeta": ("write", ["target", "description", "template", "tags"], "Update resource metadata. target: {type, id}."),

    # ── Execute — Deployments ─────────────────────────────────
    "Deploy": ("execute", ["deployment", "stop_signal", "stop_time"], "Deploy a deployment (pull image + recreate container)."),
    "PullDeployment": ("execute", ["deployment"], "Pull the latest image for a deployment."),
    "StartDeployment": ("execute", ["deployment"], "Start a stopped deployment."),
    "StopDeployment": ("execute", ["deployment", "signal", "time"], "Stop a running deployment."),
    "RestartDeployment": ("execute", ["deployment"], "Restart a deployment."),
    "PauseDeployment": ("execute", ["deployment"], "Pause a running deployment."),
    "UnpauseDeployment": ("execute", ["deployment"], "Unpause a paused deployment."),
    "DestroyDeployment": ("execute", ["deployment", "signal", "time"], "Destroy a deployment (stop and remove container)."),
    # ── Execute — Stacks ──────────────────────────────────────
    "DeployStack": ("execute", ["stack", "services", "stop_time"], "Deploy a stack. services: optional list."),
    "DeployStackIfChanged": ("execute", ["stack", "stop_time"], "Deploy a stack only if its compose file changed."),
    "PullStack": ("execute", ["stack", "services"], "Pull latest images for a stack."),
    "StartStack": ("execute", ["stack", "services"], "Start a stopped stack."),
    "StopStack": ("execute", ["stack", "services", "stop_time"], "Stop a running stack."),
    "RestartStack": ("execute", ["stack", "services"], "Restart a stack."),
    "PauseStack": ("execute", ["stack", "services"], "Pause a running stack."),
    "UnpauseStack": ("execute", ["stack", "services"], "Unpause a paused stack."),
    "DestroyStack": ("execute", ["stack", "services", "remove_orphans", "stop_time"], "Destroy a stack."),
    "RunStackService": ("execute", ["stack", "service", "command", "detach"], "Run a one-off command in a stack service."),
    # ── Execute — Containers ──────────────────────────────────
    "StartContainer": ("execute", ["server", "container"], "Start a Docker container on a server."),
    "StopContainer": ("execute", ["server", "container", "signal", "time"], "Stop a Docker container."),
    "RestartContainer": ("execute", ["server", "container"], "Restart a Docker container."),
    "PauseContainer": ("execute", ["server", "container"], "Pause a Docker container."),
    "UnpauseContainer": ("execute", ["server", "container"], "Unpause a Docker container."),
    "DestroyContainer": ("execute", ["server", "container", "signal", "time"], "Destroy a Docker container."),
    "StartAllContainers": ("execute", ["server"], "Start all Docker containers on a server."),
    "StopAllContainers": ("execute", ["server"], "Stop all Docker containers on a server."),
    "RestartAllContainers": ("execute", ["server"], "Restart all Docker containers on a server."),
    "PauseAllContainers": ("execute", ["server"], "Pause all Docker containers on a server."),
    "UnpauseAllContainers": ("execute", ["server"], "Unpause all Docker containers on a server."),
    # ── Execute — Builds ──────────────────────────────────────
    "RunBuild": ("execute", ["build"], "Run a build."),
    "CancelBuild": ("execute", ["build"], "Cancel a running build."),
    # ── Execute — Repos ───────────────────────────────────────
    "CloneRepo": ("execute", ["repo"], "Clone a repo on its configured server."),
    "PullRepo": ("execute", ["repo"], "Pull latest changes for a repo."),
    "BuildRepo": ("execute", ["repo"], "Run the build command for a repo."),
    "CancelRepoBuild": ("execute", ["repo"], "Cancel a running repo build."),
    # ── Execute — Procedures & Actions ────────────────────────
    "RunProcedure": ("execute", ["procedure"], "Run a procedure."),
    "RunAction": ("execute", ["action", "args"], "Run an action. args: optional JSON object."),
    # ── Execute — Resource Syncs ──────────────────────────────
    "RunSync": ("execute", ["sync", "resource_type", "resources"], "Run a resource sync."),
    # ── Execute — Docker Cleanup ──────────────────────────────
    "PruneContainers": ("execute", ["server"], "Prune stopped containers on a server."),
    "PruneImages": ("execute", ["server"], "Prune unused images on a server."),
    "PruneNetworks": ("execute", ["server"], "Prune unused networks on a server."),
    "PruneVolumes": ("execute", ["server"], "Prune unused volumes on a server."),
    "PruneBuildx": ("execute", ["server"], "Prune buildx cache on a server."),
    "PruneDockerBuilders": ("execute", ["server"], "Prune Docker builders on a server."),
    "PruneSystem": ("execute", ["server"], "Prune all unused Docker resources on a server."),
    "DeleteImage": ("execute", ["server", "name"], "Delete a Docker image on a server."),
    "DeleteNetwork": ("execute", ["server", "name"], "Delete a Docker network on a server."),
    "DeleteVolume": ("execute", ["server", "name"], "Delete a Docker volume on a server."),
    # ── Execute — Batch ───────────────────────────────────────
    "BatchDeploy": ("execute", ["pattern"], "Deploy multiple deployments matching a name pattern."),
    "BatchDeployStack": ("execute", ["pattern"], "Deploy multiple stacks matching a name pattern."),
    "BatchDeployStackIfChanged": ("execute", ["pattern"], "Deploy stacks (only if changed) matching a pattern."),
    "BatchDestroyDeployment": ("execute", ["pattern"], "Destroy deployments matching a name pattern."),
    "BatchDestroyStack": ("execute", ["pattern"], "Destroy stacks matching a name pattern."),
    "BatchRunBuild": ("execute", ["pattern"], "Run builds matching a name pattern."),
    "BatchCloneRepo": ("execute", ["pattern"], "Clone repos matching a name pattern."),
    "BatchPullRepo": ("execute", ["pattern"], "Pull repos matching a name pattern."),
    "BatchBuildRepo": ("execute", ["pattern"], "Build repos matching a name pattern."),
    "BatchPullStack": ("execute", ["pattern"], "Pull images for stacks matching a name pattern."),
    "BatchRunAction": ("execute", ["pattern"], "Run actions matching a name pattern."),
    "BatchRunProcedure": ("execute", ["pattern"], "Run procedures matching a name pattern."),
    # ── Execute — Misc ────────────────────────────────────────
    "SendAlert": ("execute", ["level", "message", "details", "alerters"], "Send a custom alert. level: Ok, Warning, or Critical."),
    "TestAlerter": ("execute", ["alerter"], "Test an alerter by sending a test notification."),
    "GlobalAutoUpdate": ("execute", [], "Trigger global poll for image updates. Admin only."),
    "BackupCoreDatabase": ("execute", [], "Backup the Komodo Core database. Admin only."),
    "ClearRepoCache": ("execute", [], "Clear all repos from the Core repo cache. Admin only."),
    "Sleep": ("execute", ["duration_ms"], "Sleep for a specified duration in milliseconds."),
}


def _build_help(endpoint: str) -> str:
    """Build help text listing all operations for an endpoint."""
    lines = []
    for op, (ep, params, doc) in _OPERATIONS.items():
        if ep != endpoint:
            continue
        params_str = ", ".join(params) if params else ""
        lines.append(f"  {op}({params_str}) — {doc}")
    return f"{len(lines)} operations available:\n" + "\n".join(lines)


# ── Meta-tools ────────────────────────────────────────────────────────────────


@mcp.tool()
def komodo_read(operation: str, params: str = "{}") -> str:
    """Execute a Komodo read operation (query data).

    Call with operation="help" to list all 119 available read operations with parameters.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_read(operation="GetServer", params='{"server": "my-server"}')
    """
    if operation == "help":
        return _build_help("read")

    if operation not in _OPERATIONS:
        return json.dumps({"error": f"Unknown operation: {operation}", "hint": "Call with operation='help' to list all operations."})

    ep, _, _ = _OPERATIONS[operation]
    if ep != "read":
        return json.dumps({"error": f"{operation} is a {ep} operation, not read. Use komodo_{ep}() instead."})

    parsed = json.loads(params) if isinstance(params, str) else params
    return _ok(_get_client().read(operation, parsed or None))


@mcp.tool()
def komodo_write(operation: str, params: str = "{}") -> str:
    """Execute a Komodo write operation (create/update/delete resources).

    Call with operation="help" to list all 108 available write operations with parameters.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_write(operation="CreateServer", params='{"name": "my-server", "config": {}}')
    """
    if operation == "help":
        return _build_help("write")

    if operation not in _OPERATIONS:
        return json.dumps({"error": f"Unknown operation: {operation}", "hint": "Call with operation='help' to list all operations."})

    ep, _, _ = _OPERATIONS[operation]
    if ep != "write":
        return json.dumps({"error": f"{operation} is a {ep} operation, not write. Use komodo_{ep}() instead."})

    parsed = json.loads(params) if isinstance(params, str) else params
    return _ok(_get_client().write(operation, parsed or None))


@mcp.tool()
def komodo_execute(operation: str, params: str = "{}") -> str:
    """Execute a Komodo execute operation (trigger actions: deploy, start/stop, build, etc.).

    Call with operation="help" to list all 66 available execute operations with parameters.
    Otherwise pass the operation name and a JSON object with parameters.

    Example: komodo_execute(operation="Deploy", params='{"deployment": "my-app"}')
    """
    if operation == "help":
        return _build_help("execute")

    if operation not in _OPERATIONS:
        return json.dumps({"error": f"Unknown operation: {operation}", "hint": "Call with operation='help' to list all operations."})

    ep, _, _ = _OPERATIONS[operation]
    if ep != "execute":
        return json.dumps({"error": f"{operation} is a {ep} operation, not execute. Use komodo_{ep}() instead."})

    parsed = json.loads(params) if isinstance(params, str) else params
    return _ok(_get_client().execute(operation, parsed or None))
