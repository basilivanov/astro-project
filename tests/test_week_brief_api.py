import uuid
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.app import logging_utils
from backend.app.main import get_report_detail
from backend.app.services import report_workflow


def test_get_report_detail_returns_week_brief_without_changing_chunks():
    user = SimpleNamespace(id=uuid.uuid4())
    report = SimpleNamespace(
        id=uuid.uuid4(),
        report_type="week_forecast",
        status="completed",
        created_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        client=SimpleNamespace(full_name="Week Client"),
        access_source="subscription",
        chunks=[
            SimpleNamespace(section="week_strategy", content="[]", status="completed", order_index=0),
            SimpleNamespace(section="money", content="[]", status="completed", order_index=1),
        ],
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = report

    week_brief = {
        "version": "week_brief_v1",
        "week_start": "2026-03-30",
        "week_end": "2026-04-05",
        "personalization_level": "personalized_v2",
        "fallback_mode": False,
        "status": "ready",
        "summary": {
            "headline": "Неделя просит точного темпа и фиксации решений.",
            "subhead": "Сильные дни подходят для договоренностей, а слабые лучше вести через буфер и одну линию.",
            "week_type": "balance",
            "theme": "Работа, темп и границы",
        },
        "day_cards": [{
            "id": "week-day-2026-03-30",
            "date": "2026-03-30",
            "weekday": "mon",
            "mode": "green",
            "score": 81,
            "headline": "Держите один главный ритм",
            "lead": "День держится через один главный приоритет.",
            "practical": ["Закрыть приоритет"],
            "supporting_factors": [],
            "details": {"why_text": "Опора на устойчивый ритм.", "why_title": "Почему день так звучит", "supporting_factors": []},
            "factor_ids": ["week:theme_anchor"],
            "best_for": ["Стратегия"],
            "avoid": ["Суета"],
            "peak_window_label": "до 14:00"
        }],
        "domains": [],
        "best_uses": [],
        "risks": [],
        "major_factors": [],
        "deep_sections": [],
        "explainability": {
            "confidence": 0.8,
            "birth_time_used": True,
            "factor_count": 5,
        },
        "report_ref": {
            "report_id": str(report.id),
            "report_type": "week_forecast",
            "source_status": "completed",
        },
    }

    with (
        patch("backend.app.main.load_report_payload", return_value=SimpleNamespace(llm_mode="cheap", birth_time_known=True)),
        patch("backend.app.main.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.main.build_natal_chart_svg", return_value="<svg />"),
        patch("backend.app.main.build_report_context", return_value={"week_brief_seed": {}}),
        patch("backend.app.main.build_week_brief_payload", return_value=week_brief),
        patch("backend.app.main.build_week_brief_envelope", return_value={"status": "ready", "data": week_brief, "message": None, "retry_after_seconds": None}),
    ):
        response = get_report_detail(str(report.id), user=user, db=db)

    assert response["report"]["id"] == str(report.id)
    assert response["chunks"] == [
        {"section": "week_strategy", "content": "[]", "status": "completed", "order_index": 0},
        {"section": "money", "content": "[]", "status": "completed", "order_index": 1},
    ]
    assert response["week_brief"] == week_brief
    assert response["week_brief_envelope"]["status"] == "ready"
    assert response["week_brief_envelope"]["data"] == week_brief


def test_get_report_detail_keeps_week_brief_none_for_non_week_reports():
    user = SimpleNamespace(id=uuid.uuid4())
    report = SimpleNamespace(
        id=uuid.uuid4(),
        report_type="natal_master",
        status="completed",
        created_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        client=SimpleNamespace(full_name="Natal Client"),
        access_source="subscription",
        chunks=[],
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = report

    with (
        patch("backend.app.main.load_report_payload", return_value=SimpleNamespace()),
        patch("backend.app.main.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.main.build_natal_chart_svg", return_value="<svg />"),
    ):
        response = get_report_detail(str(report.id), user=user, db=db)

    assert response["week_brief"] is None
    assert response["week_brief_envelope"] is None


def test_week_prompt_context_delegates_to_week_owned_seed_boundary():
    week_seed = {
        "days": [{"date": "2026-03-30", "weekday_ru": "понедельник"}],
        "summary": {"traffic_light": "GREEN", "avg_tension": -0.1, "status_label": "GREEN"},
        "semantic_layer": {"headline": "Неделя дает ход."},
    }

    with patch("backend.app.services.report_workflow.build_week_brief_seed_bundle_owned", return_value=week_seed) as build_week_seed:
        result = report_workflow._build_week_forecast_prompt_context(
            {
                "client": {"gender": "female", "report_type": "week_forecast", "birth_time_known": True},
                "forecast_window": {"start": "2026-03-30T05:00:00+03:00", "days": 7},
            }
        )

    build_week_seed.assert_called_once()
    assert result["week_forecast_data"]["days"] == week_seed["days"]
    assert result["week_forecast_data"]["summary"] == week_seed["summary"]
    assert result["week_forecast_data"]["semantic_layer"] == week_seed["semantic_layer"]


def test_week_brief_api_contract_keeps_packet_local_service_entrypoints_stable():
    import backend.app.services.week_brief_service as week_brief_service

    assert week_brief_service.MODULE_ID == "M-WEEK-BRIEF-SERVICE"
    assert week_brief_service.WEEK_BRIEF_EVIDENCE_LANE == "packet_local"
    assert week_brief_service.WEEK_BRIEF_PACKET_SCOPE == "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:W01:packet_local"
    assert week_brief_service.WEEK_BRIEF_PAYLOAD_BLOCK == "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
    assert callable(week_brief_service.build_week_brief_payload)
    assert callable(week_brief_service.build_week_brief_envelope)


def _read_jsonl_rows_from_offset(path: Path, offset: int) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        return [json.loads(line) for line in handle if line.strip()]


def _sample_week_context() -> dict:
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


def test_get_report_detail_emits_current_run_week_brief_report_log_chain():
    report_log = logging_utils.LOG_DIR / "report.jsonl"
    start_offset = report_log.stat().st_size if report_log.exists() else 0
    user = SimpleNamespace(id=uuid.uuid4())
    report = SimpleNamespace(
        id=uuid.uuid4(),
        report_type="week_forecast",
        status="completed",
        created_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        client=SimpleNamespace(full_name="Week Client"),
        access_source="subscription",
        chunks=[
            SimpleNamespace(
                section="week_strategy",
                content='[{"type":"header","level":2,"text":"Стратегия недели"},{"type":"paragraph","text":"Неделя лучше идет через одну линию и короткие проверки."}]',
                status="completed",
                order_index=0,
            ),
            SimpleNamespace(
                section="money",
                content='[{"type":"header","level":2,"text":"Работа и деньги"},{"type":"list","items":["Подтверждай условия письменно","Сужай фронт до главного"]}]',
                status="completed",
                order_index=1,
            ),
        ],
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = report

    run_marker = uuid.uuid4().hex
    correlation_id = f"corr-week-api-{run_marker}"
    trace_id = f"trace-week-api-{run_marker}"
    request_id = f"req-week-api-{run_marker}"

    with (
        patch("backend.app.main.load_report_payload", return_value=SimpleNamespace(llm_mode="cheap", birth_time_known=True)),
        patch("backend.app.main.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.main.build_natal_chart_svg", return_value="<svg />"),
        patch("backend.app.main.build_report_context", return_value=_sample_week_context()),
        logging_utils.correlation_scope(
            "week-brief-api-test",
            correlation_id=correlation_id,
            trace_id=trace_id,
            request_id=request_id,
        ),
    ):
        response = get_report_detail(str(report.id), user=user, db=db)

    assert response["week_brief_envelope"]["status"] == "ready"
    rows = _read_jsonl_rows_from_offset(report_log, start_offset)
    current_run_rows = [row for row in rows if row.get("trace_id") == trace_id]
    built_row = next(row for row in current_run_rows if row["event"] == "week_brief_built")
    response_row = next(row for row in current_run_rows if row["event"] == "week_brief.response_returned")

    assert built_row["module"] == "M-WEEK-BRIEF-SERVICE"
    assert built_row["fn"] == "build_week_brief_payload"
    assert built_row["block"] == "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
    assert built_row["correlation_source"] == "week-brief-api-test"
    assert built_row["trace_id"] == trace_id
    assert built_row["request_id"] == request_id
    assert built_row["report_id"] == str(report.id)

    assert response_row["module"] == "M-API-GATEWAY"
    assert response_row["fn"] == "get_report_detail"
    assert response_row["block"] == "API_REPORT_DETAIL_ROUTE"
    assert response_row["correlation_source"] == "week-brief-api-test"
    assert response_row["trace_id"] == trace_id
    assert response_row["request_id"] == request_id
    assert response_row["report_id"] == str(report.id)


def test_api_gateway_declares_grace_module_contract_map_blocks_and_entrypoints():
    source = Path("backend/app/main.py").read_text(encoding="utf-8")

    assert "START_MODULE_CONTRACT: M-API-GATEWAY" in source
    assert "END_MODULE_CONTRACT: M-API-GATEWAY" in source
    assert "START_MODULE_MAP: M-API-GATEWAY" in source
    assert "END_MODULE_MAP: M-API-GATEWAY" in source
    assert "# semantic_blocks:" in source

    for block in (
        "API_GATEWAY_LOGGING",
        "API_GATEWAY_APP_INIT",
        "API_GATEWAY_ROUTE_SCHEMAS",
        "API_GATEWAY_REPORT_ORCHESTRATION",
        "API_REPORT_DETAIL_ROUTE",
        "API_TODAY_ROUTE",
        "API_DAY_BRIEF_ROUTE",
        "API_B2C_REPORT_ROUTE",
    ):
        assert f"START_BLOCK: {block}" in source
        assert f"END_BLOCK: {block}" in source

    for contract in (
        "FN-LOG-API-GATEWAY-EVENT",
        "FN-BIND-REQUEST-CORRELATION",
        "FN-INIT-API-GATEWAY",
        "FN-GET-REPORT-DETAIL",
        "FN-GET-DAILY-FEED",
        "FN-GET-DAY-BRIEF",
        "FN-CREATE-B2C-REPORT",
    ):
        assert f"START_CONTRACT: {contract}" in source
        assert f"END_CONTRACT: {contract}" in source
