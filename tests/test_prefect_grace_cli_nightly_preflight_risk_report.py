"""
CLI contract tests for nightly-preflight-risk-report command.
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest


def test_nightly_preflight_risk_report_json_envelope(tmp_path):
    """Test that nightly-preflight-risk-report returns proper JSON envelope."""
    # Create a minimal project structure
    project_root = tmp_path / "project"
    project_root.mkdir()

    packets_dir = project_root / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    state_dir = project_root / "state"
    state_dir.mkdir()

    # Create project config
    project_yaml = project_root / "prefect_grace" / "project.yaml"
    project_yaml.parent.mkdir(exist_ok=True)
    project_yaml.write_text(f"""
project_key: test-project
repo_root: {project_root}
packets_dir: prefect_grace/packets
runtime_state_root: state
""")

    # Create a valid packet
    packet_dir = packets_dir / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: FEAT-TEST-W01

status: ready
feature_id: FEAT-TEST
wave_id: W01

## Objective
Test packet

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
pytest -q

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
    packet_file.write_text(packet_content)

    # Create registry (code expects runtime_state_root/state/packet_registry.yaml)
    registry_dir = state_dir / "state"
    registry_dir.mkdir(exist_ok=True)
    registry_file = registry_dir / "packet_registry.yaml"
    registry_file.write_text("""FEAT-TEST-W01:
  packet_id: FEAT-TEST-W01
  registry_status: ready
  source_hash: sha256:abc123
""")

    # Run command
    result = subprocess.run(
        [
            sys.executable, "-m", "prefect_grace.cli",
            "nightly-preflight-risk-report",
            "--project", str(project_yaml),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)

    # Check JSON envelope structure
    assert "ok" in output
    assert "command" in output
    assert output["command"] == "nightly-preflight-risk-report"
    assert "project_key" in output
    assert output["project_key"] == "test-project"
    assert "result" in output

    # Check result == data (no nested envelope)
    result_data = output["result"]
    assert "mode" in result_data
    assert result_data["mode"] == "nightly_preflight_risk_report"
    assert "packets_total" in result_data
    assert "ready_total" in result_data
    assert "blocked_total" in result_data
    assert "accepted_total" in result_data
    assert "safe_candidates" in result_data
    assert "safe_candidates_total" in result_data
    assert "risky_candidates" in result_data
    assert "risky_candidates_total" in result_data
    assert "blocked_candidates" in result_data
    assert "blocked_candidates_total" in result_data
    assert "approval_required_candidates" in result_data
    assert "approval_required_candidates_total" in result_data
    assert "conflict_groups" in result_data
    assert "conflict_groups_total" in result_data
    assert "packet_summaries" in result_data


def test_nightly_preflight_risk_report_bounded_output(tmp_path):
    """Test that output lists are bounded with totals."""
    # Create a minimal project structure
    project_root = tmp_path / "project"
    project_root.mkdir()

    packets_dir = project_root / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    state_dir = project_root / "state"
    state_dir.mkdir()

    # Create project config
    project_yaml = project_root / "prefect_grace" / "project.yaml"
    project_yaml.parent.mkdir(exist_ok=True)
    project_yaml.write_text(f"""
project_key: test-project
repo_root: {project_root}
packets_dir: prefect_grace/packets
runtime_state_root: state
""")

    # Create multiple packets
    registry_packets = {}
    for i in range(30):
        packet_id = f"FEAT-TEST-W{i:02d}"
        packet_dir = packets_dir / packet_id
        packet_dir.mkdir()
        packet_file = packet_dir / "EXECUTION_PACKET.md"
        packet_content = f"""# Execution Packet: {packet_id}

status: ready
feature_id: FEAT-TEST
wave_id: W{i:02d}

## Objective
Test packet {i}

## Allowed Write Scope
- test{i}.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
pytest -q

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
        packet_file.write_text(packet_content)
        registry_packets[packet_id] = {
            "packet_id": packet_id,
            "registry_status": "ready",
            "source_hash": f"sha256:abc{i}",
        }

    # Create registry (code expects runtime_state_root/state/packet_registry.yaml)
    registry_dir = state_dir / "state"
    registry_dir.mkdir(exist_ok=True)
    registry_file = registry_dir / "packet_registry.yaml"
    import yaml
    registry_file.write_text(yaml.dump(registry_packets))

    # Run command
    result = subprocess.run(
        [
            sys.executable, "-m", "prefect_grace.cli",
            "nightly-preflight-risk-report",
            "--project", str(project_yaml),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)
    result_data = output["result"]

    # Check bounded output
    assert len(result_data["safe_candidates"]) <= 25
    assert len(result_data["risky_candidates"]) <= 25
    assert len(result_data["blocked_candidates"]) <= 25
    assert len(result_data["approval_required_candidates"]) <= 25
    assert len(result_data["packet_summaries"]) <= 25
    assert len(result_data["conflict_groups"]) <= 25

    # Check totals are present
    assert "safe_candidates_total" in result_data
    assert "risky_candidates_total" in result_data
    assert "blocked_candidates_total" in result_data
    assert "approval_required_candidates_total" in result_data
    assert "conflict_groups_total" in result_data


def test_nightly_preflight_risk_report_conflict_detection(tmp_path):
    """Test that file conflicts are detected."""
    # Create a minimal project structure
    project_root = tmp_path / "project"
    project_root.mkdir()

    packets_dir = project_root / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    state_dir = project_root / "state"
    state_dir.mkdir()

    # Create project config
    project_yaml = project_root / "prefect_grace" / "project.yaml"
    project_yaml.parent.mkdir(exist_ok=True)
    project_yaml.write_text(f"""
project_key: test-project
repo_root: {project_root}
packets_dir: prefect_grace/packets
runtime_state_root: state
""")

    # Create two packets with overlapping write scopes
    for packet_id in ["FEAT-A-W01", "FEAT-B-W01"]:
        packet_dir = packets_dir / packet_id
        packet_dir.mkdir()
        packet_file = packet_dir / "EXECUTION_PACKET.md"
        packet_content = f"""# Execution Packet: {packet_id}

status: ready
feature_id: {packet_id.split('-')[1]}
wave_id: W01

## Objective
Test packet

## Allowed Write Scope
- shared.py
- {packet_id.lower()}.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
pytest -q

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
        packet_file.write_text(packet_content)

    # Create registry (code expects runtime_state_root/state/packet_registry.yaml)
    registry_dir = state_dir / "state"
    registry_dir.mkdir(exist_ok=True)
    registry_file = registry_dir / "packet_registry.yaml"
    registry_file.write_text("""FEAT-A-W01:
  packet_id: FEAT-A-W01
  registry_status: ready
  source_hash: sha256:abc123
FEAT-B-W01:
  packet_id: FEAT-B-W01
  registry_status: ready
  source_hash: sha256:def456
""")

    # Run command
    result = subprocess.run(
        [
            sys.executable, "-m", "prefect_grace.cli",
            "nightly-preflight-risk-report",
            "--project", str(project_yaml),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)
    result_data = output["result"]

    # Check conflict detection
    assert result_data["conflict_groups_total"] > 0
    assert len(result_data["conflict_groups"]) > 0
    conflict_group = result_data["conflict_groups"][0]
    assert set(conflict_group["packet_ids"]) == {"FEAT-A-W01", "FEAT-B-W01"}
    assert "shared.py" in conflict_group["conflicting_paths"]


def test_nightly_preflight_risk_report_no_secrets_in_output(tmp_path):
    """Test that output does not contain secrets or large raw data."""
    # Create a minimal project structure
    project_root = tmp_path / "project"
    project_root.mkdir()

    packets_dir = project_root / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    state_dir = project_root / "state"
    state_dir.mkdir()

    # Create project config
    project_yaml = project_root / "prefect_grace" / "project.yaml"
    project_yaml.parent.mkdir(exist_ok=True)
    project_yaml.write_text(f"""
project_key: test-project
repo_root: {project_root}
packets_dir: prefect_grace/packets
runtime_state_root: state
""")

    # Create a packet
    packet_dir = packets_dir / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: FEAT-TEST-W01

status: ready
feature_id: FEAT-TEST
wave_id: W01

## Objective
Test packet

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
pytest -q

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
    packet_file.write_text(packet_content)

    # Create registry (code expects runtime_state_root/state/packet_registry.yaml)
    registry_dir = state_dir / "state"
    registry_dir.mkdir(exist_ok=True)
    registry_file = registry_dir / "packet_registry.yaml"
    registry_file.write_text("""FEAT-TEST-W01:
  packet_id: FEAT-TEST-W01
  registry_status: ready
  source_hash: sha256:abc123
""")

    # Run command
    result = subprocess.run(
        [
            sys.executable, "-m", "prefect_grace.cli",
            "nightly-preflight-risk-report",
            "--project", str(project_yaml),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)
    output_str = json.dumps(output)

    # Check no secrets or large data
    assert "password" not in output_str.lower()
    assert "secret" not in output_str.lower()
    assert "api_key" not in output_str.lower()
    assert "full_diff" not in output_str.lower()
    assert "screenshot" not in output_str.lower()

    # Check output size is reasonable (< 1MB)
    assert len(output_str) < 1024 * 1024
