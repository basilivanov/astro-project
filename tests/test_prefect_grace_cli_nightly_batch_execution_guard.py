# ############################################################################
# AI_HEADER: test_prefect_grace_cli_nightly_batch_execution_guard
# ROLE: CLI contract tests for nightly batch execution guard command.
# ############################################################################

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_nightly_batch_execute_dry_run_default():
    """Test that nightly-batch-execute defaults to dry-run."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "2",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)  # May fail if no packets available
    output = json.loads(result.stdout)
    assert output["command"] == "nightly-batch-execute"
    assert "result" in output
    assert output["result"]["dry_run"] is True
    assert output["result"]["mode"] == "nightly_batch_execution_guard"


def test_nightly_batch_execute_missing_live_approval():
    """Test that missing live approval blocks execution when packets are available."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--execute",
            "--max-packets", "1",
            "--json",
        ],
        capture_output=True,
        text=True,
        env={"GRACE_NIGHTLY_BATCH_EXECUTION_APPROVED": "0"},
    )

    output = json.loads(result.stdout)

    # If no packets are selected, the command succeeds (nothing to execute)
    # If packets are selected, it should fail due to missing opt-in
    if output["result"]["selected_total"] == 0:
        assert result.returncode == 0
        assert output["ok"] is True
        assert output["result"]["stop_reason"] == "no_packets_selected"
    else:
        assert result.returncode == 1
        assert output["ok"] is False
        assert output["result"]["live_opt_in_confirmed"] is False
        assert output["result"]["executed_total"] == 0
        assert output["result"]["stop_reason"] == "live_opt_in_blocked"


def test_nightly_batch_execute_lock_handling():
    """Test that lock is acquired and released."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "1",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)
    assert output["result"]["lock_acquired"] is True
    assert output["result"]["lock_released"] is True


def test_nightly_batch_execute_max_packets_limit():
    """Test that max-packets limit is respected."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "3",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)
    assert output["result"]["selected_total"] <= 3


def test_nightly_batch_execute_json_envelope():
    """Test that JSON output follows envelope format."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "1",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)

    # Check envelope structure
    assert "ok" in output
    assert "command" in output
    assert "result" in output
    assert output["command"] == "nightly-batch-execute"

    # Check result == data (envelope contract)
    assert output["result"] == output.get("data", output["result"])

    # Check result structure
    result_data = output["result"]
    assert "project_key" in result_data
    assert "mode" in result_data
    assert "dry_run" in result_data
    assert "selected_total" in result_data
    assert "executed_total" in result_data
    assert "passed_total" in result_data
    assert "blocked_total" in result_data
    assert "failed_total" in result_data
    assert "stop_reason" in result_data
    assert "lock_acquired" in result_data
    assert "lock_released" in result_data
    assert "live_agents_started" in result_data
    assert "git_mutations_count" in result_data
    assert "packet_summaries" in result_data
    assert "execution_time_seconds" in result_data


def test_nightly_batch_execute_bounded_output():
    """Test that output is bounded."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "50",  # Request many packets
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)

    # Check that lists are bounded
    result_data = output["result"]
    assert len(result_data["packet_summaries"]) <= 25
    assert len(result_data.get("warnings", [])) <= 25
    assert len(result_data.get("errors", [])) <= 25


def test_nightly_batch_execute_git_mutation_flags():
    """Test that Git mutation flags are accepted."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "1",
            "--allow-git-commit",
            "--allow-git-push",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)
    assert "result" in output


def test_nightly_batch_execute_concurrency_flag():
    """Test that concurrency flag is accepted."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "2",
            "--concurrency", "2",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)
    assert "result" in output


def test_nightly_batch_execute_timeout_flag():
    """Test that timeout flag is accepted."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "1",
            "--timeout-seconds-per-packet", "60",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)
    assert "result" in output


def test_nightly_batch_execute_max_failures_flag():
    """Test that max-failures flag is accepted."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "nightly-batch-execute",
            "--project", "/opt/astro-project/prefect_grace/project.yaml",
            "--max-packets", "5",
            "--max-failures", "2",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode in (0, 1)
    output = json.loads(result.stdout)
    assert "result" in output
