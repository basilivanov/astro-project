from pathlib import Path

from prefect_grace.tasks import prefect_artifacts


def test_publish_feature_artifacts_includes_architect_planner_and_reviewer(monkeypatch) -> None:
    created: list[dict] = []

    def _fake_create_markdown_artifact(**kwargs):
        created.append(kwargs)
        return f"artifact-{len(created)}"

    monkeypatch.setattr(prefect_artifacts, "create_markdown_artifact", _fake_create_markdown_artifact)

    feature = {
        "feature_id": "FEAT-X",
        "title": "Feature X",
        "status": "planned",
        "feature_dir": "/tmp/feature-x",
    }
    packet_path = Path("/tmp/docs/feature-x/EXECUTION_PACKET.md")
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("# Execution Packet\n\n## Objective\nShip feature.\n", encoding="utf-8")

    packet_results = {
        "architect_artifact_plan": {
            "source": "agent_output",
            "parser_error": None,
        },
        "architect": {
            "packet_id": "FEAT-X-W00-ARCHITECT-FORMALIZATION",
            "returncode": 0,
            "launcher": "codex1",
            "last_message_path": "/tmp/runs/architect/last-message.md",
            "stdout_path": "/tmp/runs/architect/stdout.jsonl",
            "stderr_path": "/tmp/runs/architect/stderr.log",
        },
        "architect_artifacts": {
            "slice_id": "SLICE-FEAT-X",
            "slice_slug": "feature-x",
            "slice_dir": "/tmp/docs/feature-x",
            "architect_manifest_path": "/tmp/docs/feature-x/architect_manifest.json",
            "architect_handoff_path": "/tmp/docs/feature-x/ARCHITECT_HANDOFF.md",
            "execution_packet_path": "/tmp/docs/feature-x/EXECUTION_PACKET.md",
            "requirements_slice_path": "/tmp/docs/feature-x/requirements.slice.feature-x.xml",
            "development_plan_slice_path": "/tmp/docs/feature-x/development-plan.slice.feature-x.xml",
            "verification_matrix_slice_path": "/tmp/docs/feature-x/verification-matrix.slice.feature-x.md",
            "knowledge_graph_slice_path": "/tmp/docs/feature-x/knowledge-graph.slice.feature-x.xml",
            "manifest": {
                "slice_id": "SLICE-FEAT-X",
                "impacted_modules": ["frontend/app/page.tsx"],
                "planner_inputs": ["/tmp/docs/feature-x/ARCHITECT_HANDOFF.md"],
                "waves": [{"wave_id": "W01", "title": "Main wave", "objective": "Ship feature"}],
                "root_deltas": {"development-plan.xml": "append W01"},
            },
        },
        "planner_contract": {
            "source": "agent_output",
            "parser_error": None,
            "contract": {
                "waves": [{"wave_id": "W01", "title": "Main wave", "objective": "Ship feature"}],
                "packets": [
                    {
                        "key": "coder_main",
                        "wave_id": "W01",
                        "role": "coder",
                        "title": "Coder Main",
                        "dependencies": [],
                        "review_target_key": "",
                        "verification_profile": {},
                    },
                    {
                        "key": "verifier_main",
                        "wave_id": "W01",
                        "role": "verifier",
                        "title": "Verifier Main",
                        "dependencies": ["coder_main"],
                        "review_target_key": "",
                        "verification_profile": {
                            "execution": {
                                "frontend_commands": ["./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts"],
                                "observability_commands": ["python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"],
                                "artifact_globs": ["frontend/test-results/**/*"],
                            }
                        },
                    },
                ],
            },
        },
        "planner": {
            "packet_id": "FEAT-X-W00-PLANNER-SLICING",
            "returncode": 0,
            "launcher": "codex1",
            "last_message_path": "/tmp/runs/planner/last-message.md",
            "stdout_path": "/tmp/runs/planner/stdout.jsonl",
            "stderr_path": "/tmp/runs/planner/stderr.log",
        },
        "planner_materialized": {
            "wave_plan_path": "/tmp/feature-x/wave-plan.md",
            "packets": [
                {
                    "packet_id": "FEAT-X-W01-CODER-MAIN",
                    "wave_id": "W01",
                    "role": "coder",
                    "status": "ready",
                    "dependencies": [],
                },
                {
                    "packet_id": "FEAT-X-W01-VERIFIER-MAIN",
                    "wave_id": "W01",
                    "role": "verifier",
                    "status": "review",
                    "dependencies": ["FEAT-X-W01-CODER-MAIN"],
                },
            ],
        },
        "planner_validation": {
            "valid": True,
            "issues": [],
        },
        "run:FEAT-X-W01-CODER-MAIN": {
            "packet_id": "FEAT-X-W01-CODER-MAIN",
            "returncode": 0,
            "launcher": "codex1",
            "last_message_path": "/tmp/runs/coder/last-message.md",
            "stdout_path": "/tmp/runs/coder/stdout.jsonl",
            "stderr_path": "/tmp/runs/coder/stderr.log",
        },
    }
    review_route = {
        "review": {
            "packet_id": "FEAT-X-W01-REVIEWER-VERDICT",
            "feature_id": "FEAT-X",
            "wave_id": "W01",
            "grace_feature_ref": "feature:FEAT-X",
            "grace_wave_ref": "feature:FEAT-X:wave:W01",
            "grace_packet_ref": "feature:FEAT-X:wave:W01:packet:FEAT-X-W01-REVIEWER-VERDICT",
            "verdict": "accepted",
            "follow_up_action": "none",
            "review_path": "/tmp/feature-x/review.md",
            "reasons": [],
        }
    }

    artifact_ids = prefect_artifacts.publish_feature_artifacts(
        feature=feature,
        packet_results=packet_results,
        verification=None,
        review_route=review_route,
        wave_route=None,
        final_status={
            "feature": {"feature_id": "FEAT-X", "status": "pipeline_invalid", "summary": "Feature X summary"},
            "final_outcome": "blocked",
            "user_facing_status": "pipeline_invalid",
            "user_summary": "Итог: пайплайн некорректен. Планировщик не собрал контракт.",
            "next_action": "fix-packet-graph-contract",
            "failure_category": "pipeline_invalid",
            "wave_progression": [
                {"wave_id": "W01", "title": "Main wave", "status": "accepted", "required": True, "architect_gate_packet_id": "FEAT-X-W01-ARCH"},
                {"wave_id": "W02", "title": "Follow-up wave", "status": "pending", "required": True, "architect_gate_packet_id": "FEAT-X-W02-ARCH"},
            ],
            "next_wave_id": "W02",
            "all_required_waves_accepted": False,
        },
    )

    assert len(artifact_ids) == 6
    keys = {item["key"] for item in created}
    assert "grace-feature-feat-x" in keys
    assert "grace-execution-packet-feat-x" in keys
    assert "grace-architect-feat-x" in keys
    assert "grace-packet-graph-feat-x" in keys
    assert "grace-agent-outputs-feat-x" in keys
    assert "grace-review-feat-x-w01-reviewer-verdict" in keys

    architect_markdown = next(item["markdown"] for item in created if item["key"] == "grace-architect-feat-x")
    execution_packet_markdown = next(item["markdown"] for item in created if item["key"] == "grace-execution-packet-feat-x")
    planner_markdown = next(item["markdown"] for item in created if item["key"] == "grace-packet-graph-feat-x")
    agent_markdown = next(item["markdown"] for item in created if item["key"] == "grace-agent-outputs-feat-x")
    feature_markdown = next(item["markdown"] for item in created if item["key"] == "grace-feature-feat-x")
    assert "SLICE-FEAT-X" in architect_markdown
    assert "# Execution Packet" in execution_packet_markdown
    assert "Ship feature." in execution_packet_markdown
    assert "frontend/app/page.tsx" in architect_markdown
    assert "wave_count: 1" in architect_markdown
    assert "coder_main" in planner_markdown
    assert "wave_count: 1" in planner_markdown
    assert "./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts" in planner_markdown
    assert "FEAT-X-W01-CODER-MAIN" in agent_markdown
    assert "/tmp/runs/coder/stdout.jsonl" in agent_markdown
    assert "final_outcome: blocked" in feature_markdown
    assert "user_facing_status: pipeline_invalid" in feature_markdown
    assert "next_wave_id: W02" in feature_markdown
    assert "all_required_waves_accepted: False" in feature_markdown
    assert "Итог: пайплайн некорректен. Планировщик не собрал контракт." in feature_markdown
    assert "W02: pending (required)" in feature_markdown
    review_markdown = next(item["markdown"] for item in created if item["key"] == "grace-review-feat-x-w01-reviewer-verdict")
    assert "feature:FEAT-X:wave:W01:packet:FEAT-X-W01-REVIEWER-VERDICT" in review_markdown



def test_publish_packet_task_artifacts_creates_task_scoped_snapshots(monkeypatch) -> None:
    created: list[dict] = []

    def _fake_create_markdown_artifact(**kwargs):
        created.append(kwargs)
        return f"artifact-{len(created)}"

    monkeypatch.setattr(prefect_artifacts, "create_markdown_artifact", _fake_create_markdown_artifact)

    artifact_ids = prefect_artifacts.publish_packet_task_artifacts(
        verification={
            "packet_id": "FEAT-X-W01-VERIFY",
            "test_verdict": "failed",
            "observability_verdict": "clean",
            "frontend_visual_verdict": "insufficient",
            "commands_run": ["pytest tests/test_x.py"],
            "evidence_paths": ["frontend/test-results/x/trace.zip"],
            "blocking_issues": ["visual proof missing"],
            "verification_path": "/tmp/verification.md",
        },
        review_route={
            "review": {
                "packet_id": "FEAT-X-W01-REVIEW",
                "feature_id": "FEAT-X",
                "wave_id": "W01",
                "verdict": "rework_required",
                "follow_up_action": "localized_rework",
                "review_path": "/tmp/review.md",
                "reasons": ["needs visual proof"],
            },
            "rework": {"packet_id": "FEAT-X-W01-REWORK"},
        },
    )

    assert artifact_ids == ["artifact-1", "artifact-2"]
    keys = {item["key"] for item in created}
    assert "grace-task-verification-feat-x-w01-verify" in keys
    assert "grace-task-review-feat-x-w01-review" in keys
    verification_markdown = next(item["markdown"] for item in created if item["key"] == "grace-task-verification-feat-x-w01-verify")
    review_markdown = next(item["markdown"] for item in created if item["key"] == "grace-task-review-feat-x-w01-review")
    assert "frontend/test-results/x/trace.zip" in verification_markdown
    assert "needs visual proof" in review_markdown


def test_feature_artifact_renders_awaiting_commit_and_candidate_files(monkeypatch) -> None:
    created: list[dict] = []

    def _fake_create_markdown_artifact(**kwargs):
        created.append(kwargs)
        return f"artifact-{len(created)}"

    monkeypatch.setattr(prefect_artifacts, "create_markdown_artifact", _fake_create_markdown_artifact)

    artifact_ids = prefect_artifacts.publish_feature_artifacts(
        feature={
            "feature_id": "FEAT-COMMIT",
            "title": "Feature Commit",
            "status": "awaiting_commit",
            "feature_dir": "/tmp/feature-commit",
        },
        packet_results={},
        verification=None,
        review_route=None,
        wave_route=None,
        final_status={
            "feature": {
                "feature_id": "FEAT-COMMIT",
                "status": "awaiting_commit",
                "summary": "Итог: принято, ждёт коммита. Дальше: закоммитить изменения.",
            },
            "final_outcome": "awaiting_commit",
            "user_facing_status": "awaiting_commit",
            "user_summary": "Итог: принято, ждёт коммита. Дальше: закоммитить изменения.",
            "next_action": "commit-feature-changes",
            "commit_status": "awaiting_commit",
            "candidate_commit_files": ["prefect_grace/flows/feature_pipeline.py", "tests/test_prefect_grace_prefect_artifacts.py"],
            "wave_progression": [
                {"wave_id": "W01", "title": "Main wave", "status": "accepted", "required": True, "architect_gate_packet_id": "FEAT-COMMIT-W01-ARCH"},
            ],
            "next_wave_id": "",
            "all_required_waves_accepted": True,
        },
    )

    assert artifact_ids == ["artifact-1"]
    markdown = created[0]["markdown"]
    assert "final_outcome: awaiting_commit" in markdown
    assert "user_facing_status: awaiting_commit" in markdown
    assert "Дальше: закоммитить изменения." in markdown
    assert "## Candidate Commit Files" in markdown
    assert "prefect_grace/flows/feature_pipeline.py" in markdown
    assert "W01: accepted (required)" in markdown
