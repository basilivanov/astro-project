from __future__ import annotations

from pathlib import Path
from typing import Any

from prefect_grace.models import DecisionRecord, PacketStatus, ReasoningProfile, ReviewRecord, ReviewVerdict, WaveReviewRecord, WaveVerdict
from prefect_grace.tasks.feature_bootstrap import create_packet
from prefect_grace.tasks.grace_ids import grace_refs_for_packet
from prefect_grace.tasks.state_store import find_record, update_record, upsert_record

FEATURES_DIR = Path(__file__).resolve().parents[1] / "packets"
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"


def record_review(
    *,
    packet_id: str,
    verdict: ReviewVerdict,
    reasons: list[str],
    reviewer: str = "reviewer",
    follow_up_action: str = "none",
) -> dict[str, Any]:
    packet = find_record("packets", "packets", "packet_id", packet_id)
    feature_id = packet["feature_id"]
    grace_refs = grace_refs_for_packet(packet)
    review_dir = FEATURES_DIR / feature_id / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"{packet_id}.review.md"
    reason_text = "\n".join(f"- {reason}" for reason in reasons) or "- none"
    review_path.write_text(
        f"# Packet Review: {packet_id}\n\n"
        f"## GRACE IDs\n"
        f"- feature_ref: `{grace_refs['grace_feature_ref']}`\n"
        f"- wave_ref: `{grace_refs['grace_wave_ref']}`\n"
        f"- packet_ref: `{grace_refs['grace_packet_ref']}`\n\n"
        f"## Verdict\n{verdict.value}\n\n"
        f"## Acceptance Check\n- see packet acceptance criteria\n\n"
        f"## Blockers\n{reason_text}\n\n"
        f"## Follow-up Action\n{follow_up_action}\n",
        encoding="utf-8",
    )
    record = ReviewRecord(
        packet_id=packet_id,
        feature_id=feature_id,
        wave_id=str(packet.get("wave_id") or ""),
        grace_feature_ref=grace_refs["grace_feature_ref"],
        grace_wave_ref=grace_refs["grace_wave_ref"],
        grace_packet_ref=grace_refs["grace_packet_ref"],
        verdict=verdict,
        reasons=reasons,
        reviewer=reviewer,
        follow_up_action=follow_up_action,
        review_path=str(review_path),
    ).to_dict()
    upsert_record("reviews", "reviews", "packet_id", record)
    update_record(
        "packets",
        "packets",
        "packet_id",
        packet_id,
        {
            "status": verdict.value,
            "last_review": record,
        },
    )
    return record


def create_rework_from_review(packet_id: str, reasons: list[str]) -> dict[str, Any]:
    packet = find_record("packets", "packets", "packet_id", packet_id)
    inherited_execution_hints = dict(packet.get("execution_hints") or {})
    blocker_summary = "; ".join(reasons) if reasons else "Reviewer requested localized rework."
    return create_packet(
        feature_id=packet["feature_id"],
        wave_id=packet["wave_id"],
        title=f"Rework {packet['title']}",
        role=packet.get("role") or "coder",
        reasoning=ReasoningProfile(packet.get("reasoning") or ReasoningProfile.HIGH.value),
        summary=f"Address reviewer blockers from {packet_id}: {blocker_summary}",
        write_scope=[
            f"Only the files required to address blockers from `{packet_id}`.",
        ],
        inputs=[
            f"Parent packet `{packet_id}`.",
            "Reviewer blocker notes.",
        ],
        acceptance_criteria=[
            "Reviewer blockers are addressed directly.",
            "No unrelated scope expansion.",
            "Updated verification evidence is ready for re-review.",
        ],
        verification_profile={
            "backend": "rerun the minimally sufficient backend profile if backend code changed",
            "frontend": "rerun targeted Playwright if UI changed",
            "observability": "repeat post-test evidence review for the affected flow",
        },
        reviewer_gate=[
            "All blocker reasons are addressed.",
            "No new regressions are introduced in the scoped flow.",
        ],
        dependencies=[packet_id],
        notes=[
            "This is a localized rework packet created from reviewer blockers.",
        ],
        parent_packet_id=packet_id,
        execution_hints=inherited_execution_hints,
        status=PacketStatus.READY,
    )


def create_rework_bundle_from_review(
    *,
    packet_id: str,
    reviewer_packet_id: str,
    reasons: list[str],
) -> dict[str, Any]:
    rework_packet = create_rework_from_review(packet_id, reasons)
    reviewer_packet = find_record("packets", "packets", "packet_id", reviewer_packet_id)
    verifier_packet_id = next(
        (
            dependency
            for dependency in reviewer_packet.get("dependencies") or []
            if str(find_record("packets", "packets", "packet_id", dependency).get("role") or "") == "verifier"
        ),
        None,
    )
    verifier_hints = dict(rework_packet.get("execution_hints") or {})
    verifier_profile = {}
    if verifier_packet_id:
        verifier_source = find_record("packets", "packets", "packet_id", verifier_packet_id)
        verifier_hints = {**verifier_hints, **dict(verifier_source.get("execution_hints") or {})}
        verifier_profile = dict(verifier_source.get("verification_profile") or {})

    verifier_packet = create_packet(
        feature_id=rework_packet["feature_id"],
        wave_id=rework_packet["wave_id"],
        title=f"Verifier Rework {rework_packet['title']}",
        role="verifier",
        reasoning=ReasoningProfile.MEDIUM,
        summary=f"Validate the localized rework for `{packet_id}` and capture fresh evidence.",
        write_scope=["Verification notes and evidence references only."],
        inputs=[rework_packet["packet_id"], reviewer_packet_id],
        acceptance_criteria=[
            "Commands run are recorded for the rework packet.",
            "Evidence paths are refreshed for the reworked scope.",
            "Observability verdict is explicit for the rework.",
        ],
        verification_profile=verifier_profile
        or {
            "backend": "rerun minimally sufficient backend checks for the reworked scope",
            "frontend": "rerun targeted frontend checks if UI changed",
            "observability": "repeat post-test digest, trace, and replay review",
        },
        reviewer_gate=[
            "Evidence must correspond to the rework packet, not the original attempt.",
            "Missing visual proof remains a blocker for UI work.",
        ],
        dependencies=[rework_packet["packet_id"]],
        notes=["This verifier packet was auto-created from reviewer blockers."],
        parent_packet_id=packet_id,
        execution_hints=verifier_hints,
        status=PacketStatus.READY,
    )

    rework_reviewer_packet = create_packet(
        feature_id=rework_packet["feature_id"],
        wave_id=rework_packet["wave_id"],
        title=f"Reviewer Rework {rework_packet['title']}",
        role="reviewer",
        reasoning=ReasoningProfile.XHIGH,
        summary=f"Review whether the localized rework for `{packet_id}` addressed the reviewer blockers.",
        write_scope=["Review verdict and blocker notes only."],
        inputs=[rework_packet["packet_id"], verifier_packet["packet_id"]],
        acceptance_criteria=[
            "Exactly one verdict is returned.",
            "The original blockers are either resolved or explicitly remain.",
            "No unrelated scope expansion is accepted.",
        ],
        verification_profile={
            "backend": "consume verifier evidence",
            "frontend": "consume verifier evidence",
            "observability": "consume verifier evidence",
        },
        reviewer_gate=[
            "Assess only the original blocker scope.",
            "Escalate only if blockers imply decomposition or business changes.",
        ],
        dependencies=[rework_packet["packet_id"], verifier_packet["packet_id"]],
        notes=["This reviewer packet was auto-created from reviewer blockers."],
        parent_packet_id=packet_id,
        status=PacketStatus.READY,
    )
    rework_reviewer_packet = update_record(
        "packets",
        "packets",
        "packet_id",
        rework_reviewer_packet["packet_id"],
        {
            "review_target_packet_id": rework_packet["packet_id"],
            "execution_hints": dict(rework_packet.get("execution_hints") or {}),
        },
    )
    return {
        "rework": rework_packet,
        "verifier": verifier_packet,
        "reviewer": rework_reviewer_packet,
    }


def create_architect_decision_from_review(packet_id: str, reasons: list[str]) -> dict[str, Any]:
    packet = find_record("packets", "packets", "packet_id", packet_id)
    feature_id = packet["feature_id"]
    decision_id = f"{packet_id}-ARCH-DECISION"
    decision_dir = FEATURES_DIR / feature_id / "decisions"
    decision_dir.mkdir(parents=True, exist_ok=True)
    decision_path = decision_dir / f"{decision_id}.md"
    summary = f"Architect decision required for {packet_id}"
    reason_text = "\n".join(f"- {reason}" for reason in reasons) or "- reviewer did not provide explicit reasons"
    decision_path.write_text(
        f"# Architect Decision: {decision_id}\n\n"
        f"## Source Packet\n{packet_id}\n\n"
        f"## Summary\n{summary}\n\n"
        f"## Reasons\n{reason_text}\n\n"
        f"## Requested Action\n- Update GRACE artifacts and reslice packets if needed.\n",
        encoding="utf-8",
    )
    record = DecisionRecord(
        decision_id=decision_id,
        feature_id=feature_id,
        source_packet_id=packet_id,
        summary=summary,
        reasons=reasons,
        decision_path=str(decision_path),
    ).to_dict()
    return upsert_record("decisions", "decisions", "decision_id", record)


def record_wave_review(
    *,
    feature_id: str,
    wave_id: str,
    architect_packet_id: str,
    verdict: WaveVerdict,
    reasons: list[str],
) -> dict[str, Any]:
    review_dir = FEATURES_DIR / feature_id / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"{wave_id}.architect-review.md"
    reason_text = "\n".join(f"- {reason}" for reason in reasons) or "- none"
    review_path.write_text(
        f"# Wave Architect Review: {wave_id}\n\n"
        f"## Architect Packet\n{architect_packet_id}\n\n"
        f"## Verdict\n{verdict.value}\n\n"
        f"## Reasons\n{reason_text}\n\n"
        f"## Scope\n- wave acceptance including UX, visual proof, and business fit\n",
        encoding="utf-8",
    )
    record = WaveReviewRecord(
        feature_id=feature_id,
        wave_id=wave_id,
        architect_packet_id=architect_packet_id,
        verdict=verdict,
        reasons=reasons,
        review_path=str(review_path),
    ).to_dict()
    upsert_record("wave_reviews", "wave_reviews", "architect_packet_id", record)
    update_record(
        "packets",
        "packets",
        "packet_id",
        architect_packet_id,
        {
            "last_wave_review": record,
        },
    )
    return record
