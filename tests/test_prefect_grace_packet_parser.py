from pathlib import Path

import pytest
import yaml

from prefect_grace.platform.packet_parser import compute_normalized_source_hash, parse_packet_markdown


STRICT_PACKET_MARKDOWN = """# Execution Packet: FEAT-TEST-W01-PACKET

## Slice
- packet_id: FEAT-TEST-W01-PACKET
- feature_id: FEAT-TEST
- wave_id: W01
- depends_on: MARKDOWN-DEP-W01-PACKET

## Objective
Markdown objective.

## Impacted Modules
- markdown-module

## Allowed Write Scope
- markdown/**

## Frozen Scope
- frozen/**

## Must Preserve
- Markdown preserve.

## Verification
Markdown verification.

## Expected Evidence
- markdown evidence

## Escalation Triggers
- markdown trigger
"""


def _write_packet_with_sidecar(tmp_path: Path, sidecar: dict) -> Path:
    packet_path = tmp_path / "EXECUTION_PACKET.md"
    packet_path.write_text(STRICT_PACKET_MARKDOWN, encoding="utf-8")
    packet_path.with_name("EXECUTION_PACKET.yaml").write_text(
        yaml.safe_dump(sidecar, sort_keys=False),
        encoding="utf-8",
    )
    return packet_path


def test_parse_strict_packet_success() -> None:
    content = """# Execution Packet: FEAT-GRACE-ORCHESTRATOR-MVP-W01-TEST

## Slice
- packet_id: FEAT-GRACE-ORCHESTRATOR-MVP-W01-TEST
- feature_id: FEAT-GRACE-ORCHESTRATOR-MVP
- wave_id: W01

## Objective
Test objective explanation.

## Impacted Modules
- module-a

## Allowed Write Scope
- src/core/**
- config/*.yaml

## Frozen Scope
- tests/frozen/**

## Must Preserve
- Existing backwards compatibility.

## Verification
Run pytest tests/test_core.py.

## Expected Evidence
- test results
- git diff

## Escalation Triggers
- Any test failures.
"""
    parsed = parse_packet_markdown(content, mode="strict")
    assert parsed.packet_id == "FEAT-GRACE-ORCHESTRATOR-MVP-W01-TEST"
    assert parsed.feature_id == "FEAT-GRACE-ORCHESTRATOR-MVP"
    assert parsed.wave_id == "W01"
    assert parsed.objective == "Test objective explanation."
    assert parsed.modules == ["module-a"]
    assert parsed.allowed_write_scope == ["src/core/**", "config/*.yaml"]
    assert parsed.frozen_scope == ["tests/frozen/**"]
    assert parsed.must_preserve == ["Existing backwards compatibility."]
    assert parsed.expected_evidence == ["test results", "git diff"]
    assert parsed.escalation_triggers == ["Any test failures."]
    assert parsed.source_hash != ""


def test_parse_strict_packet_failure() -> None:
    # Missing allowed_write_scope and frozen_scope
    content = """# Execution Packet: FEAT-GRACE-ORCHESTRATOR-MVP-W01-TEST

## Slice
- packet_id: FEAT-GRACE-ORCHESTRATOR-MVP-W01-TEST
- feature_id: FEAT-GRACE-ORCHESTRATOR-MVP
- wave_id: W01
"""
    with pytest.raises(ValueError, match="Strict packet validation failed"):
        parse_packet_markdown(content, mode="strict")


def test_parse_legacy_warn_mode() -> None:
    # Missing fields, but in legacy_warn mode
    content = """# Packet: FEAT-DEMO-W01-DEMO-REFACTOR-PACKET

## Summary
Dry-run a bounded refactor packet through all roles

## Wave
W01

## Role
coder

## Write Scope
- Only files listed.
"""
    parsed = parse_packet_markdown(content, mode="legacy_warn")
    assert parsed.packet_id == "FEAT-DEMO-W01-DEMO-REFACTOR-PACKET"
    assert parsed.wave_id == "W01"
    assert len(parsed.legacy_warnings) > 0


def test_source_hash_stability() -> None:
    content_base = """# Execution Packet: FEAT-TEST-W01

## Slice
- packet_id: FEAT-TEST-W01
- feature_id: FEAT-TEST
- wave_id: W01

## Objective
Validate hash stability.

## Allowed Write Scope
- src/**

## Frozen Scope
- tests/**

## Must Preserve
- nothing

## Verification
- run test

## Expected Evidence
- proof

## Escalation Triggers
- fail
"""

    content_with_evidence = (
        content_base
        + """
## Evidence
- git diff --stat
- test output text

## Reviewer Notes
- Some notes from reviewer.
"""
    )

    parsed_base = parse_packet_markdown(content_base, mode="strict")
    parsed_with_evidence = parse_packet_markdown(content_with_evidence, mode="strict")

    # Hash must be identical because only Evidence and Reviewer Notes sections were added
    assert parsed_base.source_hash == parsed_with_evidence.source_hash

    # Modifying allowed write scope must change the hash
    content_modified = content_base.replace("src/**", "src/modified/**")
    parsed_modified = parse_packet_markdown(content_modified, mode="strict")
    assert parsed_base.source_hash != parsed_modified.source_hash


def test_yaml_sidecar_overrides_markdown_fields_and_lists(tmp_path: Path) -> None:
    packet_path = _write_packet_with_sidecar(
        tmp_path,
        {
            "schema_version": 1,
            "artifact_type": "execution_packet",
            "packet_id": "FEAT-TEST-W01-PACKET",
            "feature_id": "FEAT-TEST-YAML",
            "wave_id": "W02",
            "title": "YAML title",
            "objective": "YAML objective.",
            "status": "ready_for_review",
            "phase": "PHASE-YAML",
            "depends_on": ["YAML-DEP-A", "YAML-DEP-B"],
            "modules": "yaml-module-a, yaml-module-b",
            "allowed_write_scope": ["yaml/src/**", "yaml/tests/**"],
            "frozen_scope": "backend/**\n- frontend/**",
            "must_preserve": ["YAML preserve."],
            "verification": "YAML verification text.",
            "expected_evidence": "yaml evidence a, yaml evidence b",
            "escalation_triggers": ["yaml trigger"],
        },
    )

    parsed = parse_packet_markdown(packet_path, mode="strict")

    assert parsed.packet_id == "FEAT-TEST-W01-PACKET"
    assert parsed.feature_id == "FEAT-TEST-YAML"
    assert parsed.wave_id == "W02"
    assert parsed.title == "YAML title"
    assert parsed.objective == "YAML objective."
    assert parsed.status == "ready_for_review"
    assert parsed.phase == "PHASE-YAML"
    assert parsed.depends_on == ["YAML-DEP-A", "YAML-DEP-B"]
    assert parsed.modules == ["yaml-module-a", "yaml-module-b"]
    assert parsed.allowed_write_scope == ["yaml/src/**", "yaml/tests/**"]
    assert parsed.frozen_scope == ["backend/**", "frontend/**"]
    assert parsed.must_preserve == ["YAML preserve."]
    assert parsed.verification == "YAML verification text."
    assert parsed.expected_evidence == ["yaml evidence a", "yaml evidence b"]
    assert parsed.escalation_triggers == ["yaml trigger"]


def test_yaml_sidecar_packet_id_mismatch_fails_strict(tmp_path: Path) -> None:
    packet_path = _write_packet_with_sidecar(
        tmp_path,
        {
            "schema_version": 1,
            "artifact_type": "execution_packet",
            "packet_id": "FEAT-OTHER-W01-PACKET",
        },
    )

    with pytest.raises(ValueError, match="YAML sidecar packet_id does not match markdown packet_id"):
        parse_packet_markdown(packet_path, mode="strict")


def test_invalid_yaml_sidecar_fails_strict(tmp_path: Path) -> None:
    packet_path = tmp_path / "EXECUTION_PACKET.md"
    packet_path.write_text(STRICT_PACKET_MARKDOWN, encoding="utf-8")
    packet_path.with_name("EXECUTION_PACKET.yaml").write_text(
        "schema_version: 1\nartifact_type: [execution_packet\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid YAML sidecar"):
        parse_packet_markdown(packet_path, mode="strict")
    with pytest.raises(ValueError, match="Invalid YAML sidecar"):
        parse_packet_markdown(packet_path, mode="legacy_warn")


def test_yaml_sidecar_unknown_field_fails_closed(tmp_path: Path) -> None:
    packet_path = _write_packet_with_sidecar(
        tmp_path,
        {
            "schema_version": 1,
            "artifact_type": "execution_packet",
            "packet_id": "FEAT-TEST-W01-PACKET",
            "depend_on": ["TYPO-DEP"],
        },
    )

    with pytest.raises(ValueError, match="unknown fields: depend_on"):
        parse_packet_markdown(packet_path, mode="strict")
    with pytest.raises(ValueError, match="unknown fields: depend_on"):
        parse_packet_markdown(packet_path, mode="legacy_warn")


def test_yaml_sidecar_source_hash_changes_but_markdown_only_hash_is_stable(tmp_path: Path) -> None:
    packet_path = tmp_path / "EXECUTION_PACKET.md"
    packet_path.write_text(STRICT_PACKET_MARKDOWN, encoding="utf-8")

    markdown_only = parse_packet_markdown(packet_path, mode="strict")
    raw_markdown = parse_packet_markdown(STRICT_PACKET_MARKDOWN, mode="strict")
    assert markdown_only.source_hash == raw_markdown.source_hash
    assert markdown_only.source_hash == compute_normalized_source_hash(STRICT_PACKET_MARKDOWN)

    sidecar_path = packet_path.with_name("EXECUTION_PACKET.yaml")
    sidecar_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "artifact_type": "execution_packet",
                "packet_id": "FEAT-TEST-W01-PACKET",
                "depends_on": ["DEP-A"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    sidecar_dep_a = parse_packet_markdown(packet_path, mode="strict")

    sidecar_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "artifact_type": "execution_packet",
                "packet_id": "FEAT-TEST-W01-PACKET",
                "depends_on": ["DEP-B"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    sidecar_dep_b = parse_packet_markdown(packet_path, mode="strict")

    assert sidecar_dep_a.source_hash != markdown_only.source_hash
    assert sidecar_dep_b.source_hash != markdown_only.source_hash
    assert sidecar_dep_a.source_hash != sidecar_dep_b.source_hash
