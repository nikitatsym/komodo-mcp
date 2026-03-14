"""Komodo tool operations grouped by risk level.

All generated functions are imported and assigned to MCP groups.
Functions not explicitly grouped become standalone ROOT tools.
"""

import inspect
import re

from ._generated import *  # noqa: F403 — re-export all generated ops
from . import _generated
from ._helpers import _ok, _get_client
from .registry import Group, ROOT, _op


# ── Groups ──────────────────────────────────────────────────────────────────

komodo_read = Group(
    "komodo_read",
    "Query Komodo resources (safe, read-only).\n\n"
    "Call with operation=\"help\" to list all available read operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: komodo_read(operation=\"GetServer\", "
    "params={\"server\": \"my-server\"})",
)

komodo_write = Group(
    "komodo_write",
    "Create, update, rename, or copy Komodo resources.\n\n"
    "Call with operation=\"help\" to list all available write operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: komodo_write(operation=\"CreateServer\", "
    "params={\"name\": \"my-server\"})",
)

komodo_execute = Group(
    "komodo_execute",
    "Trigger actions: deploy, start/stop, build, run procedures.\n\n"
    "Call with operation=\"help\" to list all available execute operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: komodo_execute(operation=\"Deploy\", "
    "params={\"deployment\": \"my-app\"})",
)

komodo_delete = Group(
    "komodo_delete",
    "Delete, destroy, or prune resources (destructive, irreversible).\n\n"
    "Call with operation=\"help\" to list all available delete operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: komodo_delete(operation=\"DeleteServer\", "
    "params={\"id\": \"server-id\"})",
)

komodo_admin_read = Group(
    "komodo_admin_read",
    "Query users, permissions, groups, and API keys.\n\n"
    "Call with operation=\"help\" to list all available admin read operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: komodo_admin_read(operation=\"ListUsers\")",
)

komodo_admin_write = Group(
    "komodo_admin_write",
    "Manage users, groups, permissions, and admin-only actions.\n\n"
    "Call with operation=\"help\" to list all available admin write operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: komodo_admin_write(operation=\"CreateServiceUser\", "
    "params={\"username\": \"bot\", \"description\": \"CI bot\"})",
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _to_snake(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


# ── Group assignments (PascalCase operation names) ──────────────────────────

_SCOPE_GROUPS: dict[Group, list[str]] = {
    komodo_read: [
        # General
        "GetCoreInfo",
        # Servers
        "ListServers", "ListFullServers", "GetServer", "GetServersSummary",
        "GetServerState", "GetServerActionState", "GetSystemStats",
        "GetSystemInformation", "GetHistoricalServerStats",
        "GetPeripheryVersion", "ListSystemProcesses", "ListTerminals",
        # Deployments
        "ListDeployments", "ListFullDeployments", "GetDeployment",
        "GetDeploymentsSummary", "GetDeploymentActionState",
        "GetDeploymentContainer", "GetDeploymentLog", "GetDeploymentStats",
        "InspectDeploymentContainer",
        # Stacks
        "ListStacks", "ListFullStacks", "GetStack", "GetStacksSummary",
        "GetStackActionState", "GetStackLog", "GetStackWebhooksEnabled",
        "ListStackServices", "InspectStackContainer", "SearchStackLog",
        # Builds
        "ListBuilds", "ListFullBuilds", "GetBuild", "GetBuildsSummary",
        "GetBuildActionState", "GetBuildMonthlyStats",
        "GetBuildWebhookEnabled", "ListBuildVersions",
        # Repos
        "ListRepos", "ListFullRepos", "GetRepo", "GetReposSummary",
        "GetRepoActionState", "GetRepoWebhooksEnabled",
        # Procedures
        "ListProcedures", "ListFullProcedures", "GetProcedure",
        "GetProceduresSummary", "GetProcedureActionState",
        # Actions
        "ListActions", "ListFullActions", "GetAction", "GetActionsSummary",
        "GetActionActionState",
        # Resource Syncs
        "ListResourceSyncs", "ListFullResourceSyncs", "GetResourceSync",
        "GetResourceSyncsSummary", "GetResourceSyncActionState",
        "GetSyncWebhooksEnabled",
        # Builders
        "ListBuilders", "ListFullBuilders", "GetBuilder",
        "GetBuildersSummary",
        # Alerters
        "ListAlerters", "ListFullAlerters", "GetAlerter",
        "GetAlertersSummary", "GetAlert",
        # Docker
        "ListDockerContainers", "ListAllDockerContainers",
        "GetDockerContainersSummary", "GetContainerLog",
        "SearchContainerLog", "SearchDeploymentLog",
        "InspectDockerContainer", "ListDockerImages",
        "ListDockerImageHistory", "InspectDockerImage",
        "ListDockerNetworks", "InspectDockerNetwork",
        "ListDockerVolumes", "InspectDockerVolume",
        # Compose
        "ListComposeProjects",
        # Tags, Variables, Secrets
        "ListTags", "GetTag", "ListVariables", "GetVariable",
        # Provider Accounts
        "ListGitProviderAccounts", "GetGitProviderAccount",
        "ListGitProvidersFromConfig",
        "ListDockerRegistryAccounts", "GetDockerRegistryAccount",
        "ListDockerRegistriesFromConfig",
        # Updates & Alerts
        "ListUpdates", "GetUpdate", "ListAlerts",
        # Misc
        "ListSecrets", "ListSchedules", "GetResourceMatchingContainer",
        "ListCommonDeploymentExtraArgs", "ListCommonBuildExtraArgs",
        "ListCommonStackExtraArgs", "ListCommonStackBuildExtraArgs",
        # Export
        "ExportAllResourcesToToml", "ExportResourcesToToml",
    ],
    komodo_write: [
        # Servers
        "CreateServer", "UpdateServer", "RenameServer", "CopyServer",
        "CreateNetwork", "CreateTerminal",
        # Deployments
        "CreateDeployment", "UpdateDeployment", "RenameDeployment",
        "CopyDeployment", "CreateDeploymentFromContainer",
        # Stacks
        "CreateStack", "UpdateStack", "RenameStack", "CopyStack",
        "RefreshStackCache", "WriteStackFileContents",
        "CreateStackWebhook",
        # Builds
        "CreateBuild", "UpdateBuild", "RenameBuild", "CopyBuild",
        "RefreshBuildCache", "WriteBuildFileContents",
        "CreateBuildWebhook",
        # Repos
        "CreateRepo", "UpdateRepo", "RenameRepo", "CopyRepo",
        "RefreshRepoCache", "CreateRepoWebhook",
        # Procedures
        "CreateProcedure", "UpdateProcedure", "RenameProcedure",
        "CopyProcedure",
        # Actions
        "CreateAction", "UpdateAction", "RenameAction", "CopyAction",
        # Resource Syncs
        "CreateResourceSync", "UpdateResourceSync",
        "RenameResourceSync", "CopyResourceSync",
        "RefreshResourceSyncPending", "CommitSync",
        "WriteSyncFileContents", "CreateSyncWebhook",
        # Builders
        "CreateBuilder", "UpdateBuilder", "RenameBuilder", "CopyBuilder",
        # Alerters
        "CreateAlerter", "UpdateAlerter", "RenameAlerter", "CopyAlerter",
        # Tags
        "CreateTag", "RenameTag", "UpdateTagColor",
        # Variables
        "CreateVariable", "UpdateVariableValue",
        "UpdateVariableDescription", "UpdateVariableIsSecret",
        # Provider Accounts
        "CreateGitProviderAccount", "UpdateGitProviderAccount",
        "CreateDockerRegistryAccount", "UpdateDockerRegistryAccount",
        # Resource Meta
        "UpdateResourceMeta",
    ],
    komodo_execute: [
        # Deployments
        "Deploy", "PullDeployment", "StartDeployment", "StopDeployment",
        "RestartDeployment", "PauseDeployment", "UnpauseDeployment",
        # Stacks
        "DeployStack", "DeployStackIfChanged", "PullStack",
        "StartStack", "StopStack", "RestartStack", "PauseStack",
        "UnpauseStack", "RunStackService",
        # Containers
        "StartContainer", "StopContainer", "RestartContainer",
        "PauseContainer", "UnpauseContainer",
        "StartAllContainers", "StopAllContainers",
        "RestartAllContainers", "PauseAllContainers",
        "UnpauseAllContainers",
        # Builds
        "RunBuild", "CancelBuild",
        # Repos
        "CloneRepo", "PullRepo", "BuildRepo", "CancelRepoBuild",
        # Procedures & Actions
        "RunProcedure", "RunAction",
        # Resource Syncs
        "RunSync",
        # Batch (non-destructive)
        "BatchDeploy", "BatchDeployStack", "BatchDeployStackIfChanged",
        "BatchRunBuild", "BatchCloneRepo", "BatchPullRepo",
        "BatchBuildRepo", "BatchPullStack", "BatchRunAction",
        "BatchRunProcedure",
        # Misc
        "SendAlert", "TestAlerter",
    ],
    komodo_delete: [
        # Servers
        "DeleteServer", "DeleteTerminal", "DeleteAllTerminals",
        # Deployments
        "DeleteDeployment", "DestroyDeployment",
        # Stacks
        "DeleteStack", "DeleteStackWebhook", "DestroyStack",
        # Builds
        "DeleteBuild", "DeleteBuildWebhook",
        # Repos
        "DeleteRepo", "DeleteRepoWebhook",
        # Procedures
        "DeleteProcedure",
        # Actions
        "DeleteAction",
        # Resource Syncs
        "DeleteResourceSync", "DeleteSyncWebhook",
        # Builders
        "DeleteBuilder",
        # Alerters
        "DeleteAlerter",
        # Tags & Variables
        "DeleteTag", "DeleteVariable",
        # Provider Accounts
        "DeleteGitProviderAccount", "DeleteDockerRegistryAccount",
        # Containers
        "DestroyContainer",
        # Docker Cleanup
        "PruneContainers", "PruneImages", "PruneNetworks",
        "PruneVolumes", "PruneBuildx", "PruneDockerBuilders",
        "PruneSystem", "DeleteImage", "DeleteNetwork", "DeleteVolume",
        # Batch (destructive)
        "BatchDestroyDeployment", "BatchDestroyStack",
    ],
    komodo_admin_read: [
        "ListUsers", "FindUser", "GetUsername",
        "ListUserGroups", "GetUserGroup",
        "ListPermissions", "ListUserTargetPermissions", "GetPermission",
        "ListApiKeys", "ListApiKeysForServiceUser",
    ],
    komodo_admin_write: [
        # Users
        "CreateLocalUser", "CreateServiceUser", "DeleteUser",
        "UpdateUserAdmin", "UpdateUserPassword", "UpdateUserUsername",
        "UpdateUserBasePermissions", "UpdateServiceUserDescription",
        "CreateApiKeyForServiceUser", "DeleteApiKeyForServiceUser",
        # User Groups
        "CreateUserGroup", "DeleteUserGroup", "RenameUserGroup",
        "AddUserToUserGroup", "RemoveUserFromUserGroup",
        "SetUsersInUserGroup", "SetEveryoneUserGroup",
        # Permissions
        "UpdatePermissionOnResourceType", "UpdatePermissionOnTarget",
        # Admin-only Execute
        "GlobalAutoUpdate", "BackupCoreDatabase", "ClearRepoCache",
    ],
}


# ── Register grouped ops ────────────────────────────────────────────────────

_grouped: set[str] = set()

for _group, _op_names in _SCOPE_GROUPS.items():
    for _pascal in _op_names:
        _snake = _to_snake(_pascal)
        _fn = getattr(_generated, _snake, None)
        if _fn is None:
            continue
        _op(_group)(_fn)
        _grouped.add(_snake)


# ── Custom overrides ────────────────────────────────────────────────────────

# GetUpdate with client-side post-processing (replaces generated version)
def get_update(id: str, failed_only: bool = False, tail: int = 0) -> str:
    """Get update by id. failed_only: only failed stages. tail: limit lines."""
    result = _get_client().read("GetUpdate", {"id": id})
    if (failed_only or tail) and isinstance(result, dict):
        logs = result.get("logs", [])
        if failed_only:
            logs = [s for s in logs if not s.get("success", True)]
        if tail > 0:
            for stage in logs:
                for field in ("stdout", "stderr"):
                    text = stage.get(field, "")
                    if text:
                        lines = text.splitlines()
                        if len(lines) > tail:
                            stage[field] = (
                                f"... ({len(lines) - tail} lines truncated)\n"
                                + "\n".join(lines[-tail:])
                            )
        result["logs"] = logs
    return _ok(result)


_op(komodo_read)(get_update)
_grouped.add("get_update")


# ── Auto-ROOT for ungrouped functions ────────────────────────────────────────

for _name, _fn in inspect.getmembers(_generated, inspect.isfunction):
    if _name.startswith("_"):
        continue
    if _name not in _grouped:
        _op(ROOT)(_fn)
