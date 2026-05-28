import json
import subprocess
import sys
from pathlib import Path


def test_cli_validate_project() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "validate-project", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["project_key"] == "astro-project"
    assert data["command"] == "validate-project"
    assert data["result"] == data["data"]
    assert "project" in data["data"]
    assert "verification_profiles" in data["data"]
    assert data["warnings"] == []
    assert data["errors"] == []


def test_cli_scan_packets() -> None:
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "scan-packets",
            "--mode",
            "legacy_warn",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["project_key"] == "astro-project"
    assert data["command"] == "scan-packets"
    assert data["result"] == data["data"]
    assert "packets" in data["data"]
    # Check that we scanned some packets (there are many in the directory)
    assert len(data["data"]["packets"]) > 0


def test_cli_validate_packet() -> None:
    packet_path = (
        Path(__file__).resolve().parents[1]
        / "prefect_grace"
        / "packets"
        / "FEAT-GRACE-ORCHESTRATOR-MVP1"
        / "EXECUTION_PACKET.md"
    )
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "validate-packet",
            str(packet_path),
            "--strict",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["command"] == "validate-packet"
    assert data["result"] == data["data"]
    assert data["data"]["packet_id"] == "FEAT-GRACE-ORCHESTRATOR-MVP1-W01-PROJECT-ADAPTER-CONTRACTS"
    assert data["data"]["feature_id"] == "FEAT-GRACE-ORCHESTRATOR-MVP1"
    assert data["data"]["wave_id"] == "W01"
    assert "allowed_write_scope" in data["data"]
    assert "frozen_scope" in data["data"]


def test_cli_sync_packets_dry_run() -> None:
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "sync-packets",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["project_key"] == "astro-project"
    assert data["command"] == "sync-packets"
    assert data["result"] == data["data"]
    assert data["data"]["dry_run"] is True
    assert data["data"]["registry_updates"] == 0
    assert data["data"]["packets_total"] > 0
    assert "ready" in data["data"]
    assert "accepted" in data["data"]
    assert "blocked" in data["data"]


def test_cli_bootstrap_backlog_dry_run_contract() -> None:
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "bootstrap-backlog",
            "--project",
            "prefect_grace/project.yaml",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["project_key"] == "astro-project"
    assert data["command"] == "bootstrap-backlog"
    assert data["result"] == data["data"]
    assert data["data"]["dry_run"] is True
    assert data["data"]["apply_count"] == 0
    assert len(data["data"]["candidates"]) > 0
    candidate = data["data"]["candidates"][0]
    assert "packet_id" in candidate
    assert "source_path" in candidate
    assert "source_hash" in candidate
    assert "current_registry_status" in candidate
    assert "inferred_status" in candidate
    assert "inference_reason" in candidate
    assert "evidence_paths" in candidate
    assert "planned_action" in candidate
    assert "warnings" in candidate


def test_cli_registry_apply_smoke_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "registry-apply-smoke", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--state-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--json" in result.stdout


def test_cli_registry_bootstrap_apply_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "registry-bootstrap-apply", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--project-config" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--apply" in result.stdout
    assert "--json" in result.stdout


def test_cli_legacy_queue_dashboard_contract() -> None:
    queue = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "queue", "--help"],
        capture_output=True,
        text=True,
    )
    assert queue.returncode == 0
    assert "--limit" in queue.stdout

    dashboard = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "dashboard", "--help"],
        capture_output=True,
        text=True,
    )
    assert dashboard.returncode == 0
    assert "--json" in dashboard.stdout

    import prefect_grace.cli as cli

    assert hasattr(cli, "_cmd_queue")
    assert hasattr(cli, "_cmd_dashboard")


def test_cli_e2e_registry_seeded_smoke_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-e2e-registry-seeded-smoke", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--json" in result.stdout
    assert "--execute-agent" not in result.stdout
    assert "--no-dry-run" not in result.stdout


def test_cli_submit_packets_contract() -> None:
    """Verify submit-packets CLI exposes runner selection and dry-run defaults."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "submit-packets", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--project-config" in result.stdout
    assert "--runner" in result.stdout
    assert "--execute" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--limit" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--timeout-seconds" in result.stdout
    assert "--continue-on-error" in result.stdout
    assert "--json" in result.stdout


def test_cli_run_nightly_dry_run_contract() -> None:
    """Verify run-nightly exposes dry-run planning and fail-closed execute guard."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-nightly", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--until-blocked" in result.stdout
    assert "--execute" in result.stdout
    assert "--json" in result.stdout


def test_cli_prefect_e2e_live_smoke_contract() -> None:
    """Verify run-prefect-e2e-live-smoke CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-prefect-e2e-live-smoke", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project-config" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--no-dry-run" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--allow-live-agent-smoke" in result.stdout
    assert "--json" in result.stdout


def test_cli_prefect_e2e_batch_smoke_contract() -> None:
    """Verify run-prefect-e2e-batch-smoke CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-prefect-e2e-batch-smoke", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project-config" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--batch-size" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--json" in result.stdout


def test_cli_prefect_e2e_real_dry_run_smoke_contract() -> None:
    """Verify run-prefect-e2e-real-dry-run-smoke CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-prefect-e2e-real-dry-run-smoke", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project-config" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--timeout-seconds" in result.stdout
    assert "--poll-interval-seconds" in result.stdout
    assert "--no-wait" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--json" in result.stdout
    assert "--offline-fake-submitter" not in result.stdout


def test_cli_live_opt_in_single_scratch_packet_contract() -> None:
    """Verify run-live-opt-in-single-scratch-packet CLI follows fail-closed contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-live-opt-in-single-scratch-packet", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--i-understand-live-agent" in result.stdout
    assert "--timeout-seconds" in result.stdout
    assert "--json" in result.stdout
    assert "--offline-fake-submitter" not in result.stdout


def test_check_scope_cli_contract() -> None:
    """Verify check-scope CLI follows contract."""
    # Test that command exists and has required args
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "check-scope", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--packet" in result.stdout
    assert "--changed-file" in result.stdout
    assert "--json" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--changed-files-file" in result.stdout


def test_worktree_create_cli_contract() -> None:
    """Verify worktree-create CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-create", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--json" in result.stdout


def test_worktree_status_cli_contract() -> None:
    """Verify worktree-status CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-status", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--json" in result.stdout


def test_worktree_cleanup_cli_contract() -> None:
    """Verify worktree-cleanup CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-cleanup", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--keep-on-failure" in result.stdout
    assert "--json" in result.stdout


def test_worktree_scope_check_cli_contract() -> None:
    """Verify worktree-scope-check CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-scope-check", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--packet" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--keep-on-failure" in result.stdout
    assert "--json" in result.stdout


def test_run_worktree_scope_flow_cli_contract() -> None:
    """Verify run-worktree-scope-flow CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-worktree-scope-flow", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--packet" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--keep-on-failure" in result.stdout
    assert "--json" in result.stdout


def test_list_executors_cli_contract() -> None:
    """Verify list-executors CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "list-executors", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--json" in result.stdout


def test_select_executor_cli_contract() -> None:
    """Verify select-executor CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "select-executor", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--role" in result.stdout
    assert "--requested-executor" in result.stdout
    assert "--json" in result.stdout


def test_validate_evidence_contract_cli_contract() -> None:
    """Verify validate-evidence-contract CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "validate-evidence-contract", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "packet_path" in result.stdout
    assert "--json" in result.stdout


def test_validate_evidence_manifest_cli_contract() -> None:
    """Verify validate-evidence-manifest CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "validate-evidence-manifest", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "manifest_path" in result.stdout
    assert "--packet" in result.stdout
    assert "--artifact-root" in result.stdout
    assert "--json" in result.stdout


def test_git_mutation_gate_cli_contract() -> None:
    """Verify git-mutation-gate CLI exposes independent guarded mutation flags."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "git-mutation-gate", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--packet" in result.stdout
    assert "--worktree-path" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--apply" in result.stdout
    assert "--commit" in result.stdout
    assert "--push" in result.stdout
    assert "--merge" in result.stdout
    assert "--i-understand-merge" in result.stdout
    assert "--json" in result.stdout


def test_run_e2e_packet_flow_cli_contract() -> None:
    """Verify run-e2e-packet-flow CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-e2e-packet-flow", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project-root" in result.stdout
    assert "--packet" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--fake-verifier-output" in result.stdout
    assert "--fake-reviewer-output" in result.stdout
    assert "--json" in result.stdout


def test_cli_nightly_preflight_risk_report_contract() -> None:
    """Verify nightly-preflight-risk-report CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "nightly-preflight-risk-report", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--json" in result.stdout


def test_cli_nightly_select_batch_contract() -> None:
    """Verify nightly-select-batch CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "nightly-select-batch", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--preflight-report" in result.stdout
    assert "--max-packets" in result.stdout
    assert "--max-cost" in result.stdout
    assert "--allow-conflicts" in result.stdout
    assert "--allow-risky" in result.stdout
    assert "--json" in result.stdout
