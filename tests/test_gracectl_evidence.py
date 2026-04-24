from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from gracectl.cli import app


def test_evidence_review_records_result_and_preserves_stdout(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "gracectl.yaml"
    config_path.write_text(
        "\n".join(
            [
                "defaults:",
                "  report_path: test-results/grace-report.json",
                "  log_dir: logs/gracectl",
                "  repo_root: .",
                "watch:",
                "  flows: []",
                "slices: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_run(command, cwd, shell, stdout, stderr, text):
        assert "tools/post_test_review.py --profile today-week" in command

        class Completed:
            returncode = 0
            stdout = '{"verdict":"PASS_CLEAN"}\n'

        return Completed()

    monkeypatch.setattr("gracectl.commands.evidence.subprocess.run", fake_run)

    result = CliRunner().invoke(
        app,
        ["evidence", "review", "today-week", "--config", str(config_path), "--report-format", "json"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"verdict": "PASS_CLEAN"}
    report = (tmp_path / "test-results" / "grace-report.json").read_text(encoding="utf-8")
    assert '"command": "evidence review"' in report
    log = tmp_path / "logs" / "gracectl" / "evidence-review-today-week.log"
    assert log.read_text(encoding="utf-8") == '{"verdict":"PASS_CLEAN"}\n'


def test_evidence_generate_filters_structlog_prefix_from_stdout(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "gracectl.yaml"
    config_path.write_text(
        "\n".join(
            [
                "defaults:",
                "  report_path: test-results/grace-report.json",
                "  log_dir: logs/gracectl",
                "  repo_root: .",
                "watch:",
                "  flows: []",
                "slices: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    noisy_output = "timestamp='2026-04-24T00:00:00Z' event='feed.entry'\n{\"status\":\"ok\"}\n"

    def fake_run(command, cwd, shell, stdout, stderr, text):
        assert "scripts/generate_canonical_evidence.py" in command

        class Completed:
            returncode = 0
            stdout = noisy_output

        return Completed()

    monkeypatch.setattr("gracectl.commands.evidence.subprocess.run", fake_run)

    result = CliRunner().invoke(
        app,
        ["evidence", "generate", "--config", str(config_path), "--flows", "today,week"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"status": "ok"}
    log = tmp_path / "logs" / "gracectl" / "evidence-generate-today-week.log"
    assert log.read_text(encoding="utf-8") == noisy_output
