import json
import sys

from scripts import agent_done_notify


def test_agent_done_notify_dry_run_returns_json_without_sending(monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        agent_done_notify,
        "notify_agent_work_event",
        lambda **kwargs: calls.append(kwargs) or True,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "agent_done_notify.py",
            "--title",
            "Safe dry run",
            "--status",
            "done",
            "--dry-run",
            "--json",
        ],
    )

    assert agent_done_notify.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is True
    assert output["dry_run"] is True
    assert calls == []


def test_agent_done_notify_invokes_sender(monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        agent_done_notify,
        "notify_agent_work_event",
        lambda **kwargs: calls.append(kwargs) or True,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "agent_done_notify.py",
            "--title",
            "Packet complete",
            "--status",
            "done",
            "--message",
            "Validation passed.",
            "--packet-id",
            "PACKET-1",
            "--next-action",
            "Review.",
            "--json",
        ],
    )

    assert agent_done_notify.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is True
    assert calls == [{
        "status": "done",
        "title": "Packet complete",
        "summary": "Validation passed.",
        "packet_id": "PACKET-1",
        "next_action": "Review.",
        "link": None,
    }]
