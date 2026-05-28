# ############################################################################
# AI_HEADER: packet_artifacts
# ROLE: Writes review/evidence/rework artifacts to bounded files.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Write review/evidence/rework artifacts to REVIEWS/, EVIDENCE/, REWORK/.
# inputs: Packet directory, artifact type, content.
# returns: Path to written artifact file.
# side_effects: Creates artifact directories and files.
# emitted_logs: None.
# error_behavior: Raises IOError if write fails.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - function: write_review
#   - function: write_evidence
#   - function: write_rework
# END_MODULE_MAP

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prefect_grace.platform.packet_artifact_layout import resolve_packet_layout

# START_BLOCK_ARTIFACT_WRITERS
# START_FUNCTION_CONTRACT
# name: write_review
# purpose: Write review verdict to REVIEWS/review-XXXX.md.
# inputs:
#   packet_dir: Path to packet directory.
#   verdict: Review verdict string (accepted, rework_required, blocked).
#   body: Review body content.
#   metadata: Optional metadata dict.
# returns: Path to written review file.
# side_effects: Creates REVIEWS/ directory and review file.
# emitted_logs: None.
# error_behavior: Raises IOError if write fails.
# END_FUNCTION_CONTRACT
def write_review(
    packet_dir: Path,
    verdict: str,
    body: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    layout = resolve_packet_layout(packet_dir)
    layout.reviews_dir.mkdir(parents=True, exist_ok=True)

    # Find next review number
    existing_reviews = sorted(layout.reviews_dir.glob("review-*.md"))
    next_num = len(existing_reviews) + 1
    review_file = layout.reviews_dir / f"review-{next_num:04d}.md"

    # Build review content
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Review {next_num:04d}",
        "",
        f"**Verdict:** `{verdict}`",
        f"**Timestamp:** `{timestamp}`",
        "",
    ]

    if metadata:
        lines.append("## Metadata")
        lines.append("")
        for key, value in metadata.items():
            lines.append(f"- **{key}:** `{value}`")
        lines.append("")

    lines.extend([
        "## Review Body",
        "",
        body,
        "",
    ])

    review_content = "\n".join(lines)
    review_file.write_text(review_content, encoding="utf-8")

    return review_file


# START_FUNCTION_CONTRACT
# name: write_evidence
# purpose: Write evidence manifest to EVIDENCE/attempt-XXXX/evidence_manifest.json.
# inputs:
#   packet_dir: Path to packet directory.
#   attempt: Attempt number.
#   manifest: Evidence manifest dict.
# returns: Path to written evidence manifest file.
# side_effects: Creates EVIDENCE/attempt-XXXX/ directory and manifest file.
# emitted_logs: None.
# error_behavior: Raises IOError if write fails.
# END_FUNCTION_CONTRACT
def write_evidence(
    packet_dir: Path,
    attempt: int,
    manifest: dict[str, Any],
) -> Path:
    layout = resolve_packet_layout(packet_dir)
    attempt_dir = layout.evidence_dir / f"attempt-{attempt:04d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = attempt_dir / "evidence_manifest.json"

    # Add timestamp to manifest
    manifest_with_timestamp = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempt": attempt,
        **manifest,
    }

    manifest_file.write_text(
        json.dumps(manifest_with_timestamp, indent=2),
        encoding="utf-8",
    )

    return manifest_file


# START_FUNCTION_CONTRACT
# name: write_rework
# purpose: Write rework instructions to REWORK/attempt-XXXX.md.
# inputs:
#   packet_dir: Path to packet directory.
#   attempt: Attempt number.
#   body: Rework instruction body.
#   blockers: Optional list of blocker strings.
# returns: Path to written rework file.
# side_effects: Creates REWORK/ directory and rework file.
# emitted_logs: None.
# error_behavior: Raises IOError if write fails.
# END_FUNCTION_CONTRACT
def write_rework(
    packet_dir: Path,
    attempt: int,
    body: str,
    blockers: list[str] | None = None,
) -> Path:
    layout = resolve_packet_layout(packet_dir)
    layout.rework_dir.mkdir(parents=True, exist_ok=True)

    rework_file = layout.rework_dir / f"attempt-{attempt:04d}.md"

    # Build rework content
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Rework Instructions - Attempt {attempt:04d}",
        "",
        f"**Timestamp:** `{timestamp}`",
        "",
    ]

    if blockers:
        lines.append("## Blockers")
        lines.append("")
        for blocker in blockers:
            lines.append(f"- {blocker}")
        lines.append("")

    lines.extend([
        "## Required Actions",
        "",
        body,
        "",
    ])

    rework_content = "\n".join(lines)
    rework_file.write_text(rework_content, encoding="utf-8")

    return rework_file

# END_BLOCK_ARTIFACT_WRITERS
