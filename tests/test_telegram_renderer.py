import unittest

from backend.app.reporting.telegram_renderer import (
    render_block_to_telegram_html,
    render_chunk_content_to_telegram_messages,
    split_telegram_html,
)


class TestTelegramRenderer(unittest.TestCase):
    def test_render_supported_blocks(self):
        blocks = [
            {"type": "header", "text": "Раздел"},
            {"type": "paragraph", "text": "Текст с **акцентом** и 5 < 7."},
            {"type": "list", "items": ["Первый", "**Второй**"]},
            {
                "type": "table",
                "columns": [{"header": "Планета"}, {"header": "Знак"}],
                "rows": [["Венера", "Рыбы"]],
            },
            {
                "type": "key_value",
                "items": [{"key": "Дата", "value": "18.03.2026"}],
            },
            {
                "type": "callout",
                "variant": "warning",
                "title": "Важно",
                "content": "Проверь **фокус**.",
            },
            {"type": "rating", "value": 8, "max": 10, "label": "Сила периода"},
            {
                "type": "traffic_lights",
                "items": {"health": "green", "money": "yellow", "love": "red"},
            },
            {"type": "divider"},
        ]

        rendered = [render_block_to_telegram_html(block) for block in blocks]

        self.assertEqual(rendered[0], "<b>Раздел</b>")
        self.assertEqual(rendered[1], "Текст с <b>акцентом</b> и 5 &lt; 7.")
        self.assertEqual(rendered[2], "• Первый\n• <b>Второй</b>")
        self.assertEqual(rendered[3], "• Планета: Венера; Знак: Рыбы")
        self.assertEqual(rendered[4], "Дата: 18.03.2026")
        self.assertEqual(rendered[5], "<b>Важно:</b> Проверь <b>фокус</b>.")
        self.assertEqual(rendered[6], "Оценка: 8/10 — Сила периода")
        self.assertEqual(rendered[7], "Здоровье: 🟢\nФинансы: 🟡\nЛюбовь: 🔴")
        self.assertEqual(rendered[8], "—")

    def test_split_telegram_html_preserves_bold_tags(self):
        text = "<b>Заголовок</b>\n" + ("Очень длинный <b>текст</b> для проверки сплита. " * 12)
        messages = split_telegram_html(text, max_length=90)

        self.assertGreater(len(messages), 1)
        self.assertTrue(all(len(message) <= 90 for message in messages))
        self.assertTrue(all(message.count("<b>") == message.count("</b>") for message in messages))

    def test_render_chunk_content_plain_text_and_split(self):
        plain_text = ("Строка с **акцентом** и 5 < 7. " * 30).strip()
        messages = render_chunk_content_to_telegram_messages(plain_text, max_length=120)

        self.assertGreater(len(messages), 1)
        self.assertTrue(all(len(message) <= 120 for message in messages))
        self.assertTrue(any("<b>акцентом</b>" in message for message in messages))
        self.assertTrue(any("&lt;" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
