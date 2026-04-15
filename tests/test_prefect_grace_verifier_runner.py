from pathlib import Path

from prefect_grace.tasks.verifier_runner import (
    POST_TEST_REVIEW_MAP,
    _collect_artifacts,
    build_verifier_message,
    build_verifier_plan,
    validate_verifier_plan,
)


def test_build_verifier_plan_uses_profile_defaults() -> None:
    packet = {
        "execution_hints": {
            "backend_profile": "backend_quick",
            "frontend_profile": "frontend_quick",
            "observability_profile": "today-week",
            "touches_frontend": True,
            "requires_frontend_visual": True,
        }
    }
    config = {
        "verification": {
            "backend_profiles": {"backend_quick": "docker exec astro-project-backend-1 python3 scripts/pipeline.py"},
            "frontend_profiles": {"frontend_quick": "./scripts/run_e2e.sh --last-failed"},
            "observability_profiles": {"today-week": "python3 tools/post_test_review.py --profile today-week --report-format json"},
            "default_artifact_globs": ["test-results/**/*"],
        }
    }
    plan = build_verifier_plan(packet, config)
    assert [step.phase for step in plan["steps"]] == ["backend", "frontend", "observability"]
    assert plan["steps"][0].command == "docker exec astro-project-backend-1 python3 scripts/pipeline.py"
    assert plan["steps"][1].command == "./scripts/run_e2e.sh --last-failed"
    assert plan["touches_frontend"] is True
    assert plan["requires_frontend_visual"] is True
    assert plan["artifact_globs"] == ["test-results/**/*"]


def test_build_verifier_message_contains_machine_block() -> None:
    message = build_verifier_message(
        commands_run=["docker exec astro-project-backend-1 python3 scripts/pipeline.py"],
        test_verdict="passed",
        observability_verdict="clean",
        frontend_visual_verdict="not_applicable",
        evidence_paths=["/tmp/report.json"],
        blocking_issues=[],
    )
    assert "FINAL_VERIFIER_EVIDENCE_JSON" in message
    assert '"test_verdict": "passed"' in message
    assert "## Commands Run" in message


def test_post_test_review_map_covers_expected_verdicts() -> None:
    assert POST_TEST_REVIEW_MAP["PASS_CLEAN"] == "clean"
    assert POST_TEST_REVIEW_MAP["PASS_WITH_EXPECTED_DEGRADATION"] == "degraded-but-expected"
    assert POST_TEST_REVIEW_MAP["FAIL_NO_EVIDENCE"] == "no-evidence-blocker"


def test_collect_artifacts_respects_root_dir(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "proof.png"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("png", encoding="utf-8")
    evidence, visual = _collect_artifacts(["artifacts/**/*"], root_dir=tmp_path, started_at=__import__("datetime").datetime.now())
    assert str(artifact.resolve()) in evidence
    assert str(artifact.resolve()) in visual


def test_validate_verifier_plan_rejects_structured_command_text() -> None:
    packet = {
        "execution_hints": {
            "frontend_commands": ["{'required_commands': ['bad']}"],
            "touches_frontend": True,
            "requires_frontend_visual": True,
            "artifact_globs": ["artifacts/**/*"],
            "observability_commands": ["python3 tools/post_test_review.py --profile today-week --report-format json"],
        }
    }
    plan = {
        "steps": [],
        "touches_frontend": True,
        "requires_frontend_visual": True,
        "artifact_globs": ["artifacts/**/*"],
        "observability_profile": "today-week",
    }
    issues = validate_verifier_plan(packet, plan)
    assert any("structured text" in issue for issue in issues)
