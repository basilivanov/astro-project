from unittest.mock import patch

from backend.app.services import feed_service


@patch("backend.app.services.feed_service.log_grace_event")
def test_week_forecast_fallback_generation_logs_error_and_returns_cached_safe_text(mock_log_grace_event):
    feed_service._FEED_CACHE.clear()

    with patch("backend.app.services.feed_service.resolve_feed_llm_mode", return_value="openrouter"), \
         patch("backend.app.services.feed_service.fetch_daily_blocks", return_value={
             "personalization_prompt": "Персональный factual context: Неделя просит собранности.",
             "fallback_detail": "Контекст недели: 🔴 Шторм.",
             "editorial_image": "узкий коридор решений",
             "editorial_move": "сузить фокус до одного шага",
             "prompt_contract": {"version": "2026-03-20"},
             "contract_lines": "- test",
         }), \
         patch("backend.app.services.feed_service.build_cli_client_from_env"), \
         patch("backend.app.services.feed_service.OpenRouterClient.from_env") as mock_client_factory, \
         patch("backend.app.services.feed_service.cleanup_content_artifacts", side_effect=lambda text: text), \
         patch("backend.app.services.feed_service.normalize_daily_vibe_text", wraps=feed_service.normalize_daily_vibe_text):
        mock_client = mock_client_factory.return_value
        mock_client.generate.side_effect = RuntimeError("week fallback telemetry boom")

        with patch("backend.app.services.feed_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value.strftime.return_value = "2026-03-27"
            result = __import__("asyncio").run(
                feed_service.get_daily_vibe_llm(
                    "Овен",
                    "Растущая Луна",
                    "Марс Квадрат Венера",
                    personalization_context={
                        "level": "personalized_v2",
                        "fact_lines": ["Контекст недели: 🔴 Шторм."],
                        "semantic_layer": {
                            "headline": "Неделя просит сузить фокус до одного решения.",
                            "practical_move": "Выбери одну главную задачу и не распыляйся.",
                        },
                    },
                    cache_scope="week-fallback",
                    correlation_id="cid-week-fallback",
                )
            )

    assert isinstance(result, str)
    assert len(result) > 20
    assert "Неделя просит сузить фокус до одного решения" in result
    assert "Выбери одну главную задачу и не распыляйся" in result
    assert ("2026-03-27", "Овен", "week-fallback") in feed_service._FEED_CACHE

    error_calls = [call for call in mock_log_grace_event.call_args_list if call.args[1] == "feed.generation_error"]
    assert error_calls, mock_log_grace_event.call_args_list
    error_kwargs = error_calls[0].kwargs
    assert error_kwargs["fn"] == "get_daily_vibe_llm"
    assert error_kwargs["block"] == "LLM_INVOCATION"
    assert error_kwargs["correlation_id"] == "cid-week-fallback"
    assert error_kwargs["cache_scope"] == "week-fallback"
    assert error_kwargs["mode"] == "openrouter"
    assert "week fallback telemetry boom" in error_kwargs["error"]
