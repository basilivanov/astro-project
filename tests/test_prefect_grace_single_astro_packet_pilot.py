"""Tests for single_astro_packet_pilot module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

import yaml

from prefect_grace.platform.single_astro_packet_pilot import (
    run_single_astro_packet_pilot,
    _is_low_risk_candidate,
)
from prefect_grace.tasks.prefect_submitter import MANAGED_PACKET_DEPLOYMENT_NAME


@dataclass
class FakeSubmitResult:
    """Fake submission result."""
    ok: bool
    records: list[dict]


SAFE_PACKET_ID = "FEAT-ASTRO-SAFE-PILOT-W01-NARROW"


def _packet_markdown(packet_id: str = SAFE_PACKET_ID, allowed_scope: str = "backend/utils/helper.py") -> str:
    return f"""# Execution Packet: {packet_id}

## Objective
Exercise one narrow Astro packet through the single Astro pilot.

## Slice
- packet_id: `{packet_id}`
- feature_id: `FEAT-ASTRO-SAFE-PILOT`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- {allowed_scope}

## Frozen Scope
- frontend/**
- docker-compose*.yml

## Must Preserve
- No Git mutation.

## Verification
Run targeted pytest only.

## Expected Evidence
- Targeted pytest output.

## Escalation Triggers
- Scope violation.
"""


def _project_with_registry(
    tmp_path: Path,
    *,
    packet_id: str = SAFE_PACKET_ID,
    allowed_scope: str = "backend/utils/helper.py",
    registry_extra: dict | None = None,
):
    repo_root = tmp_path / "repo"
    packet_dir = repo_root / "prefect_grace" / "packets" / packet_id
    packet_dir.mkdir(parents=True)
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(_packet_markdown(packet_id, allowed_scope), encoding="utf-8")

    project_yaml = tmp_path / "project.yaml"
    state_root = tmp_path / "state-root"
    worktree_root = tmp_path / "worktrees"
    packet_root = tmp_path / "packet-root"
    (state_root / "state").mkdir(parents=True)
    worktree_root.mkdir()
    packet_root.mkdir()
    project_yaml.write_text(
        "\n".join(
            [
                "project_key: test-project",
                f"repo_root: {repo_root}",
                "packets_dir: prefect_grace/packets",
                f"runtime_state_root: {state_root}",
                f"artifact_root: {state_root / 'artifacts'}",
                f"worktree_root: {worktree_root}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    record = {
        "packet_id": packet_id,
        "feature_id": "FEAT-ASTRO-SAFE-PILOT",
        "wave_id": "W01",
        "path": str(packet_path.relative_to(repo_root)),
        "registry_status": "ready",
        "source_hash": "sha256:test",
        **(registry_extra or {}),
    }
    registry_path = state_root / "state" / "packet_registry.yaml"
    registry_path.write_text(yaml.safe_dump({packet_id: record}), encoding="utf-8")
    return project_yaml, state_root, worktree_root, packet_root


def test_is_low_risk_candidate_accepts_narrow_scope():
    """Low-risk check accepts packet with narrow scope."""
    packet = {
        "packet_id": "TEST-PACKET-001",
        "status": "ready",
        "allowed_write_scope": [
            "/opt/astro-project/backend/utils/helper.py",
            "/opt/astro-project/tests/test_helper.py",
        ],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is True
    assert reason is None


def test_is_low_risk_candidate_rejects_not_ready():
    """Low-risk check rejects packet not in ready status."""
    packet = {
        "packet_id": "TEST-PACKET-002",
        "status": "blocked",
        "allowed_write_scope": ["/opt/astro-project/backend/utils/helper.py"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "not ready" in reason


def test_is_low_risk_candidate_rejects_no_scope():
    """Low-risk check rejects packet with no allowed scope."""
    packet = {
        "packet_id": "TEST-PACKET-003",
        "status": "ready",
        "allowed_write_scope": [],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "no allowed_write_scope" in reason


def test_is_low_risk_candidate_rejects_broad_scope():
    """Low-risk check rejects packet with too many paths."""
    packet = {
        "packet_id": "TEST-PACKET-004",
        "status": "ready",
        "allowed_write_scope": [f"/opt/astro-project/backend/file{i}.py" for i in range(25)],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "broad scope" in reason


def test_is_low_risk_candidate_rejects_backend_wildcard():
    """Low-risk check rejects packet with backend/** scope."""
    packet = {
        "packet_id": "TEST-PACKET-005",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/backend/**"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "broad backend scope" in reason


def test_is_low_risk_candidate_rejects_frontend_wildcard():
    """Low-risk check rejects packet with frontend/** scope."""
    packet = {
        "packet_id": "TEST-PACKET-006",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/frontend/**"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "broad frontend scope" in reason


def test_is_low_risk_candidate_rejects_pipeline_modification():
    """Low-risk check rejects packet modifying pipeline.py."""
    packet = {
        "packet_id": "TEST-PACKET-007",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/scripts/pipeline.py"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "pipeline.py" in reason


def test_is_low_risk_candidate_rejects_docker_compose():
    """Low-risk check rejects packet modifying docker-compose."""
    packet = {
        "packet_id": "TEST-PACKET-008",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/docker-compose.yml"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "Docker compose" in reason


def test_dry_run_selects_low_risk_packet(tmp_path):
    """Real dry-run loads the temp registry without monkeypatching registry helpers."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(tmp_path)

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
    )

    assert result.ok is True
    assert result.selected_packet_id == SAFE_PACKET_ID
    assert result.submit_plan["packets_planned"] == [SAFE_PACKET_ID]
    assert result.submit_plan["records"][0]["runner_kind"] == "managed"
    assert result.registry_before["records_included"] is False
    assert result.registry_before["selected_packet"]["packet_id"] == SAFE_PACKET_ID
    assert SAFE_PACKET_ID not in result.registry_before
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert not any(e["code"] == "REGISTRY_LOAD_FAILED" for e in result.errors)


def test_missing_approval_blocks_execution(tmp_path):
    """Missing approval blocks live execution."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(tmp_path)

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=False,  # Missing acknowledgment
    )

    assert result.ok is False
    assert result.opt_in_confirmed is False
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert any(e["code"] == "LIVE_AGENT_NOT_ACKNOWLEDGED" for e in result.errors)


def test_explicit_packet_not_found(tmp_path):
    """Explicit packet ID not in registry returns error."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(tmp_path)

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
        packet_id="MISSING-PACKET",
    )

    assert result.ok is False
    assert result.selected_packet_id == "MISSING-PACKET"
    assert any(e["code"] == "PACKET_NOT_FOUND" for e in result.errors)


def test_explicit_packet_not_low_risk(tmp_path):
    """Explicit packet ID that is not low-risk returns error."""
    packet_id = "HIGH-RISK-PACKET"
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(
        tmp_path,
        packet_id=packet_id,
        allowed_scope="/opt/astro-project/backend/**",
    )

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
        packet_id=packet_id,
    )

    assert result.ok is False
    assert result.selected_packet_id == packet_id
    assert any(e["code"] == "PACKET_NOT_LOW_RISK" for e in result.errors)


def test_no_low_risk_candidates(tmp_path):
    """No low-risk candidates returns error."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(
        tmp_path,
        packet_id="HIGH-RISK-1",
        allowed_scope="/opt/astro-project/backend/**",
    )

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
    )

    assert result.ok is False
    assert result.selected_packet_id is None
    assert any(e["code"] == "NO_LOW_RISK_CANDIDATE" for e in result.errors)


def test_existing_blocked_review_rejected(tmp_path):
    """A packet with existing blocked review metadata is not selected."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(
        tmp_path,
        registry_extra={"latest_review_status": "rework_required"},
    )

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
        packet_id=SAFE_PACKET_ID,
    )

    assert result.ok is False
    assert any(e["code"] == "PACKET_NOT_LOW_RISK" for e in result.errors)


def test_injected_live_success_uses_managed_submission_dataclass_record(tmp_path):
    """Injected live execution submits exactly one selected packet and reads dataclass records."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(tmp_path)
    submitter_calls = []

    def submitter(**kwargs):
        submitter_calls.append(kwargs)
        assert kwargs["parameters"]["packet_id"] == SAFE_PACKET_ID
        assert kwargs["parameters"]["dry_run"] is False
        assert kwargs["parameters"]["execute_agent"] is True
        return {
            "flow_run_id": "astro-flow-001",
            "flow_run_name": "packet:astro-flow",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "grace-live",
            "url": "http://prefect.local/flow-runs/astro-flow-001",
        }

    def status_reader(**kwargs):
        assert kwargs["flow_run_id"] == "astro-flow-001"
        return {
            "ok": True,
            "domain_status": "accepted",
            "scope_verdict": "passed",
            "live_agents_started": 1,
            "changed_files": ["backend/utils/helper.py"],
            "poll_events": [{"status": "completed"}],
        }

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-astro-packet",
        submitter=submitter,
        status_reader=status_reader,
    )

    assert result.ok is True
    assert result.selected_packet_id == SAFE_PACKET_ID
    assert result.prefect_runs_created == 1
    assert result.live_agents_started == 1
    assert result.flow_run_id == "astro-flow-001"
    assert result.submit_plan["records"][0]["runner_kind"] == "managed"
    assert len(submitter_calls) == 1


def test_injected_scope_blocked_fails_closed_not_executor_failure(tmp_path):
    """Scope violation is reported as scope_blocked and not as executor failure."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(tmp_path)

    def submitter(**kwargs):
        return {
            "flow_run_id": "astro-flow-scope",
            "flow_run_name": "packet:astro-flow-scope",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
        }

    def status_reader(**kwargs):
        return {
            "ok": False,
            "domain_status": "scope_blocked",
            "scope_verdict": "blocked",
            "live_agents_started": 1,
            "changed_files": ["frontend/app.tsx"],
            "errors": [{"code": "SCOPE_BLOCKED", "message": "frontend write"}],
        }

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-astro-packet",
        submitter=submitter,
        status_reader=status_reader,
    )

    error_codes = {error["code"] for error in result.errors}
    assert result.ok is False
    assert result.domain_status == "scope_blocked"
    assert result.scope_verdict == "blocked"
    assert "SCOPE_BLOCKED" in error_codes
    assert "ASTRO_CHANGED_FILES_OUTSIDE_ALLOWED_SCOPE" in error_codes
    assert "EXECUTOR_FAILED" not in error_codes


def test_missing_status_evidence_fails_closed(tmp_path):
    """Missing final domain/scope evidence blocks the live pilot."""
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(tmp_path)

    def submitter(**kwargs):
        return {
            "flow_run_id": "astro-flow-missing-evidence",
            "flow_run_name": "packet:astro-flow-missing-evidence",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
        }

    def status_reader(**kwargs):
        return {
            "ok": False,
            "changed_files": [],
            "errors": [{"code": "FLOW_RUN_EVIDENCE_INCOMPLETE", "message": "missing domain/scope evidence"}],
        }

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-astro-packet",
        submitter=submitter,
        status_reader=status_reader,
    )

    assert result.ok is False
    assert result.prefect_runs_created == 1
    assert any(error["code"] == "FLOW_RUN_EVIDENCE_INCOMPLETE" for error in result.errors)


def test_dry_run_does_not_mutate_git_state(tmp_path):
    """Dry-run planning does not commit, push, merge, or alter Git status."""
    before = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=True).stdout
    project_yaml, state_root, worktree_root, packet_root = _project_with_registry(tmp_path)

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
    )

    after = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=True).stdout
    assert result.ok is True
    assert after == before
