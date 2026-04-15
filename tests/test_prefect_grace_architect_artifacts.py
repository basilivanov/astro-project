from pathlib import Path

from prefect_grace.tasks import architect_artifacts
from prefect_grace.tasks import state_store
from prefect_grace.tasks.agent_output_parser import parse_architect_artifact_plan_message
from prefect_grace.tasks.architect_artifacts import default_architect_artifact_plan, write_architect_artifacts
from prefect_grace.tasks.feature_bootstrap import bootstrap_feature


def test_parse_architect_artifact_plan_message_from_markers() -> None:
    text = """
FINAL_ARCHITECT_ARTIFACT_PLAN_JSON
{
  "slice_id": "SLICE-DEV-INDICATOR",
  "slice_slug": "dev-indicator",
  "impacted_modules": ["M-FRONTEND-DAY"],
  "waves": [{"wave_id":"W01","title":"Main wave","goal":"Implement"}]
}
END_FINAL_ARCHITECT_ARTIFACT_PLAN_JSON
"""
    parsed = parse_architect_artifact_plan_message(text)
    assert parsed["slice_id"] == "SLICE-DEV-INDICATOR"
    assert parsed["slice_slug"] == "dev-indicator"
    assert parsed["impacted_modules"] == ["M-FRONTEND-DAY"]


def test_write_architect_artifacts_materializes_slice_pack(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    architect_artifacts.DOCS_DIR = tmp_path / "docs"
    feature_packets_dir = Path("/opt/astro-project/prefect_grace/packets") / "FEAT-ARCH-SLICE"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    bootstrap_feature(
        feature_id="FEAT-ARCH-SLICE",
        title="Dev indicator slice",
        summary="Add a small dev-only diagnostics surface on day screen.",
        business_context={
            "scope": ["Dev-only day screen diagnostics toggle."],
            "non_goals": ["No prod behavior change."],
            "acceptance_criteria": ["Dev chip expands compact diagnostics.", "Prod stays unchanged."],
            "impacted_modules": ["M-FRONTEND-DAY", "M-RUNTIME-DIAGNOSTICS"],
            "allowed_write_scope": ["frontend/app/page.tsx", "frontend/components/today/*"],
            "frozen_scope": ["backend/*", "frontend/app/week/*"],
            "verification_commands": ["./scripts/run_e2e.sh --last-failed"],
            "touches_frontend": True,
        },
    )
    payload = default_architect_artifact_plan(
        feature_id="FEAT-ARCH-SLICE",
        title="Dev indicator slice",
        summary="Add a small dev-only diagnostics surface on day screen.",
        business_context={
            "scope": ["Dev-only day screen diagnostics toggle."],
            "non_goals": ["No prod behavior change."],
            "acceptance_criteria": ["Dev chip expands compact diagnostics.", "Prod stays unchanged."],
            "impacted_modules": ["M-FRONTEND-DAY", "M-RUNTIME-DIAGNOSTICS"],
            "allowed_write_scope": ["frontend/app/page.tsx", "frontend/components/today/*"],
            "frozen_scope": ["backend/*", "frontend/app/week/*"],
            "verification_commands": ["./scripts/run_e2e.sh --last-failed"],
            "touches_frontend": True,
        },
    )
    written = write_architect_artifacts(feature_id="FEAT-ARCH-SLICE", architect_payload=payload)

    assert Path(written["requirements_slice_path"]).exists()
    assert Path(written["development_plan_slice_path"]).exists()
    assert Path(written["verification_matrix_slice_path"]).exists()
    assert Path(written["knowledge_graph_slice_path"]).exists()
    assert Path(written["architect_handoff_path"]).exists()
    assert Path(written["execution_packet_path"]).exists()
    assert Path(written["architect_manifest_path"]).exists()

    requirements_text = Path(written["requirements_slice_path"]).read_text(encoding="utf-8")
    manifest_text = Path(written["architect_manifest_path"]).read_text(encoding="utf-8")
    execution_packet_text = Path(written["execution_packet_path"]).read_text(encoding="utf-8")

    assert "Dev-only day screen diagnostics toggle." in requirements_text
    assert '"slice_id":' in manifest_text
    assert "Source of truth" in execution_packet_text
