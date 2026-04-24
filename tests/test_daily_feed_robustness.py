import unittest
import asyncio
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.feed_service import (
    _FEED_CACHE,
    build_personalized_feed,
    enqueue_regeneration,
    fetch_daily_blocks,
    normalize_daily_vibe_text,
)


client = TestClient(app)


class TestDailyFeedRobustness(unittest.TestCase):
    def setUp(self):
        _FEED_CACHE.clear()

    def test_normalize_daily_vibe_extracts_text_from_json_blocks(self):
        raw = '[{"type":"paragraph","text":"Сегодня полезно держать темп спокойно и ровно."}]'

        text = normalize_daily_vibe_text(
            raw,
            "Овен",
            "Растущая Луна",
            "Нет мажорных аспектов",
        )

        self.assertEqual(text, "Сегодня полезно держать темп спокойно и ровно.")

    def test_normalize_daily_vibe_rejects_generic_personalized_copy(self):
        raw = "Сегодня отличный день: внутренний огонь поможет преодолеть любые препятствия."

        text = normalize_daily_vibe_text(
            raw,
            "Овен",
            "Новолуние",
            "Сатурн квадрат Венера",
            emphasis="Контекст недели: 🔴 Шторм.",
            personalization_context={
                "level": "personalized_v2",
                "fact_lines": ["Контекст недели: 🔴 Шторм."],
            },
        )

        self.assertNotIn("отличный день", text.lower())
        self.assertIn("Сатурн квадрат Венера", text)
        self.assertIn("Сделай ставку на один мягкий разговор", text)

    def test_normalize_daily_vibe_rejects_unanchored_personalized_copy(self):
        raw = (
            "Сегодня ты можешь чувствовать себя немного уязвимым, особенно в отношениях. "
            "Не стоит начинать новые конфликты и стараться избегать лишних споров."
        )

        text = normalize_daily_vibe_text(
            raw,
            "Рыбы",
            "Растущая Луна",
            "Венера Соединение (0°) Венера, Марс Квадрат (90°) Солнце",
            emphasis="Быстрые транзиты к наталу: Венера Соединение (0°) Венера, Марс Квадрат (90°) Солнце.",
            personalization_context={
                "level": "personalized_v2",
                "fact_lines": [
                    "Быстрые транзиты к наталу: Венера Соединение (0°) Венера, Марс Квадрат (90°) Солнце.",
                    "Контекст недели: 🟢 Зеленый.",
                ],
                "traffic_lights": {"health": "yellow", "money": "green", "love": "green"},
                "semantic_layer": {
                    "headline": "День про мягкий контакт и спокойные договоренности, но скорость и самолюбие легко переводят разговор в нажим.",
                    "practical_move": "Выбери один важный разговор или одну аккуратную покупку и не ускоряй ответ на эмоции.",
                    "money_admin_focus": "Хорошо закрывать одно условие сделки или один документ без лишней суеты.",
                    "relationship_softness": "Мягкость сегодня работает сильнее, чем демонстрация правоты.",
                },
            },
        )

        self.assertIn("мягкий контакт", text.lower())
        self.assertIn("разговор", text.lower())
        self.assertNotIn("венера-венера", text.lower())
        self.assertNotIn("марс-солнце", text.lower())

    @patch("backend.app.services.feed_service.log_grace_event")
    def test_fetch_daily_blocks_returns_semantic_bundle(self, mock_log_grace_event):
        blocks = fetch_daily_blocks(
            "Рыбы",
            "Растущая Луна",
            "Венера Соединение (0°) Венера, Марс Квадрат (90°) Солнце",
            personalization_context={
                "fact_lines": ["Быстрые транзиты к наталу: Венера Соединение (0°) Венера."],
                "traffic_lights": {"money": "green", "love": "yellow", "health": "red"},
                "semantic_layer": {
                    "headline": "День просит мягкого контакта без нажима.",
                    "practical_move": "Выбери один разговор и не разгоняй эмоции.",
                },
            },
            correlation_id="cid-feed-blocks",
        )

        self.assertIn("Персональный factual context", blocks["personalization_prompt"])
        self.assertEqual(blocks["prompt_contract"]["version"], "2026-03-20")
        self.assertEqual(blocks["semantic_layer"]["headline"], "День просит мягкого контакта без нажима.")
        self.assertTrue(any(call.kwargs.get("fn") == "fetch_daily_blocks" for call in mock_log_grace_event.call_args_list))

    @patch("backend.app.services.feed_service.log_grace_event")
    def test_enqueue_regeneration_invalidates_cache(self, mock_log_grace_event):
        _FEED_CACHE[("2026-03-24", "Овен", "scope-a")] = "cached vibe"

        with patch("backend.app.services.feed_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value.strftime.return_value = "2026-03-24"
            removed = enqueue_regeneration("Овен", cache_scope="scope-a", correlation_id="cid-regenerate")

        self.assertTrue(removed)
        self.assertNotIn(("2026-03-24", "Овен", "scope-a"), _FEED_CACHE)
        self.assertTrue(any(call.args[1] == "feed.regeneration_enqueued" for call in mock_log_grace_event.call_args_list))

    @patch("backend.app.services.feed_service.log_grace_event")
    def test_build_personalized_feed_uses_fallback_mode_with_correlation(self, mock_log_grace_event):
        with patch("backend.app.services.feed_service.resolve_feed_llm_mode", return_value="fallback"):
            result = asyncio.run(
                build_personalized_feed(
                    "Овен",
                    "Новолуние",
                    "Сатурн Квадрат Венера",
                    personalization_context={
                        "level": "personalized_v2",
                        "fact_lines": ["Контекст недели: 🔴 Шторм."],
                        "semantic_layer": {"headline": "День лучше сузить до одного приоритета."},
                    },
                    cache_scope="scope-build",
                    correlation_id="cid-build",
                )
            )

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)
        self.assertTrue(any(call.args[1] == "feed.generated" for call in mock_log_grace_event.call_args_list))

    @patch("backend.app.routers.public.build_personalized_daily_facts")
    def test_feed_endpoint_returns_fallback_payload_on_chart_error(self, mock_daily_facts):
        mock_daily_facts.side_effect = RuntimeError("boom")

        response = client.get("/api/feed/today")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["moon_sign"], "Луна")
        self.assertEqual(data["moon_phase"], "Текущий день")
        self.assertIsInstance(data["general_vibe"], str)
        self.assertGreater(len(data["general_vibe"]), 20)
        self.assertEqual(set(data["traffic_lights"].keys()), {"health", "money", "love"})
        self.assertEqual(data.get("moon", {}).get("sign"), "Луна")

    @patch("backend.app.routers.public.get_daily_vibe_llm", new_callable=AsyncMock)
    @patch("backend.app.routers.public.build_personalized_daily_facts")
    def test_feed_endpoint_passes_personalized_context_to_vibe_generation(self, mock_daily_facts, mock_vibe):
        mock_daily_facts.return_value = {
            "moon_sign": "Рыбы",
            "moon_phase": "Растущая Луна",
            "moon_emoji": "🌔",
            "aspect_summary": "Венера соединение Солнце",
            "aspects_count": 1,
            "traffic_lights": {"health": "yellow", "money": "green", "love": "green"},
            "personalization_level": "personalized_v2",
            "fact_lines": [
                "Локальный контекст: пятница, 19.03 09:00, Sochi, timezone Europe/Moscow.",
                "Луна дня: Рыбы, фаза Растущая Луна.",
                "Быстрые транзиты к наталу: Венера соединение Солнце.",
            ],
            "cache_scope": "daily-test-scope",
            "meta": {"cache_scope": "daily-test-scope", "personalization_level": "personalized_v2"},
            "fast_hits": [{"transit": "Venus", "natal": "Sun", "type": "Соединение", "summary": "Венера соединение Солнце"}],
        }
        mock_vibe.return_value = (
            "Венера соединение Солнце помогает мягко проявить инициативу.",
            {"generation_mode": "llm"},
        )

        response = client.get("/api/feed/today")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["moon_sign"], "Рыбы")
        self.assertEqual(data["traffic_lights"]["money"], "green")
        self.assertIn("Венера соединение Солнце", data["general_vibe"])
        self.assertEqual(data.get("moon", {}).get("phase"), "Растущая Луна")
        self.assertEqual(len(data.get("fast_hits", [])), 1)
        mock_vibe.assert_awaited_once()
        _, kwargs = mock_vibe.await_args
        self.assertEqual(kwargs["cache_scope"], "daily-test-scope")
        self.assertEqual(kwargs["personalization_context"]["level"], "personalized_v2")
        self.assertIn(
            "Быстрые транзиты к наталу: Венера соединение Солнце.",
            kwargs["personalization_context"]["fact_lines"],
        )


if __name__ == "__main__":
    unittest.main()


class TestDailyFeedDebug(unittest.TestCase):
    @patch("backend.app.routers.public.get_daily_vibe_llm", new_callable=AsyncMock)
    @patch("backend.app.routers.public.build_personalized_daily_facts")
    def test_feed_endpoint_returns_debug_meta_only_for_internal(self, mock_daily_facts, mock_vibe):
        mock_daily_facts.return_value = {
            "moon_sign": "Рыбы",
            "moon_phase": "Растущая Луна",
            "moon_emoji": "🌔",
            "aspect_summary": "Венера соединение Солнце",
            "aspects_count": 1,
            "traffic_lights": {"health": "yellow", "money": "green", "love": "green"},
            "personalization_level": "personalized_v2",
            "fact_lines": ["Локальный контекст: пятница, 19.03 09:00, Sochi, timezone Europe/Moscow."],
            "cache_scope": "daily-test-scope",
            "meta": {"cache_scope": "daily-test-scope", "fallback_mode": False},
            "fast_hits": [],
        }
        mock_vibe.return_value = (
            "Точный фон дня помогает держать приоритет собранно.",
            {"generation_mode": "llm"},
        )

        response = client.get("/api/feed/today?debug=true", headers={"X-Telegram-Auth": "123"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("meta", {}).get("cache_scope"), "daily-test-scope")

        anon = client.get("/api/feed/today?debug=true")
        self.assertEqual(anon.status_code, 200)
        self.assertIsNone(anon.json().get("meta"))

    @patch("backend.app.routers.public._log_api_gateway_event")
    @patch("backend.app.routers.public.authenticate_telegram_user")
    def test_feed_endpoint_auth_fallback_logs_without_raw_auth_detail(self, mock_authenticate, mock_log_event):
        from fastapi import HTTPException

        mock_authenticate.side_effect = HTTPException(
            status_code=401,
            detail="token=super-secret-init-data",
        )

        response = client.get("/api/feed/today", headers={"X-Telegram-Auth": "super-secret-init-data"})

        self.assertEqual(response.status_code, 200)
        debug_calls = [call for call in mock_log_event.call_args_list if len(call.args) > 1 and call.args[1] == "feed.debug"]
        auth_fallback = next(call for call in debug_calls if call.kwargs.get("stage") == "auth_fallback")
        self.assertEqual(auth_fallback.kwargs["reason"], "telegram_auth_invalid")
        self.assertNotIn("detail", auth_fallback.kwargs)
        serialized = str(mock_log_event.call_args_list)
        self.assertNotIn("super-secret-init-data", serialized)
