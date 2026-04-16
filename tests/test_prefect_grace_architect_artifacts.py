from pathlib import Path

from prefect_grace.tasks import architect_artifacts
from prefect_grace.tasks import state_store
from prefect_grace.tasks.agent_output_parser import parse_architect_artifact_plan_message
from prefect_grace.tasks.architect_artifacts import default_architect_artifact_plan, write_architect_artifacts
from prefect_grace.tasks.feature_bootstrap import PACKET_CONTRACT_END, PACKET_CONTRACT_START, bootstrap_feature


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


def test_create_packet_renders_embedded_contract_json(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    architect_artifacts.DOCS_DIR = tmp_path / "docs"
    feature_packets_dir = Path("/opt/astro-project/prefect_grace/packets") / "FEAT-PACKET-CONTRACT"
    if feature_packets_dir.exists():
        import shutil
        shutil.rmtree(feature_packets_dir)

    bootstrap_feature(
        feature_id="FEAT-PACKET-CONTRACT",
        title="Packet contract feature",
        summary="Render packet.md as primary contract with embedded JSON tail.",
        business_context={"scope": ["Packet contract rendering only."]},
    )

    from prefect_grace.models import PacketStatus, ReasoningProfile
    from prefect_grace.tasks.feature_bootstrap import create_packet

    packet = create_packet(
        feature_id="FEAT-PACKET-CONTRACT",
        wave_id="W01",
        title="Main Slice",
        role="coder",
        reasoning=ReasoningProfile.HIGH,
        summary="Implement a bounded slice.",
        write_scope=["frontend/app/page.tsx"],
        inputs=["architect formalization"],
        acceptance_criteria=["Packet contract stays compact."],
        reviewer_gate=["No unrelated scope expansion."],
        notes=["packet.md is the primary contract."],
        status=PacketStatus.READY,
    )
    packet_text = Path(packet["packet_path"]).read_text(encoding="utf-8")

    assert "## Contract JSON" in packet_text
    assert PACKET_CONTRACT_START in packet_text
    assert PACKET_CONTRACT_END in packet_text
    assert '"packet_type": "execution"' in packet_text
