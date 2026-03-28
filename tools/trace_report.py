from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_LOG_PATH = Path(os.getenv("ASTRO_REPORT_LOG", PROJECT_ROOT / "logs" / "report.jsonl"))

REQUEST_EVENTS = (
    "report.workflow.run_start",
    "report.workflow.run_started",
    "report.workflow.generation_start",
)
MODEL_RESOLUTION_EVENTS = (
    "report.workflow.model_resolution",
    "week_brief.model_resolution",
)
CHUNK_MATRIX_EVENTS = (
    "report.workflow.chunk_matrix",
    "week_brief.chunk_matrix",
)
CHUNK_PARSE_EVENTS = (
    "report.workflow.chunk_parse_result",
    "week_brief.chunk_parse_result",
)
FALLBACK_EVENTS = (
    "week_brief.fallback_decision",
    "report.workflow.fallback_decision",
)
FAILURE_PACKET_EVENTS = (
    "report.failure_packet",
)
FINAL_SUMMARY_EVENTS = (
    "report.workflow.generation_complete",
    "report.workflow.generation_stats",
    "week_brief.response_returned",
    "day_brief.response_returned",
)


@dataclass
class TraceBundle:
    report: dict[str, Any] | None
    runs: list[dict[str, Any]]
    chunks: list[dict[str, Any]]
    events: list[dict[str, Any]]


def _safe_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _stringify_uuidish(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"report log not found: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
    return records


def _serialize_report(report: Any | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "id": _stringify_uuidish(report.id),
        "client_id": _stringify_uuidish(report.client_id),
        "user_id": _stringify_uuidish(report.user_id),
        "report_type": report.report_type,
        "status": report.status,
        "is_test": report.is_test,
        "paid": report.paid,
        "error_message": report.error_message,
        "error_at": report.error_at.isoformat() if report.error_at else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }


def _serialize_chunk(chunk: Any) -> dict[str, Any]:
    return {
        "id": _stringify_uuidish(chunk.id),
        "section": chunk.section,
        "status": chunk.status,
        "order_index": chunk.order_index,
        "error_message": chunk.error_message,
        "error_at": chunk.error_at.isoformat() if chunk.error_at else None,
        "content_preview": (chunk.content or "")[:160],
    }


def _serialize_run(run: Any) -> dict[str, Any]:
    return {
        "id": _stringify_uuidish(run.id),
        "status": run.status,
        "error_message": run.error_message,
        "prompt_tokens": run.prompt_tokens,
        "completion_tokens": run.completion_tokens,
        "total_tokens": run.total_tokens,
        "estimated_cost": str(run.estimated_cost),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


def _find_trace_id(records: Iterable[dict[str, Any]], report_id: str) -> str | None:
    for record in records:
        if str(record.get("report_id") or "") == report_id and record.get("trace_id"):
            return str(record["trace_id"])
    return None


def load_trace_bundle(*, report_id: str | None, trace_id: str | None, log_path: Path, db: Any) -> TraceBundle:
    from backend.app.models import Report, ReportChunk, ReportRun

    records = _load_jsonl(log_path)
    resolved_trace_id = trace_id
    if report_id and not resolved_trace_id:
        resolved_trace_id = _find_trace_id(records, report_id)

    filtered_events = []
    for record in records:
        record_report_id = record.get("report_id")
        record_trace_id = record.get("trace_id")
        if report_id and str(record_report_id or "") == report_id:
            filtered_events.append(record)
            continue
        if resolved_trace_id and str(record_trace_id or "") == resolved_trace_id:
            filtered_events.append(record)

    resolved_report_id = report_id
    if resolved_report_id is None:
        for record in filtered_events:
            if record.get("report_id"):
                resolved_report_id = str(record["report_id"])
                break

    report = None
    if resolved_report_id:
        try:
            report_uuid = uuid.UUID(str(resolved_report_id))
        except (TypeError, ValueError, AttributeError):
            report_uuid = None
        if report_uuid is not None:
            report = db.query(Report).filter(Report.id == report_uuid).one_or_none()
    chunks = []
    runs = []
    if report is not None:
        chunks = [
            _serialize_chunk(chunk)
            for chunk in db.query(ReportChunk).filter(ReportChunk.report_id == report.id).order_by(ReportChunk.order_index.asc()).all()
        ]
        runs = [
            _serialize_run(run)
            for run in db.query(ReportRun).filter(ReportRun.report_id == report.id).order_by(ReportRun.started_at.asc().nullslast()).all()
        ]
    return TraceBundle(report=_serialize_report(report), runs=runs, chunks=chunks, events=filtered_events)


def _event_matches(event: dict[str, Any], names: tuple[str, ...]) -> bool:
    return str(event.get("event") or "") in names


def _print_section(title: str) -> None:
    print(f"\n== {title} ==")


def _print_request_info(bundle: TraceBundle) -> None:
    _print_section("request info")
    request_event = next((event for event in bundle.events if _event_matches(event, REQUEST_EVENTS)), None)
    if request_event:
        print(_safe_json_dumps(request_event))
    elif bundle.report:
        print(_safe_json_dumps(bundle.report))
    else:
        print("not found")


def _print_event_group(bundle: TraceBundle, title: str, names: tuple[str, ...]) -> None:
    _print_section(title)
    matches = [event for event in bundle.events if _event_matches(event, names)]
    if not matches:
        print("not found")
        return
    for event in matches:
        print(_safe_json_dumps(event))


def _print_chunk_matrix(bundle: TraceBundle) -> None:
    _print_section("chunk matrix")
    matrix_events = [event for event in bundle.events if _event_matches(event, CHUNK_MATRIX_EVENTS)]
    if matrix_events:
        for event in matrix_events:
            print(_safe_json_dumps(event))
        return
    if bundle.chunks:
        for chunk in bundle.chunks:
            print(_safe_json_dumps(chunk))
        return
    print("not found")


def render_trace(bundle: TraceBundle) -> str:
    from contextlib import redirect_stdout
    from io import StringIO

    stream = StringIO()
    with redirect_stdout(stream):
        _print_request_info(bundle)
        _print_event_group(bundle, "model resolution", MODEL_RESOLUTION_EVENTS)
        _print_chunk_matrix(bundle)
        _print_event_group(bundle, "chunk parse results", CHUNK_PARSE_EVENTS)
        _print_event_group(bundle, "fallback decision", FALLBACK_EVENTS)
        _print_event_group(bundle, "failure packet", FAILURE_PACKET_EVENTS)
        _print_event_group(bundle, "final response summary", FINAL_SUMMARY_EVENTS)
        if bundle.runs:
            _print_section("db runs")
            for run in bundle.runs:
                print(_safe_json_dumps(run))
    return stream.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assemble report generation trace from report.jsonl and DB.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report-id", help="Report UUID to inspect.")
    group.add_argument("--trace-id", help="Trace UUID to inspect.")
    parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH), help="Path to report.jsonl log file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    from backend.app.db import SessionLocal

    parser = build_parser()
    args = parser.parse_args(argv)
    session = SessionLocal()
    try:
        bundle = load_trace_bundle(
            report_id=args.report_id,
            trace_id=args.trace_id,
            log_path=Path(args.log_path),
            db=session,
        )
    finally:
        session.close()
    sys.stdout.write(render_trace(bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
