#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests


VALID_LLM_MODES = {
    "openrouter",
    "cheap",
    "cli",
    "gemini",
    "codex",
    "fallback",
    "local",
    "mock",
    "stub",
}
STUB_LIKE_MODES = {"fallback", "local", "mock", "stub"}
TEMPLATE_MARKERS = [
    "🧭 О чем этот блок",
    "Настройка этого блока дает устойчивую опору",
    "Сформулируйте 1-2 практичных шага",
]
REPAIR_MARKERS = [
    "Дополнено автоматически",
]
ERROR_MARKERS = [
    "Ошибка генерации",
]
DEFAULT_COMPARE_EXCLUDES = ["input_frame", "technical_appendix"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def mask_secret(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}...{value[-2:]}"


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "benchmark"


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest is not valid JSON: {path}: {exc}") from exc

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Manifest must contain a non-empty 'cases' list.")

    case_ids: list[str] = []
    for case in cases:
        case_id = str(case.get("id") or "").strip()
        if not case_id:
            raise ValueError("Every case must have a non-empty 'id'.")
        case_ids.append(case_id)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Manifest contains duplicate case ids.")

    benchmark_id = str(data.get("benchmark_id") or "").strip()
    if not benchmark_id:
        raise ValueError("Manifest must contain a non-empty 'benchmark_id'.")

    return data


def select_cases(manifest: dict[str, Any], requested_case_ids: list[str]) -> list[dict[str, Any]]:
    cases = manifest["cases"]
    if not requested_case_ids:
        return cases

    wanted = set(requested_case_ids)
    selected = [case for case in cases if case["id"] in wanted]
    found = {case["id"] for case in selected}
    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"Unknown case ids: {', '.join(missing)}")
    return selected


def resolve_case_llm_mode(
    case: dict[str, Any],
    cli_llm_mode: str | None,
    allow_stub_benchmark: bool,
) -> str:
    case_id = str(case["id"])
    raw_mode = str(case.get("llm_mode") or cli_llm_mode or "").strip().lower()
    if not raw_mode:
        raise ValueError(
            f"Case '{case_id}' has no explicit llm_mode. "
            "Pass --llm-mode or set llm_mode in the manifest."
        )
    if raw_mode not in VALID_LLM_MODES:
        raise ValueError(f"Case '{case_id}' uses unsupported llm_mode '{raw_mode}'.")
    if raw_mode in STUB_LIKE_MODES and not allow_stub_benchmark:
        raise ValueError(
            f"Case '{case_id}' resolves to stub-like llm_mode '{raw_mode}'. "
            "Pass --allow-stub-benchmark only if that benchmark is intentional."
        )
    return raw_mode


def inspect_backend_runtime(
    container_name: str,
    allow_missing_backend_env: bool,
) -> dict[str, Any]:
    command = [
        "docker",
        "exec",
        container_name,
        "/bin/sh",
        "-lc",
        'printf "DEFAULT_LLM_MODE=%s\\nLLM_SMOKE=%s\\n" "${DEFAULT_LLM_MODE:-}" "${LLM_SMOKE:-}"',
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        if allow_missing_backend_env:
            return {
                "container_name": container_name,
                "available": False,
                "error": str(exc),
            }
        raise RuntimeError(
            f"Failed to inspect backend container '{container_name}'. "
            "Pass --allow-missing-backend-env only if you intentionally cannot audit the live container env."
        ) from exc

    env_map: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_map[key.strip()] = value.strip()

    return {
        "container_name": container_name,
        "available": True,
        "default_llm_mode": env_map.get("DEFAULT_LLM_MODE") or None,
        "llm_smoke": env_map.get("LLM_SMOKE") or None,
    }


def build_request_headers(telegram_auth: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Telegram-Auth": telegram_auth,
    }


def request_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> tuple[int, dict[str, Any] | None, str]:
    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    text = response.text
    try:
        parsed = response.json()
    except ValueError:
        parsed = None
    return response.status_code, parsed, text


def flatten_blocks(blocks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            parts.append(str(block))
            continue

        block_type = block.get("type")
        if block_type == "header":
            parts.append(str(block.get("text", "")))
        elif block_type == "paragraph":
            parts.append(str(block.get("text", "")))
        elif block_type == "list":
            parts.extend(str(item) for item in block.get("items", []))
        elif block_type == "callout":
            parts.append(str(block.get("title", "")))
            parts.append(str(block.get("content", "")))
        elif block_type == "table":
            for column in block.get("columns", []):
                parts.append(str(column.get("header", "")))
            for row in block.get("rows", []):
                parts.extend(str(cell) for cell in row)
        elif block_type == "key_value":
            for item in block.get("items", []):
                parts.append(str(item.get("key", "")))
                parts.append(str(item.get("value", "")))
        elif block_type == "rating":
            parts.append(str(block.get("label", "")))
        else:
            parts.append(json.dumps(block, ensure_ascii=False, sort_keys=True))

    return " ".join(part for part in parts if part).strip()


def normalize_content_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, list):
        return flatten_blocks(content)
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False, sort_keys=True)
    if not isinstance(content, str):
        return str(content)

    stripped = content.strip()
    if not stripped:
        return ""
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped

    if isinstance(parsed, list):
        return flatten_blocks(parsed)
    if isinstance(parsed, dict):
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
    return str(parsed)


def collect_markers(text: str, markers: list[str]) -> list[str]:
    return [marker for marker in markers if marker in text]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def similarity_ratio(left: str, right: str) -> float:
    return round(SequenceMatcher(None, left, right).ratio(), 3)


def build_case_payload(
    case: dict[str, Any],
    requested_llm_mode: str,
    run_id: str,
) -> dict[str, Any]:
    payload = copy.deepcopy(case)
    case_id = str(payload.pop("id"))
    payload["llm_mode"] = requested_llm_mode
    payload.setdefault("client_name", f"Benchmark {case_id}")
    payload.setdefault("is_test", True)

    benchmark_tag = f"[benchmark:{run_id}:{case_id}]"
    existing_note = str(payload.get("client_note") or "").strip()
    if benchmark_tag not in existing_note:
        payload["client_note"] = " ".join(part for part in [existing_note, benchmark_tag] if part).strip()

    return payload


def extract_section_data(chunks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, int]]:
    section_records: list[dict[str, Any]] = []
    section_texts: dict[str, str] = {}
    template_sections = 0
    repair_sections = 0
    error_sections = 0

    for chunk in chunks:
        section_id = str(chunk.get("section") or "")
        text = normalize_content_text(chunk.get("content"))
        template_hits = collect_markers(text, TEMPLATE_MARKERS)
        repair_hits = collect_markers(text, REPAIR_MARKERS)
        error_hits = collect_markers(text, ERROR_MARKERS)

        if template_hits:
            template_sections += 1
        if repair_hits:
            repair_sections += 1
        if error_hits:
            error_sections += 1

        section_texts[section_id] = text
        section_records.append(
            {
                "section": section_id,
                "status": chunk.get("status"),
                "order_index": chunk.get("order_index"),
                "char_count": len(text),
                "text_sha256": sha256_text(text) if text else None,
                "template_markers": template_hits,
                "repair_markers": repair_hits,
                "error_markers": error_hits,
            }
        )

    marker_summary = {
        "template_marker_sections": template_sections,
        "repair_marker_sections": repair_sections,
        "error_marker_sections": error_sections,
    }
    return section_records, section_texts, marker_summary


def poll_report_until_terminal(
    api_url: str,
    headers: dict[str, str],
    report_id: str,
    poll_interval: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_detail: dict[str, Any] | None = None
    last_http_error: dict[str, Any] | None = None
    attempts = 0

    while time.monotonic() < deadline:
        attempts += 1
        status_code, payload, raw_text = request_json(
            "GET",
            f"{api_url}/api/reports/{report_id}",
            headers=headers,
        )
        if status_code == 200 and payload:
            last_detail = payload
            report_status = str((payload.get("report") or {}).get("status") or "").lower()
            if report_status in {"completed", "failed"}:
                return {
                    "timed_out": False,
                    "attempts": attempts,
                    "detail": payload,
                    "last_http_error": last_http_error,
                }
        else:
            last_http_error = {
                "status_code": status_code,
                "body": raw_text[:1000],
            }
        time.sleep(poll_interval)

    return {
        "timed_out": True,
        "attempts": attempts,
        "detail": last_detail,
        "last_http_error": last_http_error,
    }


def build_case_state(
    case: dict[str, Any],
    payload: dict[str, Any],
    requested_llm_mode: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    create_response: dict[str, Any] | None,
    report_detail: dict[str, Any] | None,
    poll_attempts: int,
    timed_out: bool,
    request_error: str | None,
    last_http_error: dict[str, Any] | None,
) -> dict[str, Any]:
    detail_report = (report_detail or {}).get("report") or {}
    chunks = (report_detail or {}).get("chunks") or []
    section_records, section_texts, marker_summary = extract_section_data(chunks)

    status = str(detail_report.get("status") or "").lower()
    if request_error and not status:
        status = "request_failed"
    if timed_out:
        status = "timeout"

    completed_chunks = sum(1 for chunk in chunks if chunk.get("status") == "completed")

    record = {
        "case_id": case["id"],
        "report_type": payload.get("report_type"),
        "requested_llm_mode": requested_llm_mode,
        "status": status,
        "duration_seconds": duration_seconds,
        "report_id": (create_response or {}).get("report_id"),
        "client_id": (create_response or {}).get("client_id"),
        "started_at": started_at,
        "finished_at": finished_at,
        "poll_attempts": poll_attempts,
        "timeout": timed_out,
        "report_error_message": detail_report.get("error_message"),
        "request_error": request_error,
        "last_http_error": last_http_error,
        "chunk_count": len(chunks),
        "completed_chunk_count": completed_chunks,
        "marker_summary": marker_summary,
        "payload": payload,
        "sections": section_records,
    }

    return {
        "record": record,
        "section_texts": section_texts,
    }


def build_comparison_record(
    comparison: dict[str, Any],
    case_states: dict[str, dict[str, Any]],
    default_excludes: list[str],
) -> dict[str, Any]:
    left_case_id = str(comparison["left"])
    right_case_id = str(comparison["right"])
    left_state = case_states.get(left_case_id)
    right_state = case_states.get(right_case_id)

    if not left_state or not right_state:
        return {
            "comparison_id": comparison["id"],
            "left_case_id": left_case_id,
            "right_case_id": right_case_id,
            "status": "skipped_missing_case",
        }

    left_texts = left_state["section_texts"]
    right_texts = right_state["section_texts"]
    include_sections = [str(item) for item in comparison.get("include_sections") or []]
    excluded_sections = sorted(
        set(default_excludes).union(str(item) for item in comparison.get("exclude_sections") or [])
    )
    excluded_set = set(excluded_sections)
    shared_sections = set(left_texts).intersection(right_texts)

    if include_sections:
        compared_sections = [
            section
            for section in include_sections
            if section in shared_sections and section not in excluded_set
        ]
    else:
        compared_sections = sorted(section for section in shared_sections if section not in excluded_set)

    left_concat = "\n\n".join(left_texts[section] for section in compared_sections)
    right_concat = "\n\n".join(right_texts[section] for section in compared_sections)

    section_similarity = []
    for section in compared_sections:
        left_text = left_texts[section]
        right_text = right_texts[section]
        section_similarity.append(
            {
                "section": section,
                "similarity": similarity_ratio(left_text, right_text),
                "left_char_count": len(left_text),
                "right_char_count": len(right_text),
                "left_sha256": sha256_text(left_text) if left_text else None,
                "right_sha256": sha256_text(right_text) if right_text else None,
            }
        )

    return {
        "comparison_id": comparison["id"],
        "left_case_id": left_case_id,
        "right_case_id": right_case_id,
        "status": "completed",
        "included_sections": include_sections or None,
        "excluded_sections": excluded_sections,
        "compared_sections": compared_sections,
        "missing_in_left": sorted(set(right_texts) - set(left_texts)),
        "missing_in_right": sorted(set(left_texts) - set(right_texts)),
        "report_similarity": similarity_ratio(left_concat, right_concat) if compared_sections else None,
        "section_similarity": section_similarity,
    }


def render_markdown_summary(result: dict[str, Any]) -> str:
    metadata = result["metadata"]
    lines = [
        f"# Live Quality Benchmark: {metadata['run_id']}",
        "",
        f"- Benchmark ID: `{metadata['benchmark_id']}`",
        f"- Manifest: `{metadata['manifest_path']}`",
        f"- API URL: `{metadata['api_url']}`",
        f"- Telegram Auth: `{metadata['telegram_auth_hint']}`",
        f"- Selected cases: `{', '.join(metadata['selected_case_ids'])}`",
        "",
        "## Runtime Audit",
    ]

    backend_runtime = metadata["backend_runtime"]
    if backend_runtime.get("available"):
        lines.extend(
            [
                f"- Backend container: `{backend_runtime['container_name']}`",
                f"- Backend DEFAULT_LLM_MODE: `{backend_runtime.get('default_llm_mode') or 'unset'}`",
                f"- Backend LLM_SMOKE: `{backend_runtime.get('llm_smoke') or 'unset'}`",
            ]
        )
    else:
        lines.extend(
            [
                f"- Backend container: `{backend_runtime['container_name']}`",
                f"- Backend env audit: unavailable",
                f"- Backend env error: `{backend_runtime.get('error')}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Type | llm_mode | Status | Duration (s) | Report ID | Sections | Template | Repair | Error |",
            "| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )

    for case in result["cases"]:
        marker_summary = case["marker_summary"]
        lines.append(
            "| {case_id} | {report_type} | {mode} | {status} | {duration:.3f} | {report_id} | {chunk_count} | {template} | {repair} | {error} |".format(
                case_id=case["case_id"],
                report_type=case["report_type"],
                mode=case["requested_llm_mode"],
                status=case["status"],
                duration=case["duration_seconds"],
                report_id=case.get("report_id") or "-",
                chunk_count=case["chunk_count"],
                template=marker_summary["template_marker_sections"],
                repair=marker_summary["repair_marker_sections"],
                error=marker_summary["error_marker_sections"],
            )
        )

    comparisons = result.get("comparisons") or []
    if comparisons:
        lines.extend(
            [
                "",
                "## Comparisons",
                "",
                "| Comparison | Status | Similarity | Compared sections | Excluded sections |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        for comparison in comparisons:
            compared = ", ".join(comparison.get("compared_sections") or []) or "-"
            excluded = ", ".join(comparison.get("excluded_sections") or []) or "-"
            similarity = comparison.get("report_similarity")
            similarity_text = "-" if similarity is None else f"{similarity:.3f}"
            lines.append(
                "| {comparison_id} | {status} | {similarity} | {compared} | {excluded} |".format(
                    comparison_id=comparison["comparison_id"],
                    status=comparison["status"],
                    similarity=similarity_text,
                    compared=compared,
                    excluded=excluded,
                )
            )

    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a live natal/forecast benchmark pack from a manifest, "
            "forcing explicit llm_mode and recording report ids plus compared sections."
        )
    )
    parser.add_argument("--manifest", required=True, help="Path to the benchmark manifest JSON file.")
    parser.add_argument("--llm-mode", help="Explicit llm_mode for cases that do not set it in the manifest.")
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Optional case id filter. Repeat to run multiple specific cases.",
    )
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend base URL.")
    parser.add_argument(
        "--telegram-auth",
        default=(
            os.getenv("X_TELEGRAM_AUTH")
            or os.getenv("TELEGRAM_AUTH")
            or os.getenv("DEV_TELEGRAM_ID")
            or "12345"
        ),
        help="X-Telegram-Auth header value.",
    )
    parser.add_argument(
        "--backend-container",
        default=os.getenv("BACKEND_CONTAINER") or "astro-project-backend-1",
        help="Backend Docker container name used for DEFAULT_LLM_MODE audit.",
    )
    parser.add_argument(
        "--out-dir",
        default="tmp/quality_benchmark_runs",
        help="Output directory for JSON/Markdown benchmark artifacts.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=None,
        help="Override poll interval in seconds.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Override per-case timeout in seconds.",
    )
    parser.add_argument(
        "--allow-stub-benchmark",
        action="store_true",
        help="Allow stub/local/mock/fallback llm_mode on purpose.",
    )
    parser.add_argument(
        "--allow-missing-backend-env",
        action="store_true",
        help="Do not fail if the backend container env cannot be inspected.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest).resolve()
    manifest = read_manifest(manifest_path)
    selected_cases = select_cases(manifest, args.case)
    backend_runtime = inspect_backend_runtime(
        container_name=args.backend_container,
        allow_missing_backend_env=args.allow_missing_backend_env,
    )

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{slugify(manifest['benchmark_id'])}-{run_stamp}"
    poll_interval = args.poll_interval or float(manifest.get("poll_interval_seconds") or 5.0)
    timeout_seconds = args.timeout or float(manifest.get("timeout_seconds") or 900.0)
    default_excludes = [str(item) for item in manifest.get("default_compare_exclude_sections") or DEFAULT_COMPARE_EXCLUDES]
    headers = build_request_headers(args.telegram_auth)
    resolved_modes = {
        case["id"]: resolve_case_llm_mode(
            case=case,
            cli_llm_mode=args.llm_mode,
            allow_stub_benchmark=args.allow_stub_benchmark,
        )
        for case in selected_cases
    }

    print(f"Benchmark: {manifest['benchmark_id']}")
    print(f"Manifest: {manifest_path}")
    if backend_runtime.get("available"):
        print(
            "Backend runtime: container={container} DEFAULT_LLM_MODE={mode} LLM_SMOKE={smoke}".format(
                container=backend_runtime["container_name"],
                mode=backend_runtime.get("default_llm_mode") or "unset",
                smoke=backend_runtime.get("llm_smoke") or "unset",
            )
        )
    else:
        print(
            "Backend runtime audit unavailable: {error}".format(
                error=backend_runtime.get("error") or "unknown error"
            )
        )
    print(f"Output run id: {run_id}")

    case_states: dict[str, dict[str, Any]] = {}
    any_failures = False

    for case in selected_cases:
        requested_llm_mode = resolved_modes[case["id"]]
        payload = build_case_payload(case, requested_llm_mode=requested_llm_mode, run_id=run_id)
        case_id = case["id"]
        started_at = utc_now_iso()
        print(f"Running case {case_id}: {payload['report_type']} llm_mode={requested_llm_mode}")

        create_response: dict[str, Any] | None = None
        report_detail: dict[str, Any] | None = None
        poll_attempts = 0
        timed_out = False
        request_error: str | None = None
        last_http_error: dict[str, Any] | None = None
        started_monotonic = time.monotonic()

        try:
            status_code, create_payload, raw_text = request_json(
                "POST",
                f"{args.api_url}/api/workflows/report/async",
                headers=headers,
                payload=payload,
            )
            if status_code != 200 or not create_payload:
                request_error = f"create failed: status={status_code} body={raw_text[:1000]}"
                any_failures = True
            else:
                create_response = create_payload
                report_id = str(create_payload["report_id"])
                poll_result = poll_report_until_terminal(
                    api_url=args.api_url,
                    headers=headers,
                    report_id=report_id,
                    poll_interval=poll_interval,
                    timeout_seconds=timeout_seconds,
                )
                report_detail = poll_result["detail"]
                poll_attempts = int(poll_result["attempts"])
                timed_out = bool(poll_result["timed_out"])
                last_http_error = poll_result.get("last_http_error")
                if timed_out:
                    any_failures = True
                elif str(((report_detail or {}).get("report") or {}).get("status") or "").lower() != "completed":
                    any_failures = True
        except requests.RequestException as exc:
            request_error = f"request exception: {exc}"
            any_failures = True

        finished_at = utc_now_iso()
        duration_seconds = round(time.monotonic() - started_monotonic, 3)
        case_state = build_case_state(
            case=case,
            payload=payload,
            requested_llm_mode=requested_llm_mode,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
            create_response=create_response,
            report_detail=report_detail,
            poll_attempts=poll_attempts,
            timed_out=timed_out,
            request_error=request_error,
            last_http_error=last_http_error,
        )
        case_states[case_id] = case_state

        record = case_state["record"]
        print(
            "  status={status} duration={duration:.3f}s report_id={report_id}".format(
                status=record["status"],
                duration=record["duration_seconds"],
                report_id=record.get("report_id") or "-",
            )
        )

    comparison_specs = []
    for comparison in manifest.get("comparisons") or []:
        left = str(comparison.get("left") or "")
        right = str(comparison.get("right") or "")
        if left in case_states and right in case_states:
            comparison_specs.append(comparison)

    comparison_records = [
        build_comparison_record(comparison, case_states, default_excludes)
        for comparison in comparison_specs
    ]

    result = {
        "metadata": {
            "run_id": run_id,
            "benchmark_id": manifest["benchmark_id"],
            "notes": manifest.get("notes"),
            "manifest_path": str(manifest_path),
            "api_url": args.api_url,
            "telegram_auth_hint": mask_secret(args.telegram_auth),
            "selected_case_ids": [case["id"] for case in selected_cases],
            "poll_interval_seconds": poll_interval,
            "timeout_seconds": timeout_seconds,
            "backend_runtime": backend_runtime,
            "default_compare_exclude_sections": default_excludes,
            "started_at": min(case_state["record"]["started_at"] for case_state in case_states.values()),
            "finished_at": max(case_state["record"]["finished_at"] for case_state in case_states.values()),
        },
        "cases": [case_states[case["id"]]["record"] for case in selected_cases],
        "comparisons": comparison_records,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{run_id}.json"
    md_path = out_dir / f"{run_id}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown_summary(result), encoding="utf-8")

    report_ids = [
        f"{case['case_id']}={case['report_id']}"
        for case in result["cases"]
        if case.get("report_id")
    ]
    print(f"Saved JSON: {json_path}")
    print(f"Saved Markdown: {md_path}")
    if report_ids:
        print("Report IDs: " + ", ".join(report_ids))

    return 1 if any_failures else 0


if __name__ == "__main__":
    sys.exit(main())
