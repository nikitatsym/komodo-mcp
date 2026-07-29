"""Komodo tool operations grouped by risk level.

All generated functions are imported and assigned to MCP groups.
Functions not explicitly grouped become standalone ROOT tools.
"""

import asyncio
import inspect
import logging
import re
import time

from . import _generated
from ._generated import *
from ._helpers import _get_client, _ok
from .client import KomodoError
from .registry import ROOT, Group, _op
from .wait_registry import (
    TERMINAL_STATUSES as _WAIT_TERMINAL,
    WAIT_REGISTRY as _WAIT_REGISTRY,
    WaitHandle as _WaitHandle,
)

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


def _register_groups():
    for group, op_names in _SCOPE_GROUPS.items():
        for pascal in op_names:
            snake = _to_snake(pascal)
            fn = getattr(_generated, snake, None)
            if fn is None:
                continue
            _op(group)(fn)
            _grouped.add(snake)


_register_groups()


# ── Custom overrides ────────────────────────────────────────────────────────

def _trim_update_logs(update, failed_only: bool, tail: int) -> list:
    """Stage logs of an update: optionally only failed stages, stdout/stderr
    trimmed to the trailing `tail` lines (0 = full). Stage dicts are copied,
    all original fields preserved."""
    logs = (update.get("logs") or []) if isinstance(update, dict) else []
    if failed_only:
        logs = [s for s in logs if not s.get("success", True)]
    out = []
    for stage in logs:
        item = dict(stage)
        if tail > 0:
            for field in ("stdout", "stderr"):
                text = item.get(field, "")
                if text:
                    lines = text.splitlines()
                    if len(lines) > tail:
                        item[field] = (
                            f"... ({len(lines) - tail} lines truncated)\n"
                            + "\n".join(lines[-tail:])
                        )
        out.append(item)
    return out


# GetUpdate with client-side post-processing (replaces generated version)
def get_update(id: str, failed_only: bool = False, tail: int = 0):
    """Get update by id. failed_only: only failed stages. tail: limit lines."""
    result = _get_client().read("GetUpdate", {"id": id})
    if (failed_only or tail) and isinstance(result, dict):
        result["logs"] = _trim_update_logs(result, failed_only, tail)
    return _ok(result)


_op(komodo_read)(get_update)
_grouped.add("get_update")


# ListTags — flatten MongoDocument query into explicit Tag fields
def list_tags(name: str | None = None, color: str | None = None, owner: str | None = None):
    """List tags. Filter by name, color (e.g. Red, Blue, Green, Slate), or owner."""
    query: dict = {}
    if name is not None:
        query["name"] = name
    if color is not None:
        query["color"] = color
    if owner is not None:
        query["owner"] = owner
    params: dict = {}
    if query:
        params["query"] = query
    return _ok(_get_client().read("ListTags", params or None))


_op(komodo_read)(list_tags)
_grouped.add("list_tags")


# ListAlerts — flatten MongoDocument query into explicit Alert fields
def list_alerts(
    resolved: bool | None = None,
    level: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    page: int | None = None,
):
    """List alerts. level: OK, WARNING, CRITICAL. target_type: Server, Stack, Deployment, etc."""
    query: dict = {}
    if resolved is not None:
        query["resolved"] = resolved
    if level is not None:
        query["level"] = level
    if target_type is not None and target_id is not None:
        query["target"] = {"type": target_type, "id": target_id}
    params: dict = {}
    if query:
        params["query"] = query
    if page is not None:
        params["page"] = page
    return _ok(_get_client().read("ListAlerts", params or None))


_op(komodo_read)(list_alerts)
_grouped.add("list_alerts")


# ListUpdates — flatten MongoDocument query into explicit Update fields
def list_updates(
    operation: str | None = None,
    success: bool | None = None,
    operator: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    page: int | None = None,
):
    """List updates. Filter by operation, success, operator, or target resource."""
    query: dict = {}
    if operation is not None:
        query["operation"] = operation
    if success is not None:
        query["success"] = success
    if operator is not None:
        query["operator"] = operator
    if target_type is not None and target_id is not None:
        query["target"] = {"type": target_type, "id": target_id}
    params: dict = {}
    if query:
        params["query"] = query
    if page is not None:
        params["page"] = page
    return _ok(_get_client().read("ListUpdates", params or None))


_op(komodo_read)(list_updates)
_grouped.add("list_updates")


# ── Auto-ROOT for ungrouped functions ────────────────────────────────────────

for _name, _fn in inspect.getmembers(_generated, inspect.isfunction):
    if _name.startswith("_"):
        continue
    if _name not in _grouped:
        _op(ROOT)(_fn)


# ── Long-running waiters (Updates) ───────────────────────────────────────────
#
# Execute ops return an Update that progresses Queued -> InProgress ->
# Complete server-side; the waiters poll GetUpdate until Complete. All
# wait ops live in komodo_read: a wait only ever reads, and cancel stops
# the local task, not the update. Pattern: mcp-server-v2 "Long-running waiters".


_log_wait = logging.getLogger("komodo_mcp.wait")

# One transient blip must not kill a minutes-long wait; fatal 4xx never heal.
_MAX_POLL_FAILURES_DEFAULT = 3
# Bounds orphan background waits (e.g. update stuck Queued, server offline).
_MAX_LIFETIME_DEFAULT = 7200.0


def _poll_error_is_fatal(e: Exception) -> bool:
    """True for poll errors that retrying cannot fix (4xx other than 429)."""
    return (
        isinstance(e, KomodoError)
        and 400 <= e.status < 500
        and e.status != 429
    )


async def _emit_progress(ctx, progress: float, total, message: str) -> None:
    """Best-effort progress emit - never breaks polling on transport errors."""
    if ctx is None:
        return
    try:
        await ctx.report_progress(progress=progress, total=total, message=message)
    except Exception:  # noqa: BLE001 - progress is best-effort, never fatal
        _log_wait.debug("report_progress failed", exc_info=True)


async def _emit_log(ctx, level: str, message: str) -> None:
    """Best-effort log emit - never breaks polling on transport errors."""
    if ctx is None:
        return
    try:
        await ctx.log(level=level, message=message)
    except Exception:  # noqa: BLE001 - log notifications are best-effort
        _log_wait.debug("ctx.log failed", exc_info=True)


def _fetch_update_raw(update_id: str):
    return _get_client().read("GetUpdate", {"id": update_id})


def _slim_update_meta(update) -> dict:
    """Update without stage stdout/stderr, so mid-flight snapshots stay small."""
    if not isinstance(update, dict):
        return {}
    uid = update.get("_id")
    if isinstance(uid, dict):
        uid = uid.get("$oid")
    return {
        "id": uid,
        "operation": update.get("operation"),
        "status": update.get("status"),
        "success": update.get("success"),
        "target": update.get("target"),
        "start_ts": update.get("start_ts"),
        "end_ts": update.get("end_ts"),
        "stages": [
            {"stage": s.get("stage"), "success": s.get("success")}
            for s in update.get("logs") or []
        ],
    }


async def updates_wait(
    update_id: str,
    timeout: float = 600.0,
    interval: float = 5.0,
    max_poll_failures: int = _MAX_POLL_FAILURES_DEFAULT,
    include_logs: bool = True,
    failed_only: bool = True,
    log_tail: int = 100,
    ctx=None,
):
    """Block until an update reaches a terminal status (Complete).

    Holds the tool call open up to `timeout` s; prefer UpdatesWaitStart +
    UpdatesWaitPoll for long actions. Transient poll failures tolerated up
    to `max_poll_failures` consecutive; other 4xx raise immediately."""
    if timeout <= 0:
        raise ValueError(f"timeout must be > 0, got {timeout}")
    if interval <= 0:
        raise ValueError(f"interval must be > 0, got {interval}")
    if max_poll_failures < 1:
        raise ValueError(f"max_poll_failures must be >= 1, got {max_poll_failures}")
    if log_tail < 0:
        raise ValueError(f"log_tail must be >= 0, got {log_tail}")

    start = time.monotonic()
    previous_status = None
    update_raw = {}
    meta: dict = {}
    polls = 0
    poll_failures = 0
    consecutive_failures = 0
    last_poll_error = None
    terminated = False

    while True:
        elapsed = time.monotonic() - start
        try:
            update_raw = await asyncio.to_thread(_fetch_update_raw, update_id)
        except Exception as e:
            polls += 1
            poll_failures += 1
            consecutive_failures += 1
            last_poll_error = str(e)
            if _poll_error_is_fatal(e) or consecutive_failures >= max_poll_failures:
                raise
            await _emit_log(
                ctx, "warning",
                f"update {update_id}: poll failed "
                f"({consecutive_failures}/{max_poll_failures} consecutive), retrying: {e}",
            )
            if elapsed + interval >= timeout:
                break
            await asyncio.sleep(interval)
            continue
        polls += 1
        consecutive_failures = 0
        meta = _slim_update_meta(update_raw)
        status = meta.get("status")

        if status != previous_status:
            await _emit_progress(
                ctx, progress=elapsed, total=timeout,
                message=f"update {update_id} status: {status}",
            )
            if previous_status is None:
                await _emit_log(
                    ctx, "info", f"update {update_id}: starting wait (status={status})",
                )
            else:
                await _emit_log(
                    ctx, "info", f"update {update_id}: {previous_status} -> {status}",
                )
            previous_status = status

        if status in _WAIT_TERMINAL:
            terminated = True
            break

        if elapsed + interval >= timeout:
            break

        await asyncio.sleep(interval)

    elapsed_final = time.monotonic() - start
    result = {
        "update": meta,
        "status": meta.get("status"),
        "success": meta.get("success"),
        "terminated": terminated,
        "timed_out": not terminated,
        "elapsed_seconds": round(elapsed_final, 2),
        "polls": polls,
    }
    if poll_failures:
        result["poll_failures"] = poll_failures
        result["last_poll_error"] = last_poll_error

    if terminated:
        ok = meta.get("success")
        await _emit_log(
            ctx, "info" if ok else "error",
            f"update {update_id} completed with success={ok} "
            f"after {polls} polls in {elapsed_final:.1f}s",
        )
        if include_logs:
            result["logs"] = _trim_update_logs(update_raw, failed_only, log_tail)
    else:
        await _emit_log(
            ctx, "warning",
            f"update {update_id} did not complete in {timeout}s "
            f"(last status={meta.get('status')}, polls={polls})",
        )

    return result


_op(komodo_read)(updates_wait)


# ── Non-blocking wait tools (start / poll / cancel) ──────────────────────────
#
# start returns wait_id immediately (background task), poll reads the
# snapshot (max_block waits on an event), cancel stops the polling task only.


async def _do_update_poll(handle: _WaitHandle) -> bool:
    """One poll. Updates handle, returns True if terminal. The HTTP call
    runs in a worker thread; the handle is mutated back on the loop."""
    payload = await asyncio.to_thread(_fetch_update_raw, handle.target_id)
    handle.polls += 1
    meta = _slim_update_meta(payload)
    handle.last_payload = meta
    handle.success = meta.get("success")
    handle.record_transition(meta.get("status"))
    return handle.status in _WAIT_TERMINAL


async def _enrich_update_final(handle: _WaitHandle) -> None:
    """Attach trimmed stage logs to final_extras. One extra GetUpdate so the
    mid-flight snapshots never carry full stdout/stderr."""
    opts = handle.options
    if not opts.get("include_logs", True):
        return
    raw = await asyncio.to_thread(_fetch_update_raw, handle.target_id)
    handle.final_extras["logs"] = _trim_update_logs(
        raw, opts.get("failed_only", True), opts.get("log_tail", 100)
    )


async def _update_loop(handle: _WaitHandle) -> None:
    """Background task body: sleep, poll, repeat until terminal."""
    interval = handle.options["interval"]
    max_failures = handle.options.get("max_poll_failures", _MAX_POLL_FAILURES_DEFAULT)
    max_lifetime = handle.options.get("max_lifetime", _MAX_LIFETIME_DEFAULT)
    consecutive_failures = 0
    try:
        while True:
            await asyncio.sleep(interval)
            if max_lifetime > 0 and (time.time() - handle.started_at) >= max_lifetime:
                handle.mark_timed_out(
                    f"exceeded max_lifetime {max_lifetime:g}s without reaching "
                    f"a terminal status (last status={handle.status})"
                )
                return
            try:
                terminal = await _do_update_poll(handle)
            except Exception as e:  # noqa: BLE001 - classified below
                consecutive_failures += 1
                handle.record_poll_failure(str(e))
                if _poll_error_is_fatal(e) or consecutive_failures >= max_failures:
                    suffix = (
                        f" ({consecutive_failures} consecutive failures)"
                        if consecutive_failures > 1 else ""
                    )
                    handle.mark_terminated(error=f"poll failed: {e}{suffix}")
                    return
                continue
            consecutive_failures = 0
            if terminal:
                try:
                    await _enrich_update_final(handle)
                except Exception as e:  # noqa: BLE001 - enrichment is best-effort
                    handle.final_extras["enrichment_error"] = str(e)
                handle.mark_terminated()
                return
    except asyncio.CancelledError:
        handle.mark_terminated(error="cancelled")
        raise


async def _cancel_handle(handle: _WaitHandle) -> None:
    """Cancel the task; defensively mark cancelled if the loop's handler
    never ran (cancel can land before the first await)."""
    task = handle.task
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001, S110 - task outcome ignored, cleanup below always runs
            pass
    if not handle.done_event.is_set():
        handle.mark_terminated(error="cancelled")


def _require_handle(wait_id: str) -> _WaitHandle:
    handle = _WAIT_REGISTRY.get(wait_id)
    if handle is None:
        raise ValueError(
            f"Unknown wait_id: {wait_id!r}. Use WaitsList to enumerate "
            "active or recently-finished waits."
        )
    return handle


async def updates_wait_start(
    update_id: str,
    interval: float = 5.0,
    max_poll_failures: int = _MAX_POLL_FAILURES_DEFAULT,
    max_lifetime: float = _MAX_LIFETIME_DEFAULT,
    include_logs: bool = True,
    failed_only: bool = True,
    log_tail: int = 100,
):
    """Start a non-blocking wait for an update; returns wait_id + snapshot
    immediately. First poll runs inline (fails fast on a wrong id)."""
    if interval <= 0:
        raise ValueError(f"interval must be > 0, got {interval}")
    if max_poll_failures < 1:
        raise ValueError(f"max_poll_failures must be >= 1, got {max_poll_failures}")
    if max_lifetime < 0:
        raise ValueError(f"max_lifetime must be >= 0, got {max_lifetime}")
    if log_tail < 0:
        raise ValueError(f"log_tail must be >= 0, got {log_tail}")

    _WAIT_REGISTRY.reap_old()

    options = {
        "interval": interval,
        "max_poll_failures": max_poll_failures,
        "max_lifetime": max_lifetime,
        "include_logs": include_logs,
        "failed_only": failed_only,
        "log_tail": log_tail,
    }
    handle = _WAIT_REGISTRY.new_handle(update_id, options)

    try:
        terminal = await _do_update_poll(handle)
    except Exception as e:  # noqa: BLE001 - reported via snapshot
        handle.mark_terminated(error=f"initial poll failed: {e}")
        return handle.snapshot()

    if terminal:
        try:
            await _enrich_update_final(handle)
        except Exception as e:  # noqa: BLE001 - enrichment is best-effort
            handle.final_extras["enrichment_error"] = str(e)
        handle.mark_terminated()
        return handle.snapshot()

    handle.task = asyncio.create_task(_update_loop(handle))
    return handle.snapshot()


_op(komodo_read)(updates_wait_start)


async def updates_wait_poll(wait_id: str, max_block: float = 0.0):
    """Snapshot of an update wait. max_block>0 blocks up to N seconds for
    the terminal event (event-driven, no busy-wait)."""
    if max_block < 0:
        raise ValueError(f"max_block must be >= 0, got {max_block}")
    handle = _require_handle(wait_id)
    if max_block > 0 and not handle.done_event.is_set():
        try:
            await asyncio.wait_for(handle.done_event.wait(), timeout=max_block)
        except asyncio.TimeoutError:
            snap = handle.snapshot()
            snap["timed_out"] = True
            return snap
    return handle.snapshot()


_op(komodo_read)(updates_wait_poll)


async def updates_wait_cancel(wait_id: str):
    """Cancel an update wait (the polling task only - NOT the Komodo
    update). Idempotent; the snapshot remains readable."""
    handle = _require_handle(wait_id)
    if handle.done_event.is_set():
        return handle.snapshot()
    await _cancel_handle(handle)
    return handle.snapshot()


_op(komodo_read)(updates_wait_cancel)


def waits_list(terminated: bool | None = None):
    """List active and recently-terminal update waits (compact, 1h TTL)."""
    out = []
    for handle in _WAIT_REGISTRY.all_handles():
        if terminated is not None and handle.terminated != terminated:
            continue
        out.append({
            "wait_id": handle.wait_id,
            "kind": handle.kind,
            "update_id": handle.target_id,
            "status": handle.status,
            "success": handle.success,
            "terminated": handle.terminated,
            "timed_out": handle.timed_out,
            "polls": handle.polls,
            "elapsed_seconds": handle.elapsed_seconds,
            "started_at": handle.started_at,
            "ended_at": handle.ended_at,
            "error": handle.error,
        })
    return out


_op(komodo_read)(waits_list)
