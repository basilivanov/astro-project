import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app import logging_utils
from backend.app.main import get_daily_feed, get_report_detail
from backend.app.services import day_brief as day_brief_module


def _read_jsonl_rows_from_offset(path: Path, offset: int) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        return [json.loads(line) for line in handle if line.strip()]


def _sample_today_facts() -> dict:
    return {
        "local_dt": "2026-03-27T07:00:00+03:00",
        "moon_phase": "Растущая Луна",
        "moon_sign": "Рыбы",
        "moon_emoji": "🌔",
        "moon_degree": 12.4,
        "aspects_count": 2,
        "aspect_summary": "Марс квадрат Солнце, Венера секстиль Венера",
        "traffic_lights": {"health": "red", "money": "green", "love": "yellow"},
        "semantic_layer": {
            "headline": "День про короткий фокус, аккуратные решения и взрослый темп.",
            "pacing": "Темп дня лучше держать короткими циклами и без лишнего разгона.",
            "rest": "Телу нужен запас по времени и пауза до следующего захода.",
            "money_admin_focus": "Хорошо закрывать один документ, одно согласование или одно денежное условие.",
            "relationship_softness": "Мягкость и честная формулировка работают сильнее, чем нажим.",
            "practical_move": "Закрой один важный вопрос и сразу зафиксируй детали письменно.",
            "focus_key": "money_admin",
            "tension": "лишняя скорость и спор на формулировках",
        },
        "personalization_level": "personalized_v2",
        "cache_scope": "today-premium-test",
        "prompt_contract": "personalized_daily_v2",
        "meta": {"source": "packet-local"},
        "year_data": {"profection": {"house": 10}},
        "fast_hits": [
            {
                "transit": "Mars",
                "natal": "Sun",
                "type": "Квадрат (90°)",
                "orb": 0.2,
                "summary": "Марс квадрат Солнце",
            },
            {
                "transit": "Venus",
                "natal": "Venus",
                "type": "Секстиль (60°)",
                "orb": 0.4,
                "summary": "Венера секстиль Венера",
            },
        ],
    }


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
                    "ingresses": [],
                    "aspects": [],
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Ровно",
                    "tension_score": 0.2,
                },
            ],
        },
        "year_forecast_data": {
            "profection": {"house": 10, "lord": "Венера", "age": 36},
            "solar_return": {"datetime": "2026-03-20T10:00:00+03:00", "asc_sign": "Овен", "sun_house": 10},
            "solar_arcs": [{"direction": "Сатурн", "natal": "MC", "orb": 0.4}],
        },
    }


def test_core_today_feed_emits_current_run_ids_across_gateway_and_day_brief() -> None:
    feed_log = logging_utils.LOG_DIR / "feed.jsonl"
    start_offset = feed_log.stat().st_size if feed_log.exists() else 0
    run_marker = uuid.uuid4().hex
    correlation_id = f"corr-core-today-{run_marker}"
    trace_id = f"trace-core-today-{run_marker}"
    request_id = f"req-core-today-{run_marker}"
    request = SimpleNamespace(url=SimpleNamespace(path="/api/feed/today"))

    with (
        patch("backend.app.routers.public.build_personalized_daily_facts", return_value=_sample_today_facts()),
        patch(
            "backend.app.routers.public.get_daily_vibe_llm",
            new=AsyncMock(return_value=("Главный акцент дня: действуй точечно.", {"generation_mode": "deterministic"})),
        ),
        logging_utils.correlation_scope(
            "backend-grace-core-today-test",
            correlation_id=correlation_id,
            trace_id=trace_id,
            request_id=request_id,
        ),
    ):
        payload = asyncio.run(
            get_daily_feed(
                request=request,
                debug=False,
                x_telegram_auth=None,
                x_feed_debug=None,
                db=MagicMock(),
            )
        )

    assert payload["day_brief"]["status"] in {"partial", "complete"}
    rows = _read_jsonl_rows_from_offset(feed_log, start_offset)
    current_run_rows = [row for row in rows if row.get("trace_id") == trace_id]

    entry_row = next(row for row in current_run_rows if row["event"] == "feed.entry")
    built_row = next(row for row in current_run_rows if row["event"] == "day_brief.built")
    response_row = next(row for row in current_run_rows if row["event"] == "day_brief.response_returned")

    for row in (entry_row, built_row, response_row):
        assert row["correlation_id"] == correlation_id
        assert row["trace_id"] == trace_id
        assert row["request_id"] == request_id

    assert entry_row["module"] == "M-API-GATEWAY"
    assert entry_row["fn"] == "get_daily_feed"
    assert entry_row["block"] == "API_TODAY_ROUTE"

    assert built_row["module"] == "M-DAY-BRIEF-SERVICE"
    assert built_row["fn"] == "build_day_brief_payload"
    assert built_row["block"] == day_brief_module.DAY_BRIEF_BUILD_BLOCK
    assert built_row["correlation_source"] == "backend-grace-core-today-test"

    assert response_row["module"] == "M-API-GATEWAY"
    assert response_row["fn"] == "get_daily_feed"
    assert response_row["block"] == "API_TODAY_ROUTE"
    assert response_row["path"] == "/api/feed/today"


def test_core_week_report_detail_emits_current_run_ids_across_gateway_and_week() -> None:
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
    correlation_id = f"corr-core-week-{run_marker}"
    trace_id = f"trace-core-week-{run_marker}"
    request_id = f"req-core-week-{run_marker}"

    with (
        patch("backend.app.routers.reports.load_report_payload", return_value=SimpleNamespace(llm_mode="cheap", birth_time_known=True)),
        patch("backend.app.routers.reports.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.routers.reports.build_natal_chart_svg", return_value="<svg />"),
        patch("backend.app.routers.reports.build_report_context", return_value=_sample_week_context()),
        logging_utils.correlation_scope(
            "backend-grace-core-week-test",
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

    for row in (built_row, response_row):
        assert row["correlation_id"] == correlation_id
        assert row["trace_id"] == trace_id
        assert row["request_id"] == request_id

    assert built_row["module"] == "M-WEEK-BRIEF-SERVICE"
    assert built_row["fn"] == "build_week_brief_payload"
    assert built_row["block"] == "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
    assert built_row["report_id"] == str(report.id)

    assert response_row["module"] == "M-API-GATEWAY"
    assert response_row["fn"] == "get_report_detail"
    assert response_row["block"] == "API_REPORT_DETAIL_ROUTE"
    assert response_row["report_id"] == str(report.id)


def test_core_day_brief_declares_stable_build_block_name() -> None:
    assert day_brief_module.DAY_BRIEF_BUILD_BLOCK == "DAY_BRIEF_BUILD"
