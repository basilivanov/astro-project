from pathlib import Path
from types import SimpleNamespace

import pytest

from prefect_grace.tasks import state_store
from prefect_grace.flows.feature_pipeline import (
    _collect_candidate_commit_files,
    _normalize_reviewer_decision_for_pipeline,
    feature_pipeline,
    route_reviewer_verdict_task,
)
from prefect_grace.models import ReviewVerdict
from prefect_grace.tasks import architect_artifacts, codex_launcher, feature_bootstrap, prefect_artifacts, review_router, verification_router
from prefect_grace.tasks.state_store import find_record


@pytest.fixture(autouse=True)
def _isolate_grace_paths(tmp_path: Path, monkeypatch):
    packets_dir = tmp_path / "packets"
    docs_dir = tmp_path / "docs"
    monkeypatch.setattr(feature_bootstrap, "FEATURES_DIR", packets_dir)
    monkeypatch.setattr(review_router, "FEATURES_DIR", packets_dir)
    monkeypatch.setattr(verification_router, "FEATURES_DIR", packets_dir)
    monkeypatch.setattr(codex_launcher, "FEATURES_DIR", packets_dir)
    monkeypatch.setattr(architect_artifacts, "FEATURES_DIR", packets_dir)
    monkeypatch.setattr(architect_artifacts, "DOCS_DIR", docs_dir)
    return packets_dir


def test_feature_pipeline_executes_multiple_waves_and_rework(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-MULTI-WAVE"
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
        verifier_observability_profile="read-only",
        rework_routing_policy="auto_bundle",
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

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    assert result["final_status"]["final_outcome"] == "awaiting_commit"
    assert result["final_status"]["user_facing_status"] == "awaiting_commit"
    assert result["final_status"]["user_summary"] == "Итог: принято, ждёт коммита. Дальше: закоммитить изменения."
    assert result["final_status"]["next_action"] == "commit-feature-changes"
    assert any(str(item).endswith("/FEAT-MULTI-WAVE/wave-plan.md") for item in result["final_status"]["candidate_commit_files"])
    assert len(result["wave_routes"]) == 2
    assert len(result["review_routes"]) == 2
    assert len(result["verification_records"]) == 2
    assert "run:FEAT-MULTI-WAVE-W02-FRONTEND-SLICE" in result["runs"]


def test_feature_pipeline_auto_executes_rework_bundle(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-REWORK-LOOP"
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
        verifier_observability_profile="read-only",
        rework_routing_policy="auto_bundle",
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

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    assert len(result["review_routes"]) == 2
    assert any("REWORK" in key for key in result["runs"])
    rework_reviewer = next(
        packet
        for packet in state_store.load_state("packets").get("packets", [])
        if packet.get("feature_id") == "FEAT-REWORK-LOOP"
        and packet.get("role") == "reviewer"
        and packet.get("parent_packet_id")
        and "REVIEWER-REWORK" in packet.get("packet_id", "")
    )
    assert rework_reviewer["review_target_packet_id"].endswith("REWORK-MAIN-SLICE")


def test_feature_pipeline_acceptance_with_commit_hash_remains_final(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-COMMITTED"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-COMMITTED",
        title="Committed feature",
        summary="Accepted feature with an existing commit marker",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="accepted",
        wave_verdict="accepted",
        commit_hash="abcdef1234567890",
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
    assert result["final_status"]["final_outcome"] == "accepted"
    assert result["final_status"]["user_facing_status"] == "accepted"
    assert result["final_status"]["commit_status"] == "committed"
    assert result["final_status"]["commit_hash"] == "abcdef1234567890"


def test_collect_candidate_commit_files_merges_scope_changed_files_and_evidence() -> None:
    files = _collect_candidate_commit_files(
        feature_id="FEAT-CANDIDATES",
        feature={
            "feature_id": "FEAT-CANDIDATES",
            "business_context": {"brief_path": "/opt/astro-project/docs/feature/brief.md"},
        },
        packet_results={
            "planner_materialized": {
                "wave_plan_path": "/opt/astro-project/prefect_grace/packets/FEAT-CANDIDATES/wave-plan.md",
                "packets": [
                    {
                        "packet_id": "FEAT-CANDIDATES-W01-CODER",
                        "write_scope": [
                            "frontend/app/page.tsx",
                            "backend/app/main.py",
                        ],
                        "changed_files": [
                            "frontend/components/today/card.tsx",
                            "backend/app/main.py",
                        ],
                        "packet_path": "/opt/astro-project/prefect_grace/packets/FEAT-CANDIDATES/packets/FEAT-CANDIDATES-W01-CODER.md",
                    }
                ],
            }
        },
        verification_records=[
            {
                "packet_id": "FEAT-CANDIDATES-W01-VERIFY",
                "evidence_paths": [
                    "artifacts/feature-proof.png",
                    "trace_id: abc123",
                    "/opt/astro-project/frontend/test/app/home-page.test.tsx",
                ],
            }
        ],
        review_routes=[
            {
                "review": {
                    "packet_id": "FEAT-CANDIDATES-W01-REVIEW",
                    "review_path": "/opt/astro-project/prefect_grace/packets/FEAT-CANDIDATES/reviews/FEAT-CANDIDATES-W01-REVIEW.md",
                }
            }
        ],
        wave_routes=[],
    )

    assert files == [
        "docs/feature/brief.md",
        "prefect_grace/packets/FEAT-CANDIDATES/wave-plan.md",
        "frontend/app/page.tsx",
        "backend/app/main.py",
        "frontend/components/today/card.tsx",
        "prefect_grace/packets/FEAT-CANDIDATES/packets/FEAT-CANDIDATES-W01-CODER.md",
        "artifacts/feature-proof.png",
        "frontend/test/app/home-page.test.tsx",
        "prefect_grace/packets/FEAT-CANDIDATES/reviews/FEAT-CANDIDATES-W01-REVIEW.md",
    ]


def test_feature_pipeline_architect_first_rework_default(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-ARCH-FIRST-REWORK"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-ARCH-FIRST-REWORK",
        title="Architect-first rework feature",
        summary="Reviewer rework should default to a single architect-bounded direct coder packet",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict_script=["rework_required", "accepted"],
        review_reasons_script=[["Fix boundary condition"], []],
        wave_verdict_script=["accepted"],
        verifier_observability_profile="read-only",
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

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    assert len(result["review_routes"]) == 2
    first_review = result["review_routes"][0]
    assert first_review["route_classification"] == "self_resolvable_rework"
    assert isinstance(first_review["rework"], dict)
    assert first_review["rework"]["role"] == "coder"
    assert first_review["rework"]["title"] == "Main Slice"
    assert first_review["rework_routing_policy"] == "architect_first"
    assert first_review["rework"]["rework_mode"] == "light_resume"
    assert first_review["rework"]["execution_hints"]["resume_strategy"] == "packet_parent"
    assert first_review["rework"]["packet_id"].endswith("MAIN-SLICE")
    assert first_review["light_resume_stage"] is True
    architect_rework_packets = [
        packet
        for packet in state_store.load_state("packets").get("packets", [])
        if packet.get("feature_id") == "FEAT-ARCH-FIRST-REWORK"
        and packet.get("role") == "architect"
        and str(packet.get("parent_packet_id") or "").endswith("MAIN-SLICE")
        and "ARCHITECT-REWORK" in str(packet.get("packet_id") or "")
    ]
    assert len(architect_rework_packets) == 1
    resumed_packet = find_record("packets", "packets", "packet_id", "FEAT-ARCH-FIRST-REWORK-W01-MAIN-SLICE")
    assert resumed_packet["execution_hints"]["light_resume_stage"] is True
    assert resumed_packet["light_resume_attempt"] == 1
    rework_reviewers = [
        packet
        for packet in state_store.load_state("packets").get("packets", [])
        if packet.get("feature_id") == "FEAT-ARCH-FIRST-REWORK"
        and packet.get("role") == "reviewer"
        and packet.get("parent_packet_id") == "FEAT-ARCH-FIRST-REWORK-W01-MAIN-SLICE"
        and "REVIEWER-REWORK" in str(packet.get("packet_id") or "")
    ]
    assert len(rework_reviewers) == 1


def test_feature_pipeline_downgrades_broad_light_resume_to_bounded_fresh(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-LIGHT-RESUME-DOWNGRADE"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-LIGHT-RESUME-DOWNGRADE",
        title="Light resume downgrade feature",
        summary="Broad blockers should not resume the existing packet in place",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict_script=["rework_required", "accepted"],
        review_reasons_script=[
            ["Fix boundary condition", "Update targeted unit expectation", "Refresh evidence note"],
            ["Fresh packet accepted"],
        ],
        wave_verdict_script=["accepted"],
        verifier_observability_profile="read-only",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {"key": "coder_main", "wave_id": "W01", "title": "Main Slice", "role": "coder", "summary": "Implement slice"},
                {"key": "verifier_main", "wave_id": "W01", "title": "Verify Slice", "role": "verifier", "summary": "Verify slice", "dependencies": ["coder_main"]},
                {"key": "reviewer_main", "wave_id": "W01", "title": "Review Slice", "role": "reviewer", "summary": "Review slice", "dependencies": ["coder_main", "verifier_main"], "review_target_key": "coder_main"},
                {"key": "architect_main", "wave_id": "W01", "title": "Architect Gate", "role": "architect", "summary": "Accept wave", "dependencies": ["reviewer_main"]},
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    first_review = result["review_routes"][0]
    assert first_review["route_classification"] == "self_resolvable_rework"
    assert first_review["rework"]["packet_id"] != "FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE"
    assert first_review["rework"]["rework_mode"] == "bounded_fresh"
    assert first_review["rework"]["requested_rework_mode"] == "bounded_fresh"


def test_feature_pipeline_blocks_second_light_resume_cycle(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-LIGHT-RESUME-LOOP-STOP"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-LIGHT-RESUME-LOOP-STOP",
        title="Light resume loop stop",
        summary="Do not allow repeated in-place light resume on the same packet",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict_script=["rework_required", "rework_required", "accepted"],
        review_reasons_script=[["Fix one small typo"], ["Fix another small typo"], ["Fresh packet accepted"]],
        wave_verdict_script=["accepted"],
        verifier_observability_profile="read-only",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {"key": "coder_main", "wave_id": "W01", "title": "Main Slice", "role": "coder", "summary": "Implement slice"},
                {"key": "verifier_main", "wave_id": "W01", "title": "Verify Slice", "role": "verifier", "summary": "Verify slice", "dependencies": ["coder_main"]},
                {"key": "reviewer_main", "wave_id": "W01", "title": "Review Slice", "role": "reviewer", "summary": "Review slice", "dependencies": ["coder_main", "verifier_main"], "review_target_key": "coder_main"},
                {"key": "architect_main", "wave_id": "W01", "title": "Architect Gate", "role": "architect", "summary": "Accept wave", "dependencies": ["reviewer_main"]},
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    assert len(result["review_routes"]) == 3
    assert result["review_routes"][0]["light_resume_stage"] is True
    second_rework = result["review_routes"][1]["rework"]
    assert second_rework["rework_mode"] == "bounded_fresh"
    assert second_rework["requested_rework_mode"] == "light_resume"


def test_feature_pipeline_accepts_small_fix_alias_for_packet_level_light_resume(tmp_path: Path, monkeypatch) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-SMALL-FIX-ALIAS"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    def _fake_launch(packet_id: str, dry_run: bool, timeout_seconds: int, logger):
        packet = find_record("packets", "packets", "packet_id", packet_id)
        run_dir = tmp_path / "runs" / packet_id
        run_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = run_dir / "stdout.jsonl"
        last_message_path = run_dir / "last-message.md"
        stdout_path.write_text("", encoding="utf-8")
        if str(packet.get("role") or "") == "architect" and "ARCHITECT-REWORK" in packet_id:
            last_message_path.write_text(
                "\n".join(
                    [
                        "FINAL_DIRECT_REWORK_PACKET_JSON",
                        '{"route_classification":"self_resolvable_rework","rework_mode":"small_fix","title":"Small Fix Main Slice","summary":"Fix one narrow typo"}',
                        "END_FINAL_DIRECT_REWORK_PACKET_JSON",
                    ]
                ),
                encoding="utf-8",
            )
        else:
            last_message_path.write_text("DRY RUN\n", encoding="utf-8")
        return {
            "packet_id": packet_id,
            "returncode": 0,
            "launcher": "fake",
            "stdout_path": str(stdout_path),
            "last_message_path": str(last_message_path),
        }

    monkeypatch.setattr("prefect_grace.flows.feature_pipeline.launch_codex_for_packet", _fake_launch)

    result = feature_pipeline(
        feature_id="FEAT-SMALL-FIX-ALIAS",
        title="Small fix alias feature",
        summary="Architect direct rework small_fix should safely map to packet-level light resume",
        dry_run=True,
        prefer_agent_output=True,
        reviewer_verdict_script=["rework_required", "accepted"],
        review_reasons_script=[["Fix one narrow typo"], []],
        wave_verdict_script=["accepted"],
        verifier_observability_profile="read-only",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {"key": "coder_main", "wave_id": "W01", "title": "Main Slice", "role": "coder", "summary": "Implement slice"},
                {"key": "verifier_main", "wave_id": "W01", "title": "Verify Slice", "role": "verifier", "summary": "Verify slice", "dependencies": ["coder_main"]},
                {"key": "reviewer_main", "wave_id": "W01", "title": "Review Slice", "role": "reviewer", "summary": "Review slice", "dependencies": ["coder_main", "verifier_main"], "review_target_key": "coder_main"},
                {"key": "architect_main", "wave_id": "W01", "title": "Architect Gate", "role": "architect", "summary": "Accept wave", "dependencies": ["reviewer_main"]},
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    first_review = result["review_routes"][0]
    assert first_review["light_resume_stage"] is True
    assert first_review["rework"]["packet_id"] == "FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE"
    assert first_review["rework"]["requested_rework_mode"] == "light_resume"
    assert first_review["rework"]["rework_mode"] == "light_resume"


def test_feature_pipeline_rework_requires_planner_escalation(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-PLANNER-REWORK"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-PLANNER-REWORK",
        title="Planner rework feature",
        summary="Reviewer rework should escalate to architect/planner only when decomposition must change",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="rework_required",
        review_reasons=["Packet graph must be resliced because the blocker spans multiple waves"],
        wave_verdict="accepted",
        verifier_observability_profile="read-only",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {"key": "coder_main", "wave_id": "W01", "title": "Main Slice", "role": "coder", "summary": "Implement slice"},
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify Slice",
                    "role": "verifier",
                    "summary": "Verify slice",
                    "dependencies": ["coder_main"],
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review Slice",
                    "role": "reviewer",
                    "summary": "Review slice",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
                {
                    "key": "architect_main",
                    "wave_id": "W01",
                    "title": "Architect Gate",
                    "role": "architect",
                    "summary": "Accept wave",
                    "dependencies": ["reviewer_main"],
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "architect_ready"
    assert result["final_status"]["final_outcome"] == "awaiting_architect"
    assert result["final_status"]["user_facing_status"] == "architect_ready"
    assert "нужно решение архитектора" in result["final_status"]["user_summary"]
    assert result["final_status"]["next_action"] == "architect-planner-decomposition-required"
    assert result["review_routes"][0]["route_classification"] == "requires_planner"
    assert result["review_routes"][0]["decision"]["route_classification"] == "requires_planner"


def test_feature_pipeline_rework_requires_architect_user_decision(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-USER-DECISION-REWORK"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-USER-DECISION-REWORK",
        title="User decision rework feature",
        summary="Reviewer rework should escalate only when blocker needs user/product decision",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="rework_required",
        review_reasons=["Business decision required before changing product behavior"],
        wave_verdict="accepted",
        verifier_observability_profile="read-only",
        planner_contract={
            "waves": [
                {"wave_id": "W01", "title": "Wave 1", "objective": "Single slice", "exit_conditions": ["accepted"]},
            ],
            "packets": [
                {"key": "coder_main", "wave_id": "W01", "title": "Main Slice", "role": "coder", "summary": "Implement slice"},
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify Slice",
                    "role": "verifier",
                    "summary": "Verify slice",
                    "dependencies": ["coder_main"],
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review Slice",
                    "role": "reviewer",
                    "summary": "Review slice",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
                {
                    "key": "architect_main",
                    "wave_id": "W01",
                    "title": "Architect Gate",
                    "role": "architect",
                    "summary": "Accept wave",
                    "dependencies": ["reviewer_main"],
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "architect_ready"
    assert result["final_status"]["final_outcome"] == "awaiting_architect"
    assert result["final_status"]["user_facing_status"] == "architect_ready"
    assert "нужно решение архитектора" in result["final_status"]["user_summary"]
    assert result["final_status"]["next_action"] == "architect-user-decision-required"
    assert result["review_routes"][0]["route_classification"] == "requires_user_decision"
    assert result["review_routes"][0]["decision"]["route_classification"] == "requires_user_decision"


def test_validate_planner_contract_rejects_today_week_without_wave_final_probe(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-BAD-OBS-CONTRACT"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-BAD-OBS-CONTRACT",
        title="Bad observability contract",
        summary="Reject today-week on packet-local verifier without canonical probe",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="accepted",
        wave_verdict="accepted",
        planner_contract={
            "waves": [{"wave_id": "W01", "title": "Wave 1", "objective": "Single slice"}],
            "packets": [
                {"key": "coder_main", "wave_id": "W01", "title": "Main", "role": "coder", "summary": "Do work"},
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify",
                    "role": "verifier",
                    "summary": "Verify",
                    "dependencies": ["coder_main"],
                    "verification_profile": {
                        "execution": {
                            "observability_commands": [
                                "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
                            ],
                        }
                    },
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review",
                    "role": "reviewer",
                    "summary": "Review",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "pipeline_invalid"
    reasons = result["final_status"]["reasons"]
    assert any("observability_scope=wave_final" in reason for reason in reasons)
    assert any("canonical_flow_commands" in reason for reason in reasons)


def test_validate_planner_contract_rejects_today_week_without_architect_authorization(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-ARCH-MISMATCH-OBS"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    result = feature_pipeline(
        feature_id="FEAT-ARCH-MISMATCH-OBS",
        title="Architect mismatch observability",
        summary="Reject planner today-week gate when architect did not authorize canonical evidence ownership",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="accepted",
        wave_verdict="accepted",
        business_context={
            "impacted_modules": ["M-FRONTEND-WEEK"],
            "allowed_write_scope": ["/opt/astro-project/frontend/app/week/page.tsx"],
            "architect_waves": [
                {
                    "wave_id": "W01",
                    "title": "Frontend helper wave",
                    "goal": "Frontend-only helper change",
                    "allowed_write_scope": ["/opt/astro-project/frontend/app/week/page.tsx"],
                    "observability_scope": "packet_local",
                    "canonical_flow_commands": [],
                    "verification_commands": [
                        "corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx",
                    ],
                }
            ],
        },
        planner_contract={
            "waves": [{"wave_id": "W01", "title": "Wave 1", "objective": "Single slice"}],
            "packets": [
                {"key": "coder_main", "wave_id": "W01", "title": "Main", "role": "coder", "summary": "Do work"},
                {
                    "key": "verifier_main",
                    "wave_id": "W01",
                    "title": "Verify",
                    "role": "verifier",
                    "summary": "Verify",
                    "dependencies": ["coder_main"],
                    "verification_profile": {
                        "execution": {
                            "observability_scope": "wave_final",
                            "canonical_flow_commands": [
                                "./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts",
                            ],
                            "observability_commands": [
                                "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
                            ],
                        }
                    },
                },
                {
                    "key": "reviewer_main",
                    "wave_id": "W01",
                    "title": "Review",
                    "role": "reviewer",
                    "summary": "Review",
                    "dependencies": ["coder_main", "verifier_main"],
                    "review_target_key": "coder_main",
                },
            ],
        },
    )

    assert result["final_status"]["feature"]["status"] == "pipeline_invalid"
    reasons = result["final_status"]["reasons"]
    assert any("does not authorize today-week wave_final ownership" in reason for reason in reasons)
    assert any("lacks canonical_flow_commands/include_day_live_canary" in reason for reason in reasons)


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
    feature_packets_dir = feature_bootstrap.FEATURES_DIR / "FEAT-OBS-REWORK-STOP"
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
        verifier_observability_profile="read-only",
        rework_routing_policy="auto_bundle",
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
    assert result["final_status"]["final_outcome"] == "blocked"
    assert result["final_status"]["user_facing_status"] == "pipeline_invalid"
    assert "пайплайн некорректен" in result["final_status"]["user_summary"]
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

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
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

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    assert result["runs"]["architect"]["launcher"] == "skipped"
    assert result["runs"]["planner"]["launcher"] == "skipped"


def test_feature_pipeline_defaults_planner_to_skipped(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"

    result = feature_pipeline(
        feature_id="FEAT-DEFAULT-PLANNER-OFF",
        title="Planner optional feature",
        summary="Planner should be skipped by default on new launches",
        dry_run=True,
        prefer_agent_output=False,
        reviewer_verdict="accepted",
        wave_verdict="accepted",
    )

    assert result["final_status"]["feature"]["status"] == "awaiting_commit"
    assert result["runs"]["planner"]["launcher"] == "skipped"


def test_route_reviewer_verdict_task_tolerates_missing_packet_record_for_notify(monkeypatch) -> None:
    notifications: list[dict] = []

    monkeypatch.setattr(
        "prefect_grace.flows.feature_pipeline.get_run_logger",
        lambda: SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None),
    )
    monkeypatch.setattr("prefect_grace.flows.feature_pipeline.record_review", lambda **kwargs: {"ok": True, **kwargs})
    monkeypatch.setattr("prefect_grace.flows.feature_pipeline.mark_packet_status_task", lambda *args, **kwargs: None)
    monkeypatch.setattr("prefect_grace.flows.feature_pipeline.notify_packet_event", lambda **kwargs: notifications.append(kwargs))

    def _missing(*args, **kwargs):
        raise KeyError("missing packet")

    monkeypatch.setattr("prefect_grace.flows.feature_pipeline.find_record", _missing)

    result = route_reviewer_verdict_task(
        coder_packet_id="PKT-MISSING",
        reviewer_packet_id="PKT-REVIEW",
        reviewer_decision={"packet_verdict": ReviewVerdict.BLOCKED.value, "reasons": ["x"]},
        create_rework=True,
    )

    assert result["reviewer_verdict"] == ReviewVerdict.BLOCKED.value
    assert notifications
    assert notifications[0]["packet_id"] == "PKT-MISSING"
    assert notifications[0]["feature_id"] == ""
