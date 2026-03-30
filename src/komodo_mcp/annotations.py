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
