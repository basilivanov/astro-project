from pathlib import Path

from prefect_grace.tasks import state_store
from prefect_grace.flows.feature_pipeline import feature_pipeline


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
