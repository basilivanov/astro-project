from pathlib import Path

from prefect_grace.platform.controller_backlog_bootstrap import build_backlog_bootstrap_plan
from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.state_store import PacketRegistryStore


class MockProjectAdapter:
    def __init__(self, repo_root: Path, packets_dir: str, runtime_state_root: Path):
        self.project_key = "test-project"
        self.repo_root = str(repo_root)
        self.packets_dir = packets_dir
        self.runtime_state_root = str(runtime_state_root)


def _write_strict_packet(
    packets_dir: Path,
    feature_id: str,
    packet_id: str,
    *,
    status: str = "ready",
    depends_on: list[str] | None = None,
) -> Path:
    packet_dir = packets_dir / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    dependency_line = ""
    if depends_on:
        dependency_line = f"- depends_on: `{', '.join(depends_on)}`\n"
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(
        f"""# Execution Packet: {packet_id}

## Objective
Test packet.

## Slice
- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `{status}`
{dependency_line}
## Allowed Write Scope
- prefect_grace/platform/example.py

## Frozen Scope
- backend/**

## Must Preserve
- Source packet files are immutable.

## Verification
pytest

## Expected Evidence
- test output

## Escalation Triggers
- missing evidence
""",
        encoding="utf-8",
    )
    return packet_path


def test_bootstrap_dry_run_infers_accepted_from_summary_without_writing(tmp_path: Path) -> None:
    packets_dir = tmp_path / "packets"
    state_root = tmp_path / "runtime"
    packet_path = _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")
    (packet_path.parent / "SUMMARY.md").write_text(
        """# Current Packet State

packet_id: FEAT-ONE-W01-PACKET
current_status: accepted
latest_review: null
latest_evidence: null
""",
        encoding="utf-8",
    )

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    plan = build_backlog_bootstrap_plan(project, dry_run=True)

    assert plan.errors == []
    assert plan.apply_count == 0
    assert len(plan.candidates) == 1
    candidate = plan.candidates[0]
    assert candidate.inferred_status == "accepted"
    assert candidate.planned_action == "create"
    assert candidate.evidence_paths == ["packets/FEAT-ONE/SUMMARY.md"]
    assert not (state_root / "state" / "packet_registry.yaml").exists()


def test_bootstrap_apply_writes_only_temp_runtime_registry(tmp_path: Path) -> None:
    packets_dir = tmp_path / "packets"
    state_root = tmp_path / "runtime"
    p1 = _write_strict_packet(packets_dir, "FEAT-BASE", "FEAT-BASE-W01-PACKET")
    p2 = _write_strict_packet(
        packets_dir,
        "FEAT-DEPENDENT",
        "FEAT-DEPENDENT-W01-PACKET",
        depends_on=["FEAT-BASE-W01-PACKET"],
    )
    (p1.parent / "REVIEWS").mkdir()
    (p1.parent / "REVIEWS" / "review-0001.md").write_text(
        """# Review

verdict: ACCEPTED
""",
        encoding="utf-8",
    )
    before_p1 = p1.read_text(encoding="utf-8")
    before_p2 = p2.read_text(encoding="utf-8")

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    plan = build_backlog_bootstrap_plan(project, dry_run=False)

    assert plan.errors == []
    assert plan.apply_count == 2
    registry = PacketRegistryStore(state_root / "state")
    assert registry.load_packet("FEAT-BASE-W01-PACKET")["registry_status"] == "accepted"
    assert registry.load_packet("FEAT-DEPENDENT-W01-PACKET")["registry_status"] == "ready"
    assert p1.read_text(encoding="utf-8") == before_p1
    assert p2.read_text(encoding="utf-8") == before_p2


def test_bootstrap_does_not_treat_nested_passed_as_packet_acceptance(tmp_path: Path) -> None:
    packets_dir = tmp_path / "packets"
    state_root = tmp_path / "runtime"
    packet_path = _write_strict_packet(packets_dir, "FEAT-NESTED", "FEAT-NESTED-W01-PACKET")
    evidence_dir = packet_path.parent / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "evidence_manifest.json").write_text(
        """{
  "packet_id": "FEAT-NESTED-W01-PACKET",
  "commands": [
    {"name": "pytest", "status": "passed"}
  ]
}
""",
        encoding="utf-8",
    )

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    plan = build_backlog_bootstrap_plan(project, dry_run=True)

    candidate = plan.candidates[0]
    assert candidate.inferred_status == "ready"
    assert candidate.inference_reason == "strict_source_ready_no_terminal_artifact_evidence"


def test_bootstrap_does_not_accept_source_status_without_artifact_evidence(tmp_path: Path) -> None:
    packets_dir = tmp_path / "packets"
    state_root = tmp_path / "runtime"
    _write_strict_packet(
        packets_dir,
        "FEAT-SOURCE-ONLY",
        "FEAT-SOURCE-ONLY-W01-PACKET",
        status="accepted",
    )

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    plan = build_backlog_bootstrap_plan(project, dry_run=True)

    assert plan.errors == []
    assert plan.candidates[0].inferred_status == "ready"
    assert plan.candidates[0].inferred_status != "accepted"
    assert plan.candidates[0].inference_reason == "strict_source_ready_no_terminal_artifact_evidence"


def test_bootstrap_preserves_existing_accepted_registry_when_evidence_is_missing(tmp_path: Path) -> None:
    packets_dir = tmp_path / "packets"
    state_root = tmp_path / "runtime"
    packet_path = _write_strict_packet(packets_dir, "FEAT-EXISTING", "FEAT-EXISTING-W01-PACKET")

    registry = PacketRegistryStore(state_root / "state")
    registry.upsert_packet(
        {
            "packet_id": "FEAT-EXISTING-W01-PACKET",
            "source_hash": parse_packet_markdown(packet_path).source_hash,
            "registry_status": "accepted",
        }
    )

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    plan = build_backlog_bootstrap_plan(project, dry_run=True)

    candidate = plan.candidates[0]
    assert candidate.current_registry_status == "accepted"
    assert candidate.inferred_status == "accepted"
    assert candidate.inference_reason == "existing_terminal_registry_source_hash_unchanged"
    assert candidate.planned_action == "noop"


def test_bootstrap_conflicting_terminal_evidence_waits(tmp_path: Path) -> None:
    packets_dir = tmp_path / "packets"
    state_root = tmp_path / "runtime"
    packet_path = _write_strict_packet(packets_dir, "FEAT-CONFLICT", "FEAT-CONFLICT-W01-PACKET")
    (packet_path.parent / "SUMMARY.md").write_text(
        "current_status: accepted\n",
        encoding="utf-8",
    )
    (packet_path.parent / "REVIEWS").mkdir()
    (packet_path.parent / "REVIEWS" / "review-0001.md").write_text(
        "verdict: BLOCKED\n",
        encoding="utf-8",
    )

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    plan = build_backlog_bootstrap_plan(project, dry_run=True)

    candidate = plan.candidates[0]
    assert candidate.inferred_status == "waiting_for_dependencies"
    assert candidate.inference_reason == "conflicting_artifact_evidence"
    assert any("Conflicting terminal bootstrap evidence" in warning for warning in candidate.warnings)


def test_bootstrap_parses_real_attempt_summary_markdown(tmp_path: Path) -> None:
    packets_dir = tmp_path / "packets"
    state_root = tmp_path / "runtime"
    packet_path = _write_strict_packet(packets_dir, "FEAT-REAL-SUMMARY", "FEAT-REAL-SUMMARY-W01-PACKET")
    evidence_dir = packet_path.parent / "EVIDENCE" / "attempt-0002"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "SUMMARY.md").write_text(
        """# Verification Summary — Attempt 0002

**Packet:** FEAT-REAL-SUMMARY-W01-PACKET
**Status:** ✅ ACCEPTED

## Verdict

ACCEPTED
""",
        encoding="utf-8",
    )

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    plan = build_backlog_bootstrap_plan(project, dry_run=True)

    candidate = plan.candidates[0]
    assert candidate.inferred_status == "accepted"
    assert candidate.inference_reason == "attempt_summary:packets/FEAT-REAL-SUMMARY/EVIDENCE/attempt-0002/SUMMARY.md"
