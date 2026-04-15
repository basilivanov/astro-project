import argparse

from prefect_grace import cli
from prefect_grace.models import ReasoningProfile
from prefect_grace.tasks.planner_contract import default_wave_plan_contract


def test_default_wave_plan_contract_uses_medium_verifier_reasoning_and_codex_runner() -> None:
    contract = default_wave_plan_contract(
        feature_id="FEAT-X",
        implementation_title="Impl",
        implementation_summary="Summary",
    )
    verifier_packet = next(packet for packet in contract["packets"] if packet["role"] == "verifier")
    assert verifier_packet["reasoning"] == ReasoningProfile.MEDIUM.value
    assert verifier_packet["execution_hints"]["runner"] == "codex"


def test_cli_run_verifier_uses_codex_launcher(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_launch(packet_id: str, *, dry_run: bool, timeout_seconds: int):
        captured["packet_id"] = packet_id
        captured["dry_run"] = dry_run
        captured["timeout_seconds"] = timeout_seconds
        return {"packet_id": packet_id, "returncode": 0}

    monkeypatch.setattr(cli, "launch_codex_for_packet", _fake_launch)
    cli._cmd_run_verifier(argparse.Namespace(packet_id="VER-1", dry_run=True, timeout_seconds=123))

    assert captured == {
        "packet_id": "VER-1",
        "dry_run": True,
        "timeout_seconds": 123,
    }
