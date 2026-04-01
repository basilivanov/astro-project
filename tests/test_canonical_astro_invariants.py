import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.app.llm.orchestrator import SectionSpec
from backend.app.services.day_brief import build_day_brief_fallback, build_day_brief_payload
from backend.app.services.feed_service import fetch_daily_blocks
from backend.app.services.report_workflow import build_chart_data, generate_section_content
from backend.app.services.week_brief_service import build_week_brief_envelope, build_week_brief_payload
from tests.canonical_persona_pack import fixture_ids, get_fixture, payload_from_fixture


class _CaptureEngine:
    def __init__(self):
        self.calls = []

    def create_natal_chart(self, name, dt, loc, house_system, birth_time_known=True):
        self.calls.append(
            {
                "name": name,
                "dt": dt,
                "loc": loc,
                "house_system": house_system,
                "birth_time_known": birth_time_known,
            }
        )
        return SimpleNamespace(
            positions=[],
            datetime=SimpleNamespace(julian_day=0),
            get_houses=lambda: SimpleNamespace(system=str(house_system), cusps=[], signs=[], sign_degrees=[]),
            location=SimpleNamespace(name="Mock City", latitude=55.75, longitude=37.61, timezone="Europe/Moscow"),
            metadata={"name": name},
        )

    def get_fixed_star_conjunctions(self, chart, orb=1.0):
        return []

    def find_natal_aspects(self, chart):
        return []

    def find_all_patterns(self, chart):
        return []

    def calculate_selena(self, julian_day):
        raise RuntimeError("not needed")

    def calculate_pars_fortuna(self, chart):
        raise RuntimeError("not needed")


class _Placidus:
    def __str__(self):
        return "Placidus"


class _WholeSign:
    def __str__(self):
        return "Whole Sign"


@pytest.mark.parametrize("fixture_id", fixture_ids())
def test_persona_pack_v1_matches_manifest_contract(fixture_id):
    fixture = get_fixture(fixture_id)
    payload = payload_from_fixture(fixture_id)

    assert payload.canonical_persona_pack == "persona_pack_v1"
    assert payload.canonical_fixture_id == fixture_id
    assert payload.client_name == fixture["canonical_inputs"]["client_name"]
    assert payload.birth_timezone == fixture["canonical_inputs"]["birth_timezone"]
    assert payload.report_type == fixture["canonical_inputs"]["report_types"][0]


def _render_input_frame(context, chart_data):
    spec = SectionSpec(section_id="input_frame", title="Паспорт карты", prompt="static")
    result = asyncio.run(
        generate_section_content(
            spec,
            context,
            chart_data,
            llm_client=None,
            fallback_models=[],
            retry_attempts=0,
            use_template=False,
        )
    )
    return json.loads(result.content)


def test_build_chart_data_preserves_requested_clock_time_when_birth_time_known():
    engine = _CaptureEngine()
    payload = payload_from_fixture("CF-BE-001-baseline-exact-time")

    with (
        patch("backend.app.services.report_workflow.StelliumEngine", return_value=engine),
        patch("backend.app.services.report_workflow.engine_utils.resolve_house_system", return_value=_Placidus()),
        patch("backend.app.services.report_workflow.engine_utils.serialize_chart", return_value={"ok": True}),
    ):
        build_chart_data(payload)

    assert engine.calls[0]["birth_time_known"] is True
    assert engine.calls[0]["dt"].endswith("06:32:00")


def test_build_chart_data_marks_unknown_birth_time_without_rewriting_wall_clock_before_engine():
    engine = _CaptureEngine()
    payload = payload_from_fixture("CF-BTU-003-birth-time-unknown")

    with (
        patch("backend.app.services.report_workflow.StelliumEngine", return_value=engine),
        patch("backend.app.services.report_workflow.engine_utils.resolve_house_system", return_value=_Placidus()),
        patch("backend.app.services.report_workflow.engine_utils.serialize_chart", return_value={"ok": True}),
    ):
        build_chart_data(payload)

    assert engine.calls[0]["birth_time_known"] is False
    assert engine.calls[0]["dt"].endswith("05:00:00")


def test_build_chart_data_forces_whole_sign_for_high_latitude_births():
    engine = _CaptureEngine()
    payload = payload_from_fixture("CF-WS-002-whole-sign-edge")

    with (
        patch("backend.app.services.report_workflow.StelliumEngine", return_value=engine),
        patch("backend.app.services.report_workflow.engine_utils.resolve_house_system", return_value=_Placidus()),
        patch("stellium.engines.houses.WholeSignHouses", _WholeSign),
        patch("backend.app.services.report_workflow.engine_utils.serialize_chart", return_value={"ok": True}),
    ):
        build_chart_data(payload)

    assert str(engine.calls[0]["house_system"]) == "Whole Sign"


def test_input_frame_hides_house_and_timezone_details_when_birth_time_unknown():
    fixture = get_fixture("CF-BTU-003-birth-time-unknown")
    blocks = _render_input_frame(
        {
            "client": {
                "name": fixture["persona_name"],
                "birth_date": "1990-01-01T05:00:00+03:00",
                "birth_location": "Moscow",
                "birth_timezone": "Europe/Moscow",
                "birth_lat": 55.75,
                "birth_time_known": False,
            },
            "report_id": "r-beta",
        },
        {
            "house_system": "Placidus",
            "positions": [
                {"name": "Sun", "sign": "Capricorn", "sign_degree": 10.0, "house": 10, "is_retrograde": False},
                {"name": "Moon", "sign": "Cancer", "sign_degree": 4.5, "house": 4, "is_retrograde": False},
                {"name": "ASC", "sign": "Aries", "sign_degree": 0.5, "house": 1, "is_retrograde": False},
            ],
            "aspects": [],
            "patterns": [],
            "fixed_stars": [],
        },
    )

    key_values = next(block for block in blocks if block["type"] == "key_value")
    planets_table = next(block for block in blocks if block["type"] == "table")

    assert any(item == {"key": "Дома", "value": "Космограмма (без домов)"} for item in key_values["items"])
    assert any(item == {"key": "Часовой пояс", "value": "-"} for item in key_values["items"])
    assert all(column["header"] != "Дом" for column in planets_table["columns"])
    assert any("время неизв." in item["value"] for item in key_values["items"] if item["key"] == "Дата")


def test_input_frame_warns_when_high_latitude_chart_uses_whole_sign_with_known_time():
    fixture = get_fixture("CF-WS-002-whole-sign-edge")
    blocks = _render_input_frame(
        {
            "client": {
                "name": fixture["persona_name"],
                "birth_date": "1980-10-30T19:50:00+03:00",
                "birth_location": "Monchegorsk",
                "birth_timezone": "Europe/Moscow",
                "birth_lat": 67.9387,
                "birth_time_known": True,
            },
            "report_id": "r-gamma",
        },
        {
            "house_system": "Whole Sign",
            "positions": [
                {"name": "Sun", "sign": "Scorpio", "sign_degree": 7.0, "house": 8, "is_retrograde": False},
                {"name": "Moon", "sign": "Leo", "sign_degree": 18.0, "house": 5, "is_retrograde": False},
            ],
            "aspects": [],
            "patterns": [],
            "fixed_stars": [],
        },
    )

    key_values = next(block for block in blocks if block["type"] == "key_value")
    warning = next(block for block in blocks if block.get("variant") == "warning")

    assert any(item == {"key": "Часовой пояс", "value": "Europe/Moscow"} for item in key_values["items"])
    assert "высоких широтах" in warning["content"]
    assert "Whole Sign" in warning["content"]


def _sample_day_facts(*, birth_time_known: bool, fallback_mode: bool = False) -> dict:
    return {
        "local_dt": "2026-03-27T09:30:00+03:00",
        "moon_phase": "Растущая Луна",
        "moon_sign": "Рыбы",
        "moon_emoji": "🌔",
        "aspects_count": 1,
        "traffic_lights": {"health": "yellow", "money": "green", "love": "yellow"},
        "week_data": {"days": [{"moon": {"sign": "Рыбы", "phase": "Растущая", "void_of_course": False}}]},
        "semantic_layer": {
            "headline": "День про короткий фокус, ясные формулировки и аккуратные решения.",
            "pacing": "Лучше держать день короткими циклами и с запасом по времени.",
            "rest": "Не тратить весь ресурс первым рывком.",
            "money_admin_focus": "Закрыть один документ или одно согласование, не дробя внимание.",
            "relationship_softness": "Говорить прямо, но мягко и без лишнего нажима.",
            "practical_move": "Продвинь один главный вопрос и сразу закрепи детали.",
            "focus_key": "money_admin",
        },
        "personalization_level": "personalized_v2",
        "meta": {"fallback_mode": fallback_mode},
        "month_data": {"status": "GREEN"},
        "year_data": {"profection": {"house": 10}, "months": [{"month": 3, "status": "GREEN"}]},
        "fast_hits": [
            {
                "transit": "Venus",
                "natal": "Venus",
                "type": "Секстиль (60°)",
                "orb": 0.4,
                "summary": "Венера секстиль Венера",
            }
        ],
        "birth_time_known": birth_time_known,
    }


@pytest.mark.parametrize(
    ("fixture_id", "birth_time_known"),
    [
        ("CF-BE-001-baseline-exact-time", True),
        ("CF-BTU-003-birth-time-unknown", False),
    ],
)
def test_day_brief_explainability_presence_rules_follow_canonical_personas(fixture_id, birth_time_known):
    payload = build_day_brief_payload(
        _sample_day_facts(birth_time_known=birth_time_known),
        user=SimpleNamespace(birth_time="06:32", birth_time_known=birth_time_known),
        general_vibe=f"fixture={fixture_id}",
        generation_mode="deterministic",
    )

    explainability = payload["explainability"]
    assert explainability["factor_count"] >= 1
    assert explainability["selected_factors"]
    assert explainability["selected_factors_support"]
    assert explainability["birth_time_used"] is birth_time_known
    assert explainability["timing_precision"] in {"exact", "date_only", "unknown", "approximate"}
    assert payload["fallback_mode"] is False


def test_feed_prompt_blocks_keep_real_persona_facts_for_known_time_fixture_without_fallback_leakage():
    fixture = get_fixture("CF-BE-001-baseline-exact-time")
    canonical_inputs = fixture["canonical_inputs"]

    personalization_context = {
        "normalized_factors": [],
        "fact_lines": [
            f"Client: {canonical_inputs['client_name']}",
            f"Birth location: {canonical_inputs['birth_location']}",
            f"Birth timezone: {canonical_inputs['birth_timezone']}",
            "Birth time used: exact known time",
        ],
        "traffic_lights": {"health": "yellow", "money": "green", "love": "yellow"},
        "semantic_layer": {
            "tone": "calm and precise",
            "pacing": "short cycles",
            "negotiation": "confirm details in writing",
            "friction": "avoid parallel threads",
            "rest": "keep energy buffered",
            "money_admin_focus": "close one material agreement",
            "relationship_softness": "stay direct and warm",
            "headline": "A focused day for one real agreement.",
            "practical_move": "Send one clean confirmation message.",
        },
        "fallback_detail": "",
        "fallback_mode": False,
        "birth_time_known": True,
        "birth_time_used": True,
        "timing_precision": "exact",
        "prompt_contract": "personalized_daily_v2",
        "canonical_fixture_id": "CF-BE-001-baseline-exact-time",
        "canonical_persona_pack": "persona_pack_v1",
    }

    blocks = fetch_daily_blocks(
        "Leo",
        "Waxing Moon",
        "Venus sextile Venus",
        personalization_context=personalization_context,
    )

    assert blocks["personalization_prompt"]
    assert canonical_inputs["client_name"] in blocks["personalization_prompt"]
    assert canonical_inputs["birth_location"] in blocks["personalization_prompt"]
    assert canonical_inputs["birth_timezone"] in blocks["personalization_prompt"]
    assert "Birth time used: exact known time" in blocks["personalization_prompt"]
    assert blocks["fallback_detail"] == ""
    assert blocks["prompt_contract"]["version"]
    assert isinstance(blocks["prompt_contract"].get("contract"), list)


def test_feed_prompt_blocks_keep_business_anchors_for_known_time_fixture():
    blocks = fetch_daily_blocks(
        "Virgo",
        "Waxing Moon",
        "Mercury trine MC",
        personalization_context={
            "normalized_factors": [
                {"label": "Mercury trine MC", "explanation_human": "Career messaging lands well."},
            ],
            "traffic_lights": {"health": "yellow", "money": "green", "love": "yellow"},
            "semantic_layer": {
                "tone": "grounded",
                "pacing": "measured",
                "negotiation": "document outcomes",
                "friction": "skip noise",
                "rest": "protect margin",
                "money_admin_focus": "move one concrete work item",
                "relationship_softness": "reduce pressure",
                "headline": "One practical move beats scattered effort.",
                "practical_move": "Confirm terms in writing.",
            },
            "fallback_detail": "",
        },
    )

    assert "Светофоры дня:" in blocks["personalization_prompt"]
    assert "- money: green" in blocks["personalization_prompt"]
    assert "Семантический слой дня" in blocks["personalization_prompt"]
    assert "money_admin_focus: move one concrete work item" in blocks["personalization_prompt"]
    assert "headline: One practical move beats scattered effort." in blocks["personalization_prompt"]


def test_day_brief_fallback_keeps_contract_but_avoids_real_data_claims():
    payload = build_day_brief_fallback(
        datetime(2026, 3, 27, 6, 0, tzinfo=timezone.utc),
        general_vibe="fixture=CF-BE-001-baseline-exact-time",
        generation_mode="fallback",
        reason="canonical-wave2",
    )

    explainability = payload["explainability"]
    assert payload["fallback_mode"] is True
    assert explainability["factor_count"] >= 1
    assert explainability["selected_factors"]
    assert explainability["selected_factors_support"]
    assert explainability["birth_time_used"] is False
    assert explainability["timing_precision"] in {"date_only", "unknown", "approximate"}



def _sample_week_context() -> dict:
    return {
        "forecast_window": {"start": "2026-03-30T05:00:00+03:00", "days": 7},
        "week_forecast_data": {
            "summary": {"traffic_light": "YELLOW", "avg_tension": 0.7},
            "days": [
                {"date": "2026-03-30", "weekday": "Monday", "moon": {"sign": "Овен", "phase": "Растущая", "void_of_course": False}, "ingresses": ["Меркурий -> Овен"], "aspects": [{"transit": "Марс", "natal": "Солнце", "aspect": "Квадрат"}], "traffic_light": "YELLOW", "traffic_desc": "🟡 Внимание", "tension_score": 0.7},
                {"date": "2026-03-31", "weekday": "Tuesday", "moon": {"sign": "Телец", "phase": "Растущая", "void_of_course": False}, "aspects": [{"transit": "Венера", "natal": "Венера", "aspect": "Секстиль"}], "traffic_light": "GREEN", "traffic_desc": "🟢 Зеленый", "tension_score": -0.4},
                {"date": "2026-04-01", "weekday": "Wednesday", "moon": {"sign": "Близнецы", "phase": "Растущая", "void_of_course": False}, "traffic_light": "YELLOW", "traffic_desc": "🟡 Внимание", "tension_score": 0.3},
                {"date": "2026-04-02", "weekday": "Thursday", "moon": {"sign": "Рак", "phase": "Растущая", "void_of_course": True}, "traffic_light": "RED", "traffic_desc": "🔴 Шторм", "tension_score": 2.3},
                {"date": "2026-04-03", "weekday": "Friday", "moon": {"sign": "Лев", "phase": "Растущая", "void_of_course": False}, "traffic_light": "GREEN", "traffic_desc": "🟢 Зеленый", "tension_score": -0.3},
                {"date": "2026-04-04", "weekday": "Saturday", "moon": {"sign": "Дева", "phase": "Растущая", "void_of_course": False}, "traffic_light": "YELLOW", "traffic_desc": "🟡 Внимание", "tension_score": 0.4},
                {"date": "2026-04-05", "weekday": "Sunday", "moon": {"sign": "Весы", "phase": "Полнолуние", "void_of_course": False}, "traffic_light": "GREEN", "traffic_desc": "🟢 Зеленый", "tension_score": -0.1},
            ],
        },
        "month_forecast_data": {
            "major_transits": ["31.03 Сатурн Квадрат Солнце", "04.04 Юпитер Тригон Меркурий"],
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



def _sample_chunks(valid: bool = True):
    if valid:
        return [
            SimpleNamespace(section="week_strategy", content='[{"type":"header","level":2,"text":"Стратегия недели"},{"type":"paragraph","text":"Неделя лучше идет через одну линию и короткие проверки."}]', status="completed", order_index=0),
            SimpleNamespace(section="money", content='[{"type":"header","level":2,"text":"Работа и деньги"},{"type":"list","items":["Подтверждай условия письменно","Сужай фронт до главного"]}]', status="completed", order_index=1),
        ]
    return [SimpleNamespace(section="week_strategy", content="{not-json", status="failed", order_index=0)]


@pytest.mark.parametrize(
    ("fixture_id", "birth_time_known"),
    [
        ("CF-BE-001-baseline-exact-time", True),
        ("CF-WS-002-whole-sign-edge", True),
        ("CF-BTU-003-birth-time-unknown", False),
    ],
)
def test_week_brief_canonical_personas_keep_day_week_contract_and_explainability(fixture_id, birth_time_known):
    report = SimpleNamespace(
        id="week-report-1",
        report_type="week_forecast",
        status="completed",
        created_at=datetime(2026, 3, 30, 5, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 30, 6, 0, tzinfo=timezone.utc),
        error_message=None,
    )

    payload = build_week_brief_payload(
        report=report,
        payload=SimpleNamespace(llm_mode="cheap", birth_time_known=birth_time_known, canonical_fixture_id=fixture_id, canonical_persona_pack="persona_pack_v1"),
        context=_sample_week_context(),
        chunks=_sample_chunks(valid=True),
        user=None,
        llm_model="deterministic",
    )

    assert payload["status"] in {"ready", "error"}
    assert len(payload["day_cards"]) == 7
    assert payload["day_cards"][0]["date"] == "2026-03-30"
    assert payload["day_cards"][-1]["date"] == "2026-04-05"
    assert payload["summary"]["headline"]
    assert payload["summary"]["subhead"]
    assert payload["best_uses"]
    assert payload["risks"]
    assert payload["deep_sections"]
    assert payload["report_ref"]["report_type"] == "week_forecast"
    assert payload["explainability"]["birth_time_used"] is birth_time_known
    assert payload["explainability"]["factor_count"] >= len(payload["major_factors"])
    assert payload["explainability"]["confidence"] >= 0
    assert payload["explainability"]["timing_precision"] in {"exact", "approximate"}
    if payload["fallback_mode"]:
        assert payload["explainability"]["timing_precision"] == "approximate"
    if birth_time_known:
        assert payload["fallback_mode"] is True
    else:
        assert payload["fallback_mode"] is True


def test_week_brief_envelope_exposes_ready_data_without_placeholder_leakage_for_known_time_fixture():
    report = SimpleNamespace(
        id="week-report-envelope",
        report_type="week_forecast",
        status="completed",
        created_at=datetime(2026, 3, 30, 5, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 30, 6, 0, tzinfo=timezone.utc),
        error_message=None,
    )
    week_brief = build_week_brief_payload(
        report=report,
        payload=SimpleNamespace(
            llm_mode="cheap",
            birth_time_known=True,
            canonical_fixture_id="CF-BE-001-baseline-exact-time",
            canonical_persona_pack="persona_pack_v1",
        ),
        context=_sample_week_context(),
        chunks=_sample_chunks(valid=True),
        user=None,
        llm_model="deterministic",
    )

    envelope = build_week_brief_envelope(report=report, week_brief=week_brief)

    assert envelope["status"] == "ready"
    assert envelope["data"] == week_brief
    assert envelope["message"] is None
    assert envelope["retry_after_seconds"] is None
    assert envelope["data"]["explainability"]["birth_time_used"] is True
    assert envelope["data"]["explainability"]["timing_precision"] == "approximate"



def test_week_brief_fallback_keeps_contract_but_marks_fallback_explainability():
    report = SimpleNamespace(
        id="week-report-err",
        report_type="week_forecast",
        status="failed",
        created_at=datetime(2026, 3, 30, 5, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 30, 6, 0, tzinfo=timezone.utc),
        error_message=None,
    )

    payload = build_week_brief_payload(
        report=report,
        payload=SimpleNamespace(llm_mode="cheap", birth_time_known=True, canonical_fixture_id="CF-BE-001-baseline-exact-time", canonical_persona_pack="persona_pack_v1"),
        context={},
        chunks=_sample_chunks(valid=False),
        user=None,
        llm_model="deterministic",
    )

    assert payload["fallback_mode"] is True
    assert payload["status"] == "error"
    assert len(payload["day_cards"]) == 7
    assert payload["summary"]["headline"]
    assert payload["best_uses"]
    assert payload["risks"]
    assert payload["deep_sections"]
    assert payload["explainability"]["factor_count"] >= 1
    assert payload["explainability"]["birth_time_used"] is True
    assert payload["explainability"]["confidence"] >= 0
