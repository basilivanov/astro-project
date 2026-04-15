from pathlib import Path

from prefect_grace.tasks import state_store
from prefect_grace.flows.feature_pipeline import feature_pipeline, _normalize_reviewer_decision_for_pipeline
from prefect_grace.tasks import prefect_artifacts


def test_feature_pipeline_executes_multiple_waves_and_rework(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = Path("/opt/astro-project/prefect_grace/packets") / "FEAT-MULTI-WAVE"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-MULTI-WAVE",
        title="Multi wave feature",
        summary="Exercise planner-driven multi-wave execution and reviewer rework",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="accepted",
        wave_verdict="accepted",
        verifier_observability_profile="today-week",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Backend slice", "exit_conditions": ["accepted"]},
                {"wave_id": "W02", "title": "Wave 2", "objective": "Frontend slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {
                    "key": "coder_backend",
                    "wave_id": "W01",
                    "title": "Backend Slice",
                    "role": "coder",
                    "reasoning": "high",
                    "summary": "Implement backend slice",
                    "dependencies": [],
                },
                {
                    "key": "verifier_backend",
                    "wave_id": "W01",
                    "title": "Verify Backend Slice",
                    "role": "verifier",
                    "reasoning": "high",
                    "summary": "Verify backend slice",
                    "dependencies": ["coder_backend"],
                },
                {
                    "key": "reviewer_backend",
                    "wave_id": "W01",
                    "title": "Review Backend Slice",
                    "role": "reviewer",
                    "reasoning": "xhigh",
                    "summary": "Review backend slice",
                    "dependencies": ["coder_backend", "verifier_backend"],
                    "review_target_key": "coder_backend",
                },
                {
                    "key": "architect_backend",
                    "wave_id": "W01",
                    "title": "Architect Gate Backend",
                    "role": "architect",
                    "reasoning": "xhigh",
                    "summary": "Accept backend wave",
                    "dependencies": ["reviewer_backend"],
                },
                {
                    "key": "coder_frontend",
                    "wave_id": "W02",
                    "title": "Frontend Slice",
                    "role": "coder",
                    "reasoning": "high",
                    "summary": "Implement frontend slice",
                    "dependencies": ["architect_backend"],
                },
                {
                    "key": "verifier_frontend",
                    "wave_id": "W02",
                    "title": "Verify Frontend Slice",
                    "role": "verifier",
                    "reasoning": "high",
                    "summary": "Verify frontend slice",
                    "dependencies": ["coder_frontend"],
                },
                {
                    "key": "reviewer_frontend",
                    "wave_id": "W02",
                    "title": "Review Frontend Slice",
                    "role": "reviewer",
                    "reasoning": "xhigh",
                    "summary": "Review frontend slice",
                    "dependencies": ["coder_frontend", "verifier_frontend"],
                    "review_target_key": "coder_frontend",
                },
                {
                    "key": "architect_frontend",
                    "wave_id": "W02",
                    "title": "Architect Gate Frontend",
                    "role": "architect",
                    "reasoning": "xhigh",
                    "summary": "Accept frontend wave",
                    "dependencies": ["reviewer_frontend"],
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "accepted"
    assert len(result["wave_routes"]) == 2
    assert len(result["review_routes"]) == 2
    assert len(result["verification_records"]) == 2
    assert "run:FEAT-MULTI-WAVE-W02-FRONTEND-SLICE" in result["runs"]


def test_feature_pipeline_auto_executes_rework_bundle(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = Path("/opt/astro-project/prefect_grace/packets") / "FEAT-REWORK-LOOP"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-REWORK-LOOP",
        title="Rework loop feature",
        summary="Exercise auto-created rework, verifier, and reviewer loop",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict_script=["rework_required", "accepted"],
        review_reasons_script=[["Fix boundary condition"], []],
        wave_verdict_script=["accepted"],
        verifier_observability_profile="today-week",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {
                    "key": "coder_main",
                    "wave_id": "W01",
                    "title": "Main Slice",
                    "role": "coder",
                    "reasoning": "high",
                    "summary": "Implement slice",
                    "dependencies": [],
                },
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify Slice",
                    "role": "verifier",
                    "reasoning": "high",
                    "summary": "Verify slice",
                    "dependencies": ["coder_main"],
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review Slice",
                    "role": "reviewer",
                    "reasoning": "xhigh",
                    "summary": "Review slice",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
                {
                    "key": "architect_main",
                    "wave_id": "W01",
                    "title": "Architect Gate",
                    "role": "architect",
                    "reasoning": "xhigh",
                    "summary": "Accept wave",
                    "dependencies": ["reviewer_main"],
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "accepted"
    assert len(result["review_routes"]) == 2
    assert any("REWORK" in key for key in result["runs"])


def test_pipeline_normalizes_evidence_only_blocked_review_to_rework() -> None:
    decision = {
        "packet_verdict": "blocked",
        "follow_up_action": "none",
        "reasons": [
            "Required frontend visual evidence is missing or insufficient for the UI change",
            "Today post-test observability verdict is no-evidence-blocker due to missing canonical logs",
        ],
        "source": "agent_output",
    }

    normalized = _normalize_reviewer_decision_for_pipeline(decision)

    assert normalized["packet_verdict"] == "rework_required"
    assert normalized["follow_up_action"] == "localized_rework"
    assert normalized["source"] == "pipeline_normalized_rework"


def test_feature_pipeline_stops_repeated_observability_rework_loop(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = Path("/opt/astro-project/prefect_grace/packets") / "FEAT-OBS-REWORK-STOP"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-OBS-REWORK-STOP",
        title="Repeated observability rework stop",
        summary="Stop infinite localized rework when canonical observability evidence is still missing",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict_script=["rework_required", "rework_required"],
        review_reasons_script=[
            ["Today post-test observability verdict is no-evidence-blocker due to missing canonical logs"],
            ["Today post-test observability verdict is no-evidence-blocker due to missing canonical logs"],
        ],
        wave_verdict_script=["accepted"],
        verifier_observability_profile="today-week",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {
                    "key": "coder_main",
                    "wave_id": "W01",
                    "title": "Main Slice",
                    "role": "coder",
                    "reasoning": "high",
                    "summary": "Implement slice",
                    "dependencies": [],
                },
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify Slice",
                    "role": "verifier",
                    "reasoning": "high",
                    "summary": "Verify slice",
                    "dependencies": ["coder_main"],
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review Slice",
                    "role": "reviewer",
                    "reasoning": "xhigh",
                    "summary": "Review slice",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
                {
                    "key": "architect_main",
                    "wave_id": "W01",
                    "title": "Architect Gate",
                    "role": "architect",
                    "reasoning": "xhigh",
                    "summary": "Accept wave",
                    "dependencies": ["reviewer_main"],
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "pipeline_invalid"
    assert result["final_status"]["next_action"].startswith("inspect-review-blockers:")
    assert len(result["review_routes"]) == 2
    assert result["review_routes"][-1]["reviewer_verdict"] == "blocked"
    assert not any("REWORK-REWORK-REWORK" in key for key in result["runs"])


def test_feature_pipeline_publishes_intermediate_architect_and_planner_artifacts(tmp_path: Path, monkeypatch) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    created: list[str] = []

    def _fake_publish_feature_artifacts(**kwargs):
        created.append(str(kwargs["feature"].get("feature_id")))
        return ["artifact-1"]

    monkeypatch.setattr(prefect_artifacts, "publish_feature_artifacts", _fake_publish_feature_artifacts)
    monkeypatch.setattr("prefect_grace.flows.feature_pipeline.publish_feature_artifacts", _fake_publish_feature_artifacts)

    result = feature_pipeline(
        feature_id="FEAT-ARTIFACT-PUBLISH",
        title="Artifact publish feature",
        summary="Exercise intermediate architect/planner artifact publishing",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="accepted",
        wave_verdict="accepted",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {
                    "key": "coder_main",
                    "wave_id": "W01",
                    "title": "Main Slice",
                    "role": "coder",
                    "reasoning": "high",
                    "summary": "Implement slice",
                    "dependencies": [],
                },
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify Slice",
                    "role": "verifier",
                    "reasoning": "medium",
                    "summary": "Verify slice",
                    "dependencies": ["coder_main"],
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review Slice",
                    "role": "reviewer",
                    "reasoning": "xhigh",
                    "summary": "Review slice",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
                {
                    "key": "architect_main",
                    "wave_id": "W01",
                    "title": "Architect Gate",
                    "role": "architect",
                    "reasoning": "xhigh",
                    "summary": "Accept wave",
                    "dependencies": ["reviewer_main"],
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "accepted"
    assert len(created) >= 4


def test_feature_pipeline_can_skip_live_w00_agents_for_fast_iteration(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"

    result = feature_pipeline(
        feature_id="FEAT-SKIP-W00",
        title="Skip W00 feature",
        summary="Skip live architect/planner execution and continue with fallback/materialized contracts",
        dry_run=True,
        prefer_agent_output=False,
        run_architect=False,
        run_planner=False,
        reviewer_verdict="accepted",
        wave_verdict="accepted",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {
                    "key": "coder_main",
                    "wave_id": "W01",
                    "title": "Main Slice",
                    "role": "coder",
                    "reasoning": "high",
                    "summary": "Implement slice",
                    "dependencies": [],
                },
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify Slice",
                    "role": "verifier",
                    "reasoning": "medium",
                    "summary": "Verify slice",
                    "dependencies": ["coder_main"],
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review Slice",
                    "role": "reviewer",
                    "reasoning": "xhigh",
                    "summary": "Review slice",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
                {
                    "key": "architect_main",
                    "wave_id": "W01",
                    "title": "Architect Gate",
                    "role": "architect",
                    "reasoning": "xhigh",
                    "summary": "Accept wave",
                    "dependencies": ["reviewer_main"],
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "accepted"
    assert result["runs"]["architect"]["launcher"] == "skipped"
    assert result["runs"]["planner"]["launcher"] == "skipped"
