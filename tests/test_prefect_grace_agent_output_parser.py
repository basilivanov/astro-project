from prefect_grace.tasks.agent_output_parser import (
    parse_reviewer_message,
    parse_verifier_message,
    parse_wave_gate_message,
    resolve_reviewer_decision,
    resolve_verifier_result,
    resolve_wave_decision,
)


def test_parse_reviewer_message_from_json_markers() -> None:
    text = """
Verdict
accepted

FINAL_PACKET_DECISION_JSON
{"packet_verdict":"rework_required","follow_up_action":"localized_rework","reasons":["Missing logs","No trace id"]}
END_FINAL_PACKET_DECISION_JSON
"""
    parsed = parse_reviewer_message(text)
    assert parsed["packet_verdict"] == "rework_required"
    assert parsed["follow_up_action"] == "localized_rework"
    assert parsed["reasons"] == ["Missing logs", "No trace id"]


def test_parse_reviewer_message_from_sections() -> None:
    text = """
## Verdict
accepted

## Acceptance Check
- scoped correctly

## Blockers
- none

## Follow-up Action
none
"""
    parsed = parse_reviewer_message(text)
    assert parsed["packet_verdict"] == "accepted"
    assert parsed["follow_up_action"] == "none"
    assert parsed["reasons"] == []


def test_parse_wave_gate_message_from_json_markers() -> None:
    text = """
FINAL_WAVE_DECISION_JSON
{"wave_verdict":"rework_required","reasons":["Frontend visual proof is insufficient"]}
END_FINAL_WAVE_DECISION_JSON
"""
    parsed = parse_wave_gate_message(text)
    assert parsed["wave_verdict"] == "rework_required"
    assert parsed["reasons"] == ["Frontend visual proof is insufficient"]


def test_parse_wave_gate_message_from_sections() -> None:
    text = """
## Wave Verdict
accepted

## Business Fit
- ok

## UX / Visual Review
- ok

## Required Rework
- none
"""
    parsed = parse_wave_gate_message(text)
    assert parsed["wave_verdict"] == "accepted"
    assert parsed["reasons"] == []


def test_parse_verifier_message_from_json_markers() -> None:
    text = """
FINAL_VERIFIER_EVIDENCE_JSON
{"test_verdict":"passed","observability_verdict":"clean","frontend_visual_verdict":"sufficient","commands_run":["./scripts/run_e2e.sh e2e/visual.spec.ts"],"evidence_paths":["frontend/artifacts/visual-proof.png"],"blocking_issues":[]}
END_FINAL_VERIFIER_EVIDENCE_JSON
"""
    parsed = parse_verifier_message(text)
    assert parsed["test_verdict"] == "passed"
    assert parsed["observability_verdict"] == "clean"
    assert parsed["frontend_visual_verdict"] == "sufficient"
    assert parsed["commands_run"] == ["./scripts/run_e2e.sh e2e/visual.spec.ts"]
    assert parsed["evidence_paths"] == ["frontend/artifacts/visual-proof.png"]
    assert parsed["blocking_issues"] == []


def test_parse_verifier_message_from_sections() -> None:
    text = """
## Commands Run
- docker exec astro-project-backend-1 python3 scripts/pipeline.py

## Test Verdict
failed

## Evidence Reviewed
- trace_id: abc123

## Observability Verdict
no-evidence-blocker

## Frontend Visual Verdict
not_applicable

## Blocking Issues
- No digest generated
"""
    parsed = parse_verifier_message(text)
    assert parsed["test_verdict"] == "failed"
    assert parsed["observability_verdict"] == "no-evidence-blocker"
    assert parsed["frontend_visual_verdict"] == "not_applicable"
    assert parsed["commands_run"] == ["docker exec astro-project-backend-1 python3 scripts/pipeline.py"]
    assert parsed["evidence_paths"] == ["trace_id: abc123"]
    assert parsed["blocking_issues"] == ["No digest generated"]


def test_resolve_reviewer_decision_uses_fallback_when_message_missing() -> None:
    decision = resolve_reviewer_decision(
        {"last_message_path": "/tmp/does-not-exist", "stdout_path": "/tmp/does-not-exist"},
        fallback_verdict="accepted",
        fallback_reasons=["manual fallback"],
    )
    assert decision["packet_verdict"] == "accepted"
    assert decision["source"] == "fallback"
    assert decision["reasons"] == ["manual fallback"]


def test_resolve_wave_decision_uses_fallback_when_message_missing() -> None:
    decision = resolve_wave_decision(
        {"last_message_path": "/tmp/does-not-exist", "stdout_path": "/tmp/does-not-exist"},
        fallback_verdict="blocked",
        fallback_reasons=["manual fallback"],
    )
    assert decision["wave_verdict"] == "blocked"
    assert decision["source"] == "fallback"
    assert decision["reasons"] == ["manual fallback"]


def test_resolve_verifier_result_uses_fallback_when_message_missing() -> None:
    decision = resolve_verifier_result(
        {"last_message_path": "/tmp/does-not-exist", "stdout_path": "/tmp/does-not-exist"},
        fallback_test_verdict="passed",
        fallback_observability_verdict="clean",
        fallback_frontend_visual_verdict="not_applicable",
        fallback_blocking_issues=["manual fallback"],
    )
    assert decision["test_verdict"] == "passed"
    assert decision["observability_verdict"] == "clean"
    assert decision["frontend_visual_verdict"] == "not_applicable"
    assert decision["source"] == "fallback"
    assert decision["blocking_issues"] == ["manual fallback"]


def test_resolve_reviewer_decision_reads_last_message(tmp_path) -> None:
    last_message = tmp_path / "reviewer.md"
    last_message.write_text(
        "\n".join(
            [
                "## Verdict",
                "rework_required",
                "",
                "## Blockers",
                "- Missing trace id",
                "",
                "## Follow-up Action",
                "localized_rework",
            ]
        ),
        encoding="utf-8",
    )
    decision = resolve_reviewer_decision(
        {"last_message_path": str(last_message), "stdout_path": None},
        prefer_agent_output=True,
    )
    assert decision["packet_verdict"] == "rework_required"
    assert decision["reasons"] == ["Missing trace id"]
    assert decision["source"] == "agent_output"


def test_resolve_wave_decision_reads_last_message(tmp_path) -> None:
    last_message = tmp_path / "architect.md"
    last_message.write_text(
        "\n".join(
            [
                "## Wave Verdict",
                "rework_required",
                "",
                "## Required Rework",
                "- Frontend visual proof is insufficient",
            ]
        ),
        encoding="utf-8",
    )
    decision = resolve_wave_decision(
        {"last_message_path": str(last_message), "stdout_path": None},
        prefer_agent_output=True,
    )
    assert decision["wave_verdict"] == "rework_required"
    assert decision["reasons"] == ["Frontend visual proof is insufficient"]
    assert decision["source"] == "agent_output"


def test_resolve_verifier_result_reads_last_message(tmp_path) -> None:
    last_message = tmp_path / "verifier.md"
    last_message.write_text(
        "\n".join(
            [
                "## Commands Run",
                "- ./scripts/run_e2e.sh e2e/visual-proof.spec.ts",
                "",
                "## Test Verdict",
                "passed",
                "",
                "## Evidence Reviewed",
                "- frontend/artifacts/visual-proof.png",
                "",
                "## Observability Verdict",
                "clean",
                "",
                "## Frontend Visual Verdict",
                "sufficient",
                "",
                "## Blocking Issues",
                "- none",
            ]
        ),
        encoding="utf-8",
    )
    decision = resolve_verifier_result(
        {"last_message_path": str(last_message), "stdout_path": None},
        prefer_agent_output=True,
    )
    assert decision["test_verdict"] == "passed"
    assert decision["observability_verdict"] == "clean"
    assert decision["frontend_visual_verdict"] == "sufficient"
    assert decision["evidence_paths"] == ["frontend/artifacts/visual-proof.png"]
    assert decision["source"] == "agent_output"
