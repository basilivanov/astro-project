from pathlib import Path

import pytest
from prefect_grace.platform.packet_parser import parse_packet_markdown


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
