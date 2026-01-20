import json
import urllib.request
import sys
import os

# GRACE Report Matrix Verification Script
# PURPOSE: Verify all core report types and downloads.
# CONTEXT: Hits the running backend via Docker.

API_URL = "http://localhost:8000"


BASE_PAYLOAD = {
    "client_name": "Grace Matrix Tester",
    "birth_date": "1990-01-01T12:00:00",
    "birth_location": "Moscow",
    "birth_lat": 55.7558,
    "birth_lon": 37.6173,
    "birth_timezone": "Europe/Moscow",
    "include_fixed_stars": False,
    "fixed_star_orb": 1.0,
    "llm_mode": "openrouter",
}

REPORT_CASES = [
    {"report_type": "natal_master"},
    {"report_type": "week_forecast"},
    {"report_type": "month_forecast"},
    {"report_type": "year_forecast"},
    {"report_type": "ten_year_forecast"},
    {"report_type": "horary_answer"},
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


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def get_text(url: str) -> tuple[str, dict]:
    with urllib.request.urlopen(url) as response:
        content = response.read().decode("utf-8")
        headers = {key.lower(): value for key, value in response.headers.items()}
        return content, headers


def get_bytes(url: str) -> tuple[bytes, dict]:
    with urllib.request.urlopen(url) as response:
        content = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}
        return content, headers


def validate_content(report_type: str, section_id: str, content: str) -> None:
    if not content or len(content.strip()) < 60:
        raise AssertionError(
            f"Empty or too short content for {report_type}:{section_id}"
        )
    if report_type == "natal_master":
        lowered = content.lower()
        if section_id == "input_frame":
            required = [
                "кверент",
                "дата рождения",
                "место рождения",
                "система домов",
                "положение планет",
                "| планета |",
                "угловые точки",
            ]
            for token in required:
                if token not in lowered:
                    raise AssertionError(
                        f"Missing {token} in {report_type}:{section_id}"
                    )
            return
        if section_id == "synthesis":
            for token in ["метафора", "главный тезис"]:
                if token not in lowered:
                    raise AssertionError(
                        f"Missing {token} in {report_type}:{section_id}"
                    )
            return
        if section_id == "axes_truths":
            for token in ["твоя правда", "правда партнера"]:
                if token not in lowered:
                    raise AssertionError(
                        f"Missing {token} in {report_type}:{section_id}"
                    )
            if "2-8" not in content or "3-9" not in content:
                raise AssertionError(
                    f"Missing axis pairs in {report_type}:{section_id}"
                )
            return
        if section_id == "balance_wheel":
            if "1 дом" not in lowered or "12 дом" not in lowered:
                raise AssertionError(
                    f"Missing houses in {report_type}:{section_id}"
                )
            for token in [
                "тема:",
                "в плюсе:",
                "в минусе:",
                "триггер:",
                "вектор зрелости:",
                "вопрос:",
            ]:
                if token not in lowered:
                    raise AssertionError(
                        f"Missing {token} in {report_type}:{section_id}"
                    )
            return
        if section_id == "final_synthesis":
            for token in ["твой девиз", "главный совет"]:
                if token not in lowered:
                    raise AssertionError(
                        f"Missing {token} in {report_type}:{section_id}"
                    )
            return
        return
    if report_type == "month_forecast":
        required = [
            "статус месяца",
            "центральная нить смысла",
            "главные активаторы",
            "карта сфер",
            "событийный слой",
            "личный слой",
            "глубинный слой",
            "солярный контекст",
            "тайм-лорды",
            "фиксирован",
            "трансураны",
            "итог месяца",
        ]
        lowered = content.lower()
        for token in required:
            if token not in lowered:
                raise AssertionError(
                    f"Missing {token} in {report_type}:{section_id}"
                )
        if "→" not in content:
            raise AssertionError(
                f"Missing activator format in {report_type}:{section_id}"
            )
        if not any(icon in content for icon in ["🟢", "🟡", "🔴"]):
            raise AssertionError(
                f"Missing status indicators in {report_type}:{section_id}"
            )
        return
    has_bullets = "\n-" in content or "\n*" in content
    if not has_bullets:
        raise AssertionError(
            f"Missing bullet list for {report_type}:{section_id}"
        )
    if "Рекомендации" not in content and "Recommendations" not in content:
        raise AssertionError(
            f"Missing recommendations block for {report_type}:{section_id}"
        )


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
        validate_content(report_type, section_id, content)

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

    markdown, markdown_headers = get_text(
        f"{API_URL}/api/admin/reports/{report_id}/markdown"
    )
    if not markdown.strip():
        raise AssertionError(f"Markdown download empty for {report_type}")
    if "text/markdown" not in markdown_headers.get("content-type", ""):
        raise AssertionError(f"Markdown content-type invalid for {report_type}")

    pdf_bytes, pdf_headers = get_bytes(
        f"{API_URL}/api/admin/reports/{report_id}/pdf"
    )
    if not pdf_bytes.startswith(b"%PDF"):
        raise AssertionError(f"PDF signature missing for {report_type}")
    if "application/pdf" not in pdf_headers.get("content-type", ""):
        raise AssertionError(f"PDF content-type invalid for {report_type}")

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
