import unittest

from backend.app.services.forecast_semantics import (
    build_daily_forecast_semantic_layer,
    build_month_forecast_semantic_layer,
    build_week_forecast_semantic_layer,
)


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


if __name__ == "__main__":
    unittest.main()
