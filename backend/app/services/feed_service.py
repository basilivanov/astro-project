# ############################################################################
# AI_HEADER: MODULE_FEED_SERVICE
# ROLE: Generate daily astrological content using LLM.
# DEPENDENCIES: backend.app.llm.orchestrator
# GRACE_ANCHORS: [FEED_GENERATION]
# ############################################################################

import json
import os
from datetime import datetime
import structlog

from ..llm.orchestrator import OpenRouterClient

logger = structlog.get_logger()

# Simple In-Memory Cache for MVP: {(date_str, moon_sign): "vibe_text"}
_FEED_CACHE = {}

# #START_BLOCK_FEED_GENERATION
async def get_daily_vibe_llm(moon_sign: str, moon_phase: str, aspects_count: int) -> str:
    """
    # PURPOSE: Generate a personalized daily vibe using a cheap LLM.
    # INPUT: Moon data, aspects count.
    # OUTPUT: 2-3 sentences of advice.
    # CONTEXT: Cached per day/sign.
    """
    
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    cache_key = (today_str, moon_sign)
    
    if cache_key in _FEED_CACHE:
        return _FEED_CACHE[cache_key]

    # Prompt construction
    prompt = (
        f"Ты — профессиональный астролог. Напиши краткий прогноз на сегодня (2-3 предложения) на русском языке.\n"
        f"Текущие показатели: Луна в знаке {moon_sign}, фаза: {moon_phase}, количество активных аспектов: {aspects_count}.\n"
        f"Стиль: вдохновляющий, современный, без сложной терминологии. Используй 1 подходящий эмодзи.\n"
        f"Ответь только текстом прогноза."
    )

    try:
        # Using "cheap" mode (GPT-4o-mini)
        client = OpenRouterClient.from_env(mode="cheap")
        vibe = client.generate(prompt)
        vibe = vibe.strip().replace('"', '') # Clean up
        
        _FEED_CACHE[cache_key] = vibe
        logger.info("feed.generated", sign=moon_sign, mode="cheap")
        return vibe
    except Exception as e:
        logger.error("feed.generation_error", error=str(e))
        # Fallback to static if LLM fails
        return f"Сегодня Луна в знаке {moon_sign}. Хороший день для планирования и заботы о себе. ✨"
# #END_BLOCK_FEED_GENERATION
