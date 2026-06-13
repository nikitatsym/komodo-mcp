"""Manual operation descriptions — not touched by codegen.

Add descriptions here for operations where the name alone is not enough.
Used by _build_help to show descriptions in the help text.
If an operation is not listed here, the help shows "{OpName}." as description.
"""

ANNOTATIONS: dict[str, str] = {
    # Read
    "CommitSync": "Exports matching resources and writes to the sync's resource file.",
    "GetContainerLog": "Get container log tail, split by stdout/stderr.",
    "GetDeploymentLog": "Get deployment log tail, split by stdout/stderr.",
    "GetStackLog": "Get stack log tail, split by stdout/stderr.",
    "GetUpdate": "Get update by id. failed_only: only failed stages. tail: limit lines.",
    "UpdatesWait": (
        "Block until an update (returned by any execute op) reaches status=Complete; "
        "result carries success + stage logs (failed_only/log_tail trim). Polls GetUpdate "
        "every `interval` s up to `timeout` s; tolerates `max_poll_failures` consecutive "
        "transient errors (5xx/429/network), other 4xx fail immediately. Holds the tool "
        "call open - prefer UpdatesWaitStart + UpdatesWaitPoll for long actions."
    ),
    "UpdatesWaitStart": (
        "Start a non-blocking wait for an update; returns wait_id + snapshot immediately "
        "(first poll inline, fails fast on a wrong id). Background loop tolerates "
        "`max_poll_failures` transient errors and stops with timed_out=True after "
        "`max_lifetime` s (default 2h, 0 disables)."
    ),
    "UpdatesWaitPoll": (
        "Snapshot of an update wait. max_block>0 blocks up to N s for the terminal "
        "event (event-driven, no busy-wait); 0 returns immediately."
    ),
    "UpdatesWaitCancel": (
        "Stop the background polling task. Does NOT cancel the Komodo update itself "
        "(use CancelBuild etc. for that). Snapshot stays readable; idempotent."
    ),
    "WaitsList": (
        "List active and recently-terminal update waits (compact; 1h TTL after "
        "termination). Recovery path after a lost wait_id."
    ),
    "GetResourceMatchingContainer": "Find the attached resource (Deployment or Stack) for a container.",
    "SearchContainerLog": "Search container log by terms.",
    "SearchDeploymentLog": "Search deployment log by terms.",
    "SearchStackLog": "Search stack log by terms.",
    "GetHistoricalServerStats": "Paginated historical server stats for graphing.",
    "ExportAllResourcesToToml": "Export all resources to TOML sync format.",
    "ExportResourcesToToml": "Export specific resources to TOML sync format.",
    # Write
    "CreateDeploymentFromContainer": "Create a Deployment from an existing container.",
    "WriteBuildFileContents": "Write/update dockerfile contents.",
    "WriteStackFileContents": "Write/update stack file contents.",
    "WriteSyncFileContents": "Write/update sync file contents.",
    "RefreshResourceSyncPending": "Refresh the computed diff logs for a sync.",
    "UpdateResourceMeta": "Update tags, description, or template flag for any resource.",
    # Execute
    "DeployStackIfChanged": "Deploy stack only if file contents changed since last deploy.",
    "RunStackService": "Run a one-time command against a stack service via docker compose run.",
    "GlobalAutoUpdate": "Trigger a global poll for image updates on Stacks and Deployments.",
}
