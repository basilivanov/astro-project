"""
CLI contract tests for nightly batch selection command.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_cli_nightly_select_batch_json_envelope():
    """Test nightly-select-batch command returns proper JSON envelope."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    # Verify JSON envelope structure
    assert "ok" in data
    assert "command" in data
    assert data["command"] == "nightly-select-batch"
    assert "project_key" in data
    assert "result" in data
    assert "data" in data
    assert data["result"] == data["data"]  # Must preserve result == data
    assert "warnings" in data
    assert "errors" in data

    # Verify result structure
    result = data["result"]
    assert "mode" in result
    assert result["mode"] == "nightly_batch_selection"
    assert "selected_packets" in result
    assert "selected_total" in result
    assert "excluded_packets" in result
    assert "excluded_total" in result
    assert "batch_limits" in result
    assert "conflict_groups_detected" in result
    assert "estimated_total_cost" in result
    assert "stop_reason" in result
    assert "dry_run" in result
    assert result["dry_run"] is True  # Always dry-run

    # Verify batch limits structure
    assert "max_packets" in result["batch_limits"]
    assert "max_cost" in result["batch_limits"]
    assert "allow_conflicts" in result["batch_limits"]
    assert "allow_risky" in result["batch_limits"]


def test_cli_nightly_select_batch_max_packets():
    """Test nightly-select-batch respects max-packets limit."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--max-packets",
            "5",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]
    assert result["batch_limits"]["max_packets"] == 5
    # Selected total should not exceed max_packets
    assert result["selected_total"] <= 5


def test_cli_nightly_select_batch_max_cost():
    """Test nightly-select-batch respects max-cost limit."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--max-cost",
            "targeted",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]
    assert result["batch_limits"]["max_cost"] == "targeted"


def test_cli_nightly_select_batch_allow_conflicts():
    """Test nightly-select-batch with allow-conflicts flag."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--allow-conflicts",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]
    assert result["batch_limits"]["allow_conflicts"] is True


def test_cli_nightly_select_batch_allow_risky():
    """Test nightly-select-batch with allow-risky flag."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--allow-risky",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]
    assert result["batch_limits"]["allow_risky"] is True


def test_cli_nightly_select_batch_excluded_packets_structure():
    """Test excluded packets have proper structure."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]

    # Check excluded packets structure
    for excluded in result["excluded_packets"]:
        assert "packet_id" in excluded
        assert "reason" in excluded
        assert "details" in excluded
        # Verify reason is one of the expected values
        valid_reasons = [
            "dependency_blocked",
            "risk_blocked",
            "approval_required",
            "file_conflict",
            "test_cost_too_high",
            "batch_limit_reached",
            "unknown_invalid_metadata",
        ]
        assert excluded["reason"] in valid_reasons


def test_cli_nightly_select_batch_bounded_output():
    """Test output lists are bounded to prevent unbounded responses."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--max-packets",
            "50",  # Request more than MAX_ITEMS
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]

    # Lists should be bounded to MAX_ITEMS (25)
    assert len(result["selected_packets"]) <= 25
    assert len(result["excluded_packets"]) <= 25
    assert len(result["warnings"]) <= 25
    assert len(result["errors"]) <= 25


def test_cli_nightly_select_batch_no_execution():
    """Test nightly-select-batch performs no execution or mutation."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]

    # Verify dry_run flag is always True
    assert result["dry_run"] is True

    # Command should succeed without any execution side effects
    # This is a read-only operation


def test_cli_nightly_select_batch_stop_reason():
    """Test stop_reason is populated."""
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())

    assert data["ok"] is True
    result = data["result"]

    # stop_reason should be one of the expected values
    valid_stop_reasons = [
        "no_safe_candidates",
        "batch_limit_reached",
        "all_safe_candidates_selected",
    ]
    assert result["stop_reason"] in valid_stop_reasons


def test_cli_nightly_select_batch_deterministic():
    """Test nightly-select-batch produces deterministic results."""
    # Run twice and compare
    res1 = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--max-packets",
            "5",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data1 = json.loads(res1.stdout.strip())

    res2 = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-select-batch",
            "--max-packets",
            "5",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data2 = json.loads(res2.stdout.strip())

    # Results should be identical
    assert data1["result"]["selected_packets"] == data2["result"]["selected_packets"]
    assert data1["result"]["selected_total"] == data2["result"]["selected_total"]
    assert data1["result"]["stop_reason"] == data2["result"]["stop_reason"]
