import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

from backend.app import logging_utils

# test_day_brief installs a lightweight week_brief_service stub for isolated
# day tests. Drop that stub when this module is collected in the same process.
_week_brief_module = sys.modules.get("backend.app.services.week_brief_service")
if _week_brief_module is not None and not getattr(_week_brief_module, "__file__", None):
    sys.modules.pop("backend.app.services.week_brief_service", None)

from backend.app.services.week_brief_service import (
    build_week_brief_envelope,
    build_week_brief_payload,
)
from backend.app.services.week_brief_seed import build_week_brief_seed_bundle
from backend.app.services.week_brief_validators import (
    validate_week_brief_envelope_payload,
    validate_week_brief_payload,
)


def _sample_context() -> dict:
    return {
        "forecast_window": {"start": "2026-03-30T05:00:00+03:00", "days": 7},
        "week_forecast_data": {
            "summary": {"traffic_light": "YELLOW", "avg_tension": 0.7},
            "days": [
                {
                    "date": "2026-03-30",
                    "weekday": "Monday",
                    "moon": {"sign": "Овен", "phase": "Растущая", "void_of_course": False},
                    "ingresses": ["Меркурий -> Овен"],
                    "aspects": [{"transit": "Марс", "natal": "Солнце", "aspect": "Квадрат"}],
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                    "tension_score": 0.7,
                },
                {
                    "date": "2026-03-31",
                    "weekday": "Tuesday",
                    "moon": {"sign": "Телец", "phase": "Растущая", "void_of_course": False},
                    "aspects": [{"transit": "Венера", "natal": "Венера", "aspect": "Секстиль"}],
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "tension_score": -0.4,
                },
                {
                    "date": "2026-04-01",
                    "weekday": "Wednesday",
                    "moon": {"sign": "Близнецы", "phase": "Растущая", "void_of_course": False},
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                    "tension_score": 0.3,
                },
                {
                    "date": "2026-04-02",
                    "weekday": "Thursday",
                    "moon": {"sign": "Рак", "phase": "Растущая", "void_of_course": True},
                    "traffic_light": "RED",
                    "traffic_desc": "🔴 Шторм",
                    "tension_score": 2.3,
                },
                {
                    "date": "2026-04-03",
                    "weekday": "Friday",
                    "moon": {"sign": "Лев", "phase": "Растущая", "void_of_course": False},
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "tension_score": -0.3,
                },
                {
                    "date": "2026-04-04",
                    "weekday": "Saturday",
                    "moon": {"sign": "Дева", "phase": "Растущая", "void_of_course": False},
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                    "tension_score": 0.4,
                },
                {
                    "date": "2026-04-05",
                    "weekday": "Sunday",
                    "moon": {"sign": "Весы", "phase": "Полнолуние", "void_of_course": False},
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "tension_score": -0.1,
                },
            ],
        },
        "month_forecast_data": {
            "major_transits": [
                "31.03 Сатурн Квадрат Солнце",
                "04.04 Юпитер Тригон Меркурий",
            ],
            "ingresses": ["30.03 Меркурий -> Овен"],
            "retrogrades": ["01.04 Меркурий -> R (Ретро)"],
            "lunations": ["05.04 Полнолуние в Весах"],
        },
        "year_forecast_data": {
            "profection": {"house": 10, "lord": "Венера", "age": 36},
            "solar_return": {"datetime": "2026-03-20T10:00:00+03:00", "asc_sign": "Овен", "sun_house": 10},
            "solar_arcs": [{"direction": "Сатурн", "natal": "MC", "orb": 0.4}],
        },
    }


def _sample_chunks():
    return [
        SimpleNamespace(section="week_strategy", content='[{"type":"header","level":2,"text":"Стратегия недели"},{"type":"paragraph","text":"Неделя лучше идет через одну линию и короткие проверки."}]', status="completed", order_index=0),
        SimpleNamespace(section="money", content='[{"type":"header","level":2,"text":"Работа и деньги"},{"type":"list","items":["Подтверждай условия письменно","Сужай фронт до главного"]}]', status="completed", order_index=1),
    ]


def _sample_report(status: str = "completed"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        report_type="week_forecast",
        status=status,
        created_at=datetime(2026, 3, 30, 5, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 30, 6, 0, tzinfo=timezone.utc),
        error_message=None,
    )


def _sample_payload():
    return SimpleNamespace(llm_mode="cheap", birth_time_known=True)


def _read_jsonl_rows_from_offset(path: Path, offset: int) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        return [json.loads(line) for line in handle if line.strip()]


def test_build_week_brief_payload_validates_schema_and_logs_telemetry():
    report = _sample_report()
    chunks = _sample_chunks()
    telemetry = []

    with patch("backend.app.services.week_brief_service.log_grace_event", side_effect=lambda *args, **kwargs: telemetry.append((args, kwargs))):
        payload = build_week_brief_payload(
            report=report,
            payload=_sample_payload(),
            context=_sample_context(),
            chunks=chunks,
            user=SimpleNamespace(subscription_active_until=datetime(2026, 4, 30, tzinfo=timezone.utc)),
            llm_model="deterministic",
        )

    validated = validate_week_brief_payload(payload)
    assert validated["status"] == "ready"
    assert validated["fallback_mode"] is False
    assert len(validated["day_cards"]) == 7
    assert len(validated["domains"]) == 4
    assert len(validated["major_factors"]) >= 1
    assert len(validated["deep_sections"]) >= 2
    assert [section["slug"] for section in validated["deep_sections"][:2]] == ["overview", "timing"]
    assert validated["report_ref"]["report_id"] == str(report.id)
    built_events = [call for call in telemetry if call[0][1] == "week_brief_built"]
    assert built_events
    assert built_events[-1][1]["module"] == "M-WEEK-BRIEF-SERVICE"
    assert built_events[-1][1]["fn"] == "build_week_brief_payload"
    assert built_events[-1][1]["block"] == "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
    assert built_events[-1][1]["week_brief_evidence_lane"] == "packet_local"
    assert built_events[-1][1]["week_brief_fallback_mode"] is False
    assert built_events[-1][1]["week_brief_confidence_bucket"] in {"medium", "high"}


def test_build_week_brief_payload_keeps_neighbor_day_cards_differentiated():
    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=_sample_chunks(),
        user=None,
    )

    monday = payload["day_cards"][0]
    tuesday = payload["day_cards"][1]
    thursday = payload["day_cards"][3]

    assert monday["headline"] != tuesday["headline"]
    assert monday["best_for"] != tuesday["best_for"]
    assert monday["headline"] == "День лучше вести спокойно и по шагам"
    assert any("Телец" in item for item in tuesday["best_for"])
    assert any("Квадрат" in item for item in monday["avoid"])
    assert any(any(token in item.lower() for token in ("перегруз", "жесткий спор", "пустот")) for item in thursday["avoid"])


def test_build_week_brief_payload_falls_back_but_stays_schema_valid():
    report = _sample_report(status="failed")
    bad_chunks = [SimpleNamespace(section="week_strategy", content="{not-json", status="failed", order_index=0)]
    telemetry = []

    with patch("backend.app.services.week_brief_service.log_grace_event", side_effect=lambda *args, **kwargs: telemetry.append((args, kwargs))):
        payload = build_week_brief_payload(
            report=report,
            payload=_sample_payload(),
            context={},
            chunks=bad_chunks,
            user=None,
            llm_model="deterministic",
        )

    validated = validate_week_brief_payload(payload)
    assert validated["status"] == "error"
    assert validated["fallback_mode"] is True
    assert len(validated["day_cards"]) == 7
    assert len(validated["major_factors"]) == 1
    assert [section["slug"] for section in validated["deep_sections"]] == ["overview"]
    assert "# Каркас недели" in validated["deep_sections"][0]["body_markdown"]
    fallback_events = [call for call in telemetry if call[0][1] == "week_brief_fallback_triggered"]
    assert fallback_events
    assert fallback_events[-1][1]["module"] == "M-WEEK-BRIEF-SERVICE"
    assert fallback_events[-1][1]["fn"] == "build_week_brief_payload"
    assert fallback_events[-1][1]["block"] == "WEEK_BRIEF_FALLBACK_RECOVERY"
    assert fallback_events[-1][1]["week_brief_evidence_lane"] == "packet_local"
    assert any(call[0][1] == "week_brief_built" and call[1]["week_brief_fallback_mode"] is True for call in telemetry)


def test_build_week_brief_payload_keeps_seed_sections_when_chunk_json_is_invalid():
    report = _sample_report()
    bad_chunks = [
        SimpleNamespace(section="week_strategy", content="{not-json", status="failed", order_index=0),
        SimpleNamespace(section="money", content="plain prose that is not json", status="completed", order_index=1),
    ]

    payload = build_week_brief_payload(
        report=report,
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=bad_chunks,
        user=None,
        llm_model="deterministic",
    )

    validated = validate_week_brief_payload(payload)
    assert validated["fallback_mode"] is False
    assert [section["slug"] for section in validated["deep_sections"][:3]] == ["overview", "timing", "background"]
    assert all(section["summary"] for section in validated["deep_sections"])
    assert "Неделя" in validated["deep_sections"][0]["body_markdown"] or "Каркас недели" in validated["deep_sections"][0]["body_markdown"]


def test_build_week_brief_envelope_supports_ready_and_in_progress_states():
    ready_report = _sample_report()
    ready_payload = build_week_brief_payload(
        report=ready_report,
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )
    ready_envelope = build_week_brief_envelope(report=ready_report, week_brief=ready_payload)
    validated_ready = validate_week_brief_envelope_payload(ready_envelope)

    assert validated_ready["status"] == "ready"
    assert validated_ready["data"]["report_ref"]["report_id"] == str(ready_report.id)

    pending_report = _sample_report(status="in_progress")
    pending_envelope = build_week_brief_envelope(report=pending_report, week_brief=None)
    validated_pending = validate_week_brief_envelope_payload(pending_envelope)

    assert validated_pending["status"] == "in_progress"
    assert validated_pending["data"] is None
    assert validated_pending["retry_after_seconds"] == 3


def test_week_top_layer_is_deterministic_for_same_seed():
    report = _sample_report()
    context = _sample_context()
    payload_a = build_week_brief_payload(
        report=report,
        payload=_sample_payload(),
        context=context,
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )
    payload_b = build_week_brief_payload(
        report=report,
        payload=_sample_payload(),
        context=context,
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    assert payload_a["major_factors"] == payload_b["major_factors"]
    assert [item["id"] for item in payload_a["major_factors"]] == [item["id"] for item in payload_b["major_factors"]]


def test_week_brief_prefers_theme_anchor_and_preserves_explainability_order():
    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    factor_ids = [item["id"] for item in payload["major_factors"]]
    assert factor_ids[0] == "week:theme_anchor"
    assert "week:profection:10" in factor_ids
    assert payload["explainability"]["factor_count"] >= len(payload["major_factors"])
    assert payload["explainability"]["reliability_support"]
    assert payload["explainability"]["calibration"]["weight_profile_version"] == "v2"

def test_validate_week_brief_payload_preserves_week_explainability_extension_fields():
    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    validated = validate_week_brief_payload(payload)

    assert validated["fallback_mode"] is False
    assert validated["explainability"]["reliability_support"]
    assert validated["explainability"]["calibration"]["weight_profile_version"] == "v2"
    assert "entrypoints" in validated["explainability"]["calibration"]

def test_week_brief_keeps_non_fallback_when_seed_is_complete_but_some_chunks_are_degraded():
    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=[
            SimpleNamespace(
                section="week_strategy",
                content='[{"type":"header","level":2,"text":"Стратегия недели"},{"type":"paragraph","text":"Неделя лучше идет через одну линию и короткие проверки."}]',
                status="completed",
                order_index=0,
            ),
            SimpleNamespace(
                section="money",
                content="plain markdown text from degraded live chunk",
                status="failed",
                order_index=1,
            ),
        ],
        user=None,
        llm_model="deterministic",
    )

    validated = validate_week_brief_payload(payload)

    assert validated["fallback_mode"] is False
    assert validated["deep_sections"]
    assert any(section["slug"] == "overview" for section in validated["deep_sections"])
    assert validated["explainability"]["confidence"] < 0.9
    assert validated["explainability"]["explanation_depth"] in {"full", "standard"}


def test_week_brief_does_not_flag_chunk_parse_degraded_for_traffic_lights_blocks():
    telemetry = []
    week_strategy_chunk = SimpleNamespace(
        section="week_strategy",
        content="""
        [
          {"type":"header","level":2,"text":"📅 ПРОГНОЗ НА НЕДЕЛЮ"},
          {"type":"callout","variant":"warning","title":"СТАТУС НЕДЕЛИ","content":"Неделя требует спокойного темпа и коротких проверок."},
          {"type":"header","level":2,"text":"Главная тема"},
          {"type":"paragraph","text":"Главный результат даст одна опорная линия и ясные договоренности."},
          {"type":"header","level":2,"text":"Резюме по срезам"},
          {"type":"traffic_lights","items":{"money":"yellow","health":"yellow","love":"green"}}
        ]
        """,
        status="completed",
        order_index=0,
    )

    with patch("backend.app.services.week_brief_service.log_grace_event", side_effect=lambda *args, **kwargs: telemetry.append((args, kwargs))):
        payload = build_week_brief_payload(
            report=_sample_report(),
            payload=_sample_payload(),
            context=_sample_context(),
            chunks=[week_strategy_chunk],
            user=None,
            llm_model="deterministic",
        )

    validated = validate_week_brief_payload(payload)
    assert validated["fallback_mode"] is False
    built_events = [call for call in telemetry if call[0][1] == "week_brief_built"]
    assert built_events
    assert built_events[-1][1]["chunk_parse_degraded"] is False


def test_week_brief_uses_report_created_window_when_seed_days_are_stale_or_missing():
    report = _sample_report()

    payload = build_week_brief_payload(
        report=report,
        payload=_sample_payload(),
        context={},
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    assert payload["week_start"] == "2026-03-30"
    assert payload["week_end"] == "2026-04-05"


def test_week_brief_suppresses_raw_astro_phrases_in_user_facing_day_and_risk_copy():
    context = _sample_context()
    context["week_forecast_data"]["days"] = [
        {
            "date": "2026-03-30",
            "weekday": "Monday",
            "moon": {"sign": "Весы", "phase": "Полнолуние", "void_of_course": False},
            "events": ["03.04 Нептун Квадрат (90°) MC"],
            "traffic_light": "RED",
            "traffic_desc": "🔴 Шторм",
            "tension_score": 2.8,
        }
    ]

    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=context,
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    first_day = payload["day_cards"][0]
    assert "Нептун Квадрат" not in first_day["headline"]
    assert first_day["id"].startswith("week-day-")
    assert isinstance(first_day["factor_ids"], list)
    assert "details" in first_day
    assert set(first_day["details"].keys()) == {"why_text", "why_title", "supporting_factors"}
    assert all("Нептун Квадрат" not in item for item in first_day["best_for"])
    assert payload["risks"][0]["text"]
    assert "Нептун Квадрат" not in payload["risks"][0]["text"]


def test_week_brief_service_imports_week_owned_seed_boundary():
    source = Path("backend/app/services/week_brief_service.py").read_text(encoding="utf-8")

    assert "from .week_brief_seed import (" in source
    assert "from .report_workflow import (" not in source


def test_week_brief_service_exposes_packet_local_grace_contract_markers():
    source = Path("backend/app/services/week_brief_service.py").read_text(encoding="utf-8")

    assert "# START_MODULE_CONTRACT: M-WEEK-BRIEF-SERVICE" in source
    assert "# START_MODULE_MAP: M-WEEK-BRIEF-SERVICE" in source
    assert 'MODULE_ID = "M-WEEK-BRIEF-SERVICE"' in source
    assert 'WEEK_BRIEF_EVIDENCE_LANE = "packet_local"' in source
    assert 'WEEK_BRIEF_PACKET_SCOPE = "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:W01:packet_local"' in source
    assert 'WEEK_BRIEF_PAYLOAD_BLOCK = "WEEK_BRIEF_PAYLOAD_ASSEMBLY"' in source


def test_week_brief_service_declares_grace_module_contract_map_blocks_and_entrypoints():
    source = Path("backend/app/services/week_brief_service.py").read_text(encoding="utf-8")

    assert "START_MODULE_CONTRACT: M-WEEK-BRIEF" in source
    assert "END_MODULE_CONTRACT: M-WEEK-BRIEF" in source
    assert "START_MODULE_MAP: M-WEEK-BRIEF" in source
    assert "END_MODULE_MAP: M-WEEK-BRIEF" in source
    assert "# GRACE_ANCHORS: [WEEK_BRIEF_CONSTANTS, WEEK_BRIEF_TYPES, WEEK_BRIEF_TELEMETRY, WEEK_BRIEF_NORMALIZATION, WEEK_BRIEF_FACTORS, WEEK_BRIEF_ENTRYPOINTS]" in source

    for block in [
        "WEEK_BRIEF_CONSTANTS",
        "WEEK_BRIEF_TYPES",
        "WEEK_BRIEF_TELEMETRY",
        "WEEK_BRIEF_NORMALIZATION",
        "WEEK_BRIEF_FACTORS",
        "WEEK_BRIEF_ENTRYPOINTS",
    ]:
        assert f"START_BLOCK: {block}" in source
        assert f"END_BLOCK: {block}" in source

    for contract in [
        "FN-LOG-WEEK-BRIEF",
        "FN-BUILD-WEEK-BRIEF-SEED",
        "FN-BUILD-WEEK-BRIEF-FALLBACK",
        "FN-BUILD-WEEK-BRIEF-PAYLOAD",
        "FN-BUILD-WEEK-BRIEF-ENVELOPE",
    ]:
        assert f"START_CONTRACT: {contract}" in source
        assert f"END_CONTRACT: {contract}" in source


def test_build_week_brief_payload_keeps_stable_behavior_with_partial_seed_context():
    partial_context = {
        "forecast_window": {"start": "2026-03-30T05:00:00+03:00", "days": 7},
        "week_forecast_data": {
            "days": [
                {
                    "date": "2026-03-30",
                    "weekday": "Monday",
                    "moon": {"sign": "Aries", "phase": "Растущая", "void_of_course": False},
                    "aspects": [{"transit": "Mars", "natal": "Sun", "aspect": "square"}],
                    "traffic_light": "YELLOW",
                    "tension_score": 0.7,
                }
            ],
        },
    }

    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=partial_context,
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    validated = validate_week_brief_payload(payload)
    assert validated["fallback_mode"] is False
    assert validated["summary"]["headline"]
    assert validated["day_cards"][0]["weekday"] == "mon"
    assert validated["day_cards"][0]["details"]["why_text"]
    assert validated["major_factors"]
    assert validated["report_ref"]["report_type"] == "week_forecast"

    seed = build_week_brief_seed_bundle(partial_context)
    assert seed["summary"]["traffic_light"] == "YELLOW"
    assert seed["days"][0]["events"] == ["Марс square Солнце"]
    assert seed["days"][0]["moon"]["sign"] == "Овен"


def test_build_week_brief_payload_appends_current_run_packet_local_report_log():
    report_log = logging_utils.LOG_DIR / "report.jsonl"
    start_offset = report_log.stat().st_size if report_log.exists() else 0
    report = _sample_report()
    run_marker = uuid.uuid4().hex
    correlation_id = f"corr-week-packet-{run_marker}"
    trace_id = f"trace-week-packet-{run_marker}"
    request_id = f"req-week-packet-{run_marker}"

    previous = logging_utils.set_correlation_ids(
        correlation_id=None,
        trace_id=None,
        correlation_source=None,
        request_id=None,
    )
    try:
        with logging_utils.correlation_scope(
            "week-brief-test",
            correlation_id=correlation_id,
            trace_id=trace_id,
            request_id=request_id,
        ):
            payload = build_week_brief_payload(
                report=report,
                payload=_sample_payload(),
                context=_sample_context(),
                chunks=_sample_chunks(),
                user=None,
                llm_model="deterministic",
            )
    finally:
        logging_utils.set_correlation_ids(**previous)

    validated = validate_week_brief_payload(payload)
    assert validated["fallback_mode"] is False

    rows = _read_jsonl_rows_from_offset(report_log, start_offset)
    built_row = next(
        row
        for row in rows
        if row["event"] == "week_brief_built" and row.get("trace_id") == trace_id
    )

    assert built_row["module"] == "M-WEEK-BRIEF-SERVICE"
    assert built_row["fn"] == "build_week_brief_payload"
    assert built_row["block"] == "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
    assert built_row["week_brief_evidence_lane"] == "packet_local"
    assert built_row["week_brief_packet_scope"] == "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:W01:packet_local"
    assert built_row["trace_id"] == trace_id
    assert built_row["correlation_id"] == correlation_id
    assert built_row["request_id"] == request_id
    assert built_row["report_id"] == str(report.id)
