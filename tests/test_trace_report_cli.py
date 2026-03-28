from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from tools.trace_report import TraceBundle, render_trace


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


def test_render_trace_includes_all_sections_for_simulated_bundle():
    bundle = TraceBundle(
        report={
            "id": "11111111-1111-1111-1111-111111111111",
            "report_type": "week",
            "status": "completed",
            "client_id": "33333333-3333-3333-3333-333333333333",
            "user_id": "22222222-2222-2222-2222-222222222222",
        },
        runs=[
            {
                "id": "run-1",
                "status": "completed",
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "estimated_cost": "0.0012",
            }
        ],
        chunks=[
            {"id": "chunk-1", "section": "overview", "status": "completed", "order_index": 0},
            {"id": "chunk-2", "section": "love", "status": "completed", "order_index": 1, "error_message": "invalid json from llm"},
        ],
        events=[
            {
                "event": "report.workflow.run_start",
                "report_id": "11111111-1111-1111-1111-111111111111",
                "trace_id": "trace-report-123",
                "report_type": "week",
                "llm_mode": "live",
            },
            {
                "event": "report.workflow.model_resolution",
                "report_id": "11111111-1111-1111-1111-111111111111",
                "trace_id": "trace-report-123",
                "provider": "openrouter",
                "requested_model": "openai/gpt-5-mini",
                "resolved_model": "openai/gpt-5-mini",
            },
            {
                "event": "report.workflow.chunk_matrix",
                "report_id": "11111111-1111-1111-1111-111111111111",
                "trace_id": "trace-report-123",
                "expected_sections": ["overview", "love"],
                "completed_sections": ["overview", "love"],
                "required_sections_missing": [],
            },
            {
                "event": "report.workflow.chunk_parse_result",
                "report_id": "11111111-1111-1111-1111-111111111111",
                "trace_id": "trace-report-123",
                "section_id": "love",
                "result": "degraded",
                "degraded_reason": "llm_invalid_json",
            },
            {
                "event": "week_brief.fallback_decision",
                "report_id": "11111111-1111-1111-1111-111111111111",
                "trace_id": "trace-report-123",
                "fallback_mode": True,
                "primary_reason_code": "llm_invalid_json",
                "reason_codes": ["llm_invalid_json"],
            },
            {
                "event": "report.failure_packet",
                "report_id": "11111111-1111-1111-1111-111111111111",
                "trace_id": "trace-report-123",
                "status": "degraded",
                "reason_codes": ["llm_invalid_json"],
                "failed_section": "love",
            },
            {
                "event": "report.workflow.generation_complete",
                "report_id": "11111111-1111-1111-1111-111111111111",
                "trace_id": "trace-report-123",
                "success": 1,
                "fallback": 1,
                "error": 0,
            },
        ],
    )

    output = render_trace(bundle)
    assert "== request info ==" in output
    assert "== model resolution ==" in output
    assert "== chunk matrix ==" in output
    assert "== chunk parse results ==" in output
    assert "== fallback decision ==" in output
    assert "== failure packet ==" in output
    assert "== final response summary ==" in output
    assert "== db runs ==" in output
    assert '"resolved_model": "openai/gpt-5-mini"' in output
    assert '"primary_reason_code": "llm_invalid_json"' in output
    assert '"failed_section": "love"' in output



def test_trace_report_cli_help_and_trace_only_mode():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        log_path = tmp / "report.jsonl"
        _write_jsonl(
            log_path,
            [
                {"event": "report.workflow.run_start", "trace_id": "trace-only-456", "report_id": "r-x", "llm_mode": "stub"},
                {"event": "report.workflow.generation_complete", "trace_id": "trace-only-456", "report_id": "r-x", "success": 0, "fallback": 1},
            ],
        )

        help_result = subprocess.run(
            ["python3", "tools/trace_report.py", "--help"],
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": ".", "DATABASE_URL": "sqlite:///:memory:"},
        )
        assert "--report-id" in help_result.stdout
        assert "--trace-id" in help_result.stdout

        trace_result = subprocess.run(
            ["python3", "tools/trace_report.py", "--trace-id", "trace-only-456", "--log-path", str(log_path)],
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": ".", "DATABASE_URL": "sqlite:///:memory:"},
        )
        assert '"llm_mode": "stub"' in trace_result.stdout
        assert "== model resolution ==" in trace_result.stdout
        assert "not found" in trace_result.stdout
