from __future__ import annotations

from pathlib import Path
from typing import Any

from prefect_grace.models import FrontendVisualVerdict, ObservabilityVerdict, TestVerdict, VerificationRecord
from prefect_grace.tasks.state_store import find_record, update_record, upsert_record

FEATURES_DIR = Path(__file__).resolve().parents[1] / "packets"


def record_verification(
    *,
    packet_id: str,
    test_verdict: str,
    observability_verdict: str,
    frontend_visual_verdict: str,
    commands_run: list[str],
    evidence_paths: list[str],
    blocking_issues: list[str],
) -> dict[str, Any]:
    packet = find_record("packets", "packets", "packet_id", packet_id)
    feature_id = packet["feature_id"]
    evidence_dir = FEATURES_DIR / feature_id / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    verification_path = evidence_dir / f"{packet_id}.verification.md"
    commands_text = "\n".join(f"- {command}" for command in commands_run) or "- none"
    evidence_text = "\n".join(f"- {path}" for path in evidence_paths) or "- none"
    issues_text = "\n".join(f"- {issue}" for issue in blocking_issues) or "- none"
    verification_path.write_text(
        f"# Verifier Evidence: {packet_id}\n\n"
        f"## Test Verdict\n{test_verdict}\n\n"
        f"## Observability Verdict\n{observability_verdict}\n\n"
        f"## Frontend Visual Verdict\n{frontend_visual_verdict}\n\n"
        f"## Commands Run\n{commands_text}\n\n"
        f"## Evidence Reviewed\n{evidence_text}\n\n"
        f"## Blocking Issues\n{issues_text}\n",
        encoding="utf-8",
    )
    record = VerificationRecord(
        packet_id=packet_id,
        test_verdict=TestVerdict(test_verdict),
        observability_verdict=ObservabilityVerdict(observability_verdict),
        frontend_visual_verdict=FrontendVisualVerdict(frontend_visual_verdict),
        commands_run=commands_run,
        evidence_paths=evidence_paths,
        blocking_issues=blocking_issues,
        verification_path=str(verification_path),
    ).to_dict()
    upsert_record("verifications", "verifications", "packet_id", record)
    update_record(
        "packets",
        "packets",
        "packet_id",
        packet_id,
        {
            "last_verification": record,
        },
    )
    return record
