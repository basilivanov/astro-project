import json
import unittest
from unittest.mock import MagicMock, patch

from backend.app.llm.orchestrator import SectionResult, SectionSpec
from backend.app.services.report_workflow import (
    _render_week_strategy_content,
    generate_section_content,
)


def _build_week_context():
    return {
        "client": {
            "gender": "female",
            "report_type": "week_forecast",
            "birth_time_known": True,
        },
        "week_forecast_data": {
            "summary": {
                "traffic_light": "YELLOW",
                "avg_tension": 0.8,
            },
            "days": [
                {
                    "date": f"2026-03-{day:02d}",
                    "weekday_ru": weekday,
                    "date_label": f"{day:02d}.03",
                    "traffic_light": traffic,
                    "traffic_desc": traffic_desc,
                    "tension_score": score,
                    "moon": {
                        "sign": moon_sign,
                        "phase": moon_phase,
                        "void_of_course": void,
                    },
                    "moon_label": f"{moon_sign}, {moon_phase}",
                    "events": events,
                }
                for day, weekday, traffic, traffic_desc, score, moon_sign, moon_phase, void, events in [
                    (19, "понедельник", "YELLOW", "🟡 Внимание", 1.0, "Овен", "Растущая", False, ["Марс Квадрат Луна"]),
                    (20, "вторник", "GREEN", "🟢 Зеленый", -0.2, "Телец", "Растущая", False, []),
                    (21, "среда", "RED", "🔴 Шторм", 2.4, "Близнецы", "Растущая", True, ["Меркурий -> Овен"]),
                    (22, "четверг", "YELLOW", "🟡 Внимание", 0.9, "Рак", "Растущая", False, []),
                    (23, "пятница", "GREEN", "🟢 Зеленый", -0.4, "Лев", "Полнолуние", False, ["Венера Тригон Венера"]),
                    (24, "суббота", "YELLOW", "🟡 Внимание", 0.6, "Дева", "Убывающая", False, []),
                    (25, "воскресенье", "YELLOW", "🟡 Внимание", 0.5, "Весы", "Убывающая", False, []),
                ]
            ],
        },
    }


class TestWeekRenderer(unittest.IsolatedAsyncioTestCase):
    def test_week_renderer_keeps_factual_structure_and_colors(self):
        context = _build_week_context()
        llm_content = json.dumps(
            [
                {
                    "type": "callout",
                    "variant": "success",
                    "title": "СТАТУС НЕДЕЛИ",
                    "content": "Неделя требует аккуратной координации, чтобы не расплескать силы на параллельные реакции.",
                },
                {
                    "type": "paragraph",
                    "text": "Главная тема недели в том, чтобы не путать срочность с важностью и не отдавать центр дня чужому давлению.",
                },
                {
                    "type": "traffic_lights",
                    "items": {"money": "green", "health": "green", "love": "green"},
                },
            ],
            ensure_ascii=False,
        )

        blocks = json.loads(_render_week_strategy_content(context, llm_content=llm_content))

        self.assertEqual(blocks[0]["type"], "header")
        self.assertIn("📅 ПРОГНОЗ НА НЕДЕЛЮ", blocks[0]["text"])
        self.assertEqual(blocks[1]["type"], "callout")
        self.assertEqual(blocks[1]["variant"], "warning")
        self.assertIn("Пик напряжения", blocks[1]["content"])
        self.assertEqual(blocks[2]["text"], "Главная тема")
        self.assertIn("Главный внешний триггер недели", blocks[3]["text"])

        day_headers = [block["text"] for block in blocks if block.get("type") == "header" and block.get("level") == 3]
        self.assertEqual(len(day_headers), 7)
        self.assertIn("Среда, 21.03 (🔴 Шторм)", day_headers)

        traffic_block = next(block for block in blocks if block.get("type") == "traffic_lights")
        self.assertEqual(traffic_block["items"], {"money": "yellow", "health": "yellow", "love": "yellow"})

    @patch("backend.app.services.report_workflow.generate_section_with_retries")
    async def test_generate_section_content_normalizes_week_llm_success_path(self, mock_generate):
        context = _build_week_context()
        spec = SectionSpec(section_id="week_strategy", title="Стратегия недели", prompt="test")
        mock_generate.return_value = SectionResult(
            section_id="week_strategy",
            title="Стратегия недели",
            content=json.dumps(
                [
                    {"type": "header", "level": 2, "text": "Сломанный заголовок"},
                    {
                        "type": "paragraph",
                        "text": "Неделя требует собранного темпа и отказа от лишних обещаний до факта.",
                    },
                ],
                ensure_ascii=False,
            ),
        )

        result = await generate_section_content(
            spec,
            context,
            chart_data={},
            llm_client=MagicMock(),
            fallback_models=[],
            retry_attempts=1,
            use_template=False,
        )

        blocks = json.loads(result.content)
        top_headers = [block["text"] for block in blocks if block.get("type") == "header" and block.get("level") == 2]
        self.assertIn("Главная тема", top_headers)
        self.assertIn("Подневная стратегия", top_headers)
        self.assertIn("Резюме по срезам", top_headers)

        day_lists = [block for block in blocks if block.get("type") == "list"]
        self.assertEqual(len(day_lists), 7)
        self.assertTrue(all(any("**Фокус:**" in item for item in block["items"]) for block in day_lists))


if __name__ == "__main__":
    unittest.main()
