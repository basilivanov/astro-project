import json
import os
import re
import sys
import urllib.request
from typing import Optional

sys.path.append(os.getcwd())

from backend.app.llm.validator import validate_llm_hallucinations
from backend.app.reporting.markdown_helpers import get_chart_facts_json

# GRACE Report Matrix Verification Script
# PURPOSE: Verify all core report types and downloads.
# CONTEXT: Hits the running backend via Docker.

API_URL = "http://localhost:8000"

AUTH_HEADER = (
    os.getenv("X_TELEGRAM_AUTH")
    or os.getenv("TELEGRAM_AUTH")
    or os.getenv("TELEGRAM_INIT_DATA")
    or os.getenv("DEV_TELEGRAM_ID")
)
REQUIRE_AUTH = (os.getenv("REQUIRE_AUTH") or "").strip().lower() in {"1", "true", "yes"}
if not AUTH_HEADER:
    if REQUIRE_AUTH:
        print("!!! Missing X-Telegram-Auth header. Set TELEGRAM_AUTH to run API tests.")
        sys.exit(1)
    print("!!! Missing X-Telegram-Auth header. Set TELEGRAM_AUTH or REQUIRE_AUTH=1. Skipping API tests.")
    sys.exit(0)

BASE_PAYLOAD = {
    "client_name": "Grace Matrix Tester",
    "birth_date": "1990-01-01T12:00:00",
    "birth_location": "Moscow",
    "birth_lat": 55.7558,
    "birth_lon": 37.6173,
    "birth_timezone": "Europe/Moscow",
    "include_fixed_stars": False,
    "fixed_star_orb": 1.0,
    "llm_mode": "cli",
}

LLM_MODE = (os.getenv("LLM_MODE") or "").strip().lower()
if LLM_MODE:
    BASE_PAYLOAD["llm_mode"] = LLM_MODE

RELAX_VALIDATION = BASE_PAYLOAD["llm_mode"] in {"fallback", "local", "mock", "stub"}

REPORT_CASES = [
    {"report_type": "natal_master"},
    {"report_type": "week_forecast"},
    {"report_type": "month_forecast"},
    {"report_type": "year_forecast"},
    {"report_type": "ten_year_forecast"},
    {"report_type": "solar_return"},
    {
        "report_type": "horary_answer",
        "extra": {
            "question": "Завтра суд: права заберут или обойдется штрафом?",
            "client_note": "Суд завтра",
        },
    },
    {
        "report_type": "synastry",
        "extra": {
            "partner_name": "Partner Tester",
            "partner_birth_date": "1992-02-02T06:30:00",
            "partner_birth_location": "London",
            "partner_birth_lat": 51.5074,
            "partner_birth_lon": -0.1278,
            "partner_birth_timezone": "Europe/London",
        },
    },
]

REPORT_FILTER = (os.getenv("REPORT_TYPE") or "").strip().lower()

PROGRAMMATIC_SECTIONS = {
    "input_frame",
    "technical_appendix",
    "horary_00_passport",
    "horary_00_technical",
}

FORBIDDEN_TAIL_PHRASES = [
    "ключевой фокус",
    "потенциал и ресурс",
    "риск и зона внимания",
]

ALLOWED_LATIN_PATTERNS = [
    r"\bL\d+\b",
    r"\bASC\b",
    r"\bMC\b",
    r"\bDSC\b",
    r"\bIC\b",
]


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Telegram-Auth": AUTH_HEADER or "",
        },
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "X-Telegram-Auth": AUTH_HEADER or "",
        },
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_blocks(content: str, section_id: str) -> list:
    if isinstance(content, list):
        blocks = content
    else:
        try:
            blocks = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Invalid JSON blocks for {section_id}: {content[:120]}..."
            ) from exc
    if not isinstance(blocks, list) or not blocks:
        raise AssertionError(f"Empty JSON blocks for {section_id}")
    for block in blocks:
        if not isinstance(block, dict) or "type" not in block:
            raise AssertionError(f"Block missing type for {section_id}")
    return blocks


def flatten_blocks(blocks: list) -> str:
    parts: list[str] = []
    for block in blocks:
        b_type = block.get("type")
        if b_type == "header":
            parts.append(str(block.get("text", "")))
        elif b_type == "paragraph":
            parts.append(str(block.get("text", "")))
        elif b_type == "list":
            parts.extend([str(item) for item in block.get("items", [])])
        elif b_type == "callout":
            parts.append(str(block.get("title", "")))
            parts.append(str(block.get("content", "")))
        elif b_type == "table":
            cols = block.get("columns", [])
            parts.extend([str(col.get("header", "")) for col in cols])
            for row in block.get("rows", []):
                parts.extend([str(cell) for cell in row])
        elif b_type == "key_value":
            for item in block.get("items", []):
                parts.append(str(item.get("key", "")))
                parts.append(str(item.get("value", "")))
        elif b_type == "rating":
            parts.append(str(block.get("label", "")))
    return " ".join(parts)


def collect_headers(blocks: list) -> list[str]:
    return [
        str(block.get("text", "")).strip().lower()
        for block in blocks
        if block.get("type") == "header"
    ]


def strip_allowed_latin(text: str) -> str:
    cleaned = text
    for pattern in ALLOWED_LATIN_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned)
    return cleaned


def require_headers(headers: list[str], required: list[str], report_type: str, section_id: str) -> None:
    for token in required:
        if not any(token in header for header in headers):
            raise AssertionError(f"Missing header '{token}' in {report_type}:{section_id}")


def validate_content(report_type: str, section_id: str, content: str, facts: Optional[dict]) -> None:
    blocks = parse_blocks(content, section_id)
    all_text = flatten_blocks(blocks)
    lowered = all_text.lower()

    if RELAX_VALIDATION:
        return

    if section_id not in PROGRAMMATIC_SECTIONS:
        for phrase in FORBIDDEN_TAIL_PHRASES:
            if phrase in lowered:
                raise AssertionError(
                    f"Forbidden tail phrase '{phrase}' in {report_type}:{section_id}"
                )

        if re.search(r"[A-Za-z]", strip_allowed_latin(all_text)):
            raise AssertionError(f"Latin letters found in {report_type}:{section_id}")

    if report_type == "natal_master" and section_id not in PROGRAMMATIC_SECTIONS:
        errors = validate_llm_hallucinations(blocks, facts or {})
        if errors:
            raise AssertionError(
                f"Hallucinations detected in {report_type}:{section_id}: {errors}"
            )

    headers = collect_headers(blocks)
    if report_type == "year_forecast" and section_id.startswith("month_"):
        require_headers(
            headers,
            ["статус", "нить смысла", "активаторы", "карта сфер", "события", "личный слой", "итог"],
            report_type,
            section_id,
        )
    if report_type == "month_forecast" and section_id == "month_full_forecast":
        require_headers(
            headers,
            ["статус месяца", "ключевые события", "стратегия по неделям", "итог месяца"],
            report_type,
            section_id,
        )
    if report_type == "week_forecast" and section_id == "week_strategy":
        require_headers(
            headers,
            ["главная тема", "статус недели", "подневная стратегия", "резюме по срезам"],
            report_type,
            section_id,
        )
    if report_type == "horary_answer" and section_id == "horary_01_verdict":
        has_callout = any(block.get("type") == "callout" for block in blocks)
        if not has_callout:
            raise AssertionError(f"Missing callout in {report_type}:{section_id}")


def run_case(case: dict) -> None:
    report_type = case["report_type"]
    print(f"\n--- [PCAM] Action: Generate {report_type} ---")

    payload = dict(BASE_PAYLOAD)
    payload["report_type"] = report_type
    for key, value in case.get("extra", {}).items():
        payload[key] = value

    response = post_json(f"{API_URL}/api/workflows/report", payload)
    report_id = response.get("report_id")
    sections = response.get("sections", [])
    chart = response.get("chart", {})
    facts = get_chart_facts_json(chart) if chart else {}

    print(f"--- [PCAM] Measure: Report ID: {report_id} ---")
    print(f"--- [PCAM] Measure: Sections Count: {len(sections)} ---")

    if not report_id:
        raise AssertionError(f"Missing report_id for {report_type}")
    if not sections:
        raise AssertionError(f"No sections generated for {report_type}")

    for section in sections:
        section_id = section.get("section_id", "unknown")
        content = section.get("content", "")
        print(f"  > Section [{section_id}]: {len(content)} chars")
        validate_content(report_type, section_id, content, facts)

    report_detail = get_json(
        f"{API_URL}/api/admin/reports/{report_id}?include_content=0"
    )
    report_status = report_detail.get("report", {}).get("status")
    if report_status != "completed":
        raise AssertionError(
            f"Report status not completed for {report_type}: {report_status}"
        )
    for chunk in report_detail.get("chunks", []):
        if chunk.get("status") == "failed":
            raise AssertionError(
                f"Chunk failed for {report_type}: {chunk.get('section')}"
            )

    print(f"--- [GRACE] Result: SUCCESS ({report_type}) ---")


def run_test() -> None:
    print("--- [GRACE] Starting Report Matrix Verification ---")
    cases = REPORT_CASES
    if REPORT_FILTER:
        cases = [
            case
            for case in REPORT_CASES
            if case.get("report_type") == REPORT_FILTER
        ]
        if not cases:
            raise AssertionError(f"Unknown report type: {REPORT_FILTER}")
    for case in cases:
        run_case(case)
    print("\n--- [GRACE] Result: SUCCESS (All report types) ---")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:
        print(f"\n!!! FAILURE: {exc} !!!")
        sys.exit(1)
