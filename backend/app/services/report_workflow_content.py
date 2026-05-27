# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_CONTENT
# ROLE: Content cleanup and deterministic template rendering helpers.
# DEPENDENCIES: json, re, backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [CONTENT_CLEANUP, TEMPLATE_CONTENT]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTENT
# purpose: Own JSON-safe report copy cleanup, emoji injection, and deterministic section template content.
# inputs:
#   - Raw LLM or fallback text payloads
#   - SectionSpec values for template section rendering
# outputs:
#   - Cleaned report content strings and JSON block strings
# trace_obligations:
#   - Pure helper module; caller workflow retains report_id/block logging attribution
# invariants:
#   - Text cleanup and template copy remain byte-compatible with the pre-extraction workflow helpers
# non_goals:
#   - Does not call LLMs or mutate Report/ReportChunk persistence state
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTENT

# START_MODULE_MAP: M-REPORT-WORKFLOW-CONTENT
# entrypoints:
#   - cleanup_content_artifacts -> CONTENT_CLEANUP
#   - inject_planet_emojis -> CONTENT_EMOJI_INJECTION
#   - build_section_template_content -> TEMPLATE_CONTENT
# owned_tests:
#   - tests/test_validation_template_fallback.py
#   - tests/test_week_renderer.py
# END_MODULE_MAP: M-REPORT-WORKFLOW-CONTENT

from __future__ import annotations

import json
import re
from typing import Any, List

from ..llm.orchestrator import SectionSpec

PLANET_EMOJI_MAP = {
    "Солнце": "☀️",
    "Луна": "🌙",
    "Меркурий": "☿",
    "Венера": "♀️",
    "Марс": "♂️",
    "Юпитер": "♃",
    "Сатурн": "♄",
    "Уран": "♅",
    "Нептун": "♆",
    "Плутон": "♇",
    "Хирон": "⚷",
    "Лилит": "⚸",
    "Селена": "🌟",
    "Северный узел": "☊",
    "Южный узел": "☋",
    "Sun": "☀️",
    "Moon": "🌙",
    "Mercury": "☿",
    "Venus": "♀️",
    "Mars": "♂️",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
    "Chiron": "⚷",
    "Lilith": "⚸",
    "Selena": "🌟",
    "North Node": "☊",
    "South Node": "☋",
}

# START_BLOCK: CONTENT_CLEANUP
def _clean_text_artifacts(text: str) -> str:
    """Internal text cleaner."""
    if not text:
        return ""

    # 1. Fix L-tokens (L 1, L 10)
    text = re.sub(r'\b([Ll])\s+(\d+)\b', r'\1\2', text)
    
    # 2. Fix Fractions "8 / 10" -> "8/10"
    text = re.sub(r'(\d)\s+/\s+(\d)', r'\1/\2', text)
    
    # 3. Fix Date Dots "27 . 01" -> "27.01"
    text = re.sub(r'(\d)\s+\.\s+(\d)', r'\1.\2', text)
    
    # 4. Fix Double Spaces (except newlines)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # 4.1 Normalize line-leading bullets
    text = re.sub(r'(?m)^\s*[•●▪▫◦]\s+', '- ', text)
    text = re.sub(r'(?m)^\s*[–—]\s+', '- ', text)

    # 4.2 Normalize recommendations heading
    text = re.sub(
        r'(?m)^\s*#{2,4}\s+.*рекомендации.*$',
        '### 💡 Рекомендации',
        text,
        flags=re.IGNORECASE,
    )

    # 5. Fix inline bullets
    def replace_bullet(match):
        return f"\n- {match.group(1)}"
    text = re.sub(r'(?<!^)(?<!\n)\s*[•●]\s*(.+?)(?=[•●\n]|$)', replace_bullet, text)

    # 6. EN -> RU Zodiac Translation (Anti-Anglicism)
    # Using word boundaries to avoid replacing parts of other words
    en_ru_pure = {
        "Aries": "Овен", "Taurus": "Телец", "Gemini": "Близнецы", "Cancer": "Рак",
        "Leo": "Лев", "Virgo": "Дева", "Libra": "Весы", "Scorpio": "Скорпион",
        "Sagittarius": "Стрелец", "Capricorn": "Козерог", "Aquarius": "Водолей", "Pisces": "Рыбы"
    }
    for en, ru in en_ru_pure.items():
        text = re.sub(rf"\b{en}\b", ru, text, flags=re.IGNORECASE)

    return text.strip()


def _inject_emojis_text(text: str) -> str:
    """Internal emoji injector."""
    for name, emoji in PLANET_EMOJI_MAP.items():
        escaped = re.escape(name)
        pattern = rf"(?<!{re.escape(emoji)}\s)(?<!{re.escape(emoji)})\b{escaped}\b"
        text = re.sub(pattern, f"{emoji} {name}", text)
    return text


def _process_json_recursively(data: Any, processors: List[callable]) -> Any:
    if isinstance(data, str):
        res = data
        for p in processors:
            res = p(res)
        return res
    if isinstance(data, list):
        return [_process_json_recursively(item, processors) for item in data]
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Process text fields
            if k in {"text", "content", "title", "key", "value", "header", "description"}:
                new_dict[k] = _process_json_recursively(v, processors)
            # Recurse into containers
            elif k in {"items", "rows", "columns"}:
                new_dict[k] = _process_json_recursively(v, processors)
            else:
                new_dict[k] = v
        return new_dict
    return data


def cleanup_content_artifacts(text: str) -> str:
    """
    # PURPOSE: Fix common LLM formatting artifacts (JSON-aware).
    """
    if not text:
        return ""
    
    # Try JSON
    try:
        if text.strip().startswith("["):
            blocks = json.loads(text)
            processed = _process_json_recursively(blocks, [_clean_text_artifacts])
            return json.dumps(processed, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        pass
        
    return _clean_text_artifacts(text)


def inject_planet_emojis(content: str) -> str:
    """
    # PURPOSE: Ensure planet names include emoji prefixes (JSON-aware).
    """
    if not content:
        return ""
        
    # Try JSON
    try:
        if content.strip().startswith("["):
            blocks = json.loads(content)
            # Apply clean then inject
            processed = _process_json_recursively(
                blocks, 
                [_clean_text_artifacts, _inject_emojis_text]
            )
            return json.dumps(processed, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        pass
        
    # Fallback text
    txt = _clean_text_artifacts(content)
    return _inject_emojis_text(txt)
# END_BLOCK: CONTENT_CLEANUP

# START_BLOCK: TEMPLATE_CONTENT
def build_section_template_content(spec: SectionSpec) -> str:
    """
    # PURPOSE: Provide a low-cost local template for test-mode generation (JSON Blocks).
    # INPUT: section spec.
    # OUTPUT: JSON string (list of blocks).
    # CONTEXT: Used when LLM calls are disabled for tests.
    """

    blocks = []

    if spec.section_id == "executive_summary":
        blocks.extend([
            {
                "type": "header",
                "level": 2,
                "text": "Главное по карте"
            },
            {
                "type": "list",
                "items": [
                    "Сильная сторона: устойчивость в важных задачах.",
                    "Сильная сторона: умение видеть ключевой приоритет.",
                    "Риск: переутомление при перегрузе обязательствами.",
                    "Риск: внутренние сомнения перед резким шагом.",
                    "Ключ к отношениям: говорить прямо о чувствах и границах.",
                    "Ключ к деньгам: опираться на дисциплину и долгий горизонт."
                ],
                "ordered": False
            },
            {
                "type": "callout",
                "variant": "info",
                "title": "Фокус развития",
                "content": "Лучший результат приходит там, где есть ритм, ясные критерии и отказ от лишнего."
            }
        ])
    elif spec.section_id == "synthesis":
        blocks.extend([
            {
                "type": "callout",
                "variant": "quote",
                "title": "Образ карты",
                "content": "Карта про внутренний стержень, который раскрывается через осознанный выбор."
            },
            {
                "type": "paragraph",
                "text": "В этой карте важны собранность, чувство собственного курса и умение не отдавать энергию второстепенному."
            },
            {
                "type": "paragraph",
                "text": "**Главный тезис:** устойчивость рождается из ясности приоритетов."
            }
        ])
    elif spec.section_id == "framework_elements_modes":
        blocks.extend([
            {
                "type": "list",
                "items": [
                    "Огонь - 10%",
                    "Земля - 50%",
                    "Воздух - 20%",
                    "Вода - 20%",
                ],
                "ordered": False,
            },
            {
                "type": "paragraph",
                "text": "Доминанта: Земля и Кардинальность собирают темперамент системного организатора, который лучше всего раскрывается через ясную задачу, план и видимый результат."
            },
            {
                "type": "paragraph",
                "text": "Дефицит: слабее Огонь и Мутабельность, поэтому полезно отдельно тренировать право на старт, гибкость и способность менять маршрут без чувства провала."
            },
            {
                "type": "paragraph",
                "text": "Стиль жизни: жизненный ритм лучше строить циклами, где есть запуск, опора и короткие пересборки, чтобы Кардинальность не перегревала систему."
            },
            {
                "type": "paragraph",
                "text": "Формула баланса: опираться на Землю, Кардинальность и Фиксированность, но сознательно подпитывать Огонь, Воздух, Воду и Мутабельность через движение, контакт и эмоциональную паузу."
            },
        ])
    elif spec.section_id == "final_synthesis":
        blocks.extend([
            {
                "type": "callout",
                "variant": "success",
                "title": "Финальная сборка",
                "content": "**Девиз:** двигайся в своем темпе и не разменивайся на шум.\n**Главный совет:** опирайся на факты, ритм и последовательность."
            }
        ])
    elif spec.section_id == "week_strategy":
        blocks.extend([
            {
                "type": "header",
                "level": 2,
                "text": "📅 ПРОГНОЗ НА НЕДЕЛЮ (Stub)"
            },
            {
                "type": "callout",
                "variant": "warning",
                "title": "СТАТУС НЕДЕЛИ",
                "content": "🟡 Неделя просит держать темп ровным: сначала приоритет, потом все остальное."
            },
            {
                "type": "header",
                "level": 2,
                "text": "Главная тема"
            },
            {
                "type": "paragraph",
                "text": "Неделя не про красивый разгон, а про умение не расплескать силы на лишние фронты."
            },
            {
                "type": "header",
                "level": 2,
                "text": "Подневная стратегия"
            },
            {
                "type": "header",
                "level": 3,
                "text": "Понедельник, 01.01 (🟢 Зеленый)"
            },
            {
                "type": "list",
                "items": [
                    "**Луна:** Овен, Растущая",
                    "**Астро-события:** Луна секстиль Юпитер",
                    "**Фокус:** Старт проектов",
                    "**Риск:** Импульсивность"
                ],
                "ordered": False
            },
            {
                "type": "header", 
                "level": 2, 
                "text": "Резюме по срезам"
            },
            {
                "type": "traffic_lights", 
                "items": {
                    "money": "green", 
                    "health": "yellow", 
                    "love": "red" 
                }
            }
        ])
    elif spec.section_id == "month_full_forecast" or spec.section_id == "month_theme":
        blocks.extend([
            {
                "type": "header",
                "level": 2,
                "text": "📅 ПРОГНОЗ НА МЕСЯЦ"
            },
            {
                "type": "callout",
                "variant": "warning",
                "title": "СТАТУС МЕСЯЦА",
                "content": "🟡 Месяц просит не суетиться: реальный результат придет через ритм, а не через рывок."
            },
            {
                "type": "header", 
                "level": 2, 
                "text": "Ключевые события"
            },
            {
                "type": "list",
                "items": [
                    "01.03: Новолуние в Рыбах",
                    "15.03: Марс квадрат Уран"
                ],
                "ordered": False
            },
            {
                "type": "header",
                "level": 2,
                "text": "Стратегия по неделям"
            },
            {
                "type": "paragraph",
                "text": "Месяц идет не одной прямой, а четырьмя фазами: сначала собери курс, потом двигай то, что дает реальный ход, и не подменяй стратегию суетой."
            },
            {
                "type": "header",
                "level": 3,
                "text": "Неделя 1 (01.03-07.03)"
            },
            {
                "type": "list",
                "items": [
                    "**Фокус:** Собрать одну главную ставку месяца.",
                    "**Что продвигать:** Переговоры и подготовку опорной задачи.",
                    "**Где не форсировать:** Не открывать лишние фронты без ясной базы."
                ],
                "ordered": False
            },
            {
                "type": "header",
                "level": 3,
                "text": "Неделя 2 (08.03-14.03)"
            },
            {
                "type": "list",
                "items": [
                    "**Фокус:** Проверить, где темп реально держится.",
                    "**Что продвигать:** Рабочие договоренности и сборку процесса.",
                    "**Где не форсировать:** Не путать промежуточный результат с финальным."
                ],
                "ordered": False
            },
            {
                "type": "header",
                "level": 3,
                "text": "Неделя 3 (15.03-21.03)"
            },
            {
                "type": "list",
                "items": [
                    "**Фокус:** Удержать главный трек без распыления.",
                    "**Что продвигать:** Ключевые решения и точечные переговоры.",
                    "**Где не форсировать:** Не разгонять конфликт и не обещать лишнего."
                ],
                "ordered": False
            },
            {
                "type": "header",
                "level": 3,
                "text": "Неделя 4 (22.03-28.03)"
            },
            {
                "type": "list",
                "items": [
                    "**Фокус:** Зафиксировать результат и подготовить следующий шаг.",
                    "**Что продвигать:** Завершение, упаковку и подтверждение договоренностей.",
                    "**Где не форсировать:** Не штурмовать финиш из суеты."
                ],
                "ordered": False
            },
            {
                "type": "header", 
                "level": 2, 
                "text": "Итог месяца"
            },
            {
                "type": "key_value",
                "items": [
                    {"key": "Финансы", "value": "Ставка на осторожные решения и контроль ритма расходов."},
                    {"key": "Отношения", "value": "Меньше резких реакций, больше ясных договоренностей."},
                    {"key": "Энергия", "value": "Результат держится на режиме, а не на коротком всплеске."}
                ]
            },
            {
                "type": "callout",
                "variant": "success",
                "title": "Практический ход",
                "content": "Каждую неделю возвращайся к одной главной ставке месяца и отсекай шум раньше, чем он съест внимание."
            }
        ])
    else:
        title = spec.title.strip()
        blocks.extend([
            {
                "type": "header",
                "level": 3,
                "text": f"🧭 О чем этот блок: {title}"
            },
            {
                "type": "paragraph",
                "text": f"{title} раскрывает ключевые процессы и фокус внимания. Здесь важно отметить динамику и зоны роста."
            },
            {
                "type": "table",
                "columns": [
                    {"header": "Параметр", "width": "30%"},
                    {"header": "Содержание", "width": "70%"}
                ],
                "rows": [
                    ["Фокус", "Основные задачи и акценты"],
                    ["Ресурс", "Сильные стороны и опоры"],
                    ["Риск", "Слепые зоны и напряжение"]
                ]
            },
            {
                "type": "callout",
                "variant": "info",
                "title": "Тезис",
                "content": "Настройка этого блока дает устойчивую опору и ясный вектор."
            },
            {
                "type": "header",
                "level": 3,
                "text": "💡 Рекомендации"
            },
            {
                "type": "list",
                "style": "bullet",
                "items": [
                    "Сформулируйте 1-2 практичных шага.",
                    "Отмечайте сигналы и фиксируйте наблюдения."
                ]
            }
        ])

    return json.dumps(blocks, ensure_ascii=False)
# END_BLOCK: TEMPLATE_CONTENT
