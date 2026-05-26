# ############################################################################
# AI_HEADER: managed_packet_artifacts
# ROLE: Publish managed packet run results as Prefect markdown artifacts.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Publish managed packet run results as operator-visible Prefect artifacts.
# inputs: Managed packet run result dict.
# returns: List of artifact IDs (empty if Prefect unavailable).
# side_effects: Creates Prefect markdown artifact if available.
# emitted_logs: None.
# error_behavior: Returns empty list on failure, does not raise.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - function: publish_managed_packet_run_artifact
#   - function: _build_artifact_markdown
#   - function: _get_create_markdown_artifact
# END_MODULE_MAP

from __future__ import annotations

import importlib
from typing import Any, Callable


# START_FUNCTION_CONTRACT
# name: _get_create_markdown_artifact
# purpose: Lazy import of Prefect create_markdown_artifact function.
# inputs: None.
# returns: Callable | None - create_markdown_artifact function or None if unavailable.
# side_effects: None.
# emitted_logs: None.
# error_behavior: Returns None if Prefect unavailable, does not raise.
# END_FUNCTION_CONTRACT
def _get_create_markdown_artifact() -> Callable[..., Any] | None:
    """
    Lazy import of Prefect create_markdown_artifact function.

    Returns None if Prefect is not available.
    Uses importlib to avoid direct prefect import at module level.
    """
    try:
        prefect_artifacts = importlib.import_module("prefect.artifacts")
        return getattr(prefect_artifacts, "create_markdown_artifact", None)
    except (ImportError, ModuleNotFoundError, AttributeError):
        return None


# START_FUNCTION_CONTRACT
# name: _build_artifact_markdown
# purpose: Build markdown content for managed packet run artifact.
# inputs:
#   result: dict[str, Any] - Managed packet run result dict.
# returns: str - Markdown content for artifact.
# side_effects: None.
# emitted_logs: None.
# error_behavior: None.
# END_FUNCTION_CONTRACT
def _build_artifact_markdown(result: dict[str, Any]) -> str:
    """
    Build markdown content for managed packet run artifact.

    Includes:
    - Packet ID and attempt
    - Domain status (passed/scope_blocked/agent_failed/runner_error)
    - Worktree path and branch name
    - Changed files list
    - Agent result (returncode, termination reason, session mode)
    - Lifecycle status
    - Scope violations (frozen, outside allowed, invalid paths)
    - Blocker reason if present
    - Run directory / stdout / stderr paths if present
    """
    packet_id = result.get("packet_id", "unknown")
    attempt = result.get("attempt", 0)
    domain_status = result.get("domain_status", "unknown")
    worktree_path = result.get("worktree_path", "")
    branch_name = result.get("branch_name", "")
    changed_files = result.get("changed_files", [])
    agent_result = result.get("agent_result", {})
    lifecycle_result = result.get("lifecycle_result", {})
    scope_guard = result.get("scope_guard", {})
    blocker_reason = result.get("blocker_reason")

    # Status emoji
    status_emoji = {
        "passed": "✅",
        "scope_blocked": "🚫",
        "agent_failed": "❌",
        "runner_error": "⚠️",
    }.get(domain_status, "❓")

    lines = [
        f"# Managed Packet Run: {status_emoji} {domain_status.upper()}",
        "",
        f"**Packet ID:** `{packet_id}`  ",
        f"**Attempt:** `{attempt}`  ",
        f"**Domain Status:** `{domain_status}`  ",
        "",
    ]

    # Worktree details
    if worktree_path:
        lines.extend([
            "## Worktree",
            "",
            f"**Path:** `{worktree_path}`  ",
            f"**Branch:** `{branch_name}`  ",
            "",
        ])

    # Changed files
    lines.extend([
        "## Changed Files",
        "",
    ])

    if changed_files:
        lines.append(f"**Total:** {len(changed_files)}")
        lines.append("")
        for file_path in changed_files[:20]:
            lines.append(f"- `{file_path}`")
        if len(changed_files) > 20:
            lines.append(f"- ... and {len(changed_files) - 20} more")
    else:
        lines.append("*No changed files*")

    lines.append("")

    # Agent result
    if agent_result:
        lines.extend([
            "## Agent Result",
            "",
        ])
        returncode = agent_result.get("returncode")
        if returncode is not None:
            lines.append(f"**Return Code:** `{returncode}`  ")
        termination_reason = agent_result.get("termination_reason")
        if termination_reason:
            lines.append(f"**Termination Reason:** `{termination_reason}`  ")
        session_mode = agent_result.get("session_mode")
        if session_mode:
            lines.append(f"**Session Mode:** `{session_mode}`  ")
        thread_id = agent_result.get("thread_id")
        if thread_id:
            lines.append(f"**Thread ID:** `{thread_id}`  ")

        # Run artifacts
        stdout_path = agent_result.get("stdout_path")
        stderr_path = agent_result.get("stderr_path")
        last_message_path = agent_result.get("last_message_path")
        if stdout_path or stderr_path or last_message_path:
            lines.append("")
            lines.append("**Run Artifacts:**")
            if stdout_path:
                lines.append(f"- Stdout: `{stdout_path}`")
            if stderr_path:
                lines.append(f"- Stderr: `{stderr_path}`")
            if last_message_path:
                lines.append(f"- Last Message: `{last_message_path}`")

        lines.append("")

    # Lifecycle status
    lifecycle_status = lifecycle_result.get("status")
    if lifecycle_status:
        lines.extend([
            "## Lifecycle Status",
            "",
            f"**Status:** `{lifecycle_status}`  ",
            "",
        ])

    # Scope violations
    frozen_violations = scope_guard.get("frozen_violations", [])
    outside_allowed = scope_guard.get("outside_allowed", [])
    invalid_paths = scope_guard.get("invalid_paths", [])

    if frozen_violations or outside_allowed or invalid_paths:
        lines.extend([
            "## Scope Violations",
            "",
        ])

        if frozen_violations:
            lines.append(f"### 🚫 Frozen Violations ({len(frozen_violations)})")
            lines.append("")
            for v in frozen_violations[:10]:
                file_path = v.get("file_path", "unknown")
                matched_pattern = v.get("matched_pattern")
                if matched_pattern:
                    lines.append(f"- `{file_path}` (matched: `{matched_pattern}`)")
                else:
                    lines.append(f"- `{file_path}`")
            if len(frozen_violations) > 10:
                lines.append(f"- ... and {len(frozen_violations) - 10} more")
            lines.append("")

        if outside_allowed:
            lines.append(f"### ⚠️ Outside Allowed Scope ({len(outside_allowed)})")
            lines.append("")
            for v in outside_allowed[:10]:
                file_path = v.get("file_path", "unknown")
                lines.append(f"- `{file_path}`")
            if len(outside_allowed) > 10:
                lines.append(f"- ... and {len(outside_allowed) - 10} more")
            lines.append("")

        if invalid_paths:
            lines.append(f"### ❌ Invalid Paths ({len(invalid_paths)})")
            lines.append("")
            for v in invalid_paths[:10]:
                file_path = v.get("file_path", "unknown")
                reason = v.get("reason", "unknown")
                lines.append(f"- `{file_path}`: {reason}")
            if len(invalid_paths) > 10:
                lines.append(f"- ... and {len(invalid_paths) - 10} more")
            lines.append("")

    # Blocker reason
    if blocker_reason:
        lines.extend([
            "## Blocker Reason",
            "",
            "```",
            blocker_reason,
            "```",
            "",
        ])

    # Footer
    lines.extend([
        "---",
        "",
        "*Generated by GRACE Managed Packet Runner*",
    ])

    return "\n".join(lines)


# START_FUNCTION_CONTRACT
# name: publish_managed_packet_run_artifact
# purpose: Publish managed packet run result as Prefect markdown artifact.
# inputs:
#   result: dict[str, Any] - Managed packet run result dict.
# returns: list[str] - List of artifact IDs (empty if Prefect unavailable or publication failed).
# side_effects: Creates Prefect markdown artifact if available.
# emitted_logs: None.
# error_behavior: Returns empty list on failure, does not raise.
# END_FUNCTION_CONTRACT
def publish_managed_packet_run_artifact(result: dict[str, Any]) -> list[str]:
    """
    Publish managed packet run result as Prefect markdown artifact.

    Best-effort publication:
    - Returns empty list if Prefect artifacts are unavailable
    - Returns empty list if publication fails
    - Does not raise exceptions

    Args:
        result: Managed packet run result dict

    Returns:
        List of artifact IDs (empty if unavailable/failed)
    """
    create_markdown_artifact = _get_create_markdown_artifact()
    if create_markdown_artifact is None:
        # Prefect not available
        return []

    try:
        markdown = _build_artifact_markdown(result)

        packet_id = result.get("packet_id", "unknown")
        attempt = result.get("attempt", 0)
        domain_status = result.get("domain_status", "unknown")

        artifact_id = create_markdown_artifact(
            key=f"managed-packet-{packet_id}-attempt-{attempt}",
            markdown=markdown,
            description=f"Managed packet run: {domain_status}",
        )

        return [artifact_id] if artifact_id else []

    except Exception:
        # Publication failed, return empty list
        return []
