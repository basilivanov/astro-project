import os
import sys
import types

import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(os.getcwd())

if "stellium" not in sys.modules:
    stellium = types.ModuleType("stellium")
    engines = types.ModuleType("stellium.engines")
    houses = types.ModuleType("stellium.engines.houses")

    class _StubHouseSystem:
        def __init__(self, *args, **kwargs):
            pass

    houses.EqualHouses = _StubHouseSystem
    houses.PlacidusHouses = _StubHouseSystem
    houses.WholeSignHouses = _StubHouseSystem
    engines.houses = houses
    stellium.engines = engines
    stellium.ChartBuilder = object
    stellium.ReturnBuilder = object
    stellium.ChartLocation = object
    stellium.FIXED_STARS_REGISTRY = {}
    stellium.get_fixed_star_info = lambda *args, **kwargs: None
    sys.modules["stellium"] = stellium
    sys.modules["stellium.engines"] = engines
    sys.modules["stellium.engines.houses"] = houses

if "stellium_engine" not in sys.modules:
    stellium_engine = types.ModuleType("stellium_engine")

    class _StubStelliumEngine:
        pass

    stellium_engine.StelliumEngine = _StubStelliumEngine
    sys.modules["stellium_engine"] = stellium_engine

from backend.app.services import personalized_daily


class TestPersonalizedDailyService(unittest.TestCase):
    def setUp(self) -> None:
        personalized_daily._PERSONALIZED_DAILY_CACHE.clear()

    @patch("backend.app.services.personalized_daily.StelliumEngine")
    def test_build_personalized_daily_facts_uses_profile_horizon_and_fast_hits(self, mock_engine_cls):
        moon = type("Body", (), {"name": "Moon", "sign": "Pisces", "longitude": 15.0})()
        sun = type("Body", (), {"name": "Sun", "sign": "Pisces", "longitude": 5.0})()
        transit_chart = type("Chart", (), {"positions": [moon, sun]})()
        natal_chart = object()

        engine = mock_engine_cls.return_value
        engine.create_transit_chart.return_value = transit_chart
        engine.find_natal_aspects.return_value = [
            {"p1": "Venus", "p2": "Jupiter", "type": "square", "orb": 0.4},
        ]
        engine.create_natal_chart.return_value = natal_chart
        engine.find_transit_aspects.return_value = [
            {"transit": "Venus", "natal": "Venus", "type": "Соединение (0°)", "exact_diff": 0.3},
            {"transit": "Mars", "natal": "Sun", "type": "Квадрат (90°)", "exact_diff": 0.7},
            {"transit": "Jupiter", "natal": "Sun", "type": "Тригон (120°)", "exact_diff": 0.1},
        ]
        engine.calculate_forecast_week_data.return_value = {
            "days": [
                {
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "moon": {"sign": "Рыбы", "phase": "Растущая", "void_of_course": False},
                }
            ],
            "summary": {"traffic_light": "GREEN", "avg_tension": -0.2},
        }
        engine.calculate_forecast_month_data.return_value = {
            "status": "GREEN",
            "lunations": ["21.03 Новолуние в Овне"],
            "ingresses": ["23.03 Венера -> Телец"],
            "major_transits": ["27.03 Марс Квадрат Солнце"],
            "retrogrades": [],
        }
        engine.calculate_forecast_year_data.return_value = {
            "profection": {"house": 5, "lord": "Венера", "age": 35},
            "months": [
                {"month": 3, "status": "GREEN", "aspects": [{"transit": "Венера", "aspect": "Соединение", "natal": "Венера"}]},
            ],
        }

        user = SimpleNamespace(
            id="user-1",
            full_name="Daily Tester",
            birth_date="1990-01-01",
            birth_time="09:15",
            birth_time_known=True,
            birth_place="Sochi",
            birth_lat=43.5855,
            birth_lon=39.7231,
            birth_timezone="Europe/Moscow",
            current_location="Sochi",
            current_lat=43.5855,
            current_lon=39.7231,
            current_timezone="Europe/Moscow",
            sun_sign="Pisces",
        )

        facts = personalized_daily.build_personalized_daily_facts(
            datetime(2026, 3, 19, 6, 0, tzinfo=timezone.utc),
            user=user,
        )

        self.assertEqual(facts["personalization_level"], "personalized_v2")
        self.assertEqual(facts["moon_sign"], "Рыбы")
        self.assertIn("Венера Соединение (0°) Венера", facts["aspect_summary"])
        self.assertEqual(facts["traffic_lights"]["health"], "yellow")
        self.assertEqual(facts["traffic_lights"]["money"], "green")
        self.assertEqual(facts["traffic_lights"]["love"], "green")
        self.assertIn(facts["semantic_layer"]["focus_key"], {"money_admin", "relationship"})
        self.assertIn("симпат", facts["semantic_layer"]["headline"])
        self.assertTrue(
            any(token in facts["semantic_layer"]["practical_move"].lower() for token in ("соглас", "разговор", "документ"))
        )
        joined_lines = " ".join(facts["fact_lines"])
        self.assertIn("Контекст недели", joined_lines)
        self.assertIn("Контекст месяца: статус GREEN", joined_lines)
        self.assertIn("Годовой фон на этот месяц: GREEN", joined_lines)

    @patch("backend.app.services.personalized_daily.log_grace_event")
    @patch("backend.app.services.personalized_daily.StelliumEngine")
    def test_build_personalized_daily_facts_emits_structured_logs_without_sensitive_auth(self, mock_engine_cls, mock_log_grace_event):
        moon = type("Body", (), {"name": "Moon", "sign": "Pisces", "longitude": 15.0})()
        sun = type("Body", (), {"name": "Sun", "sign": "Pisces", "longitude": 5.0})()
        transit_chart = type("Chart", (), {"positions": [moon, sun]})()
        engine = mock_engine_cls.return_value
        engine.create_transit_chart.return_value = transit_chart
        engine.find_natal_aspects.return_value = []

        user = SimpleNamespace(
            id="user-3",
            birth_date="1990-01-01",
            current_location="Sochi",
            current_timezone="Europe/Moscow",
            sun_sign="Pisces",
        )

        personalized_daily.build_personalized_daily_facts(
            datetime(2026, 3, 19, 6, 0, tzinfo=timezone.utc),
            user=user,
        )

        events = [call.args[1] for call in mock_log_grace_event.call_args_list]
        self.assertIn("feed.entry", events)
        self.assertIn("feed.debug", events)
        serialized = json.dumps(
            [{"args": call.args, "kwargs": call.kwargs} for call in mock_log_grace_event.call_args_list],
            ensure_ascii=False,
        )
        self.assertNotIn("initData", serialized)

    @patch("backend.app.services.personalized_daily.StelliumEngine")
    def test_build_personalized_daily_facts_supports_partial_profile_without_birth_place(self, mock_engine_cls):
        moon = type("Body", (), {"name": "Moon", "sign": "Pisces", "longitude": 15.0})()
        sun = type("Body", (), {"name": "Sun", "sign": "Pisces", "longitude": 5.0})()
        transit_chart = type("Chart", (), {"positions": [moon, sun]})()
        engine = mock_engine_cls.return_value
        engine.create_transit_chart.return_value = transit_chart
        engine.find_natal_aspects.return_value = []

        user = SimpleNamespace(
            id="user-2",
            full_name="Partial Tester",
            birth_date="1990-01-01",
            birth_place=None,
            birth_lat=None,
            birth_lon=None,
            birth_timezone="Europe/Moscow",
            current_location="Sochi",
            current_lat=43.5855,
            current_lon=39.7231,
            current_timezone="Europe/Moscow",
            sun_sign="Pisces",
        )

        facts = personalized_daily.build_personalized_daily_facts(
            datetime(2026, 3, 19, 6, 0, tzinfo=timezone.utc),
            user=user,
        )

        self.assertEqual(facts["personalization_level"], "profile_light")
        self.assertEqual(facts["location_label"], "Sochi")
        self.assertEqual(facts["timezone"], "Europe/Moscow")
        self.assertFalse(facts["meta"]["has_fast_hits"])

    def test_summarize_personalization_for_prompt_returns_public_prompt_slice(self):
        facts = {
            "personalization_level": "personalized_v2",
            "fact_lines": [
                "  Первая строка  ",
                "",
                "Вторая строка",
                "   ",
                "Третья строка",
                "Четвертая строка",
                "Пятая строка",
                "Шестая строка",
                "Седьмая строка",
            ],
            "cache_scope": "scope-123",
            "traffic_lights": {"health": "green", "money": "yellow", "love": "red"},
            "semantic_layer": {"headline": "Фокус дня", "practical_move": "Сделай шаг", "private_hint": "hidden"},
            "meta": {"internal": "ignored"},
            "user_id": "secret-user",
        }

        summary = personalized_daily.summarize_personalization_for_prompt(facts)

        self.assertEqual(summary["level"], "personalized_v2")
        self.assertEqual(
            summary["fact_lines"],
            [
                "Первая строка",
                "Вторая строка",
                "Третья строка",
                "Четвертая строка",
                "Пятая строка",
                "Шестая строка",
            ],
        )
        self.assertEqual(summary["fallback_detail"], "Третья строка Четвертая строка Пятая строка")
        self.assertEqual(summary["cache_scope"], "scope-123")
        self.assertEqual(summary["traffic_lights"], {"health": "green", "money": "yellow", "love": "red"})
        self.assertEqual(summary["semantic_layer"]["headline"], "Фокус дня")
        self.assertEqual(summary["semantic_layer"]["private_hint"], "hidden")
        self.assertEqual(summary["prompt_contract"], "personalized_daily_v2")
        self.assertNotIn("meta", summary)
        self.assertNotIn("user_id", summary)

    def test_summarize_personalization_for_prompt_uses_second_line_as_fallback_when_slice_is_short(self):
        facts = {
            "fact_lines": ["Первая строка", "Вторая строка"],
            "traffic_lights": None,
            "semantic_layer": None,
        }

        summary = personalized_daily.summarize_personalization_for_prompt(facts)

        self.assertEqual(summary["level"], "anonymous")
        self.assertEqual(summary["fact_lines"], ["Первая строка", "Вторая строка"])
        self.assertEqual(summary["fallback_detail"], "Вторая строка")
        self.assertEqual(summary["cache_scope"], None)
        self.assertIsNone(summary["traffic_lights"])
        self.assertIsNone(summary["semantic_layer"])
        self.assertEqual(summary["prompt_contract"], "personalized_daily_v2")


if __name__ == "__main__":
    unittest.main()
