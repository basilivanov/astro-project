import os
import sys
import types
import unittest
from datetime import datetime, timezone
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

from backend.app.services.forecast_semantics import (
    build_daily_forecast_semantic_layer,
    build_month_forecast_semantic_layer,
    build_week_forecast_semantic_layer,
)
from backend.app.services.aggregation_weights import apply_weighted_factors
from backend.app.services.week_map import build_week_map


class _StubUser:
    def __init__(self):
        self.birth_date = "1990-01-01"
        self.birth_time = "08:00"
        self.birth_time_known = True
        self.birth_place = "Moscow"
        self.birth_lat = 55.75
        self.birth_lon = 37.62
        self.birth_timezone = "Europe/Moscow"
        self.current_location = "Moscow"
        self.current_timezone = "Europe/Moscow"


class TestForecastSemantics(unittest.TestCase):
    def test_daily_semantic_layer_prefers_life_patterns_over_aspect_pairs(self):
        semantic = build_daily_forecast_semantic_layer(
            fast_hits=[
                {"transit": "Venus", "natal": "Venus", "type": "Соединение (0°)"},
                {"transit": "Mars", "natal": "Sun", "type": "Квадрат (90°)"},
            ],
            traffic_lights={"health": "yellow", "money": "green", "love": "green"},
            day_context={"moon": {"void_of_course": False}},
            month_data={"status": "GREEN"},
        )

        self.assertEqual(semantic["focus_key"], "money_admin")
        self.assertIn("симпат", semantic["headline"])
        self.assertIn("нажим", semantic["headline"])
        self.assertIn("документ", semantic["practical_move"].lower())
        self.assertNotIn("венера-венера", semantic["headline"].lower())

    def test_week_semantic_layer_builds_human_week_arc(self):
        semantic = build_week_forecast_semantic_layer(
            {"traffic_light": "YELLOW", "avg_tension": 0.8},
            [
                {
                    "traffic_light": "YELLOW",
                    "moon": {"void_of_course": False},
                    "events": ["Меркурий -> Овен"],
                },
                {
                    "traffic_light": "RED",
                    "moon": {"void_of_course": True},
                    "events": ["Марс Квадрат Луна"],
                },
                {
                    "traffic_light": "GREEN",
                    "moon": {"void_of_course": False},
                    "events": ["Венера Тригон Венера"],
                },
            ],
        )

        self.assertIn("неделя", semantic["headline"].lower())
        self.assertTrue(
            any(token in semantic["money_admin_focus"].lower() for token in ("соглас", "разговор", "рабоч"))
        )
        self.assertIn("коротк", semantic["pacing"].lower())
        self.assertTrue(
            any(token in semantic["relationship_softness"].lower() for token in ("разговор", "обратн", "отнош"))
        )

    def test_month_semantic_layer_keeps_campaign_language(self):
        semantic = build_month_forecast_semantic_layer(
            status="YELLOW",
            event_cards=[
                {
                    "event": "Меркурий -> Овен",
                    "life_signal": "переговоры, письма, документы и короткие согласования выходят на первый план.",
                    "pressure": "low",
                },
                {
                    "event": "Марс квадрат Солнце",
                    "life_signal": "темп легко превращается в конфликт: силу нужно дозировать, а не демонстрировать.",
                    "pressure": "high",
                },
            ],
            phases=[{"pressure": "high"}],
        )

        self.assertIn("месяц", semantic["headline"].lower())
        self.assertTrue(
            any(token in semantic["tension"].lower() for token in ("распыл", "стык", "цена", "координац"))
        )
        self.assertTrue(
            any(token in semantic["money_admin_focus"].lower() for token in ("цена", "услов", "работ"))
        )
        self.assertIn("мягк", semantic["relationship_softness"].lower())
        self.assertTrue(
            any(token in semantic["scene_seed"].lower() for token in ("переговор", "услов", "координац", "график"))
        )
        self.assertIn("сначала", semantic["campaign_shape"].lower())
        self.assertTrue(
            any(token in semantic["finale"].lower() for token in ("финал", "фикс", "разговор", "результат"))
        )

    def test_apply_weighted_factors_enforces_profile_table(self):
        factors = [
            {"category": "slow_background", "label": "фон", "weight": 1.0, "confidence": 0.5},
            {"category": "day_decomposition", "label": "дни", "weight": 0.4, "confidence": 1.0},
            {"category": "weekly_triggers", "label": "триггеры", "weight": 0.7},
        ]
        result = apply_weighted_factors("week_map", factors, top_n=2)
        self.assertEqual(result["profile"], "week_map")
        self.assertEqual(len(result["top_factors"]), 2)
        self.assertGreater(result["total_score"], 0)
        categories = {f["category"] for f in result["factors"]}
        self.assertTrue({"slow_background", "day_decomposition", "weekly_triggers"}.issubset(categories))

    @patch("backend.app.services.week_map.StelliumEngine")
    def test_build_week_map_assembles_structured_payload(self, mock_engine_cls):
        engine = mock_engine_cls.return_value
        moon = type("Body", (), {"name": "Moon", "longitude": 30.0})()
        sun = type("Body", (), {"name": "Sun", "longitude": 0.0})()
        engine.create_transit_chart.return_value = type("Chart", (), {"positions": [moon, sun]})()
        engine.create_natal_chart.return_value = object()
        engine.calculate_forecast_week_data.return_value = {
            "days": [
                {
                    "date": "2026-03-24",
                    "weekday": "Tuesday",
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "tension_score": 0.1,
                    "events": ["Венера тригон ASC"],
                },
                {
                    "date": "2026-03-25",
                    "weekday": "Wednesday",
                    "traffic_light": "RED",
                    "traffic_desc": "🔴 Шторм",
                    "tension_score": 2.4,
                    "events": ["Марс квадрат Солнце"],
                },
            ],
            "summary": {"traffic_light": "YELLOW", "avg_tension": 0.8},
        }

        user = _StubUser()
        payload = build_week_map(datetime(2026, 3, 24, 6, 0, tzinfo=timezone.utc), user)

        self.assertIn("theme", payload)
        self.assertEqual(len(payload["day_cards"]), 2)
        self.assertEqual(payload["domains"]["work"], 55)
        self.assertEqual(payload["timezone"], "Europe/Moscow")
        self.assertTrue(payload["major_factors"])


if __name__ == "__main__":
    unittest.main()
