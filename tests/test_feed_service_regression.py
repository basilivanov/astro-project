import asyncio
from datetime import datetime
from unittest.mock import patch

from backend.app.services import feed_service


def test_fetch_daily_blocks_returns_deterministic_fallback_bundle_without_personalization():
    blocks = feed_service.fetch_daily_blocks(
        "Овен",
        "Новолуние",
        "Сатурн Квадрат Венера",
        correlation_id="cid-fetch-regression",
    )

    assert blocks["personalization_prompt"] == ""
    assert blocks["fallback_detail"] == ""
    assert blocks["moon_sign"] == "Овен"
    assert blocks["moon_phase"] == "Новолуние"
    assert blocks["aspects_summary"] == "Сатурн Квадрат Венера"
    assert isinstance(blocks["editorial_image"], str) and blocks["editorial_image"]
    assert isinstance(blocks["editorial_move"], str) and blocks["editorial_move"]
    assert isinstance(blocks["prompt_contract"], dict)
    assert blocks["prompt_contract"]["version"] == "2026-03-20"
    assert "Ровно 2 коротких предложения" in blocks["contract_lines"]
    assert blocks["semantic_layer"] == {}


def test_enqueue_regeneration_returns_false_for_missing_cache_entry_and_keeps_fallback_safe():
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    cache_key = (today_str, "Лев", "scope-miss")
    feed_service._FEED_CACHE.pop(cache_key, None)

    invalidated = feed_service.enqueue_regeneration(
        "Лев",
        cache_scope="scope-miss",
        correlation_id="cid-enqueue-miss",
    )

    assert invalidated is False
    assert cache_key not in feed_service._FEED_CACHE


def test_enqueue_regeneration_removes_existing_cache_entry():
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    cache_key = (today_str, "Дева", "scope-hit")
    feed_service._FEED_CACHE[cache_key] = "cached-vibe"

    invalidated = feed_service.enqueue_regeneration(
        "Дева",
        cache_scope="scope-hit",
        correlation_id="cid-enqueue-hit",
    )

    assert invalidated is True
    assert cache_key not in feed_service._FEED_CACHE


def test_build_personalized_feed_falls_back_when_llm_generation_raises():
    personalization_context = {
        "level": "personalized_v2",
        "fact_lines": ["Контекст недели: 🔴 плотный ритм и узкий приоритет."],
        "fallback_detail": "Сначала закрой один обязательный вопрос.",
        "semantic_layer": {
            "headline": "День лучше сузить до одного понятного шага.",
            "practical_move": "Сначала закрой один обязательный вопрос.",
        },
    }

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    cache_key = (today_str, "Овен", "scope-build-fallback")
    feed_service._FEED_CACHE.pop(cache_key, None)

    with patch("backend.app.services.feed_service.resolve_feed_llm_mode", return_value="openrouter"), patch(
        "backend.app.services.feed_service.OpenRouterClient.from_env"
    ) as mock_client_factory:
        mock_client_factory.return_value.generate.side_effect = RuntimeError("llm boom")

        result = asyncio.run(
            feed_service.build_personalized_feed(
                "Овен",
                "Новолуние",
                "Сатурн Квадрат Венера",
                personalization_context=personalization_context,
                cache_scope="scope-build-fallback",
                correlation_id="cid-build-fallback",
            )
        )

    assert isinstance(result, str)
    assert len(result) > 20
    assert result.count(".") >= 1
    assert "отличный день" not in result.lower()
    assert feed_service._FEED_CACHE[cache_key] == result
