from pathlib import Path
import json
import pytest
from unittest.mock import patch
from argparse import Namespace

from prefect_grace.platform.brief_intake import parse_brief_markdown, generate_strict_packet
from prefect_grace.cli_commands.brief_intake import _cmd_dynamic_plan


def test_parse_brief_markdown(tmp_path: Path) -> None:
    brief_file = tmp_path / "feature-brief.md"
    brief_file.write_text(
        "# Feature Brief: FEAT-TEST-DYNAMIC-PLAN\n\n"
        "## Business Intent\n"
        "Verify dynamic planning capability automatically.\n\n"
        "## Acceptance Criteria\n"
        "- The packet is validated without errors.\n"
        "- Sidecar matches standard fields.\n",
        encoding="utf-8"
    )

    parsed = parse_brief_markdown(brief_file)
    assert parsed["feature_id"] == "FEAT-TEST-DYNAMIC-PLAN"
    assert parsed["title"] == "Feature Brief: FEAT-TEST-DYNAMIC-PLAN"
    assert "business intent" in parsed["sections"]
    assert "acceptance criteria" in parsed["sections"]


def test_generate_strict_packet_dry_run(tmp_path: Path) -> None:
    brief_file = tmp_path / "feature-brief.md"
    brief_file.write_text(
        "# Feature Brief: FEAT-TEST-DRY\n\n"
        "## Business Intent\n"
        "Test dry-run option of dynamic planning.\n",
        encoding="utf-8"
    )

    result = generate_strict_packet(brief_file, output_dir=tmp_path, write=False)
    assert result["packet_id"] == "FEAT-TEST-DRY-W01-DYNAMIC-PLANNING"
    assert result["md_path"] is None
    assert result["yaml_path"] is None
    assert "FEAT-TEST-DRY-W01-DYNAMIC-PLANNING" in result["md_content"]
    assert "FEAT-TEST-DRY-W01-DYNAMIC-PLANNING" in result["yaml_content"]

    # Make sure no files were written
    assert not (tmp_path / "EXECUTION_PACKET.md").exists()
    assert not (tmp_path / "EXECUTION_PACKET.yaml").exists()


def test_generate_strict_packet_apply(tmp_path: Path) -> None:
    brief_file = tmp_path / "feature-brief.md"
    brief_file.write_text(
        "# Feature Brief: FEAT-TEST-APPLY\n\n"
        "## Business Intent\n"
        "Test write option of dynamic planning.\n",
        encoding="utf-8"
    )

    result = generate_strict_packet(brief_file, output_dir=tmp_path, write=True)
    assert result["md_path"] == tmp_path / "EXECUTION_PACKET.md"
    assert result["yaml_path"] == tmp_path / "EXECUTION_PACKET.yaml"

    assert (tmp_path / "EXECUTION_PACKET.md").exists()
    assert (tmp_path / "EXECUTION_PACKET.yaml").exists()


def test_cli_command_dry_run(tmp_path: Path, capsys) -> None:
    brief_file = tmp_path / "feature-brief.md"
    brief_file.write_text(
        "# Feature Brief: FEAT-TEST-CLI-DRY\n\n"
        "## Business Intent\n"
        "Verify CLI dry-run execution.\n",
        encoding="utf-8"
    )

    args = Namespace(
        brief=str(brief_file),
        output_dir=str(tmp_path),
        apply=False,
        json=False
    )

    with pytest.raises(SystemExit) as excinfo:
        _cmd_dynamic_plan(args)

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "Dynamic Plan generated successfully" in captured.out
    assert "[DRY-RUN]" in captured.out


def test_cli_command_json_dry_run(tmp_path: Path, capsys) -> None:
    brief_file = tmp_path / "feature-brief.md"
    brief_file.write_text(
        "# Feature Brief: FEAT-TEST-CLI-JSON\n\n"
        "## Business Intent\n"
        "Verify CLI JSON output.\n",
        encoding="utf-8"
    )

    args = Namespace(
        brief=str(brief_file),
        output_dir=str(tmp_path),
        apply=False,
        json=True
    )

    with pytest.raises(SystemExit) as excinfo:
        _cmd_dynamic_plan(args)

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    parsed_json = json.loads(captured.out)
    assert parsed_json["ok"] is True
    assert parsed_json["command"] == "dynamic-plan"
    assert parsed_json["result"]["packet_id"] == "FEAT-TEST-CLI-JSON-W01-DYNAMIC-PLANNING"
    assert parsed_json["result"]["dry_run"] is True


def test_cli_command_missing_file(tmp_path: Path, capsys) -> None:
    args = Namespace(
        brief=str(tmp_path / "non-existent-brief.md"),
        output_dir=str(tmp_path),
        apply=False,
        json=False
    )

    with pytest.raises(SystemExit) as excinfo:
        _cmd_dynamic_plan(args)

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Dynamic plan failed" in captured.err


def test_cli_command_missing_file_json(tmp_path: Path, capsys) -> None:
    args = Namespace(
        brief=str(tmp_path / "non-existent-brief.md"),
        output_dir=str(tmp_path),
        apply=False,
        json=True
    )

    with pytest.raises(SystemExit) as excinfo:
        _cmd_dynamic_plan(args)

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    parsed_json = json.loads(captured.out)
    assert parsed_json["ok"] is False
    assert parsed_json["command"] == "dynamic-plan"
    assert len(parsed_json["errors"]) == 1
    assert parsed_json["errors"][0]["code"] == "DYNAMIC_PLAN_FAILED"
