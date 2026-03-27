import os
import sys
import types
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

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

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.day_brief import build_day_brief_payload, build_day_brief_fallback


client = TestClient(app)


def _sample_facts() -> dict:
    return {
        "local_dt": "2026-03-27T07:00:00+03:00",
        "moon_phase": "Растущая Луна",
        "moon_sign": "Рыбы",
        "traffic_lights": {"health": "red", "money": "green", "love": "yellow"},
        "week_data": {
            "days": [
                {
                    "moon": {"sign": "Рыбы", "phase": "Растущая", "void_of_course": True},
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                }
            ]
        },
        "semantic_layer": {"headline": "Тестовый день", "focus_key": "money_admin"},
        "personalization_level": "personalized_v2",
        "meta": {"fallback_mode": False},
        "month_data": {"status": "GREEN"},
        "year_data": {
            "profection": {"house": 10},
            "months": [{"month": 3, "status": "GREEN"}],
        },
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


class TestDayBriefService(unittest.TestCase):
    def test_build_day_brief_payload_scores_and_factors(self):
        facts = _sample_facts()
        user = SimpleNamespace(birth_time="07:05", birth_time_known=True)

        payload = build_day_brief_payload(facts, user=user)

        self.assertIn(payload["summary"]["day_type"], {"push", "balance", "deep_focus", "caution", "recovery"})
        self.assertGreaterEqual(payload["scores"]["work"], payload["scores"]["relationships"])
        self.assertEqual(len(payload["windows"]), 3)
        self.assertTrue(any(window["type"] == "caution" for window in payload["windows"]))
        self.assertTrue(payload["best_uses"])
        self.assertTrue(payload["risks"])
        self.assertTrue(payload["personalized_factors"])
        explainability = payload["explainability"]
        self.assertTrue(explainability["uses_precise_birth_time"])
        self.assertGreater(explainability["confidence"], 0.4)

    def test_build_day_brief_fallback_returns_safe_payload(self):
        now = datetime(2026, 3, 27, 6, 0, tzinfo=timezone.utc)

        payload = build_day_brief_fallback(now)

        self.assertEqual(payload["summary"]["day_type"], payload["summary"]["day_type"])
        self.assertEqual(len(payload["windows"]), 3)
        self.assertEqual(set(payload["scores"].keys()), {"energy", "work", "relationships", "focus"})


class TestDayBriefEndpoint(unittest.TestCase):
    @patch("backend.app.main.build_day_brief_payload")
    @patch("backend.app.main.build_personalized_daily_facts")
    def test_day_brief_endpoint_returns_payload(self, mock_facts, mock_payload):
        mock_facts.return_value = _sample_facts()
        mock_payload.return_value = {
            "summary": {"headline": "h", "subhead": "s", "day_type": "push"},
            "scores": {"energy": 60, "work": 70, "relationships": 55, "focus": 58},
            "windows": [],
            "best_uses": ["Do"],
            "risks": ["Avoid"],
            "personalized_factors": [],
            "explainability": {
                "confidence": 0.6,
                "uses_precise_birth_time": False,
                "factors_considered": 2,
                "personalization_level": "anonymous",
            },
        }

        response = client.get("/api/day/brief")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["day_type"], "push")
        mock_facts.assert_called_once()
        mock_payload.assert_called_once()

    @patch("backend.app.main.build_day_brief_fallback")
    @patch("backend.app.main.build_personalized_daily_facts")
    def test_day_brief_endpoint_returns_fallback_on_error(self, mock_facts, mock_fallback):
        mock_facts.side_effect = RuntimeError("boom")
        mock_fallback.return_value = {
            "summary": {"headline": "fallback", "subhead": "", "day_type": "caution"},
            "scores": {"energy": 55, "work": 55, "relationships": 55, "focus": 55},
            "windows": [],
            "best_uses": [],
            "risks": [],
            "personalized_factors": [],
            "explainability": {
                "confidence": 0.4,
                "uses_precise_birth_time": False,
                "factors_considered": 0,
                "personalization_level": "anonymous",
            },
        }

        response = client.get("/api/day/brief")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["headline"], "fallback")
        mock_fallback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
