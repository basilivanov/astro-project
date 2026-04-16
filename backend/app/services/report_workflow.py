# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW
# ROLE: Domain service for report generation pipeline.
# DEPENDENCIES: stellium_engine.py, backend/app/models.py, backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [WORKFLOW_UTILS, WORKFLOW_CONTEXT, WORKFLOW_CHART, WORKFLOW_SECTIONS, WORKFLOW_MARKDOWN, WORKFLOW_GENERATION]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW
# purpose: Orchestrate report context assembly, chart calculation, section generation, persistence, and delivery notifications.
# inputs:
#   - Report payload/request objects with client, chart, and report-type fields
#   - SQLAlchemy session plus Report / ReportChunk / ReportRun rows
#   - LLM orchestration dependencies, chart engines, and semantic-layer builders
# outputs:
#   - Report context dictionaries, chart payloads, section specs, section content, and delivery side effects
#   - Report row/chunk/run mutations aligned with backend runtime and admin flows
# trace_obligations:
#   - Public workflow entrypoints emit contract/block-aware logs through shared workflow helper
#   - Every lifecycle log carries module, contract, block, and correlation_id or report_id
#   - Resume/checkout/admin bridge wording stays aligned with access_control and one_off_entitlements semantics
# vm_ids:
#   - VM-REPORT-WORKFLOW-PIPELINE
#   - VM-REPORT-CONTRACT
#   - VM-REPORT-CONTEXT
# dependencies:
#   - backend/app/services/access_control.py
#   - backend/app/services/one_off_entitlements.py
#   - backend/app/llm/orchestrator.py
#   - backend/app/reporting/section_templates.py
# side_effects:
#   - Persists ReportRun/ReportChunk/report status changes
#   - Emits workflow/admin trace logs and telegram delivery notifications
# invariants:
#   - Section ordering remains stable for persisted chunks and rendered delivery
#   - Fallback content preserves usable report output when allowed by workflow policy
# failure_policy:
#   - Propagates unrecoverable generation/chart failures to caller-managed flows
#   - Marks report/chunks/runs failed or partial with structured trace evidence
# non_goals:
#   - Does not decide billing/access entitlements directly
#   - Does not own checkout resume state transitions outside workflow logging alignment
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW

# START_MODULE_MAP: M-REPORT-WORKFLOW
# purpose: Map workflow entrypoints to semantic generation blocks and verification traces.
# entrypoints:
#   - start_report_run -> RUN_START_RECORD
#   - build_section_specs -> SECTION_SPEC_RESOLUTION
#   - load_section_specs_for_report -> SECTION_SPEC_RESTORE
#   - build_chart_data -> CHART_ENGINE_DISPATCH / HORARY_ADAPTER_BRIDGE / SOLAR_RETURN_BRIDGE / SYNASTRY_BRIDGE
#   - build_report_context -> FORECAST_WINDOW_RESOLUTION / CLIENT_PROFILE_NORMALIZATION / FACTS_CONTEXT_TRIM / FORECAST_SEMANTIC_LAYER
#   - initialize_report_chunks -> CHUNK_RESET / CHUNK_UPSERT / CHUNK_STATUS_SUMMARY
#   - generate_section_content -> SECTION_STATIC_OVERRIDE / SECTION_LLM_GENERATION / SECTION_FALLBACK_POLICY
#   - generate_report_sections -> GENERATION_PREPARE / GENERATION_PARALLEL_SECTIONS / GENERATION_FINAL_SYNTHESIS / GENERATION_FINALIZE / REPORT_READY_NOTIFY
# trace_obligations:
#   - Logs use workflow helper with module, contract, block, and report_id/correlation_id
#   - Admin queue/resume/checkout wording stays aligned with access_control and one_off_entitlements bridges
# vm_ids:
#   - VM-REPORT-WORKFLOW-PIPELINE
#   - VM-REPORT-CONTRACT
#   - VM-REPORT-CONTEXT
# owned_tests:
#   - tests/test_report_workflow.py
#   - tests/test_report_contract.py
#   - tests/test_report_context.py
# adjacent_modules:
#   - backend/app/services/access_control.py
#   - backend/app/services/one_off_entitlements.py
#   - backend/app/reporting/section_templates.py
# END_MODULE_MAP: M-REPORT-WORKFLOW

from __future__ import annotations

import asyncio
import calendar
import json
from datetime import datetime, timedelta, timezone
import os
import copy
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session
import structlog

from stellium_engine import StelliumEngine

from .. import engine_utils

from ..engine_utils import normalize_datetime_input

from ..llm.orchestrator import (
    CliLLMClient,
    LLMClient,
    LLMContentValidationError,
    LLMOrchestrator,
    NATAL_SECTION_IDS,
    OpenRouterClient,
    SectionResult,
    SectionSpec,
)
from ..llm.validator import validate_llm_hallucinations
from ..horary.core import HoraryCore
from ..horary.adapters import detect_adapter
from ..models import Report, ReportChunk, ReportRun, User
from ..reporting.section_templates import (
    build_horary_sections,
    build_month_sections,
    build_natal_sections,
    build_solar_sections,
    build_synastry_sections,
    build_ten_year_sections,
    build_week_sections,
    build_year_sections,
    get_default_sections,
)
from ..reporting.static_content import SECTION_INTROS
from ..reporting.markdown_helpers import (
    format_technical_appendix, 
    format_house_context, 
    format_chart_facts,
    get_chart_facts_json
)
from ..reporting.telegram_renderer import render_report_chunks_to_messages
from ..logging_utils import get_correlation_ids, log_grace_event
from .notification import send_bot_notification
from .forecast_semantics import (
    build_month_forecast_semantic_layer,
    build_week_forecast_semantic_layer,
)
from .week_brief_seed import (
    build_week_brief_seed_bundle as build_week_brief_seed_bundle_owned,
    normalize_week_day_payload as normalize_week_day_payload_owned,
    normalize_week_summary as normalize_week_summary_owned,
    parse_json_block_list as parse_json_block_list_owned,
)

logger = structlog.get_logger()
MODULE_ID = "M-REPORT-WORKFLOW"


CANONICAL_TEMPLATE_BUILDERS = {
    "week_forecast": build_week_sections,
    "month_forecast": build_month_sections,
    "year_forecast": build_year_sections,
    "ten_year_forecast": build_ten_year_sections,
    "natal_master": build_natal_sections,
    "solar_return": build_solar_sections,
    "synastry": build_synastry_sections,
    "horary": build_horary_sections,
    "horary_answer": build_horary_sections,
}


def _admin_report_log_context(report: Report | None, **fields: object) -> dict[str, object]:
    context: dict[str, object] = {}
    if report is not None:
        context["report_id"] = str(report.id)
        context["report_type"] = report.report_type
        context["report_status"] = report.status
        context["client_id"] = str(report.client_id)
    context.update({key: value for key, value in fields.items() if value is not None})
    return context


def _workflow_trace_context(
    *,
    correlation_id: Optional[str] = None,
    report: Optional[Report] = None,
    report_id: Optional[object] = None,
) -> dict[str, Optional[str]]:
    """Return normalized workflow trace identifiers for report lifecycle logs."""
    trace_context = get_correlation_ids()
    resolved_report_id = str(report.id) if report is not None else (str(report_id) if report_id is not None else None)
    return {
        "correlation_id": correlation_id or trace_context.get("correlation_id"),
        "trace_id": trace_context.get("trace_id"),
        "correlation_source": trace_context.get("correlation_source"),
        "report_id": resolved_report_id,
    }


def _build_workflow_logger(
    *,
    contract: str,
    block: str,
    correlation_id: Optional[str] = None,
    report_id: Optional[str] = None,
    **fields,
):
    """Create a bound workflow logger with canonical GRACE trace fields."""
    return logger.bind(
        module=MODULE_ID,
        contract=contract,
        block=block,
        correlation_id=correlation_id,
        report_id=report_id,
        **fields,
    )


def _workflow_log(
    level: str,
    event: str,
    *,
    fn: str,
    contract: str,
    block: str,
    correlation_id: Optional[str] = None,
    report: Optional[Report] = None,
    report_id: Optional[object] = None,
    **fields,
) -> None:
    """Emit canonical workflow logs aligned with access and entitlement modules."""
    trace_context = _workflow_trace_context(
        correlation_id=correlation_id,
        report=report,
        report_id=report_id,
    )
    payload = {
        **(
            {
                key: value
                for key, value in _admin_report_log_context(report).items()
                if key != "report_id"
            }
            if report is not None
            else {}
        ),
        **{key: value for key, value in fields.items() if value is not None},
    }
    bound_logger = _build_workflow_logger(
        contract=contract,
        block=block,
        correlation_id=trace_context["correlation_id"],
        report_id=trace_context["report_id"],
        fn=fn,
    )
    getattr(bound_logger, level)(event, **payload)
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        contract=contract,
        block=block,
        correlation_id=trace_context["correlation_id"],
        report_id=trace_context["report_id"],
        trace_id=trace_context["trace_id"],
        correlation_source=trace_context["correlation_source"],
        **payload,
    )

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

RU_SIGNS = {
    "Aries": "Овен ♈", "Taurus": "Телец ♉", "Gemini": "Близнецы ♊", "Cancer": "Рак ♋",
    "Leo": "Лев ♌", "Virgo": "Дева ♍", "Libra": "Весы ♎", "Scorpio": "Скорпион ♏",
    "Sagittarius": "Стрелец ♐", "Capricorn": "Козерог ♑", "Aquarius": "Водолей ♒", "Pisces": "Рыбы ♓"
}

RU_PLANETS_FULL = {
    "Sun": "☀️ Солнце", "Moon": "🌙 Луна", "Mercury": "☿ Меркурий", "Venus": "♀️ Венера",
    "Mars": "♂️ Марс", "Jupiter": "♃ Юпитер", "Saturn": "♄ Сатурн", "Uranus": "♅ Уран",
    "Neptune": "♆ Нептун", "Pluto": "♇ Плутон", "Chiron": "⚷ Хирон", "Lilith": "⚸ Лилит",
    "Selena": "🌟 Селена", "North Node": "☊ Сев. Узел", "South Node": "☋ Южн. Узел",
    "Mean Apogee": "⚸ Лилит", "True Node": "☊ Сев. Узел", "Part of Fortune": "⊗ Парс Фортуны",
    "ASC": "⬆️ ASC", "MC": "🏔️ MC", "DSC": "⬇️ DSC", "IC": "🏠 IC", "Vertex": "✴️ Вертекс",
    "Ceres": "Церера", "Pallas": "Паллада", "Juno": "Юнона", "Vesta": "Веста"
}

RU_ASPECTS = {
    "conjunction": "соединение",
    "opposition": "оппозиция",
    "trine": "трин",
    "square": "квадрат",
    "sextile": "секстиль",
}

RU_SIGNS_PLAIN = {
    sign: value.split(" ", 1)[0]
    for sign, value in RU_SIGNS.items()
}

RU_PLANET_NAMES = {
    name: value.split(" ", 1)[-1] if " " in value else value
    for name, value in RU_PLANETS_FULL.items()
}

EN_WEEKDAY_TO_RU = {
    "monday": "понедельник",
    "tuesday": "вторник",
    "wednesday": "среда",
    "thursday": "четверг",
    "friday": "пятница",
    "saturday": "суббота",
    "sunday": "воскресенье",
}

MOON_SIGN_ALIASES = {
    "Близ": "Близнецы",
}

RU_MONTH_NAMES = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}

SIGN_ELEMENT_MAP = {
    "Aries": "Fire",
    "Taurus": "Earth",
    "Gemini": "Air",
    "Cancer": "Water",
    "Leo": "Fire",
    "Virgo": "Earth",
    "Libra": "Air",
    "Scorpio": "Water",
    "Sagittarius": "Fire",
    "Capricorn": "Earth",
    "Aquarius": "Air",
    "Pisces": "Water",
}

SIGN_MODE_MAP = {
    "Aries": "Cardinal",
    "Taurus": "Fixed",
    "Gemini": "Mutable",
    "Cancer": "Cardinal",
    "Leo": "Fixed",
    "Virgo": "Mutable",
    "Libra": "Cardinal",
    "Scorpio": "Fixed",
    "Sagittarius": "Mutable",
    "Capricorn": "Cardinal",
    "Aquarius": "Fixed",
    "Pisces": "Mutable",
}

SIGN_RULER_MAP = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Pluto",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Uranus",
    "Pisces": "Neptune",
}

POINT_NAME_ALIASES = {
    "Mean Apogee": "Lilith",
}

FACTS_FIRST_P0_SECTION_IDS = {
    "executive_summary",
    "synthesis",
    "money_realization",
    "love_intimacy",
    "final_synthesis",
}

FACTS_FIRST_P1_SECTION_IDS = {
    "dispositor_office",
    "balance_wheel_1_6",
    "balance_wheel_7_12",
    "time_cycles",
}

FACTS_FIRST_P2_SECTION_IDS = {
    "axes_truths",
    "aspects_beginner",
    "nodes_growth",
    "mercury_mind",
    "shadow_trauma",
}

FACTS_FIRST_P3_SECTION_IDS = {
    "core_triad",
    "configurations_geometry",
    "vertex_fate",
    "stars_transuranus",
}

FACTS_FIRST_P4_SECTION_IDS = {
    "framework_elements_modes",
}

FACTS_FIRST_INSIGHT_PACK_SECTION_IDS = (
    FACTS_FIRST_P0_SECTION_IDS
    | FACTS_FIRST_P1_SECTION_IDS
    | FACTS_FIRST_P2_SECTION_IDS
    | FACTS_FIRST_P3_SECTION_IDS
    | FACTS_FIRST_P4_SECTION_IDS
)

MAJOR_DISPOSITOR_PLANETS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
]

HOUSE_DOMAIN_MAP = {
    1: "личная подача, тело и способ входить в мир",
    2: "деньги, ценность и чувство опоры",
    3: "мышление, речь, обучение и ближний круг",
    4: "дом, корни и внутренняя база",
    5: "радость, романтика, творчество и самовыражение",
    6: "ритм, работа, здоровье и повседневная дисциплина",
    7: "партнерство, зеркало и контракты",
    8: "близость, кризисы, общие ресурсы и контроль",
    9: "смысл, вера, горизонт и большие маршруты",
    10: "статус, карьера и видимая роль",
    11: "сообщества, связи, друзья и долгие цели",
    12: "тишина, завершения, восстановление и бессознательное",
}

SIGN_STYLE_HINTS = {
    "Aries": {
        "tone": "прямой старт, скорость и право действовать первым",
        "plus": "инициатива, смелость и быстрый запуск",
        "minus": "импульсивность, напор и жизнь в режиме атаки",
        "growth": "сочетать скорость с выдержкой и экологичной силой",
    },
    "Taurus": {
        "tone": "устойчивость, материальная база и телесная опора",
        "plus": "надежность, терпение и умение удерживать ресурс",
        "minus": "инерция, застревание и страх менять привычное",
        "growth": "сохранять опору, не превращая ее в застой",
    },
    "Gemini": {
        "tone": "подвижность, обмен, обучение и множество связей",
        "plus": "гибкость, контактность и быстрый сбор информации",
        "minus": "распыление, шум и недоведенные решения",
        "growth": "собирать разнообразие в ясную мысль и маршрут",
    },
    "Cancer": {
        "tone": "чувствительность, защита, память и создание базы",
        "plus": "забота, интуиция и умение удерживать близких",
        "minus": "обидчивость, закрытость и зависание в прошлом",
        "growth": "строить безопасность без изоляции и гиперконтроля",
    },
    "Leo": {
        "tone": "видимость, творческое ядро и потребность светить",
        "plus": "щедрость, харизма и здоровая уверенность",
        "minus": "драма, самолюбие и болезненная реакция на непризнание",
        "growth": "нести свет без театрального перегрева и гордыни",
    },
    "Virgo": {
        "tone": "точность, сервис, настройка процесса и полезность",
        "plus": "системность, внимательность и качество",
        "minus": "перфекционизм, тревога и вечное исправление",
        "growth": "оставлять высокую планку, не превращая ее в самокритику",
    },
    "Libra": {
        "tone": "баланс, диалог, партнерство и поиск формы",
        "plus": "дипломатия, чувство меры и способность договориться",
        "minus": "зависание в выборе и зависимость от внешнего согласия",
        "growth": "сохранять баланс, не теряя собственный вектор",
    },
    "Scorpio": {
        "tone": "глубина, контроль, кризисы и трансформация",
        "plus": "сила, стойкость и умение идти в сложное",
        "minus": "подозрительность, крайности и борьба за власть",
        "growth": "нести глубину без тотального контроля и войн",
    },
    "Sagittarius": {
        "tone": "горизонт, риск, вера и движение вперед",
        "plus": "широта взгляда, оптимизм и смелость маршрута",
        "minus": "избыточная уверенность, разгон и уход от конкретики",
        "growth": "держать горизонт, не теряя точность шага",
    },
    "Capricorn": {
        "tone": "структура, ответственность и длинный подъем",
        "plus": "дисциплина, выносливость и управленческий каркас",
        "minus": "жесткость, холодность и жизнь под внутренним прессом",
        "growth": "сохранять взрослость без самоцементирования",
    },
    "Aquarius": {
        "tone": "свобода, сеть, обновление и собственные правила",
        "plus": "оригинальность, независимость и работа с будущим",
        "minus": "отстраненность, резкие развороты и протест ради протеста",
        "growth": "давать себе свободу без эмоционального выключения",
    },
    "Pisces": {
        "tone": "проницаемость, воображение, сострадание и растворение границ",
        "plus": "эмпатия, образность и тонкое считывание атмосферы",
        "minus": "размытость, бегство и слабые контуры реальности",
        "growth": "оставлять глубину, но укреплять границы и форму",
    },
}

PLANET_ROLE_HINTS = {
    "Sun": "воля и видимость",
    "Moon": "эмоции и базовые потребности",
    "Mercury": "мысль и коммуникация",
    "Venus": "симпатия, ценность и выбор",
    "Mars": "энергия, конфликт и действие",
    "Jupiter": "рост и возможности",
    "Saturn": "долг, рамка и зрелость",
    "Uranus": "свобода и резкие обновления",
    "Neptune": "идеал, тонкость и размывание",
    "Pluto": "контроль, кризис и глубинная сила",
    "Chiron": "уязвимость и настройка",
    "North Node": "вектор роста",
    "True Node": "вектор роста",
    "South Node": "привычный сценарий",
    "ASC": "личный способ входа",
    "MC": "видимая роль и статус",
}


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


# #START_BLOCK_WORKFLOW_UTILS
def build_forecast_window(report_type: str, tz_str: str = "UTC") -> dict:
    """
    # PURPOSE: Build forecast window metadata for prompts.
    # INPUT: report_type (str), tz_str (str).
    # OUTPUT: Dict with window fields (start in local time).
    # CONTEXT: Used in report context for forecasts.
    """
    try:
        tz = ZoneInfo(tz_str)
    except:
        tz = timezone.utc

    # Start from local "now"
    start_dt = datetime.now(tz)
    start = start_dt.isoformat()
    
    if report_type == "week_forecast":
        return {"start": start, "days": 7}
    if report_type == "month_forecast":
        return {"start": start, "months": 1}
    if report_type == "year_forecast":
        return {"start": start, "months": 12}
    if report_type == "ten_year_forecast":
        return {"start": start, "months": 120}
    return {"start": start, "months": 12}


def start_report_run(report: Report, db: Session) -> ReportRun:
    """
    # START_CONTRACT: FN-START-REPORT-RUN
    # purpose: Persist a workflow run record before section generation begins.
    # inputs: report entity, db session.
    # returns: ReportRun instance bound to report lifecycle.
    # side_effects: inserts ReportRun row and emits workflow lifecycle logs.
    # errors: propagates database write failures to caller-managed transaction scope.
    # END_CONTRACT: FN-START-REPORT-RUN
    """

    # START_BLOCK: RUN_START_RECORD
    _workflow_log(
        "info",
        "report.workflow.run_start",
        fn="start_report_run",
        contract="FN-START-REPORT-RUN",
        block="RUN_START_RECORD",
        report=report,
        status="in_progress",
    )

    run = ReportRun(
        report_id=report.id,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    _workflow_log(
        "info",
        "report.workflow.run_started",
        fn="start_report_run",
        contract="FN-START-REPORT-RUN",
        block="RUN_START_RECORD",
        report=report,
        run_id=str(run.id),
    )
    # END_BLOCK: RUN_START_RECORD
    return run


async def _send_report_delivery_messages(telegram_id: int, messages: list[str]) -> None:
    for index, message in enumerate(messages):
        if not message or not message.strip():
            continue
        ok = await send_bot_notification(telegram_id, message)
        if not ok:
            logger.warning(
                "report.notify.delivery_failed",
                telegram_id=telegram_id,
                message_index=index,
            )
            break


def should_fallback_on_llm_error(exc: Exception) -> bool:
    """
    # PURPOSE: Decide whether to use fallback content for an LLM error.
    # INPUT: exception from LLM call.
    # OUTPUT: True if fallback should be used.
    # CONTEXT: Keeps report generation resilient to credit/network issues.
    """

    message = str(exc)
    return any(
        token in message
        for token in (
            "OpenRouter error:",
            "OpenRouter connection error",
            "OpenRouter returned empty content",
            "CLI error:",
            "CLI timeout",
        )
    )


def _format_fallback_positions(facts: dict, limit: int = 6) -> list[str]:
    items = []
    for p in facts.get("pos", [])[:limit]:
        name = RU_PLANETS_FULL.get(p.get("p"), p.get("p", ""))
        sign = RU_SIGNS.get(p.get("s"), p.get("s", ""))
        deg = p.get("deg", "")
        house = p.get("h")
        house_part = f", дом {house}" if house else ""
        items.append(f"{name}: {sign} {deg}°{house_part}".strip())
    return items


def _format_fallback_aspects(facts: dict, limit: int = 4) -> list[str]:
    items = []
    aspects = sorted(facts.get("aspects", []), key=lambda a: a.get("o", 99))
    for a in aspects[:limit]:
        p1 = RU_PLANETS_FULL.get(a.get("p1"), a.get("p1", ""))
        p2 = RU_PLANETS_FULL.get(a.get("p2"), a.get("p2", ""))
        at = RU_ASPECTS.get(a.get("t"), a.get("t", ""))
        orb = a.get("o", "")
        items.append(f"{p1} — {at} — {p2} (орб {orb}°)")
    return items


def _translate_weekday_to_ru(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return EN_WEEKDAY_TO_RU.get(raw.lower(), raw.lower())


def _normalize_moon_sign_label(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return MOON_SIGN_ALIASES.get(raw, RU_SIGNS_PLAIN.get(raw, raw))


def _format_short_date_label(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw).strftime("%d.%m")
    except ValueError:
        return raw


def _normalize_status_variant(status: Any) -> str:
    normalized = str(status or "").strip().upper()
    if normalized == "RED":
        return "error"
    if normalized == "YELLOW":
        return "warning"
    return "success"


def _coerce_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _default_week_traffic_desc(status: Any) -> str:
    normalized = str(status or "").strip().upper()
    if normalized == "RED":
        return "🔴 Шторм"
    if normalized == "GREEN":
        return "🟢 Зеленый"
    return "🟡 Внимание"


def _normalize_week_day_payload(day: dict[str, Any]) -> dict[str, Any]:
    return normalize_week_day_payload_owned(day)


def _normalize_week_summary(week_data: dict[str, Any], days: list[dict[str, Any]]) -> dict[str, Any]:
    return normalize_week_summary_owned(week_data, days)


def _summarize_week_events(day: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for ingress in day.get("ingresses", [])[:2]:
        text = str(ingress or "").strip()
        if text:
            items.append(text)
    for aspect in day.get("aspects", [])[:3]:
        transit = str(aspect.get("transit") or "").strip()
        natal = str(aspect.get("natal") or "").strip()
        aspect_label = str(aspect.get("aspect") or "").strip()
        if transit and natal and aspect_label:
            transit_label = RU_PLANET_NAMES.get(transit, transit)
            natal_label = RU_PLANET_NAMES.get(natal, natal)
            items.append(f"{transit_label} {aspect_label} {natal_label}")
    return items


def _parse_forecast_window_start(forecast_window: dict[str, Any]) -> datetime:
    raw = str((forecast_window or {}).get("start") or "").strip()
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _format_month_window_label(forecast_window: dict[str, Any]) -> str:
    start_dt = _parse_forecast_window_start(forecast_window)
    month_name = RU_MONTH_NAMES.get(start_dt.month, "")
    if not month_name:
        return str(start_dt.year)
    return f"{month_name} {start_dt.year}"


def _parse_month_event_line(raw_text: Any, start_dt: datetime) -> dict[str, Any]:
    raw = str(raw_text or "").strip()
    if not raw:
        return {"raw": "", "date_label": "", "event": "", "event_dt": None}

    date_label = ""
    event = raw
    match = re.match(r"^(?P<date>\d{2}\.\d{2})\s+(?P<body>.+)$", raw)
    if match:
        date_label = match.group("date")
        event = match.group("body").strip()

    event_dt = None
    if date_label:
        try:
            day_raw, month_raw = date_label.split(".", 1)
            day = int(day_raw)
            month = int(month_raw)
            year = start_dt.year + (1 if month < start_dt.month else 0)
            event_dt = datetime(
                year,
                month,
                day,
                tzinfo=start_dt.tzinfo,
            )
        except ValueError:
            event_dt = None

    return {
        "raw": raw,
        "date_label": date_label,
        "event": event,
        "event_dt": event_dt,
    }


def _build_month_event_life_signal(kind: str, event_text: str) -> str:
    lower = str(event_text or "").lower()

    if kind == "lunations":
        if "новолуние" in lower:
            return "запуск нового цикла: выбери одну ставку и сразу переведи ее в календарь."
        return "развязка и обратная связь: пора завершить висящий сюжет, а не держать его в подвешенном виде."

    if kind == "retrogrades":
        if "меркурий" in lower:
            return "перепроверка документов, переписок и условий сделки: цена спешки здесь выше обычного."
        if "венера" in lower:
            return "ревизия цены, симпатий и договоренностей: важно понять, что для тебя действительно ценно."
        return "возврат к старым обязательствам и настройке процесса: лучше править, чем форсировать."

    if kind == "ingresses":
        if "солнце" in lower:
            return "смена центра тяжести месяца: внимание уходит туда, где нужен личный жест и ясная позиция."
        if "меркурий" in lower:
            return "переговоры, письма, документы и короткие согласования выходят на первый план."
        if "венера" in lower:
            return "деньги, личные договоренности и вкус к выбору требуют более точной настройки."
        if "марс" in lower:
            return "темп заметно растет: запуск, дедлайны и силовые разговоры становятся острее."
        if "юпитер" in lower:
            return "окно для расширения, обучения или выхода к более широкой аудитории."
        return "меняется способ действовать и распределять внимание: старый режим уже не тянет месяц."

    if kind == "major_transits":
        hard = any(token in lower for token in ["квадрат", "оппозиц"])
        if "сатурн" in lower:
            return "проверка прочности планов и дедлайнов: месяц быстро наказывает за слабую сборку."
        if "марс" in lower and hard:
            return "темп легко превращается в конфликт: силу нужно дозировать, а не демонстрировать."
        if "уран" in lower:
            return "сюжет меняется рывком: оставляй запас на неожиданный разворот, а не цементируй план."
        if "плутон" in lower:
            return "вопрос контроля и цены решения выходит наружу: по инерции этот сюжет не пройти."
        if "юпитер" in lower:
            return "есть окно для роста, если уже собрана база и понятен вектор расширения."
        if hard:
            return "месяц требует точности и трезвого темпа: лишнее давление быстро даст отдачу."
        return "внешний триггер меняет ход событий: смотри, где пора закреплять результат, а не спорить."

    return "это один из внешних триггеров месяца: важно заметить, где он меняет твой реальный режим решений."


def _build_month_event_pressure(kind: str, event_text: str) -> str:
    lower = str(event_text or "").lower()
    if kind == "retrogrades":
        return "high"
    if kind == "major_transits" and any(token in lower for token in ["квадрат", "оппозиц"]):
        return "high"
    if kind in {"lunations", "major_transits"}:
        return "medium"
    return "low"


def _build_month_event_cards(
    month_data: dict[str, Any],
    forecast_window: dict[str, Any],
) -> list[dict[str, Any]]:
    start_dt = _parse_forecast_window_start(forecast_window)
    event_cards: list[dict[str, Any]] = []
    order = 0
    limits = {
        "lunations": 3,
        "ingresses": 4,
        "major_transits": 6,
        "retrogrades": 3,
    }

    for kind in ("lunations", "ingresses", "major_transits", "retrogrades"):
        for raw_item in (month_data.get(kind) or [])[: limits[kind]]:
            parsed = _parse_month_event_line(raw_item, start_dt)
            if not parsed["event"]:
                continue
            event_cards.append(
                {
                    "order": order,
                    "kind": kind,
                    "date_label": parsed["date_label"],
                    "event": parsed["event"],
                    "event_dt": parsed["event_dt"],
                    "life_signal": _build_month_event_life_signal(kind, parsed["event"]),
                    "pressure": _build_month_event_pressure(kind, parsed["event"]),
                }
            )
            order += 1

    def _sort_key(card: dict[str, Any]) -> tuple[int, int]:
        event_dt = card.get("event_dt")
        ordinal = event_dt.date().toordinal() if isinstance(event_dt, datetime) else 9999999
        return (ordinal, int(card.get("order", 0)))

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for card in sorted(event_cards, key=_sort_key):
        key = (str(card.get("date_label") or ""), str(card.get("event") or ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(card)

    return deduped[:10]


def _build_month_phase_focus(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if "новолуние" in lower:
        return "Собери новую ставку месяца и сразу привяжи ее к реальному графику."
    if "полнолуние" in lower:
        return "Закрой висящий сюжет и добудь честную обратную связь, вместо того чтобы тянуть неопределенность."
    if any(event.get("kind") == "retrogrades" for event in phase_events):
        return "Проверь хвосты и слабые места процесса: здесь полезнее корректировка, чем разгон."
    if any(event.get("pressure") == "high" for event in phase_events):
        return "Сузь повестку до одного-двух фронтов и держи управление руками, а не инерцией."
    if any(event.get("kind") == "ingresses" for event in phase_events):
        return "Перенастрой режим и формат общения под новые вводные, не держась за старую механику."

    default_map = {
        "RED": [
            "Начинай месяц с ревизии ресурсов, а не с красивого рывка.",
            "Держи середину месяца собранной и не дроби внимание.",
            "Проверяй, что выдерживает реальность, а что пора снимать с повестки.",
            "Подводи месяц к спокойной фиксации результата, а не к штурму в последний момент.",
        ],
        "YELLOW": [
            "Собери опорный ритм и не принимай промежуточный результат за финальный.",
            "Проверяй детали и стыки между задачами: на этом месяц либо едет, либо рассыпается.",
            "Используй середину месяца для выравнивания курса и точечных действий.",
            "Дожимай только то, что уже прошло проверку делом.",
        ],
        "GREEN": [
            "Запусти то, что давно готово, и дай сильной идее реальный ход.",
            "Усили видимость и качество коммуникации вокруг главной ставки.",
            "Середину месяца используй для закрепления темпа и переговоров.",
            "Финальную неделю посвяти упаковке результата и фиксации следующего шага.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_push(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if "меркурий" in lower:
        return "Продвигай переговоры, документы, письма, брифы и все, что зависит от ясной формулировки."
    if "венера" in lower:
        return "Продвигай деньги, условия сотрудничества, личные договоренности и вопросы ценности."
    if "марс" in lower:
        return "Продвигай запуск, дедлайны, силовые задачи и короткие решающие разговоры."
    if "юпитер" in lower:
        return "Продвигай обучение, публичность и выход в более широкий контур возможностей."
    if any(event.get("kind") == "lunations" for event in phase_events):
        return "Продвигай одно решение, которое либо открывает новый цикл, либо чисто закрывает старый."

    default_map = {
        "RED": [
            "Продвигай только обязательное и уже подтвержденное: месяц не любит лишний фронт.",
            "Продвигай структуру, договоренности и режим, а не амбициозную надстройку.",
            "Продвигай проверенные задачи с коротким циклом обратной связи.",
            "Продвигай фиксацию результата и разгрузку хвостов.",
        ],
        "YELLOW": [
            "Продвигай задачи, где важны аккуратность, последовательность и ясная договоренность.",
            "Продвигай то, что можно собрать по шагам и быстро перепроверить.",
            "Продвигай один главный трек, а не россыпь параллельных инициатив.",
            "Продвигай завершение, упаковку и внятную передачу результата.",
        ],
        "GREEN": [
            "Продвигай запуск и все, что готово выйти из подготовки в реальное движение.",
            "Продвигай коммуникацию, встречи и заметные ходы вокруг главной темы месяца.",
            "Продвигай масштабирование сильной идеи через системный темп, а не через азарт.",
            "Продвигай закрепление результата и подготовку следующего шага.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_restraint(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if any(event.get("kind") == "retrogrades" for event in phase_events):
        return "Не обещай больше, чем успеешь перепроверить, и не игнорируй правки ради скорости."
    if "марс" in lower and any(token in lower for token in ["квадрат", "оппозиц"]):
        return "Не переводи темп в спор и не жги ресурс на доказательство правоты."
    if "сатурн" in lower:
        return "Не дави на срок там, где система явно просит пересборки и уточнений."
    if "уран" in lower:
        return "Не цементируй жесткий план без запаса на разворот и непредвиденную правку."
    if "плутон" in lower:
        return "Не заходи в силовой контроль и не делай ставку на перетягивание каната."

    default_map = {
        "RED": [
            "Не начинай месяц с второго главного фронта и не живи в аварийном режиме.",
            "Не путай контроль с гиперконтролем: лишнее давление здесь только сжигает ресурс.",
            "Не обещай разворот быстрее, чем позволяет реальная система.",
            "Не штурмуй финал месяца рывком из чувства вины или спешки.",
        ],
        "YELLOW": [
            "Не принимай первую рабочую версию за готовый результат.",
            "Не разбрасывайся на параллельные задачи без общего ритма.",
            "Не ускоряйся раньше, чем закрыты слабые места и зависшие детали.",
            "Не оставляй итог без упаковки и подтверждения договоренностей.",
        ],
        "GREEN": [
            "Не трать сильную неделю на суету и второстепенные переписки.",
            "Не дроби внимание на чужие срочности, если они не двигают твою главную ставку.",
            "Не принимай хороший темп за бессмертный ресурс: телу нужен режим.",
            "Не бросай закрепление результата сразу после удачного хода.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_role(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    lower = " ".join(str(event.get("event") or "").lower() for event in phase_events)
    if "новолуние" in lower:
        return "Запуск новой ставки"
    if "полнолуние" in lower:
        return "Развязка и обратная связь"
    if any(event.get("kind") == "retrogrades" for event in phase_events):
        return "Перепроверка и правки"
    if any(event.get("pressure") == "high" for event in phase_events):
        return "Точка напряжения" if status != "RED" else "Жесткий выбор"
    if any(event.get("kind") == "ingresses" for event in phase_events):
        return "Смена режима"

    default_map = {
        "RED": [
            "Сужение фронта",
            "Техническая пересборка",
            "Жесткий выбор",
            "Спокойная фиксация",
        ],
        "YELLOW": [
            "Сборка курса",
            "Проверка стыков",
            "Точка хода",
            "Упаковка результата",
        ],
        "GREEN": [
            "Запуск ставки",
            "Усиление видимости",
            "Закрепление темпа",
            "Фиксация результата",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_scene(
    status: str,
    phase_index: int,
    phase_events: list[dict[str, Any]],
) -> str:
    if phase_events:
        lead_signal = str(phase_events[0].get("life_signal") or "").strip()
        lead_anchor = " — ".join(
            part
            for part in [
                str(phase_events[0].get("date_label") or "").strip(),
                str(phase_events[0].get("event") or "").strip(),
            ]
            if part
        ).strip()
        text = ""
        if lead_signal:
            text = f"На поверхности недели — {lead_signal.rstrip('.')}."
        if lead_anchor:
            anchor_line = f"Опорная дата: {lead_anchor}."
            text = f"{text} {anchor_line}".strip() if text else anchor_line
        return text

    default_map = {
        "RED": [
            "Неделя чувствуется через необходимость быстро понять, что действительно обязательно, а что пора снять с повестки.",
            "На первый план выходят правки, возвраты и техническая пересборка того, что не выдержало первую проверку.",
            "В центре окажется момент выбора: подтверждать обязательство, переносить срок или честно отказываться от лишнего.",
            "Эта фаза про разгрузку хвостов и спокойную фиксацию результата без финального штурма.",
        ],
        "YELLOW": [
            "Неделя чувствуется через сборку графика, договоренностей и ясного приоритета.",
            "На первый план выходят стыки: кто что обещал, где нужен второй проход и что требует уточнения.",
            "Появляется окно для реального движения по главной теме, если база уже проверена.",
            "Неделя просит упаковать сделанное, подтвердить договоренности и закрыть висящие хвосты.",
        ],
        "GREEN": [
            "На старте недели важно вынести вперед одну главную ставку и сразу дать ей видимый ход.",
            "Неделя чаще проявляется через встречи, переговоры и внешний отклик на то, что уже запущено.",
            "Фаза нужна для удержания темпа: меньше суеты, больше системного продвижения.",
            "Финальная неделя про закрепление результата и подготовку следующего хода без лишнего шума.",
        ],
    }
    return default_map.get(status, default_map["YELLOW"])[phase_index]


def _build_month_phase_transition(status: str, phase_index: int) -> str:
    transition_map = {
        "RED": [
            "Сначала месяц просит остановить расползание и сузить фронт.",
            "После этого становится видно, где нужна пересборка, а не давление.",
            "К середине вопрос уже не в подготовке, а в цене выбора и выдержке.",
            "В финале выигрывает спокойная фиксация, а не попытка все добежать рывком.",
        ],
        "YELLOW": [
            "Сначала важнее собрать курс, чем создавать видимость быстрого движения.",
            "Дальше месяц переводит внимание на стыки, сроки и качество координации.",
            "К середине появляется право на точечный ход там, где база уже проверена.",
            "Финал нужен для упаковки результата и подтверждения того, что действительно поехало.",
        ],
        "GREEN": [
            "Старт месяца дает окно на запуск, но только для того, что уже готово к реальному ходу.",
            "Затем фокус смещается на видимость, разговоры и поддержку основной ставки.",
            "К середине важно не ускоряться еще сильнее, а удержать темп и качество.",
            "Финальная неделя нужна, чтобы превратить импульс в устойчивый результат.",
        ],
    }
    return transition_map.get(status, transition_map["YELLOW"])[phase_index]


def _build_month_phase_cards(
    event_cards: list[dict[str, Any]],
    forecast_window: dict[str, Any],
    status: str,
) -> list[dict[str, Any]]:
    start_dt = _parse_forecast_window_start(forecast_window)
    phase_cards: list[dict[str, Any]] = []

    for phase_index in range(4):
        phase_start = start_dt + timedelta(days=phase_index * 7)
        phase_end = phase_start + timedelta(days=6)
        phase_events: list[dict[str, Any]] = []
        for event in event_cards:
            event_dt = event.get("event_dt")
            if not isinstance(event_dt, datetime):
                continue
            day_offset = (event_dt.date() - start_dt.date()).days
            if phase_index * 7 <= day_offset <= phase_index * 7 + 6:
                phase_events.append(event)

        pressure = "low"
        if any(event.get("pressure") == "high" for event in phase_events):
            pressure = "high"
        elif any(event.get("pressure") == "medium" for event in phase_events):
            pressure = "medium"

        phase_role = _build_month_phase_role(status, phase_index, phase_events)
        phase_cards.append(
            {
                "label": f"Неделя {phase_index + 1}",
                "date_range_label": f"{phase_start.strftime('%d.%m')}-{phase_end.strftime('%d.%m')}",
                "pressure": pressure,
                "events": [
                    " ".join(
                        part
                        for part in [event.get("date_label"), event.get("event")]
                        if part
                    ).strip()
                    for event in phase_events[:3]
                ],
                "phase_role": phase_role,
                "lead_event": (phase_events[0].get("event") if phase_events else ""),
                "lead_signal": (phase_events[0].get("life_signal") if phase_events else ""),
                "scene_hint": _build_month_phase_scene(status, phase_index, phase_events),
                "transition_hint": _build_month_phase_transition(status, phase_index),
                "focus_hint": _build_month_phase_focus(status, phase_index, phase_events),
                "push_hint": _build_month_phase_push(status, phase_index, phase_events),
                "restraint_hint": _build_month_phase_restraint(status, phase_index, phase_events),
            }
        )

    return phase_cards


def _build_month_status_summary(status: str) -> str:
    summary_map = {
        "RED": "Месяц выглядит как пересборка кампании: давление есть, но выигрыш придет через дисциплину и сужение фронта.",
        "YELLOW": "Месяц неровный, но рабочий: результат держится на ритме, проверке деталей и умении не дергаться раньше времени.",
        "GREEN": "Месяц дает ход для заметного продвижения: важно не распылиться и провести сильную ставку через весь горизонт.",
    }
    return summary_map.get(status, summary_map["YELLOW"])


def _build_month_central_task(status: str) -> str:
    task_map = {
        "RED": "Собери один рабочий контур и убери все, что множит давление без отдачи.",
        "YELLOW": "Держи месяц как длинную партию: сначала настройка и проверка, потом ускорение.",
        "GREEN": "Переведи готовую идею в реальные действия и закрепи темп по ходу месяца.",
    }
    return task_map.get(status, task_map["YELLOW"])


def _build_month_campaign_arc(
    semantic_layer: dict[str, Any],
    phases: list[dict[str, Any]],
) -> dict[str, str]:
    phase_roles = [str(phase.get("phase_role") or "").strip().lower() for phase in phases[:4] if str(phase.get("phase_role") or "").strip()]
    if len(phase_roles) >= 4:
        phase_sequence = (
            f"Сначала {phase_roles[0]}, затем {phase_roles[1]}, "
            f"к середине {phase_roles[2]}, в финале {phase_roles[3]}."
        )
    else:
        phase_sequence = str(semantic_layer.get("campaign_shape") or "").strip()

    return {
        "opening_scene": str(semantic_layer.get("scene_seed") or "").strip(),
        "phase_sequence": phase_sequence,
        "close_focus": str(semantic_layer.get("finale") or semantic_layer.get("practical_move") or "").strip(),
    }


def _build_week_brief_seed_bundle(context: dict[str, Any]) -> dict[str, Any]:
    return build_week_brief_seed_bundle_owned(context)


def _build_week_forecast_prompt_context(context: dict[str, Any]) -> dict[str, Any]:
    client = context.get("client", {}) or {}
    week_seed = _build_week_brief_seed_bundle(context)
    days = week_seed["days"]
    summary = week_seed["summary"]

    return {
        "client": {
            "gender": client.get("gender"),
            "report_type": client.get("report_type"),
            "birth_time_known": client.get("birth_time_known", True),
        },
        "forecast_window": copy.deepcopy(context.get("forecast_window") or {}),
        "week_forecast_data": {
            "summary": summary,
            "days": days,
            "semantic_layer": week_seed["semantic_layer"],
        },
    }


def _build_month_forecast_prompt_context(context: dict[str, Any]) -> dict[str, Any]:
    client = context.get("client", {}) or {}
    month_data = copy.deepcopy(context.get("month_forecast_data") or {})
    forecast_window = copy.deepcopy(context.get("forecast_window") or {})
    event_cards = _build_month_event_cards(month_data, forecast_window)
    status = str(month_data.get("status") or "YELLOW").upper()
    key_events = [
        " ".join(
            part
            for part in [card.get("date_label"), card.get("event")]
            if part
        ).strip()
        for card in event_cards
    ]
    phases = _build_month_phase_cards(event_cards, forecast_window, status)
    status_summary = _build_month_status_summary(status)
    central_task = _build_month_central_task(status)
    semantic_layer = build_month_forecast_semantic_layer(
        status=status,
        event_cards=event_cards,
        phases=phases,
        status_summary=status_summary,
        central_task=central_task,
    )
    campaign_arc = _build_month_campaign_arc(semantic_layer, phases)

    return {
        "client": {
            "gender": client.get("gender"),
            "report_type": client.get("report_type"),
            "birth_time_known": client.get("birth_time_known", True),
        },
        "forecast_window": forecast_window,
        "month_forecast_data": {
            "month_label": _format_month_window_label(forecast_window),
            "status": status,
            "status_label": status,
            "tension_index": month_data.get("tension_index"),
            "key_events": key_events[:10],
            "status_summary": status_summary,
            "central_task": central_task,
            "event_cards": [
                {
                    "date_label": card.get("date_label"),
                    "event": card.get("event"),
                    "kind": card.get("kind"),
                    "life_signal": card.get("life_signal"),
                    "pressure": card.get("pressure"),
                }
                for card in event_cards
            ],
            "phases": phases,
            "semantic_layer": semantic_layer,
            "campaign_arc": campaign_arc,
            "lunations": month_data.get("lunations", [])[:3],
            "ingresses": month_data.get("ingresses", [])[:4],
            "major_transits": month_data.get("major_transits", [])[:6],
            "retrogrades": month_data.get("retrogrades", [])[:3],
        },
    }


def _build_forecast_prompt_context(context: dict[str, Any]) -> dict[str, Any]:
    report_type = ((context.get("client") or {}).get("report_type") or "").strip().lower()
    if report_type == "week_forecast":
        return _build_week_forecast_prompt_context(context)
    if report_type == "month_forecast":
        return _build_month_forecast_prompt_context(context)
    return copy.deepcopy(context)


def _build_week_focus_line(day: dict[str, Any]) -> str:
    traffic_light = str(day.get("traffic_light") or "").upper()
    moon_label = str(day.get("moon_label") or "").strip()
    if traffic_light == "RED":
        return f"Сузь день до одного приоритета и держи темп руками, а не импульсом. Опора: {moon_label}."
    if traffic_light == "YELLOW":
        return f"Закрывай хвосты, проверяй договоренности и оставляй запас по времени. Опора: {moon_label}."
    return f"Выноси вперед переговоры, запуск или важную встречу, пока день дает ход. Опора: {moon_label}."


def _build_week_risk_line(day: dict[str, Any]) -> str:
    traffic_light = str(day.get("traffic_light") or "").upper()
    if day.get("moon", {}).get("void_of_course"):
        return "Не форсируй жесткие решения в пустоту: сначала проверь, что у тебя есть обратная связь и ясные вводные."
    if traffic_light == "RED":
        return "Не разбрасывайся и не лезь в лишний спор: перегруз быстро превращается в потери по силам и вниманию."
    if traffic_light == "YELLOW":
        return "Не считай промежуточный результат финалом и не обещай лишнего."
    return "Не трать сильный день на мелкую суету и второстепенные переписки."


def _build_week_traffic_items(summary: dict[str, Any]) -> dict[str, str]:
    traffic_light = str(summary.get("traffic_light") or "").upper()
    if traffic_light == "RED":
        return {"money": "yellow", "health": "red", "love": "yellow"}
    if traffic_light == "YELLOW":
        return {"money": "yellow", "health": "yellow", "love": "yellow"}
    return {"money": "green", "health": "green", "love": "green"}


def _parse_json_block_list(content: Any) -> list[dict[str, Any]]:
    return parse_json_block_list_owned(content)


def _normalize_week_llm_text(value: Any) -> str:
    raw = cleanup_content_artifacts(str(value or "")).strip()
    if not raw:
        return ""
    raw = re.sub(r"\s+", " ", raw).strip()
    lowered = raw.lower()
    if "ошибка генерации" in lowered or "авто-режим" in lowered:
        return ""
    if len(raw) < 35:
        return ""
    if len(raw) > 320:
        sentences = re.split(r"(?<=[.!?])\s+", raw)
        raw = " ".join(sentences[:2]).strip() or raw[:320].rstrip()
    return raw


def _extract_week_strategy_llm_fragments(content: Any) -> dict[str, str]:
    blocks = _parse_json_block_list(content)
    if not blocks:
        return {"status_content": "", "theme_text": ""}

    status_content = ""
    theme_text = ""
    active_header = ""

    for block in blocks:
        block_type = str(block.get("type") or "").strip()
        if block_type == "header":
            active_header = str(block.get("text") or "").strip().lower()
            continue
        if block_type == "callout":
            candidate = _normalize_week_llm_text(block.get("content"))
            title = str(block.get("title") or "").strip().lower()
            if candidate and (not status_content or "статус" in title or "статус недели" in active_header):
                status_content = candidate
            continue
        if block_type != "paragraph":
            continue
        candidate = _normalize_week_llm_text(block.get("text"))
        if not candidate:
            continue
        if not theme_text and "главная тема" in active_header:
            theme_text = candidate
            continue
        if not theme_text:
            theme_text = candidate

    return {
        "status_content": status_content,
        "theme_text": theme_text,
    }


def _format_week_day_title(day: dict[str, Any], *, include_traffic: bool) -> str:
    weekday = str(day.get("weekday_ru") or "").strip().capitalize()
    date_label = str(day.get("date_label") or "").strip()
    if weekday and date_label:
        base = f"{weekday}, {date_label}"
    else:
        base = weekday or date_label or "День"
    traffic_desc = str(day.get("traffic_desc") or "").strip()
    if include_traffic and traffic_desc:
        return f"{base} ({traffic_desc})"
    return base


def _merge_week_text(base_text: str, factual_tail: str) -> str:
    base = str(base_text or "").strip()
    extra = str(factual_tail or "").strip()
    if not base:
        return extra
    if not extra:
        return base
    if extra.lower() in base.lower():
        return base
    if base[-1] not in ".!?":
        base = f"{base}."
    return f"{base} {extra}"


def _upper_first(text: Any) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    return value[0].upper() + value[1:]


def _join_sentence_parts(*parts: Any) -> str:
    merged = ""
    for part in parts:
        text = _upper_first(part)
        if not text:
            continue
        if text[-1] not in ".!?":
            text = f"{text}."
        merged = _merge_week_text(merged, text)
    return merged


def _build_week_fact_tail(days: list[dict[str, Any]]) -> str:
    if not days:
        return ""

    peak_day = max(days, key=lambda item: item.get("tension_score") or 0.0)
    calm_day = min(days, key=lambda item: item.get("tension_score") or 0.0)
    red_days = sum(1 for item in days if item.get("traffic_light") == "RED")
    green_days = sum(1 for item in days if item.get("traffic_light") == "GREEN")
    void_days = sum(1 for item in days if (item.get("moon") or {}).get("void_of_course"))

    parts: list[str] = []
    if red_days:
        parts.append(f"на перегрузе проходят {red_days} дн.")
    if green_days:
        parts.append(f"окон для хода {green_days}")
    if void_days:
        parts.append(f"Луна без курса {void_days} раз")

    extremes = ""
    if peak_day is not calm_day:
        peak_label = _format_week_day_title(peak_day, include_traffic=False)
        calm_label = _format_week_day_title(calm_day, include_traffic=False)
        extremes = f"Пик напряжения: {peak_label}. Самый свободный день: {calm_label}."

    tail = ""
    if parts:
        tail = "По фактам недели: " + ", ".join(parts) + "."
    return _merge_week_text(tail, extremes)


def _build_week_trigger_tail(days: list[dict[str, Any]]) -> str:
    ranked_days = sorted(
        days,
        key=lambda item: (len(item.get("events") or []), item.get("tension_score") or 0.0),
        reverse=True,
    )
    for day in ranked_days:
        events = day.get("events") or []
        if not events:
            continue
        label = _format_week_day_title(day, include_traffic=False)
        return f"Главный внешний триггер недели: {label} — {events[0]}."
    return ""


def _normalize_month_llm_text(value: Any) -> str:
    raw = cleanup_content_artifacts(str(value or "")).strip()
    if not raw:
        return ""
    raw = re.sub(r"\s+", " ", raw).strip()
    lowered = raw.lower()
    if "ошибка генерации" in lowered or "авто-режим" in lowered:
        return ""
    if any(
        token in lowered
        for token in (
            "новые возможности",
            "важные дела",
            "важные планы",
            "избегай конфликтов",
            "не переутомляйся",
            "используй энергию",
            "энергия планет",
            "успех и гармония",
            "общий фон месяца",
        )
    ):
        return ""
    if len(raw) < 45:
        return ""
    if len(raw) > 360:
        sentences = re.split(r"(?<=[.!?])\s+", raw)
        raw = " ".join(sentences[:3]).strip() or raw[:360].rstrip()
    return raw


def _extract_month_forecast_llm_fragments(content: Any) -> dict[str, str]:
    blocks = _parse_json_block_list(content)
    if not blocks:
        return {"status_content": "", "strategy_text": "", "practical_text": ""}

    status_content = ""
    strategy_text = ""
    practical_text = ""
    active_header = ""

    for block in blocks:
        block_type = str(block.get("type") or "").strip()
        if block_type == "header":
            active_header = str(block.get("text") or "").strip().lower()
            continue
        if block_type == "callout":
            candidate = _normalize_month_llm_text(block.get("content"))
            title = str(block.get("title") or "").strip().lower()
            if candidate and (not status_content or "статус" in title):
                status_content = candidate
            if candidate and "практич" in title and not practical_text:
                practical_text = candidate
            continue
        if block_type != "paragraph":
            continue
        candidate = _normalize_month_llm_text(block.get("text"))
        if not candidate:
            continue
        if not strategy_text and "стратег" in active_header:
            strategy_text = candidate
            continue
        if not strategy_text:
            strategy_text = candidate

    return {
        "status_content": status_content,
        "strategy_text": strategy_text,
        "practical_text": practical_text,
    }


def _render_month_forecast_content(context: dict[str, Any], llm_content: Optional[str] = None) -> str:
    month_data = (context or {}).get("month_forecast_data") or {}
    status = str(month_data.get("status") or "YELLOW").upper()
    month_label = str(month_data.get("month_label") or "").strip()
    event_cards = [item for item in (month_data.get("event_cards") or []) if isinstance(item, dict)]
    phases = [item for item in (month_data.get("phases") or []) if isinstance(item, dict)]
    semantic_layer = month_data.get("semantic_layer")
    if not isinstance(semantic_layer, dict) or not semantic_layer:
        semantic_layer = build_month_forecast_semantic_layer(
            status=status,
            event_cards=event_cards,
            phases=phases,
            status_summary=str(month_data.get("status_summary") or "").strip(),
            central_task=str(month_data.get("central_task") or "").strip(),
        )
    campaign_arc = month_data.get("campaign_arc")
    if not isinstance(campaign_arc, dict) or not campaign_arc:
        campaign_arc = _build_month_campaign_arc(semantic_layer, phases)
    key_events = [
        " - ".join(
            part
            for part in [
                str(item.get("date_label") or "").strip(),
                str(item.get("event") or "").strip(),
                str(item.get("life_signal") or "").strip(),
            ]
            if part
        )
        for item in event_cards
        if str(item.get("event") or "").strip()
    ]

    status_content = _join_sentence_parts(
        str(semantic_layer.get("headline") or "").strip(),
        str(campaign_arc.get("opening_scene") or "").strip(),
        str(month_data.get("central_task") or semantic_layer.get("practical_move") or "").strip(),
    )

    strategy_text = _join_sentence_parts(
        str(campaign_arc.get("phase_sequence") or semantic_layer.get("campaign_shape") or "").strip(),
        str(semantic_layer.get("money_admin_focus") or "").strip(),
        str(semantic_layer.get("relationship_softness") or "").strip(),
    )

    finance_value = _merge_week_text(
        _upper_first(str(semantic_layer.get("money_admin_focus") or "").strip()),
        {
            "RED": "Любая срочность требует повторной проверки цены и обязательств.",
            "YELLOW": "Сначала назови условия и объем, потом соглашайся на ход.",
            "GREEN": "Рост приходит через уже собранную идею, а не через азарт.",
        }.get(status, ""),
    )
    relationship_value = _merge_week_text(
        _upper_first(str(semantic_layer.get("relationship_softness") or "").strip()),
        {
            "RED": "Резкая реакция в этом месяце обходится слишком дорого.",
            "YELLOW": "Лучше один честный разговор, чем длинная серия домыслов.",
            "GREEN": "Контакт укрепляется там, где совпадают тон, ритм и намерение.",
        }.get(status, ""),
    )
    energy_value = _merge_week_text(
        _upper_first(str(semantic_layer.get("rest") or "").strip()),
        {
            "RED": "Не строй весь месяц на одном всплеске.",
            "YELLOW": "Ритм с паузами работает лучше аварийного героизма.",
            "GREEN": "Хороший темп нужно удерживать режимом, а не эйфорией.",
        }.get(status, ""),
    )
    practical_text = _join_sentence_parts(
        str(semantic_layer.get("practical_move") or "").strip(),
        str(campaign_arc.get("close_focus") or "").strip(),
    )

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "level": 2,
            "text": f"📅 ПРОГНОЗ НА МЕСЯЦ{f' ({month_label})' if month_label else ''}",
        },
        {
            "type": "callout",
            "variant": _normalize_status_variant(status),
            "title": "СТАТУС МЕСЯЦА",
            "content": status_content,
        },
        {"type": "header", "level": 2, "text": "Ключевые события"},
        {
            "type": "list",
            "items": key_events[:8]
            or [
                "Без крупных внешних разворотов: месяц будет проявляться через темп, повседневные решения и то, как ты держишь главный приоритет."
            ],
            "ordered": False,
        },
        {"type": "header", "level": 2, "text": "Стратегия по неделям"},
        {"type": "paragraph", "text": strategy_text},
    ]

    for phase in phases[:4]:
        role = str(phase.get("phase_role") or "").strip()
        header_text = f"{phase.get('label')} ({phase.get('date_range_label')})"
        if role:
            header_text = f"{phase.get('label')}. {role} ({phase.get('date_range_label')})"
        blocks.append({"type": "header", "level": 3, "text": header_text})
        phase_paragraph = " ".join(
            part
            for part in [
                str(phase.get("transition_hint") or "").strip(),
                str(phase.get("scene_hint") or "").strip(),
            ]
            if part
        )
        if phase_paragraph:
            blocks.append({"type": "paragraph", "text": phase_paragraph})
        blocks.append(
            {
                "type": "list",
                "items": [
                    f"**Фокус:** {phase.get('focus_hint') or 'Держи одну центральную линию и не распыляйся.'}",
                    f"**Что продвигать:** {phase.get('push_hint') or 'Продвигай только то, что дает реальный ход.'}",
                    f"**Где не форсировать:** {phase.get('restraint_hint') or 'Не ускоряй то, что еще не прошло проверку.'}",
                ],
                "ordered": False,
            }
        )

    blocks.extend(
        [
            {"type": "header", "level": 2, "text": "Итог месяца"},
            {
                "type": "key_value",
                "items": [
                    {"key": "Финансы", "value": finance_value},
                    {"key": "Отношения", "value": relationship_value},
                    {"key": "Энергия", "value": energy_value},
                ],
            },
            {
                "type": "callout",
                "variant": "success",
                "title": "Практический ход",
                "content": practical_text,
            },
        ]
    )
    return json.dumps(blocks, ensure_ascii=False)


def _render_week_strategy_content(context: dict[str, Any], llm_content: Optional[str] = None) -> str:
    week_data = (context or {}).get("week_forecast_data") or {}
    days = [_normalize_week_day_payload(day) for day in week_data.get("days", [])[:7]]
    summary = _normalize_week_summary(week_data, days)
    fragments = _extract_week_strategy_llm_fragments(llm_content)
    semantic_layer = week_data.get("semantic_layer")
    if not isinstance(semantic_layer, dict) or not semantic_layer:
        semantic_layer = build_week_forecast_semantic_layer(summary, days)

    start_label = days[0].get("date_label") if days else ""
    end_label = days[-1].get("date_label") if days else ""
    title = "📅 ПРОГНОЗ НА НЕДЕЛЮ"
    if start_label and end_label:
        title = f"{title} ({start_label} - {end_label})"

    status = str(summary.get("traffic_light") or "YELLOW").upper()
    status_text_map = {
        "RED": "Неделя просит не героизма, а дисциплины: выиграет тот, кто сузит повестку и не отдаст силы лишним конфликтам.",
        "YELLOW": "Неделя неровная, но рабочая: многое решат темп, проверка деталей и способность не дергаться раньше времени.",
        "GREEN": "Неделя дает ход там, где ты уже готова или готов: можно выносить вперед переговоры, запуск и заметные действия.",
    }
    theme_text_map = {
        "RED": "Главная задача недели не в том, чтобы сделать все, а в том, чтобы удержать один опорный приоритет и не разменять силы на давление со стороны.",
        "YELLOW": "Неделя идет рывками, поэтому лучший результат даст спокойный темп, короткие проверки и отказ от лишних обещаний раньше факта.",
        "GREEN": "Неделя поддерживает то, что уже собрано: можно двигать переговоры, запускать подготовленные шаги и закреплять полезные договоренности.",
    }

    semantic_status = str(semantic_layer.get("headline") or "").strip()
    semantic_theme = " ".join(
        part.strip()
        for part in [
            str(semantic_layer.get("pacing") or "").strip(),
            str(semantic_layer.get("negotiation") or "").strip(),
            str(semantic_layer.get("relationship_softness") or "").strip(),
        ]
        if part and str(part).strip()
    )

    status_content = _merge_week_text(
        fragments.get("status_content") or semantic_status or status_text_map.get(status, status_text_map["YELLOW"]),
        _build_week_fact_tail(days),
    )
    theme_text = _merge_week_text(
        fragments.get("theme_text") or semantic_theme or theme_text_map.get(status, theme_text_map["YELLOW"]),
        _build_week_trigger_tail(days),
    )

    blocks: list[dict[str, Any]] = [
        {"type": "header", "level": 2, "text": title},
        {
            "type": "callout",
            "variant": _normalize_status_variant(status),
            "title": "СТАТУС НЕДЕЛИ",
            "content": status_content,
        },
        {"type": "header", "level": 2, "text": "Главная тема"},
        {
            "type": "paragraph",
            "text": theme_text,
        },
        {"type": "header", "level": 2, "text": "Подневная стратегия"},
    ]

    for day in days:
        events = day.get("events") or []
        blocks.append(
            {
                "type": "header",
                "level": 3,
                "text": _format_week_day_title(day, include_traffic=True),
            }
        )
        blocks.append(
            {
                "type": "list",
                "items": [
                    f"**Луна:** {day.get('moon_label') or 'Без уточнения'}",
                    f"**Астро-события:** {', '.join(events) if events else 'Без новых триггеров, держи темп ровным.'}",
                    f"**Фокус:** {_build_week_focus_line(day)}",
                    f"**Риск:** {_build_week_risk_line(day)}",
                ],
                "ordered": False,
            }
        )

    blocks.extend(
        [
            {"type": "header", "level": 2, "text": "Резюме по срезам"},
            {"type": "traffic_lights", "items": _build_week_traffic_items(summary)},
        ]
    )
    return json.dumps(blocks, ensure_ascii=False)


def _build_week_strategy_fallback_content(context: dict[str, Any]) -> str:
    return _render_week_strategy_content(context)


def _build_month_forecast_fallback_content(context: dict[str, Any]) -> str:
    return _render_month_forecast_content(context)


def build_section_fallback_content(spec: SectionSpec, context: dict) -> str:
    """
    # PURPOSE: Provide a user-friendly fallback body for a failed section.
    # INPUT: section spec + context.
    # OUTPUT: JSON string (basic informative blocks).
    # CONTEXT: Used when LLM credits/network errors occur.
    """
    if spec.section_id == "week_strategy":
        return _build_week_strategy_fallback_content(context)
    if spec.section_id in {"month_full_forecast", "month_theme"}:
        return _build_month_forecast_fallback_content(context)

    facts = (context or {}).get("facts", {}) or {}
    blocks = [
        {"type": "header", "level": 2, "text": spec.title},
        {
            "type": "paragraph",
            "text": "Авто-режим: базовая интерпретация по ключевым фактам карты.",
        },
    ]

    pos_items = _format_fallback_positions(facts)
    if pos_items:
        blocks.append({"type": "list", "items": pos_items, "ordered": False})

    aspect_items = _format_fallback_aspects(facts)
    if aspect_items:
        blocks.append({"type": "list", "items": aspect_items, "ordered": False})

    if not pos_items and not aspect_items:
        blocks.append({
            "type": "callout",
            "variant": "warning",
            "title": "Данных недостаточно",
            "content": "Не хватило фактов для детального разбора, попробуйте повторить позже.",
        })

    return json.dumps(blocks, ensure_ascii=False)


def _build_insight_pack_fallback_content(spec: SectionSpec, insight_pack: dict) -> str:
    """
    # PURPOSE: Build meaningful fallback using deterministic insight_pack when LLM validation fails.
    # INPUT: section spec, insight_pack (dict with section-specific structured data).
    # OUTPUT: JSON string (list of blocks) verbalizing the insight pack.
    # CONTEXT: Ensures natal sections don't fall to generic template markers.
    """
    import json

    blocks = []
    title = spec.title.strip()

    # Executive summary fallback
    if spec.section_id == "executive_summary":
        scene_seed = ""
        for scene in insight_pack.get("scene_seeds", []):
            if isinstance(scene, dict) and str(scene.get("seed", "")).strip():
                scene_seed = str(scene.get("seed")).strip()
                break
        if not scene_seed:
            for manifestation in insight_pack.get("life_manifestations", []):
                if isinstance(manifestation, dict) and str(manifestation.get("label", "")).strip():
                    scene_seed = str(manifestation.get("label")).strip()
                    break
        if scene_seed:
            scene_seed = scene_seed[0].upper() + scene_seed[1:]
            if scene_seed[-1] not in ".!?":
                scene_seed += "."

        strength_desc = _format_insight_value(insight_pack.get("strengths_score"))
        risk_desc = _format_insight_value(insight_pack.get("risk_score"))
        relationship_desc = _format_insight_value(insight_pack.get("relationship_theme"))
        money_desc = _format_insight_value(insight_pack.get("money_theme"))
        development_desc = _format_insight_value(insight_pack.get("development_focus"))
        best_mode_desc = _format_insight_value(insight_pack.get("best_mode_of_action"))
        practical_hint = _pick_first_action_item(insight_pack.get("what_to_do"))
        sun_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("sun_vector")))
        moon_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("moon_vector")))
        axis_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("asc_mc_axis")))
        items = []
        if strength_desc:
            items.append(f"Сильная опора здесь в том, что {strength_desc}")
        if risk_desc:
            items.append(f"Перегиб включается через {risk_desc}")
        if relationship_desc:
            items.append(f"В отношениях сильнее всего работает {relationship_desc}")
        if money_desc:
            items.append(f"В работе и деньгах сильнее всего работает {money_desc}")
        if sun_anchor:
            items.append(f"☀️ Опорный солнечный вектор: {sun_anchor}")
        if moon_anchor:
            items.append(f"🌙 Эмоциональный якорь: {moon_anchor}")
        if axis_anchor:
            items.append(f"⬆️/🏔️ Социальная ось: {axis_anchor}")
        if development_desc:
            items.append(f"Следующий вектор роста здесь в том, чтобы {development_desc}")
        if practical_hint:
            items.append(f"Практический ход на сейчас — {practical_hint}")

        intro_parts = []
        if scene_seed:
            intro_parts.append(scene_seed)
        if sun_anchor:
            intro_parts.append(_clean_sentence(f"☀️ Солнце: {sun_anchor}"))
        if moon_anchor:
            intro_parts.append(_clean_sentence(f"🌙 Луна: {moon_anchor}"))
        intro_text = " ".join(part for part in intro_parts if part).strip() or "Карта собирается вокруг сильного внутреннего паттерна, который важно переводить в живое действие без перегиба."

        closing_bits = []
        if axis_anchor:
            closing_bits.append(_clean_sentence(f"⬆️ ASC / 🏔️ MC: {axis_anchor}"))
        closing_bits.append(
            _clean_sentence(
                f"Зрелый режим здесь — {best_mode_desc}"
                if best_mode_desc
                else "Зрелый режим здесь — двигаться не рывком, а в ясном взрослом ритме"
            )
        )

        blocks.extend([
            {
                "type": "paragraph",
                "text": intro_text,
            },
            {"type": "list", "items": items[:6], "ordered": False},
            {
                "type": "paragraph",
                "text": " ".join(bit for bit in closing_bits if bit),
            },
        ])

    # Synthesis fallback
    elif spec.section_id == "synthesis":
        blocks.extend([
            {"type": "callout", "variant": "quote", "title": "Образ карты", "content": _format_insight_value(insight_pack.get("map_metaphor_seed"))},
            {"type": "paragraph", "text": _format_insight_value(insight_pack.get("core_life_story"))},
            {"type": "paragraph", "text": f"**Главный тезис:** {_format_insight_value(insight_pack.get('core_conflict'))}"},
        ])

    # Framework elements fallback
    elif spec.section_id == "framework_elements_modes":
        balance_list = [f"{k} - {v}%" for k, v in insight_pack.get("element_rank", {}).items()]
        blocks.append({"type": "list", "items": balance_list, "ordered": False})
        blocks.append({"type": "paragraph", "text": f"**Доминанта:** {_format_insight_value(insight_pack.get('dominant_signature'))}"})
        blocks.append({"type": "paragraph", "text": f"**Дефицит:** {_format_insight_value(insight_pack.get('deficit_signature'))}"})
        blocks.append({"type": "paragraph", "text": f"**Стиль жизни:** {_format_insight_value(insight_pack.get('lifestyle_vector'))}"})
        blocks.append({"type": "paragraph", "text": f"**Формула баланса:** {_format_insight_value(insight_pack.get('balance_formula'))}"})

    # Axes truths fallback
    elif spec.section_id == "axes_truths":
        for axis in insight_pack.get("axis_polarities", [])[:4]:
            axis_name = axis.get("axis", "")
            your_truth = axis.get("your_truth", "")
            partner_truth = axis.get("partner_truth", "")
            task = axis.get("task", "")
            blocks.append({"type": "header", "level": 3, "text": f"Ось {axis_name}"})
            blocks.append({"type": "list", "items": [f"Твоя правда: {your_truth}", f"Правда партнера: {partner_truth}", f"Задача: {task}"], "ordered": False})

    # Aspects beginner fallback
    elif spec.section_id == "aspects_beginner":
        for card in insight_pack.get("aspect_cards", [])[:5]:
            anchor = card.get("anchor", "")
            scenario = card.get("scenario", "")
            resource = card.get("resource", "")
            blocks.append({"type": "header", "level": 3, "text": anchor})
            blocks.append({"type": "list", "items": [f"Сценарий: {scenario}", f"Ресурс: {resource}"], "ordered": False})

    # Configurations fallback
    elif spec.section_id == "configurations_geometry":
        cards = insight_pack.get("configuration_cards", [])
        if cards:
            for card in cards[:3]:
                geometry = card.get("geometry", "")
                gift = card.get("gift", "")
                risk = card.get("risk", "")
                blocks.append({"type": "header", "level": 3, "text": geometry})
                blocks.append({"type": "list", "items": [f"Дар: {gift}", f"Риск: {risk}"], "ordered": False})
        else:
            blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("absence_summary", "В карте нет устойчивых конфигураций."))})

    # Dispositor office fallback
    elif spec.section_id == "dispositor_office":
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("engine_summary"))})
        for office in insight_pack.get("office_map", [])[:3]:
            ruler = office.get("ruler", "")
            role = office.get("role", "")
            blocks.append({"type": "paragraph", "text": f"**{ruler}** управляет: {role}"})
        bosses = insight_pack.get("final_bosses", [])
        if bosses:
            blocks.append({"type": "callout", "variant": "info", "title": "Главный Босс", "content": ", ".join(bosses)})

    # Core triad fallback
    elif spec.section_id == "core_triad":
        asc_mask = insight_pack.get("asc_mask", {})
        solar_drive = insight_pack.get("solar_drive", {})
        lunar_need = insight_pack.get("lunar_need", {})
        blocks.append({"type": "header", "level": 3, "text": f"⬆️ ASC: {_format_insight_value(asc_mask.get('label'))}"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(asc_mask.get('mode'))})
        blocks.append({"type": "header", "level": 3, "text": f"☀️ Солнце: {_format_insight_value(solar_drive.get('label'))}"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(solar_drive.get('drive'))})
        blocks.append({"type": "header", "level": 3, "text": f"🌙 Луна: {_format_insight_value(lunar_need.get('label'))}"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(lunar_need.get('need'))})
        triad_info = insight_pack.get("triad_integration", {})
        blocks.append({"type": "callout", "variant": "info", "title": "Сборка ядра", "content": _format_insight_value(triad_info.get("summary") or triad_info.get("steps"))})

    # Mercury mind fallback
    elif spec.section_id == "mercury_mind":
        blocks.append({"type": "header", "level": 3, "text": "☿ Меркурий"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("thinking_style"))})
        blocks.append({"type": "list", "items": [
            f"**Стиль:** {_format_insight_value(insight_pack.get('thinking_style'))}",
            f"**Режим:** {_format_insight_value(insight_pack.get('processing_mode'))}",
            f"**Ловушка:** {_format_insight_value(', '.join(insight_pack.get('cognitive_risks', [])))}",
            f"**Ключ:** {_format_insight_value(', '.join(insight_pack.get('mind_keys', [])))}"
        ], "ordered": False})

    # Shadow trauma fallback
    elif spec.section_id == "shadow_trauma":
        chiron_pattern = insight_pack.get("chiron_pattern", {})
        lilith_pattern = insight_pack.get("lilith_pattern", {})
        blocks.append({"type": "header", "level": 3, "text": f"⚷ Хирон: {_format_insight_value(chiron_pattern.get('anchor'))}"})
        blocks.append({"type": "list", "items": [
            f"**Сценарий:** {_format_insight_value(chiron_pattern.get('scenario'))}",
            f"**Ресурс:** {_format_insight_value(chiron_pattern.get('resource'))}"
        ], "ordered": False})
        blocks.append({"type": "header", "level": 3, "text": f"⚸ Лилит: {_format_insight_value(lilith_pattern.get('anchor'))}"})
        blocks.append({"type": "list", "items": [
            f"**Сценарий:** {_format_insight_value(lilith_pattern.get('scenario'))}",
            f"**Ресурс:** {_format_insight_value(lilith_pattern.get('resource'))}"
        ], "ordered": False})
        blocks.append({"type": "callout", "variant": "info", "title": "Задача интеграции", "content": _format_insight_value(insight_pack.get("integration_task"))})

    # Nodes growth fallback
    elif spec.section_id == "nodes_growth":
        blocks.append({"type": "header", "level": 3, "text": f"☊ Северный узел"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("north_node_direction"))})
        blocks.append({"type": "list", "items": [
            f"**Миссия:** {_format_insight_value(insight_pack.get('north_node_direction'))}"
        ], "ordered": False})
        blocks.append({"type": "header", "level": 3, "text": f"☋ Южный узел"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("south_node_habit"))})
        blocks.append({"type": "list", "items": [
            f"**Ловушка:** {_format_insight_value(insight_pack.get('south_node_habit'))}"
        ], "ordered": False})
        blocks.append({"type": "callout", "variant": "info", "title": "Мост", "content": _format_insight_value(insight_pack.get("bridge_task"))})

    # Vertex fate fallback
    elif spec.section_id == "vertex_fate":
        blocks.append({"type": "header", "level": 3, "text": "✴️ Вертекс"})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("vertex_signature"))})
        blocks.append({"type": "list", "items": [
            f"**Триггеры встреч:** {_format_insight_value(', '.join(insight_pack.get('encounter_triggers', [])))}",
            f"**Вектор:** {_format_insight_value(insight_pack.get('relationship_vector'))}"
        ], "ordered": False})
        blocks.append({"type": "callout", "variant": "quote", "title": "Урок судьбы", "content": _format_insight_value(insight_pack.get("fated_lesson"))})

    # Balance wheel fallback
    elif spec.section_id in {"balance_wheel_1_6", "balance_wheel_7_12"}:
        for house in insight_pack.get("house_pack", []):
            h_num = house.get("house", "")
            h_theme = house.get("theme", "")
            blocks.append({"type": "header", "level": 3, "text": f"{h_num} Дом"})
            blocks.append({"type": "list", "items": [
                f"**Тема:** {h_theme}",
                f"**В плюсе:** {house.get('plus', '')}",
                f"**В минусе:** {house.get('minus', '')}",
                f"**Триггер:** {house.get('trigger', '')}",
                f"**Вектор зрелости:** {house.get('growth_vector', '')}"
            ], "ordered": False})

    # Love intimacy fallback
    elif spec.section_id == "love_intimacy":
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("relationship_theme"))})
        blocks.append({"type": "paragraph", "text": _format_insight_value(insight_pack.get("relationship_manifestations"))})
        items = []
        if insight_pack.get("self_sabotage_pattern"):
            items.append(f"**Ловушка:** {insight_pack['self_sabotage_pattern']}")
        if insight_pack.get("what_to_do"):
            items.extend(_format_list_items(insight_pack['what_to_do']))
        if items:
            blocks.append({"type": "list", "items": items, "ordered": False})
        blocks.append({"type": "paragraph", "text": f"**Зрелый режим:** {_format_insight_value(insight_pack.get('best_mode_of_action'))}"})

    # Money realization fallback
    elif spec.section_id == "money_realization":
        blocks.append({"type": "paragraph", "text": f"**Вектор карьеры:** {_format_insight_value(insight_pack.get('career_vector'))}"})
        blocks.append({"type": "paragraph", "text": f"**Паттерн денег:** {_format_insight_value(insight_pack.get('money_pattern'))}"})
        items = []
        if insight_pack.get("work_risk_flags"):
            items.append(f"**Риски:** {', '.join(insight_pack['work_risk_flags'])}")
        if items:
            blocks.append({"type": "list", "items": items, "ordered": False})
        blocks.append({"type": "paragraph", "text": f"**Режим реализации:** {_format_insight_value(insight_pack.get('realization_mode'))}"})

    # Stars transuranus fallback
    elif spec.section_id == "stars_transuranus":
        for planet, vec_key in [("⚅ Уран", "uranus_vector"), ("⛆ Нептун", "neptune_vector"), ("⯓ Плутон", "pluto_vector")]:
            vec = insight_pack.get(vec_key, {})
            mode = vec.get("mode", "")
            gift = vec.get("gift", "")
            risk = vec.get("risk", "")
            key = vec.get("key", "")
            blocks.append({"type": "header", "level": 3, "text": planet})
            blocks.append({"type": "paragraph", "text": f"**Режим:** {mode}"})
            blocks.append({"type": "list", "items": [f"**Дар:** {gift}", f"**Риск:** {risk}", f"**Ключ:** {key}"], "ordered": False})

    # Time cycles fallback
    elif spec.section_id == "time_cycles":
        age_info = insight_pack.get("current_age", {})
        cycles = insight_pack.get("cycle_markers", [])
        blocks.append({"type": "paragraph", "text": f"**Текущий период:** {_format_insight_value(age_info.get('summary', age_info.get('years')))}"})
        if cycles:
            blocks.append({"type": "list", "items": [f"**Цикл:** {c}" for c in cycles[:3]], "ordered": False})
        sj_phase = insight_pack.get("saturn_jupiter_phase", "")
        if sj_phase:
            blocks.append({"type": "callout", "variant": "info", "title": "Сатурн-Юпитер фаза", "content": sj_phase})
        growth = insight_pack.get("growth_tension", "")
        if growth:
            blocks.append({"type": "callout", "variant": "warning", "title": "Напряжение роста", "content": growth})

    # Final synthesis fallback
    elif spec.section_id == "final_synthesis":
        motto = _format_insight_value(insight_pack.get("final_motto_seed"))
        advice = _format_insight_value(insight_pack.get("one_sentence_advice"))
        blocks.append({
            "type": "callout",
            "variant": "success",
            "title": "Финальная сборка",
            "content": f"**Девиз:** {motto}\n**Главный совет:** {advice}"
        })

    # Default: minimal but section-aware
    else:
        blocks.append({
            "type": "callout",
            "variant": "warning",
            "title": "Временное содержание",
            "content": f"Секция '{title}' требует донастройки. Данные insight_pack загружены, но вербализация требует перезапуска."
        })

    return json.dumps(blocks, ensure_ascii=False)


def _clean_sentence(text: Any) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    cleaned = cleaned[0].upper() + cleaned[1:]
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


def _strip_known_prefixes(text: Any, patterns: list[str]) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    for pattern in patterns:
        candidate = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE).strip(" ,:;-")
        if candidate and candidate != cleaned:
            return candidate
    return cleaned


def _normalize_executive_fragment(text: Any, patterns: list[str]) -> str:
    cleaned = _strip_known_prefixes(text, patterns)
    if not cleaned:
        return ""
    return re.sub(r"^[—–-]+\s*", "", cleaned).strip()


def _strip_fact_anchor_parentheticals(text: Any) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    while True:
        updated = re.sub(r"\s*\([^()]*\)", "", cleaned)
        if updated == cleaned:
            break
        cleaned = updated
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*;\s*", "; ", cleaned)
    return cleaned.strip(" ;,")


def _build_final_synthesis_fact_anchor(insight_pack: dict, *, include_axis: bool = True) -> str:
    sun_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("sun_vector")))
    moon_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("moon_vector")))
    if not sun_line:
        sun_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("solar_drive")))
    if not moon_line:
        moon_line = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("lunar_need")))

    axis_line = ""
    if include_axis:
        axis_line = _strip_fact_anchor_parentheticals(
            _format_insight_value(insight_pack.get("asc_mc_axis"))
        )
        if not axis_line:
            axis_line = _strip_fact_anchor_parentheticals(
                _format_insight_value(insight_pack.get("closing_bridge"))
            )

    fragments = []
    if sun_line:
        fragments.append(_clean_sentence(f"☀️ Солнце: {sun_line}"))
    if moon_line:
        fragments.append(_clean_sentence(f"🌙 Луна: {moon_line}"))
    if axis_line:
        fragments.append(_clean_sentence(f"⬆️ ASC / 🏔️ MC: {axis_line}"))
    return " ".join(part for part in fragments if part).strip()


def _build_timed_final_synthesis_content(insight_pack: dict) -> str:
    motto_raw = _format_insight_value(insight_pack.get("final_motto_seed"))
    integration_raw = _strip_fact_anchor_parentheticals(
        _format_insight_value(insight_pack.get("integration_focus"))
    )
    bridge = insight_pack.get("closing_bridge") or {}
    work_line = str(bridge.get("work_line") or "").strip()
    love_line = str(bridge.get("love_line") or "").strip()
    fallback_advice = _format_insight_value(insight_pack.get("one_sentence_advice"))

    motto_parts = []
    for index, part in enumerate(re.split(r"\s*;\s*", motto_raw)):
        chunk = part.strip(" ,;")
        if not chunk:
            continue
        if index == 0:
            motto_parts.append(_clean_sentence(chunk))
            continue
        chunk = re.sub(
            r"^режим\s+карты\s*[—:-]\s*",
            "Зрелый ход этой карты: ",
            chunk,
            count=1,
            flags=re.IGNORECASE,
        )
        motto_parts.append(_clean_sentence(chunk))
    motto_text = " ".join(motto_parts).strip()
    if not motto_text:
        motto_text = _clean_sentence("Держи сильную сторону карты в ясном взрослом ритме")
    fact_anchor = _build_final_synthesis_fact_anchor(insight_pack, include_axis=True)
    if fact_anchor:
        motto_text = f"{motto_text} {fact_anchor}".strip()

    advice_parts = []
    for part in re.split(r"\s*;\s*", integration_raw):
        chunk = part.strip(" ,;")
        if not chunk:
            continue
        chunk = re.sub(
            r"^твоя\s+сила\s+максимальна,\s+когда\b",
            "Сильная версия этой карты раскрывается, когда",
            chunk,
            count=1,
            flags=re.IGNORECASE,
        )
        chunk = re.sub(
            r"^большой\s+образ\s+должен\s+получать\b",
            "Большому образу важно сразу давать",
            chunk,
            count=1,
            flags=re.IGNORECASE,
        )
        advice_parts.append(_clean_sentence(chunk))
    if work_line:
        advice_parts.append(_clean_sentence(f"В работе {work_line}"))
    if love_line:
        advice_parts.append(_clean_sentence(f"В близости {love_line}"))
    if not advice_parts and fallback_advice:
        advice_parts.append(_clean_sentence(fallback_advice))
    advice_text = " ".join(advice_parts).strip()
    if fact_anchor and fact_anchor not in advice_text:
        advice_text = f"{fact_anchor} {advice_text}".strip()

    blocks = [
        {
            "type": "callout",
            "variant": "success",
            "title": "Финальная сборка",
            "content": f"**Девиз:** {motto_text}\n**Главный совет:** {advice_text}",
        }
    ]
    return json.dumps(blocks, ensure_ascii=False)


def _build_untimed_final_synthesis_content(insight_pack: dict) -> str:
    motto = _clean_sentence(_format_insight_value(insight_pack.get("final_motto_seed")))
    advice = _clean_sentence(_format_insight_value(insight_pack.get("one_sentence_advice")))
    bridge = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("closing_bridge")))
    fact_anchor = _build_final_synthesis_fact_anchor(insight_pack, include_axis=False)

    content_parts = []
    if motto:
        content_parts.append(f"**Девиз:** {motto}")
    elif fact_anchor:
        content_parts.append(f"**Девиз:** {fact_anchor}")

    advice_parts = []
    if fact_anchor:
        advice_parts.append(fact_anchor)
    if bridge:
        advice_parts.append(_clean_sentence(bridge))
    if advice:
        advice_parts.append(advice)
    if not advice_parts:
        advice_parts.append("**Главный совет:** Держи сильную сторону карты в живом и проверяемом ритме.")
    else:
        advice_parts[0] = f"**Главный совет:** {advice_parts[0]}"

    blocks = [{
        "type": "callout",
        "variant": "success",
        "title": "Финальная сборка",
        "content": "\n".join(content_parts + advice_parts),
    }]
    return json.dumps(blocks, ensure_ascii=False)


def _build_timed_natal_executive_summary_content(insight_pack: dict) -> str:
    scene_seed = ""
    for scene in insight_pack.get("scene_seeds", []):
        if isinstance(scene, dict) and str(scene.get("seed", "")).strip():
            scene_seed = str(scene.get("seed")).strip()
            break
    if not scene_seed:
        for manifestation in insight_pack.get("life_manifestations", []):
            if isinstance(manifestation, dict) and str(manifestation.get("label", "")).strip():
                scene_seed = str(manifestation.get("label")).strip()
                break

    strength_desc = _format_insight_value(insight_pack.get("strengths_score"))
    risk_desc = _format_insight_value(insight_pack.get("risk_score"))
    relationship_desc = _format_insight_value(insight_pack.get("relationship_theme"))
    money_desc = _format_insight_value(insight_pack.get("money_theme"))
    development_desc = _format_insight_value(insight_pack.get("development_focus"))
    best_mode_desc = _format_insight_value(insight_pack.get("best_mode_of_action"))
    stress_desc = _format_insight_value(insight_pack.get("stress_manifestation"))
    practical_hint = _pick_first_action_item(insight_pack.get("what_to_do"))
    sun_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("sun_vector")))
    moon_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("moon_vector")))
    axis_anchor = _strip_fact_anchor_parentheticals(_format_insight_value(insight_pack.get("asc_mc_axis")))
    stress_desc = _normalize_executive_fragment(
        stress_desc,
        [r"^под\s+стрессом\b", r"^под\s+давлением\b"],
    )
    relationship_desc = _normalize_executive_fragment(
        relationship_desc,
        [
            r"^в\s+отношениях\b",
            r"^отношения\s+(?:раскрываются|строятся|держатся)\s+через\b",
            r"^близость\s+раскрывается\s+через\b",
        ],
    )
    money_desc = _normalize_executive_fragment(
        money_desc,
        [
            r"^деньги\s+лучше\s+всего\s+приходят\s+через\b",
            r"^лучше\s+всего\s+приходят\s+через\b",
            r"^работа\s+и\s+деньги\s+(?:идут|приходят|строятся)\s+через\b",
            r"^в\s+деньгах\s+и\s+работе\b",
            r"^в\s+работе\s+и\s+деньгах\b",
            r"^деньги\b",
        ],
    )
    best_mode_desc = _normalize_executive_fragment(
        best_mode_desc,
        [r"^лучший\s+режим\s+действия\b", r"^лучший\s+режим\b", r"^зрелый\s+режим\b"],
    )

    intro_parts = []
    scene_line = _clean_sentence(scene_seed)
    if scene_line:
        intro_parts.append(scene_line)
    if strength_desc:
        intro_parts.append(_clean_sentence(f"Сильнее всего карта раскрывается там, где {strength_desc}"))
    if sun_anchor:
        intro_parts.append(_clean_sentence(f"☀️ Солнце: {sun_anchor}"))
    if moon_anchor:
        intro_parts.append(_clean_sentence(f"🌙 Луна: {moon_anchor}"))
    if stress_desc:
        intro_parts.append(_clean_sentence(f"Под давлением особенно видно, как {stress_desc}"))
    intro_text = " ".join(part for part in intro_parts if part).strip()
    if not intro_text:
        intro_text = (
            "Карта собирается вокруг сильного внутреннего паттерна, который важно переводить "
            "в живое действие без перегиба."
        )

    items = []
    if strength_desc:
        items.append(_clean_sentence(f"Сильная опора здесь в том, что {strength_desc}"))
    if risk_desc:
        items.append(_clean_sentence(f"Перегиб включается через {risk_desc}"))
    if relationship_desc:
        items.append(_clean_sentence(f"Отношения держатся на том, что {relationship_desc}"))
    if money_desc:
        items.append(_clean_sentence(f"Деньги и реализация растут через {money_desc}"))
    if axis_anchor:
        items.append(_clean_sentence(f"⬆️ ASC / 🏔️ MC задают социальную ось: {axis_anchor}"))
    if development_desc:
        items.append(_clean_sentence(f"Фокус роста сейчас — {development_desc}"))
    if practical_hint:
        items.append(_clean_sentence(f"Практический ход на сейчас — {practical_hint}"))

    closing_text = _clean_sentence(
        f"Зрелый режим здесь — {best_mode_desc}"
        if best_mode_desc
        else "Зрелый режим здесь — двигаться не рывком, а в ясном зрелом ритме"
    )

    blocks = [
        {"type": "paragraph", "text": intro_text},
        {"type": "list", "items": items, "ordered": False},
        {"type": "paragraph", "text": closing_text},
    ]
    return json.dumps(blocks, ensure_ascii=False)


def _format_insight_value(value: Any) -> str:
    """Format insight value for display, handling dicts, lists, and strings."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("label", "text", "seed", "summary", "content"):
            text = str(value.get(key, "")).strip()
            if text:
                return text
        items = value.get("items")
        if isinstance(items, list):
            preview = [str(item).strip() for item in items if str(item).strip()]
            if preview:
                return ", ".join(preview[:2])
        return str(value)
    if isinstance(value, list):
        if len(value) == 0:
            return ""
        first = value[0]
        if isinstance(first, dict):
            return str(
                first.get("label")
                or first.get("text")
                or first.get("seed")
                or first.get("value")
                or first
            )
        return str(first)
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def _format_list_items(items: Any) -> list:
    """Format insight pack list items for display."""
    if isinstance(items, list):
        return [
            f"• {item}" if isinstance(item, str) else f"• {_format_insight_value(item)}"
            for item in items[:5]
            if _format_insight_value(item if not isinstance(item, str) else {"label": item}) or isinstance(item, str)
        ]
    if isinstance(items, dict):
        nested_items = items.get("items")
        if isinstance(nested_items, list):
            return _format_list_items(nested_items)
        formatted = _format_insight_value(items)
        return [f"• {formatted}"] if formatted else []
    return []


def _pick_first_action_item(items: Any) -> str:
    """Extract the first human-readable action from insight-pack list fields."""
    if isinstance(items, dict):
        nested_items = items.get("items")
        if isinstance(nested_items, list):
            return _pick_first_action_item(nested_items)
        return _format_insight_value(items)
    if isinstance(items, list):
        for item in items:
            if isinstance(item, str) and item.strip():
                return item.strip()
            text = _format_insight_value(item)
            if text:
                return text
        return ""
    return _format_insight_value(items)


def _collect_fact_anchor_evidence(*sources: Any, limit: int = 2) -> List[str]:
    anchors: List[str] = []
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        evidence = source.get("evidence")
        if not isinstance(evidence, list):
            continue
        for raw in evidence:
            text = str(raw or "").strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            anchors.append(text)
            if len(anchors) >= limit:
                return anchors
    return anchors


def _extract_named_anchor(*sources: Any, names: tuple[str, ...]) -> str:
    normalized_names = tuple(name.lower() for name in names if name)
    for source in sources:
        if not isinstance(source, dict):
            continue
        evidence = source.get("evidence")
        if not isinstance(evidence, list):
            continue
        for raw in evidence:
            text = str(raw or "").strip()
            lowered = text.lower()
            if text and any(name in lowered for name in normalized_names):
                return text
    return ""


def _compose_fact_first_fragment(
    text: Any,
    *sources: Any,
    limit: int = 1,
    prefix_patterns: Optional[list[str]] = None,
) -> str:
    cleaned = _normalize_executive_fragment(text, prefix_patterns or [])
    anchors = _collect_fact_anchor_evidence(*sources, limit=limit)
    if anchors:
        anchor_text = "; ".join(anchors)
        if cleaned:
            return f"{cleaned} ({anchor_text})"
        return anchor_text
    return cleaned


def build_section_validation_fallback_content(spec: SectionSpec, context: dict) -> str:
    if spec.section_id in {"week_strategy", "month_full_forecast", "month_theme"}:
        return build_section_fallback_content(spec, context)
    # For natal sections, use insight_pack-aware fallback instead of generic template
    # This ensures meaningful content even when LLM validation fails
    if spec.section_id in NATAL_SECTION_IDS or spec.section_id == "executive_summary":
        insight_pack = (context.get("section_context") or {}).get("insight_pack")
        if insight_pack:
            if spec.section_id == "executive_summary":
                if context.get("client", {}).get("birth_time_known", True):
                    return _build_timed_natal_executive_summary_content(insight_pack)
                return _build_insight_pack_fallback_content(spec, insight_pack)
            if spec.section_id == "final_synthesis" and context.get("client", {}).get("birth_time_known", True):
                return _build_timed_final_synthesis_content(insight_pack)
            if spec.section_id == "final_synthesis":
                return _build_untimed_final_synthesis_content(insight_pack)
            return _build_insight_pack_fallback_content(spec, insight_pack)
    return build_section_template_content(spec)


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


def resolve_llm_retry_attempts() -> int:
    """
    # PURPOSE: Resolve retry attempts for structural validation failures.
    # INPUT: None.
    # OUTPUT: Retry count (>=1).
    # CONTEXT: Used before switching to fallback model.
    """

    raw = os.getenv("OPENROUTER_RETRY_ATTEMPTS", "3").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 3
    return max(1, value)


def resolve_llm_fallback_model() -> str:
    """
    # PURPOSE: Resolve fallback OpenRouter model name.
    # INPUT: None.
    # OUTPUT: Model name string (empty means disabled).
    # CONTEXT: Used when primary model fails structural validation.
    """

    model = os.getenv(
        "OPENROUTER_FALLBACK_MODEL", "openai/gpt-4o-mini"
    ).strip()
    return model


def resolve_llm_fallback_chain() -> List[str]:
    """
    # PURPOSE: Resolve a list of fallback models for the chain.
    # INPUT: None.
    # OUTPUT: List of model names.
    """
    raw = os.getenv("OPENROUTER_FALLBACK_CHAIN", "").strip()
    if not raw:
        # Defaults for MVP (all free and verified stable)
        return [
            "openai/gpt-4o-mini"
        ]
    return [m.strip() for m in raw.split(",") if m.strip()]


def resolve_primary_model(report_type: Optional[str]) -> str:
    """
    # PURPOSE: Pick a primary OpenRouter model based on report type.
    # INPUT: report_type (str | None).
    # OUTPUT: Model name string.
    # CONTEXT: Used to route expensive vs. cheap models per product.
    """

    report_key = (report_type or "").strip().lower()
    if report_key.startswith("natal"):
        model = os.getenv("OPENROUTER_MODEL_NATAL", "").strip()
    elif "forecast" in report_key:
        model = os.getenv("OPENROUTER_MODEL_FORECAST", "").strip()
    elif "horary" in report_key:
        model = os.getenv("OPENROUTER_MODEL_HORARY", "").strip()
    elif "synastry" in report_key:
        model = os.getenv("OPENROUTER_MODEL_SYNASTRY", "").strip()
    else:
        model = ""

    if model:
        return model

    return os.getenv(
        "OPENROUTER_MODEL", "openai/gpt-4.1-nano"
    ).strip()


def resolve_llm_concurrency(llm_mode: str) -> int:
    mode = (llm_mode or "").strip().lower()
    if mode in {"cli", "gemini", "codex"}:
        env_name = "LLM_CLI_CONCURRENCY"
        default = 3
    else:
        env_name = "LLM_CONCURRENCY"
        default = 10  # High concurrency for paid/budget models

    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def resolve_openrouter_throttle_seconds() -> float:
    raw = os.getenv("OPENROUTER_THROTTLE_SECONDS", "0.0").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


def generate_section_with_retries(
    spec: SectionSpec,
    context: Dict[str, Any],
    *,
    primary_client: LLMClient,
    fallback_models: List[str],
    max_attempts: int,
) -> SectionResult:
    """
    # PURPOSE: Generate a section with retries + model switching on bad structure or API errors.
    # INPUT: spec, context, primary client, fallback models list, max attempts per model.
    # OUTPUT: SectionResult.
    """

    all_models = []
    # Add primary model if it's an OpenRouter client
    if isinstance(primary_client, OpenRouterClient):
        all_models.append(primary_client.model)
    
    # Add fallbacks
    for m in fallback_models:
        if m and m not in all_models:
            all_models.append(m)

    logger.info("report.section.model_chain", section_id=spec.section_id, models=all_models)

    if not all_models and not isinstance(primary_client, CliLLMClient):
         # If no models defined, at least use what we have
         all_models = ["default"]

    last_error: Optional[Exception] = None
    facts = context.get("facts")

    # Iterate over models in the chain
    for model_name in all_models:
        # Construct client for this specific model if it's not the primary one already active
        current_client = primary_client
        if isinstance(primary_client, OpenRouterClient) and model_name != primary_client.model:
            try:
                current_client = OpenRouterClient.from_env(model_override=model_name)
            except Exception as e:
                logger.warning("report.section.client_init_failed", model=model_name, error=str(e))
                continue

        orchestrator = LLMOrchestrator(current_client)
        
        # Try this model N times
        for attempt in range(max_attempts):
            try:
                result = orchestrator.generate_sections([spec], context=context)[0]
                
                # HALLUCINATION VALIDATION (Natal only)
                content = result.content or ""
                is_natal = spec.section_id in NATAL_SECTION_IDS or "natal" in str(spec.section_id)
                if is_natal and facts and ("[" in content and "]" in content):
                    try:
                        clean = content.strip()
                        if clean.startswith("```json"): clean = clean[7:]
                        elif clean.startswith("```"): clean = clean[3:]
                        if clean.endswith("```"): clean = clean[:-3]
                        
                        blocks = json.loads(clean.strip())
                        if isinstance(blocks, list):
                            errors = validate_llm_hallucinations(blocks, facts)
                            if errors:
                                msg = "; ".join(errors)
                                logger.warning("report.section.hallucination", section_id=spec.section_id, model=model_name, errors=msg)
                                raise LLMContentValidationError(f"Hallucination control failed: {msg}")
                    except json.JSONDecodeError:
                        pass 
                
                return result

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "report.section.retry",
                    block_id="REPORT_SECTION",
                    section_id=spec.section_id,
                    model=model_name,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    error=str(exc),
                )
                # If it's a validation error, we retry the SAME model.
                # If it's a 429 or other API error, we might want to skip to next model immediately,
                # but for simplicity we just finish all attempts for this model.
                continue
        
        # If we are here, all attempts for current model failed. 
        # Move to next model in chain.
        logger.error("report.section.model_failed", section_id=spec.section_id, model=model_name)

    if last_error:
        raise last_error
    raise LLMContentValidationError("content validation failed after trying all models")


def finish_report_run(
    run: Optional[ReportRun],
    db: Session,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """
    # PURPOSE: Finalize a report run record with status and timestamps.
    # INPUT: run, db session, status, optional error_message.
    # OUTPUT: None.
    # CONTEXT: Used after report generation completes or fails.
    """

    if not run:
        return
    run.status = status
    run.error_message = error_message
    run.finished_at = datetime.now(timezone.utc)
    db.commit()


def build_section_specs(payload: Any) -> List[SectionSpec]:
    """Resolve semantic section specs using canonical builders and workflow overrides.

    # START_CONTRACT: FN-BUILD-REPORT-SECTIONS
    # purpose: Resolve semantic section specs for a report request.
    # inputs: report workflow payload with report_type and optional custom section data.
    # returns: ordered list of SectionSpec entries for generation/resume flows.
    # side_effects: emits semantic section-resolution logs only.
    # errors: propagates template/spec normalization failures.
    # END_CONTRACT: FN-BUILD-REPORT-SECTIONS
    """
    # START_BLOCK: SECTION_SPEC_RESOLUTION
    _workflow_log(
        "info",
        "report.workflow.section_specs_resolve",
        fn="build_section_specs",
        contract="FN-BUILD-REPORT-SECTIONS",
        block="SECTION_SPEC_RESOLUTION",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
    )
    """
    # PURPOSE: Resolve section specs from payload or defaults.
    # INPUT: payload (ReportWorkflowRequest-like).
    # OUTPUT: List[SectionSpec].
    # CONTEXT: Used by report workflow services.
    """

    if getattr(payload, "sections", None):
        specs = [
            SectionSpec(
                section_id=section.section_id,
                title=section.title,
                prompt=section.prompt,
                max_tokens=getattr(section, "max_tokens", None),
            )
            for section in payload.sections
        ]
        _workflow_log(
            "info",
            "report.workflow.section_specs_resolved",
            fn="build_section_specs",
            contract="FN-BUILD-REPORT-SECTIONS",
            block="SECTION_SPEC_RESOLUTION",
            report_id=getattr(payload, "report_id", None),
            report_type=getattr(payload, "report_type", None),
            section_total=len(specs),
            source="payload_sections",
        )
        # END_BLOCK: SECTION_SPEC_RESOLUTION
        return specs
    
    mode = getattr(payload, "report_mode", "full")
    canonical_builder = CANONICAL_TEMPLATE_BUILDERS.get(payload.report_type)
    sections = canonical_builder() if canonical_builder and mode == "full" else get_default_sections(payload.report_type, mode=mode)
    
    # Filter out house-based sections if time is unknown
    if not getattr(payload, "birth_time_known", True):
        house_based = {"axes_truths", "balance_wheel_1_6", "balance_wheel_7_12", "solar_money", "solar_love"}
        sections = [s for s in sections if s.section_id not in house_based]
        
    _workflow_log(
        "info",
        "report.workflow.section_specs_resolved",
        fn="build_section_specs",
        contract="FN-BUILD-REPORT-SECTIONS",
        block="SECTION_SPEC_RESOLUTION",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
        section_total=len(sections),
        source="default_catalog",
        report_mode=mode,
    )
    # END_BLOCK: SECTION_SPEC_RESOLUTION
    return sections


def load_section_specs_for_report(report: Report, payload_data: Optional[dict]) -> List[SectionSpec]:
    """
    # START_CONTRACT: FN-RESUME-REPORT-CREATION
    # purpose: Restore section specs for persisted report resume/admin replay flows.
    # inputs: report row and optional serialized payload data.
    # returns: ordered list of SectionSpec entries for resumed workflow execution.
    # side_effects: emits resume-bridge workflow logs aligned with checkout/admin wording.
    # errors: propagates invalid payload/spec restoration failures.
    # END_CONTRACT: FN-RESUME-REPORT-CREATION
    """
    # START_BLOCK: SECTION_SPEC_RESTORE
    _workflow_log(
        "info",
        "report.workflow.resume_restore_start",
        fn="load_section_specs_for_report",
        contract="FN-RESUME-REPORT-CREATION",
        block="SECTION_SPEC_RESTORE",
        report=report,
        payload_present=payload_data is not None,
    )
    """
    # PURPOSE: Resolve section specs for a report without raising errors.
    # INPUT: report, payload_data (dict|None).
    # OUTPUT: List[SectionSpec].
    # CONTEXT: Used when markdown/PDF are requested without payload.
    """

    if payload_data:
        try:
            payload = payload_data
            if isinstance(payload_data, dict):
                class PayloadShim:
                    def __init__(self, data: dict) -> None:
                        self.sections = data.get("sections")
                        self.report_type = data.get("report_type", report.report_type)
                        self.report_mode = data.get("report_mode", "full")

                payload = PayloadShim(payload_data)
            specs = build_section_specs(payload)
            _workflow_log(
                "info",
                "report.workflow.resume_restore_complete",
                fn="load_section_specs_for_report",
                contract="FN-RESUME-REPORT-CREATION",
                block="SECTION_SPEC_RESTORE",
                report=report,
                section_total=len(specs),
                source="payload_data",
            )
            # END_BLOCK: SECTION_SPEC_RESTORE
            return specs
        except Exception as exc:
            _workflow_log(
                "error",
                "report.workflow.resume_restore_invalid_payload",
                fn="load_section_specs_for_report",
                contract="FN-RESUME-REPORT-CREATION",
                block="SECTION_SPEC_RESTORE",
                report=report,
                error=str(exc),
            )
    specs = get_default_sections(report.report_type, mode="full")
    _workflow_log(
        "info",
        "report.workflow.resume_restore_complete",
        fn="load_section_specs_for_report",
        contract="FN-RESUME-REPORT-CREATION",
        block="SECTION_SPEC_RESTORE",
        report=report,
        section_total=len(specs),
        source="default_catalog",
        bridge="resume_checkout_fallback",
    )
    # END_BLOCK: SECTION_SPEC_RESTORE
    return specs
# #END_BLOCK_WORKFLOW_UTILS


# #START_BLOCK_WORKFLOW_CHART
def resolve_solar_return_location(payload: Any) -> Any:
    solar_location = getattr(payload, "solar_current_location", None)
    solar_lat = getattr(payload, "solar_current_lat", None)
    solar_lon = getattr(payload, "solar_current_lon", None)

    if solar_lat is not None and solar_lon is not None:
        return {
            "latitude": solar_lat,
            "longitude": solar_lon,
            "name": solar_location or getattr(payload, "birth_location", None) or "Solar Location",
            "timezone": getattr(payload, "solar_current_timezone", None),
        }

    return solar_location or getattr(payload, "birth_location", None) or "Greenwich"


def resolve_solar_return_target_year(payload: Any, now: Optional[datetime] = None) -> int:
    now_utc = now or datetime.now(timezone.utc)
    tz_str = getattr(payload, "solar_current_timezone", None) or getattr(payload, "birth_timezone", None)

    try:
        now_local = now_utc.astimezone(ZoneInfo(tz_str)) if tz_str else now_utc
    except Exception:
        now_local = now_utc

    birth_input = getattr(payload, "birth_date", None)
    if not birth_input:
        return now_local.year

    birth_local = normalize_datetime_input(
        birth_input,
        getattr(payload, "birth_timezone", None),
        assume_local=False,
    )

    try:
        birth_dt = datetime.fromisoformat(birth_local)
    except ValueError:
        return now_local.year

    last_day = calendar.monthrange(now_local.year, birth_dt.month)[1]
    birthday_this_year = datetime(
        now_local.year,
        birth_dt.month,
        min(birth_dt.day, last_day),
        birth_dt.hour,
        birth_dt.minute,
        birth_dt.second,
        tzinfo=now_local.tzinfo,
    )

    if now_local < birthday_this_year:
        return now_local.year - 1
    return now_local.year


def build_chart_data(payload: Any) -> dict:
    """
    # START_CONTRACT: FN-CREATE-REPORT-CHART-DATA
    # purpose: Build canonical chart payload for report generation and resume flows.
    # inputs: report workflow payload with report_type, birth data, and optional bridge fields.
    # returns: chart data dictionary used by context builders and sections.
    # side_effects: emits chart-engine and bridge-aligned workflow logs.
    # errors: propagates engine/adaptor failures to caller.
    # END_CONTRACT: FN-CREATE-REPORT-CHART-DATA
    """
    # START_BLOCK: CHART_ENGINE_DISPATCH
    _workflow_log(
        "info",
        "report.workflow.chart_build_start",
        fn="build_chart_data",
        contract="FN-CREATE-REPORT-CHART-DATA",
        block="CHART_ENGINE_DISPATCH",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
    )
    """
    # PURPOSE: Calculate chart data for report context.
    # INPUT: payload (ReportWorkflowRequest-like).
    # OUTPUT: Serialized chart dict.
    # CONTEXT: Used by report generation prompts.
    """

    engine = StelliumEngine()
    house_system = engine_utils.resolve_house_system(payload.house_system)

    # 1. Resolve Location (Prefer coordinates)
    is_horary = payload.report_type in ["horary", "horary_answer"]
    
    if is_horary and payload.solar_current_lat is not None and payload.solar_current_lon is not None:
        loc_input = {
            "latitude": payload.solar_current_lat,
            "longitude": payload.solar_current_lon,
            "name": payload.solar_current_location or "Current Location",
            "timezone": payload.solar_current_timezone
        }
        current_lat = payload.solar_current_lat
        tz_str = payload.solar_current_timezone
    else:
        loc_input = payload.birth_location
        tz_str = payload.birth_timezone
        current_lat = payload.birth_lat
        
        if payload.birth_lat is not None and payload.birth_lon is not None:
            loc_input = {
                "latitude": payload.birth_lat,
                "longitude": payload.birth_lon,
                "name": payload.birth_location or payload.client_name or "Unknown",
                "timezone": tz_str
            }
            current_lat = payload.birth_lat

    # Force Whole Sign for high latitudes to avoid SwissEph crash
    if current_lat is not None and abs(current_lat) >= 60.0:
        from stellium.engines.houses import WholeSignHouses
        house_system = WholeSignHouses()

    # 2. Resolve Time
    clean_date = ""
    if is_horary:
        # Horary: Use NOW. Try to find local timezone if coords available.
        now_utc = datetime.now(timezone.utc)
        
        target_tz = tz_str
        if not target_tz and payload.solar_current_lat and payload.solar_current_lon:
            try:
                from timezonefinder import TimezoneFinder
                tf = TimezoneFinder()
                target_tz = tf.timezone_at(lng=payload.solar_current_lon, lat=payload.solar_current_lat)
            except: pass
        
        # Format current time according to target TZ (or UTC if none)
        clean_date = normalize_datetime_input(now_utc.isoformat(), target_tz or "UTC")
    else:
        # Natal/Forecast: Use Birth Date
        clean_date = normalize_datetime_input(payload.birth_date, tz_str, assume_local=False)

    try:
        chart = engine.create_natal_chart(
            payload.client_name,
            clean_date,
            loc_input,
            house_system,
            birth_time_known=getattr(payload, "birth_time_known", True)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Chart error: {exc}"
        ) from exc

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(chart, orb=payload.fixed_star_orb)
        
    aspects = engine.find_natal_aspects(chart)
    patterns = engine.find_all_patterns(chart)
    
    extra_points = []
    try:
        selena_lon = engine.calculate_selena(chart.datetime.julian_day)
        extra_points.append({"name": "Selena", "longitude": selena_lon})
    except: pass
    
    try:
        pars_lon = engine.calculate_pars_fortuna(chart)
        extra_points.append({"name": "Part of Fortune", "longitude": pars_lon})
    except: pass

    chart_dict = engine_utils.serialize_chart(
        chart, 
        chart_type="natal", 
        fixed_stars=stars,
        aspects=aspects,
        patterns=patterns,
        extra_points=extra_points
    )
    
    if payload.report_type in ["horary", "horary_answer"]:
        q_text = getattr(payload, "question", "") or getattr(payload, "client_note", "") or ""
        adapter_id = detect_adapter(q_text)
        logger.info("horary.adapter.detect", adapter=adapter_id, question=q_text[:50])
        
        horary_core = HoraryCore(engine)
        chart_dict["horary"] = horary_core.analyze(chart, adapter_id)

    if payload.report_type == "solar_return":
        try:
            now = datetime.now(timezone.utc)
            target_year = resolve_solar_return_target_year(payload, now=now)
            sr_location = resolve_solar_return_location(payload)
            sr_chart = engine.calculate_solar_return_chart(chart, target_year, sr_location)
            chart_dict["solar_return"] = engine_utils.serialize_chart(sr_chart, "solar_return")
        except Exception as e:
            logger.error("solar_return.calc.error", error=str(e))

    if payload.report_type == "synastry":
        try:
            p_dt = normalize_datetime_input(
                payload.partner_birth_date,
                payload.partner_birth_timezone,
                assume_local=False,
            )
            p_loc = payload.partner_birth_location
            if payload.partner_birth_lat and payload.partner_birth_lon:
                p_loc = {
                    "latitude": payload.partner_birth_lat,
                    "longitude": payload.partner_birth_lon,
                    "name": payload.partner_birth_location or "Partner Loc"
                }
            
            p_chart = engine.create_natal_chart(payload.partner_name or "Partner", p_dt, p_loc or "Unknown")
            chart_dict["partner_chart"] = engine_utils.serialize_chart(p_chart, "natal")
            chart_dict["synastry"] = engine.calculate_synastry_data(chart, p_chart)
        except Exception as e:
            logger.error("synastry.calc.error", error=str(e))
        
    return chart_dict
# #END_BLOCK_WORKFLOW_CHART


def infer_gender(full_name: str) -> str:
    """Simple heuristic for Russian names."""
    name = full_name.strip().split()[0].lower() # Take first name
    if name.endswith(('а', 'я')): return "female"
    return "male"

# #START_BLOCK_WORKFLOW_CONTEXT
NATAL_SECTION_CONTEXT_RULES: Dict[str, Dict[str, Any]] = {
    "executive_summary": {
        "focus": "Краткая выжимка по сильным сторонам, рискам, отношениям и деньгам.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC", "North Node", "Chiron"],
        "houses": [1, 2, 5, 6, 7, 8, 10],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
        "aspect_limit": 8,
        "include_balance": True,
        "include_patterns": True,
    },
    "synthesis": {
        "focus": "Образ карты, ядро личности и центральный внутренний конфликт.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
        "houses": [1, 4, 7, 10],
        "aspect_points": ["Sun", "Moon", "ASC", "MC", "Mercury", "Venus", "Mars"],
        "aspect_limit": 8,
        "include_balance": True,
        "include_patterns": True,
    },
    "framework_elements_modes": {
        "focus": "Баланс стихий и модальностей без лишних деталей карты.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"],
        "aspect_limit": 4,
        "include_balance": True,
    },
    "axes_truths": {
        "focus": "Главные оси карты: ASC/DSC и IC/MC.",
        "positions": ["ASC", "DSC", "IC", "MC", "Sun", "Moon"],
        "houses": [1, 4, 7, 10],
        "aspect_points": ["ASC", "DSC", "IC", "MC", "Sun", "Moon"],
        "aspect_limit": 6,
    },
    "aspects_beginner": {
        "focus": "Только самые важные и точные аспекты.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"],
        "aspect_limit": 8,
    },
    "configurations_geometry": {
        "focus": "Фигуры и конфигурации карты.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"],
        "aspect_limit": 8,
        "include_patterns": True,
    },
    "dispositor_office": {
        "focus": "Иерархия управления планетами и центры принятия решений.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"],
        "aspect_limit": 6,
        "include_balance": True,
    },
    "core_triad": {
        "focus": "ASC, Солнце и Луна как личное ядро.",
        "positions": ["ASC", "Sun", "Moon", "Mercury"],
        "houses": [1, 4, 10],
        "aspect_points": ["ASC", "Sun", "Moon", "Mercury"],
        "aspect_limit": 6,
    },
    "mercury_mind": {
        "focus": "Как человек думает, говорит и обрабатывает информацию.",
        "positions": ["Mercury", "Moon", "Saturn", "Uranus"],
        "aspect_points": ["Mercury", "Moon", "Saturn", "Uranus"],
        "aspect_limit": 6,
    },
    "shadow_trauma": {
        "focus": "Теневая зона через Хирон, Лилит и напряженные связки.",
        "positions": ["Chiron", "Lilith", "Moon", "Saturn", "Pluto"],
        "aspect_points": ["Chiron", "Lilith", "Moon", "Saturn", "Pluto"],
        "aspect_limit": 6,
    },
    "nodes_growth": {
        "focus": "Ось роста и привычный сценарий через лунные узлы.",
        "positions": ["North Node", "True Node", "South Node", "Sun", "Moon", "Saturn"],
        "aspect_points": ["North Node", "True Node", "South Node", "Sun", "Moon", "Saturn"],
        "aspect_limit": 6,
    },
    "vertex_fate": {
        "focus": "Сюжетные встречи, Вертекс и связанная динамика отношений.",
        "positions": ["Vertex", "Venus", "Mars", "Moon", "DSC"],
        "houses": [5, 7, 8],
        "aspect_points": ["Vertex", "Venus", "Mars", "Moon"],
        "aspect_limit": 6,
    },
    "balance_wheel_1_6": {
        "focus": "Дома 1-6, их темы, управители и триггеры.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
        "houses": [1, 2, 3, 4, 5, 6],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
        "aspect_limit": 8,
    },
    "balance_wheel_7_12": {
        "focus": "Дома 7-12, их темы, управители и триггеры.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
        "houses": [7, 8, 9, 10, 11, 12],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "MC"],
        "aspect_limit": 8,
    },
    "love_intimacy": {
        "focus": "Любовный стиль, близость и сексуальная динамика.",
        "positions": ["Venus", "Mars", "Moon", "Sun", "Saturn"],
        "houses": [5, 7, 8],
        "aspect_points": ["Venus", "Mars", "Moon", "Sun", "Saturn"],
        "aspect_limit": 6,
    },
    "money_realization": {
        "focus": "Деньги, работа и реализация через дома 2/6/10 и Юпитер/Сатурн.",
        "positions": ["Jupiter", "Saturn", "Venus", "Mars", "Sun", "ASC", "MC"],
        "houses": [2, 6, 10],
        "aspect_points": ["Jupiter", "Saturn", "Venus", "Mars", "Sun", "MC"],
        "aspect_limit": 6,
    },
    "stars_transuranus": {
        "focus": "Высшие планеты и долгие смысловые линии карты.",
        "positions": ["Uranus", "Neptune", "Pluto", "Sun", "Moon", "Saturn"],
        "aspect_points": ["Uranus", "Neptune", "Pluto", "Sun", "Moon", "Saturn"],
        "aspect_limit": 6,
    },
    "time_cycles": {
        "focus": "Текущий жизненный период и циклы взросления.",
        "positions": ["Sun", "Moon", "Saturn", "Jupiter", "North Node", "ASC", "MC"],
        "houses": [1, 10],
        "aspect_points": ["Sun", "Moon", "Saturn", "Jupiter", "North Node"],
        "aspect_limit": 6,
    },
    "final_synthesis": {
        "focus": "Финальный девиз и главный совет по всей карте.",
        "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC", "North Node"],
        "houses": [1, 2, 5, 6, 7, 8, 10],
        "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
        "aspect_limit": 8,
        "include_balance": True,
        "include_patterns": True,
    },
}

DEFAULT_NATAL_SECTION_CONTEXT_RULE: Dict[str, Any] = {
    "focus": "Ключевые факты карты для этого раздела.",
    "positions": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC", "MC"],
    "houses": [1, 4, 7, 10],
    "aspect_points": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "ASC"],
    "aspect_limit": 6,
    "include_balance": True,
}


def _unique_preserve_order(values: List[Any]) -> List[Any]:
    result: List[Any] = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize_point_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    return POINT_NAME_ALIASES.get(name, name)


def _compact_position_fact(position: dict) -> dict:
    name = _normalize_point_name(position.get("key") or position.get("p") or position.get("name"))
    degree = position.get("deg")
    if degree is None:
        degree = position.get("sign_degree")
    try:
        degree = int(float(degree))
    except (TypeError, ValueError):
        degree = 0
    return {
        "p": name,
        "s": position.get("s") or position.get("sign"),
        "deg": degree,
        "h": position.get("h", position.get("house")),
        "r": bool(position.get("r", position.get("is_retrograde", False))),
    }


def _compact_house_fact(house: dict) -> dict:
    degree = house.get("deg")
    if degree is None:
        degree = house.get("sign_degree")
    try:
        degree = int(float(degree))
    except (TypeError, ValueError):
        degree = 0
    return {
        "h": house.get("h", house.get("house")),
        "s": house.get("s", house.get("sign")),
        "deg": degree,
    }


def _compact_aspect_fact(aspect: dict) -> dict:
    orb = aspect.get("o")
    if orb is None:
        orb = aspect.get("orb")
    try:
        orb = round(float(orb), 1)
    except (TypeError, ValueError):
        orb = 0.0
    return {
        "p1": _normalize_point_name(aspect.get("p1_key") or aspect.get("p1")),
        "t": aspect.get("t", aspect.get("type")),
        "p2": _normalize_point_name(aspect.get("p2_key") or aspect.get("p2")),
        "o": orb,
    }


def _build_position_lookup(facts: dict, chart_data: dict) -> Dict[str, dict]:
    lookup: Dict[str, dict] = {}
    for position in facts.get("pos", []):
        compact = _compact_position_fact(position)
        name = compact.get("p")
        if name:
            lookup[name] = compact
    for position in chart_data.get("positions", []):
        compact = _compact_position_fact(position)
        name = compact.get("p")
        if name and name not in lookup:
            lookup[name] = compact
    return lookup


def _build_house_lookup(facts: dict, chart_data: dict) -> Dict[int, dict]:
    lookup: Dict[int, dict] = {}
    for house in facts.get("houses", []):
        compact = _compact_house_fact(house)
        house_id = compact.get("h")
        if isinstance(house_id, int):
            lookup[house_id] = compact
    for house in chart_data.get("houses", []):
        compact = _compact_house_fact(house)
        house_id = compact.get("h")
        if isinstance(house_id, int) and house_id not in lookup:
            lookup[house_id] = compact
    return lookup


def _collect_section_aspects(chart_data: dict, point_names: List[str], limit: int) -> List[dict]:
    aspect_points = {_normalize_point_name(name) for name in (point_names or [])}
    items: List[dict] = []
    for aspect in chart_data.get("aspects", []):
        p1 = _normalize_point_name(aspect.get("p1_key") or aspect.get("p1"))
        p2 = _normalize_point_name(aspect.get("p2_key") or aspect.get("p2"))
        if aspect_points and p1 not in aspect_points and p2 not in aspect_points:
            continue
        items.append(_compact_aspect_fact(aspect))
    items.sort(key=lambda aspect: aspect.get("o", 99.0))
    return items[:limit] if limit else items


def _collect_section_patterns(chart_data: dict, point_names: List[str]) -> List[dict]:
    point_set = {_normalize_point_name(name) for name in (point_names or [])}
    patterns: List[dict] = []
    for pattern in chart_data.get("patterns", []):
        points = [
            _normalize_point_name(point)
            for point in (pattern.get("point_keys") or pattern.get("points", []))
        ]
        if point_set and not any(point in point_set for point in points):
            continue
        patterns.append({
            "type": pattern.get("type"),
            "points": points,
        })
    return patterns


def _build_section_chart_pack(rule: dict, chart_data: dict) -> dict:
    position_names = _unique_preserve_order(rule.get("positions", []))
    house_numbers = _unique_preserve_order(rule.get("houses", []))
    aspect_points = _unique_preserve_order(rule.get("aspect_points", position_names))
    aspect_limit = int(rule.get("aspect_limit", 0) or 0)

    positions = []
    for position in chart_data.get("positions", []):
        normalized_name = _normalize_point_name(position.get("key") or position.get("name"))
        if position_names and normalized_name not in position_names:
            continue
        normalized_position = copy.deepcopy(position)
        if normalized_name:
            normalized_position["name"] = normalized_name
        positions.append(normalized_position)

    houses = []
    for house in chart_data.get("houses", []):
        if house_numbers and house.get("house") not in house_numbers:
            continue
        houses.append(copy.deepcopy(house))

    chart_pack: Dict[str, Any] = {
        "house_system": chart_data.get("house_system"),
        "datetime_utc": chart_data.get("datetime_utc"),
        "datetime_local": chart_data.get("datetime_local"),
        "location": copy.deepcopy(chart_data.get("location", {})),
    }
    if positions:
        chart_pack["positions"] = positions
    if houses:
        chart_pack["houses"] = houses

    aspects = _collect_section_aspects(chart_data, aspect_points, aspect_limit)
    if aspects:
        chart_pack["aspects"] = aspects

    if rule.get("include_patterns"):
        patterns = _collect_section_patterns(chart_data, position_names)
        if patterns:
            chart_pack["patterns"] = patterns

    if rule.get("include_balance") and chart_data.get("balances"):
        chart_pack["balances"] = copy.deepcopy(chart_data.get("balances"))

    return chart_pack


def _score_to_int(value: Any, fallback: int = 50) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = fallback
    return max(0, min(100, score))


def _append_unique(items: List[str], *values: Optional[str]) -> None:
    for value in values:
        if value and value not in items:
            items.append(value)


def _new_rank_item(key: str, label: str) -> Dict[str, Any]:
    return {"key": key, "label": label, "score": 0, "evidence": []}


def _bump_rank(
    bucket: Dict[str, Dict[str, Any]],
    key: str,
    delta: int,
    *evidence: Optional[str],
) -> None:
    item = bucket[key]
    item["score"] += delta
    _append_unique(item["evidence"], *evidence)


def _finalize_ranked(
    bucket: Dict[str, Dict[str, Any]],
    *,
    limit: int,
) -> List[Dict[str, Any]]:
    ranked = sorted(
        bucket.values(),
        key=lambda item: (item.get("score", 0), len(item.get("evidence", []))),
        reverse=True,
    )
    selected = ranked[:limit]
    for item in selected:
        item["score"] = _score_to_int(item.get("score", 0), fallback=0)
        item["evidence"] = item.get("evidence", [])[:4]
    return selected


def _pick_primary_ranked(
    bucket: Dict[str, Dict[str, Any]],
    *,
    fallback_key: str,
    fallback_label: str,
    fallback_evidence: Optional[List[str]] = None,
) -> Dict[str, Any]:
    ranked = _finalize_ranked(bucket, limit=1)
    if ranked and ranked[0].get("score", 0) > 0:
        return ranked[0]
    evidence: List[str] = []
    _append_unique(evidence, *(fallback_evidence or []))
    return {
        "key": fallback_key,
        "label": fallback_label,
        "score": 50,
        "evidence": evidence[:4],
    }


def _get_balance_snapshot(facts: dict, chart_data: dict) -> dict:
    return copy.deepcopy(facts.get("balance") or chart_data.get("balances") or {})


def _balance_value(balance: dict, family: str, key: str) -> int:
    return _score_to_int((balance.get(family) or {}).get(key, 0), fallback=0)


def _format_balance_evidence(balance: dict, family: str, key: str) -> Optional[str]:
    value = (balance.get(family) or {}).get(key)
    if value is None:
        return None
    ru_family = "стихия" if family == "elements" else "модальность"
    ru_key_map = {
        "Fire": "Огонь",
        "Earth": "Земля",
        "Air": "Воздух",
        "Water": "Вода",
        "Cardinal": "Кардинальность",
        "Fixed": "Фиксированность",
        "Mutable": "Мутабельность",
    }
    ru_key = ru_key_map.get(key, key)
    return f"{ru_family}: {ru_key} {value}%"


def _rank_balance_family(balance: dict, family: str, keys: List[str]) -> List[Dict[str, Any]]:
    ranked = []
    for key in keys:
        ranked.append(
            {
                "key": key,
                "score": _balance_value(balance, family, key),
                "evidence": [_format_balance_evidence(balance, family, key)],
            }
        )
    ranked.sort(key=lambda item: item.get("score", 0), reverse=True)
    return ranked


def _format_position_evidence(position: Optional[dict]) -> Optional[str]:
    if not position:
        return None
    name = position.get("key") or position.get("p") or position.get("name")
    sign = position.get("s") or position.get("sign")
    house = position.get("h", position.get("house"))
    retro = bool(position.get("r", position.get("is_retrograde", False)))
    parts = [RU_PLANET_NAMES.get(name, name or "Точка")]
    if sign:
        parts.append(f"в {RU_SIGNS_PLAIN.get(sign, sign)}")
    if house:
        parts.append(f"дом {house}")
    if retro:
        parts.append("ретро")
    return ", ".join(parts)


def _format_aspect_evidence(aspect: Optional[dict]) -> Optional[str]:
    if not aspect:
        return None
    p1_key = _normalize_point_name(aspect.get("p1_key") or aspect.get("p1"))
    p2_key = _normalize_point_name(aspect.get("p2_key") or aspect.get("p2"))
    p1 = RU_PLANET_NAMES.get(p1_key, p1_key or "")
    p2 = RU_PLANET_NAMES.get(p2_key, p2_key or "")
    aspect_type = RU_ASPECTS.get(aspect.get("t"), aspect.get("t") or "аспект")
    orb = aspect.get("o")
    orb_text = f" ({orb}°)" if orb is not None else ""
    return f"{p1} {aspect_type} {p2}{orb_text}"


def _get_point(position_lookup: Dict[str, dict], *names: str) -> Optional[dict]:
    for name in names:
        if name in position_lookup:
            return position_lookup[name]
    return None


def _find_aspect(chart_data: dict, first: str, second: str) -> Optional[dict]:
    first = _normalize_point_name(first)
    second = _normalize_point_name(second)
    for aspect in chart_data.get("aspects", []):
        points = {
            _normalize_point_name(aspect.get("p1_key") or aspect.get("p1")),
            _normalize_point_name(aspect.get("p2_key") or aspect.get("p2")),
        }
        if {first, second} == points:
            return _compact_aspect_fact(aspect)
    return None


def _is_harmonious(aspect: Optional[dict]) -> bool:
    return bool(aspect and aspect.get("t") in {"trine", "sextile"})


def _is_tense(aspect: Optional[dict]) -> bool:
    return bool(aspect and aspect.get("t") in {"square", "opposition"})


def _sign_in(position: Optional[dict], signs: set[str]) -> bool:
    return bool(position and position.get("s") in signs)


def _house_in(position: Optional[dict], houses: set[int]) -> bool:
    house = position.get("h") if position else None
    return isinstance(house, int) and house in houses


def _count_points_in_houses(
    position_lookup: Dict[str, dict],
    houses: set[int],
    point_names: Optional[List[str]] = None,
) -> int:
    names = point_names or list(position_lookup.keys())
    total = 0
    for name in names:
        position = position_lookup.get(name)
        if _house_in(position, houses):
            total += 1
    return total


def _build_house_snapshot(
    house_lookup: Dict[int, dict],
    position_lookup: Dict[str, dict],
    house_number: int,
) -> Optional[Dict[str, Any]]:
    house = house_lookup.get(house_number)
    if not house:
        return None
    sign = house.get("s")
    ruler = SIGN_RULER_MAP.get(sign)
    ruler_position = position_lookup.get(ruler) if ruler else None
    return {
        "house": house_number,
        "sign": sign,
        "ruler": ruler,
        "ruler_position": ruler_position,
    }


def _format_house_snapshot(snapshot: Optional[dict]) -> Optional[str]:
    if not snapshot:
        return None
    sign = RU_SIGNS_PLAIN.get(snapshot.get("sign"), snapshot.get("sign") or "?")
    ruler = RU_PLANET_NAMES.get(snapshot.get("ruler"), snapshot.get("ruler") or "?")
    ruler_position = snapshot.get("ruler_position") or {}
    if ruler_position:
        ruler_sign = RU_SIGNS_PLAIN.get(ruler_position.get("s"), ruler_position.get("s") or "?")
        ruler_house = ruler_position.get("h")
        return (
            f"{snapshot.get('house')} дом в {sign}, "
            f"управитель {ruler} в {ruler_sign}, дом {ruler_house}"
        )
    return f"{snapshot.get('house')} дом в {sign}, управитель {ruler}"


def _build_executive_summary_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    balance = _get_balance_snapshot(facts, chart_data)
    earth = _balance_value(balance, "elements", "Earth")
    water = _balance_value(balance, "elements", "Water")
    air = _balance_value(balance, "elements", "Air")
    fire = _balance_value(balance, "elements", "Fire")
    cardinal = _balance_value(balance, "modes", "Cardinal")

    sun = position_lookup.get("Sun")
    moon = position_lookup.get("Moon")
    mercury = position_lookup.get("Mercury")
    venus = position_lookup.get("Venus")
    mars = position_lookup.get("Mars")
    jupiter = position_lookup.get("Jupiter")
    saturn = position_lookup.get("Saturn")
    uranus = position_lookup.get("Uranus")
    neptune = position_lookup.get("Neptune")
    pluto = position_lookup.get("Pluto")
    asc = position_lookup.get("ASC")
    mc = position_lookup.get("MC")

    sun_saturn = _find_aspect(chart_data, "Sun", "Saturn")
    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")
    moon_jupiter = _find_aspect(chart_data, "Moon", "Jupiter")
    uranus_jupiter = _find_aspect(chart_data, "Uranus", "Jupiter")
    venus_mars = _find_aspect(chart_data, "Venus", "Mars")
    saturn_pluto = _find_aspect(chart_data, "Saturn", "Pluto")

    house2 = _build_house_snapshot(house_lookup, position_lookup, 2)
    house7 = _build_house_snapshot(house_lookup, position_lookup, 7)
    house10 = _build_house_snapshot(house_lookup, position_lookup, 10)

    strengths = {
        "structured_ambition": _new_rank_item(
            "structured_ambition",
            "структура, амбиция и умение держать высокий стандарт",
        ),
        "intuitive_depth": _new_rank_item(
            "intuitive_depth",
            "эмпатия, интуиция и чувство подводных процессов",
        ),
        "independent_innovation": _new_rank_item(
            "independent_innovation",
            "самостоятельность, свежий взгляд и способность обновлять правила",
        ),
        "resilient_influence": _new_rank_item(
            "resilient_influence",
            "стойкость в кризисах и влияние в сложных ситуациях",
        ),
    }
    risks = {
        "overcontrol_and_pressure": _new_rank_item(
            "overcontrol_and_pressure",
            "самопрессинг, перегруз и жесткость к себе",
        ),
        "emotional_withdrawal": _new_rank_item(
            "emotional_withdrawal",
            "привычка уходить в дистанцию вместо раннего разговора",
        ),
        "idealization_and_blur": _new_rank_item(
            "idealization_and_blur",
            "идеализация, размытые границы и неверная оценка ресурса",
        ),
        "stability_vs_freedom_swings": _new_rank_item(
            "stability_vs_freedom_swings",
            "качели между безопасной базой и резкими разворотами",
        ),
    }
    relationship_themes = {
        "freedom_plus_depth": _new_rank_item(
            "freedom_plus_depth",
            "в отношениях нужны свобода, дружеская база и при этом настоящая глубина",
        ),
        "safety_before_merging": _new_rank_item(
            "safety_before_merging",
            "близость раскрывается через безопасность, бережный темп и право не спешить",
        ),
        "shared_mission": _new_rank_item(
            "shared_mission",
            "сильнее всего работает союз, где есть общая цель и общий маршрут",
        ),
        "clear_honesty": _new_rank_item(
            "clear_honesty",
            "ключ к отношениям в прямом разговоре и ясных договоренностях",
        ),
    }
    money_themes = {
        "long_game_builder": _new_rank_item(
            "long_game_builder",
            "деньги лучше всего приходят через длинную стратегию, систему и репутацию",
        ),
        "network_value_creator": _new_rank_item(
            "network_value_creator",
            "доход усиливается через связи, сообщества, аудитории и современные форматы",
        ),
        "care_and_usefulness": _new_rank_item(
            "care_and_usefulness",
            "ресурс приходит там, где есть полезность, удержание и забота о людях",
        ),
        "crisis_strategy": _new_rank_item(
            "crisis_strategy",
            "финансовый ресурс включается в сложных задачах, трансформациях и работе с риском",
        ),
    }

    if _house_in(sun, {10}):
        _bump_rank(strengths, "structured_ambition", 18, _format_position_evidence(sun))
        _bump_rank(risks, "overcontrol_and_pressure", 12, _format_position_evidence(sun))
    if _house_in(saturn, {10}):
        _bump_rank(strengths, "structured_ambition", 18, _format_position_evidence(saturn))
        _bump_rank(risks, "overcontrol_and_pressure", 14, _format_position_evidence(saturn))
    if _house_in(mc, {10}) or _sign_in(mc, {"Capricorn"}):
        _bump_rank(strengths, "structured_ambition", 10, _format_position_evidence(mc))
        _bump_rank(money_themes, "long_game_builder", 12, _format_position_evidence(mc))
    if earth >= 35:
        evidence = _format_balance_evidence(balance, "elements", "Earth")
        _bump_rank(strengths, "structured_ambition", 12, evidence)
        _bump_rank(money_themes, "long_game_builder", 10, evidence)
        _bump_rank(risks, "overcontrol_and_pressure", 8, evidence)
    if cardinal >= 45:
        evidence = _format_balance_evidence(balance, "modes", "Cardinal")
        _bump_rank(strengths, "structured_ambition", 8, evidence)
        _bump_rank(risks, "stability_vs_freedom_swings", 8, evidence)
    if sun_saturn:
        evidence = _format_aspect_evidence(sun_saturn)
        _bump_rank(strengths, "structured_ambition", 16, evidence)
        _bump_rank(risks, "overcontrol_and_pressure", 16, evidence)
    if _sign_in(moon, {"Cancer", "Scorpio", "Pisces"}) or _house_in(moon, {8, 12}):
        evidence = _format_position_evidence(moon)
        _bump_rank(strengths, "intuitive_depth", 18, evidence)
        _bump_rank(relationship_themes, "safety_before_merging", 16, evidence)
        _bump_rank(risks, "emotional_withdrawal", 14, evidence)
    if water >= 30:
        evidence = _format_balance_evidence(balance, "elements", "Water")
        _bump_rank(strengths, "intuitive_depth", 10, evidence)
        _bump_rank(risks, "idealization_and_blur", 8, evidence)
    if moon_jupiter and _is_harmonious(moon_jupiter):
        evidence = _format_aspect_evidence(moon_jupiter)
        _bump_rank(strengths, "intuitive_depth", 12, evidence)
        _bump_rank(money_themes, "care_and_usefulness", 10, evidence)
    if _sign_in(venus, {"Aquarius", "Gemini", "Libra"}) or _house_in(venus, {11}):
        evidence = _format_position_evidence(venus)
        _bump_rank(strengths, "independent_innovation", 14, evidence)
        _bump_rank(relationship_themes, "freedom_plus_depth", 15, evidence)
        _bump_rank(money_themes, "network_value_creator", 12, evidence)
        _bump_rank(risks, "emotional_withdrawal", 8, evidence)
    if _sign_in(asc, {"Aries"}) or _sign_in(mars, {"Aries", "Sagittarius", "Aquarius"}):
        evidence = _format_position_evidence(mars) or _format_position_evidence(asc)
        _bump_rank(strengths, "independent_innovation", 10, evidence)
        _bump_rank(relationship_themes, "clear_honesty", 10, evidence)
        _bump_rank(risks, "stability_vs_freedom_swings", 8, evidence)
    if uranus and (_house_in(uranus, {1, 10, 11}) or _sign_in(uranus, {"Aquarius"})):
        evidence = _format_position_evidence(uranus)
        _bump_rank(strengths, "independent_innovation", 10, evidence)
        _bump_rank(money_themes, "network_value_creator", 8, evidence)
    if _house_in(pluto, {7, 8}) or _house_in(mars, {8}):
        evidence = _format_position_evidence(pluto) or _format_position_evidence(mars)
        _bump_rank(strengths, "resilient_influence", 14, evidence)
        _bump_rank(relationship_themes, "freedom_plus_depth", 12, evidence)
        _bump_rank(money_themes, "crisis_strategy", 12, evidence)
    if saturn_pluto and saturn_pluto.get("t") in {"sextile", "trine", "conjunction"}:
        evidence = _format_aspect_evidence(saturn_pluto)
        _bump_rank(strengths, "resilient_influence", 14, evidence)
        _bump_rank(money_themes, "crisis_strategy", 8, evidence)
    if sun_neptune:
        evidence = _format_aspect_evidence(sun_neptune)
        _bump_rank(strengths, "intuitive_depth", 8, evidence)
        _bump_rank(risks, "idealization_and_blur", 18, evidence)
    if _sign_in(moon, {"Pisces"}) or _house_in(neptune, {10, 12}):
        evidence = _format_position_evidence(moon) or _format_position_evidence(neptune)
        _bump_rank(risks, "idealization_and_blur", 10, evidence)
    if uranus_jupiter and _is_tense(uranus_jupiter):
        evidence = _format_aspect_evidence(uranus_jupiter)
        _bump_rank(risks, "stability_vs_freedom_swings", 18, evidence)
        _bump_rank(strengths, "independent_innovation", 8, evidence)
    if venus_mars and _is_harmonious(venus_mars):
        evidence = _format_aspect_evidence(venus_mars)
        _bump_rank(relationship_themes, "freedom_plus_depth", 8, evidence)
        _bump_rank(relationship_themes, "clear_honesty", 6, evidence)
    if venus and venus.get("r"):
        evidence = _format_position_evidence(venus)
        _bump_rank(risks, "emotional_withdrawal", 10, evidence)
    if house7:
        _bump_rank(relationship_themes, "shared_mission", 6, _format_house_snapshot(house7))
    if house10:
        _bump_rank(money_themes, "long_game_builder", 10, _format_house_snapshot(house10))
    if house2:
        snapshot_evidence = _format_house_snapshot(house2)
        _bump_rank(money_themes, "long_game_builder", 6, snapshot_evidence)
        if (house2.get("ruler_position") or {}).get("h") == 11:
            _bump_rank(money_themes, "network_value_creator", 12, snapshot_evidence)
        if (house2.get("ruler_position") or {}).get("h") == 8:
            _bump_rank(money_themes, "crisis_strategy", 12, snapshot_evidence)

    strengths_score = _finalize_ranked(strengths, limit=2)
    risk_score = _finalize_ranked(risks, limit=2)
    relationship_theme = _pick_primary_ranked(
        relationship_themes,
        fallback_key="clear_honesty",
        fallback_label="ключ к отношениям в прямом разговоре и ясных договоренностях",
        fallback_evidence=[
            _format_position_evidence(venus),
            _format_position_evidence(moon),
        ],
    )
    money_theme = _pick_primary_ranked(
        money_themes,
        fallback_key="long_game_builder",
        fallback_label="деньги лучше всего приходят через длинную стратегию, систему и репутацию",
        fallback_evidence=[
            _format_house_snapshot(house10),
            _format_position_evidence(saturn),
        ],
    )

    top_risk = risk_score[0]["key"] if risk_score else ""
    if top_risk == "overcontrol_and_pressure":
        development_label = "снижать внутренний прессинг и раньше замечать свои чувства, усталость и пределы"
        development_key = "soften_pressure_with_self_contact"
    elif top_risk == "idealization_and_blur":
        development_label = "проверять большие цели и сильные чувства фактами, сроками и режимом"
        development_key = "ground_vision_in_facts"
    elif top_risk == "stability_vs_freedom_swings":
        development_label = "сначала собирать базу и ритм, а уже потом делать резкие повороты"
        development_key = "stabilize_before_pivot"
    else:
        development_label = "не уходить в дистанцию: переводить напряжение в разговор и конкретные договоренности"
        development_key = "speak_before_withdrawal"

    development_focus = {
        "key": development_key,
        "label": development_label,
        "score": _score_to_int(
            (
                (risk_score[0]["score"] if risk_score else 55)
                + (strengths_score[0]["score"] if strengths_score else 55)
            )
            / 2
        ),
        "evidence": [
            *(risk_score[0]["evidence"][:2] if risk_score else []),
            *(strengths_score[0]["evidence"][:2] if strengths_score else []),
        ][:4],
    }

    top_strength = strengths_score[0] if strengths_score else {}
    top_risk_item = risk_score[0] if risk_score else {}
    strength_key = top_strength.get("key", "")
    risk_key = top_risk_item.get("key", "")
    relationship_key = relationship_theme.get("key", "")
    money_key = money_theme.get("key", "")

    strength_life_map = {
        "structured_ambition": "в жизни это выглядит как привычка брать на себя каркас, держать стандарт и собирать хаос в систему",
        "intuitive_depth": "в жизни это проявляется как раннее считывание подтекста, настроения и скрытых развилок",
        "independent_innovation": "в жизни это видно в нежелании жить по чужой схеме и в умении находить собственный ход",
        "resilient_influence": "в жизни это заметно в способности не разваливаться в кризисе, а собирать из него рычаг влияния",
    }
    relationship_manifestation_map = {
        "freedom_plus_depth": "в отношениях притягивают люди, с которыми можно и дышать свободно, и нырять глубоко без поверхностной игры",
        "safety_before_merging": "в отношениях всё раскрывается не быстро, а через ощущение безопасности, права на паузу и бережный темп",
        "shared_mission": "в отношениях сильнее всего включается союз, где есть общий маршрут, проект или ощущение совместной сборки будущего",
        "clear_honesty": "в отношениях лучше всего работает прямота: недосказанность быстро съедает энергию и доверие",
    }
    career_manifestation_map = {
        "long_game_builder": "в работе и деньгах лучший результат приходит там, где можно строить долго, накапливать репутацию и не жить только быстрым дофамином",
        "network_value_creator": "в карьере и деньгах ресурс включается через связи, среду, аудиторию и современные гибкие форматы",
        "care_and_usefulness": "в карьере и деньгах выигрыш идёт через полезность, удержание качества и реальную заботу о людях или процессе",
        "crisis_strategy": "в карьере и деньгах сила раскрывается, когда нужно разбирать сложность, риски и то, где другим некомфортно",
    }
    stress_manifestation_map = {
        "overcontrol_and_pressure": "под стрессом всё сжимается в режим внутреннего менеджера: больше контроля, меньше воздуха и почти нулевая терпимость к ошибке",
        "emotional_withdrawal": "под стрессом контакт гаснет раньше слов: становится проще исчезнуть внутрь себя, чем обозначить потребность прямо",
        "idealization_and_blur": "под стрессом растёт туман: хочется верить в красивую картину, игнорируя реальные сроки, границы и цену",
        "stability_vs_freedom_swings": "под стрессом включаются качели: сначала терпеть слишком долго, а потом резко переворачивать стол и маршрут",
    }
    trigger_map = {
        "overcontrol_and_pressure": ["высокая ставка", "слишком много ответственности", "ощущение, что ошибаться нельзя"],
        "emotional_withdrawal": ["неясные договоренности", "чувство небезопасности", "страх быть неправильно понятым"],
        "idealization_and_blur": ["слишком красивое обещание", "эмоционально заряженный образ", "отсутствие четких критериев"],
        "stability_vs_freedom_swings": ["долгое накопление скуки", "ощущение клетки", "внезапная тяга всё изменить одним рывком"],
    }
    sabotage_map = {
        "overcontrol_and_pressure": "самосаботаж идёт через привычку сначала пережать себя, а потом терять живую энергию и контакт с реальным состоянием",
        "emotional_withdrawal": "самосаботаж идёт через молчаливую дистанцию: важное не озвучивается вовремя и постепенно превращается в отчуждение",
        "idealization_and_blur": "самосаботаж идёт через красивую фантазию без достаточной проверки фактами, цифрами и режимом",
        "stability_vs_freedom_swings": "самосаботаж идёт через крайности: сначала удерживать слишком долго, потом ломать слишком резко",
    }
    compensation_map = {
        "overcontrol_and_pressure": "компенсация чаще всего выглядит как ещё большее ужесточение режима, требований и самоконтроля",
        "emotional_withdrawal": "компенсация чаще всего выглядит как уход в самостоятельность и демонстрацию, что помощь и разговор не нужны",
        "idealization_and_blur": "компенсация чаще всего выглядит как вера, что вдохновение и правильное чувство сами всё решат",
        "stability_vs_freedom_swings": "компенсация чаще всего выглядит как резкая смена курса вместо постепенной перенастройки",
    }
    do_map = {
        "structured_ambition": ["держать длинный горизонт", "снижать внутренний прессинг раньше перегруза", "назначать себе ясные критерии завершения"],
        "intuitive_depth": ["проверять ощущения фактами", "давать чувствам язык, а не только тишину", "оставлять место для восстановления"],
        "independent_innovation": ["сначала тестировать поворот на малом масштабе", "сохранять право на свой ход без разрушения базы", "искать среду, где идеи можно быстро проверять"],
        "resilient_influence": ["работать с кризисом дозированно", "переводить давление в стратегию", "не путать силу с постоянной перегрузкой"],
    }
    not_do_map = {
        "overcontrol_and_pressure": ["не принимать ключевые решения в пике самопрессинга", "не путать дисциплину с самонаказанием"],
        "emotional_withdrawal": ["не ждать, пока другой сам догадается", "не превращать паузу в исчезновение"],
        "idealization_and_blur": ["не соглашаться на красивый туман без критериев", "не строить всё на вдохновении без режима"],
        "stability_vs_freedom_swings": ["не делать резкий разворот без базы", "не терпеть слишком долго только ради видимой стабильности"],
    }
    best_mode_map = {
        "structured_ambition": "лучший режим действия — длинная стратегия, ясный каркас и ранняя коррекция перегруза",
        "intuitive_depth": "лучший режим действия — сначала почувствовать тон процесса, затем приземлить это в конкретный шаг",
        "independent_innovation": "лучший режим действия — короткие экспериментальные циклы поверх сохраненной опоры",
        "resilient_influence": "лучший режим действия — брать сложные узлы по одному и сразу превращать давление в структуру",
    }

    life_manifestations = [
        {
            "domain": "daily_life",
            "label": strength_life_map.get(strength_key, top_strength.get("label", "")),
            "evidence": top_strength.get("evidence", [])[:3],
        },
        {
            "domain": "relationships",
            "label": relationship_manifestation_map.get(relationship_key, relationship_theme.get("label", "")),
            "evidence": relationship_theme.get("evidence", [])[:3],
        },
        {
            "domain": "career",
            "label": career_manifestation_map.get(money_key, money_theme.get("label", "")),
            "evidence": money_theme.get("evidence", [])[:3],
        },
    ]
    stress_manifestation = {
        "key": f"{risk_key}_stress",
        "label": stress_manifestation_map.get(risk_key, top_risk_item.get("label", "")),
        "triggers": trigger_map.get(risk_key, []),
        "evidence": top_risk_item.get("evidence", [])[:4],
    }
    self_sabotage_pattern = {
        "key": f"{risk_key}_self_sabotage",
        "label": sabotage_map.get(risk_key, top_risk_item.get("label", "")),
        "evidence": top_risk_item.get("evidence", [])[:4],
    }
    compensation_pattern = {
        "key": f"{risk_key}_compensation",
        "label": compensation_map.get(risk_key, development_focus.get("label", "")),
        "evidence": [
            *(top_risk_item.get("evidence", [])[:2]),
            *(development_focus.get("evidence", [])[:2]),
        ][:4],
    }
    what_to_do = {
        "items": [
            *do_map.get(strength_key, []),
            development_focus.get("label"),
        ][:4],
        "evidence": development_focus.get("evidence", [])[:4],
    }
    what_not_to_do = {
        "items": not_do_map.get(risk_key, [])[:3],
        "evidence": top_risk_item.get("evidence", [])[:3],
    }
    best_mode_of_action = {
        "key": f"{strength_key or 'steady'}_best_mode",
        "label": best_mode_map.get(strength_key, development_focus.get("label", "")),
        "evidence": [
            *(top_strength.get("evidence", [])[:2]),
            *(money_theme.get("evidence", [])[:2]),
        ][:4],
    }
    scene_seeds = [
        {
            "title": "рабочая сцена",
            "seed": (
                "человек, который первым собирает задачу в систему, но рискует взять на себя лишний вес и слишком долго держать всё на личной воле"
                if strength_key == "structured_ambition"
                else "человек, который быстро чувствует, где скрытый узел, но под стрессом может уйти в перегруз, туман или дистанцию"
            ),
        },
        {
            "title": "личная сцена",
            "seed": relationship_manifestation_map.get(
                relationship_key,
                "в близости важнее всего не сама интенсивность, а то, насколько рано удаётся назвать потребность и границу",
            ),
        },
    ]

    return {
        "version": "natal_v2_p0",
        "strengths_score": strengths_score,
        "risk_score": risk_score,
        "relationship_theme": relationship_theme,
        "money_theme": money_theme,
        "development_focus": development_focus,
        "life_manifestations": life_manifestations,
        "stress_manifestation": stress_manifestation,
        "self_sabotage_pattern": self_sabotage_pattern,
        "compensation_pattern": compensation_pattern,
        "what_to_do": what_to_do,
        "what_not_to_do": what_not_to_do,
        "best_mode_of_action": best_mode_of_action,
        "scene_seeds": scene_seeds,
        "cross_links": [
            "synthesis.identity_vector",
            "love_intimacy.attachment_style",
            "money_realization.career_vector",
        ],
    }


def _build_synthesis_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    executive_pack = _build_executive_summary_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    strengths = executive_pack.get("strengths_score", [])
    risks = executive_pack.get("risk_score", [])

    primary_strength = strengths[0] if strengths else {}
    secondary_strength = strengths[1] if len(strengths) > 1 else primary_strength
    primary_risk = risks[0] if risks else {}

    primary_key = primary_strength.get("key")
    secondary_key = secondary_strength.get("key")
    risk_key = primary_risk.get("key")

    if primary_key == "structured_ambition" and secondary_key == "intuitive_depth":
        identity_key = "structured_sensitive_strategist"
        identity_label = "структурный стратег: снаружи строишь каркас, внутри считываешь тонкие процессы"
    elif primary_key == "structured_ambition" and secondary_key == "independent_innovation":
        identity_key = "system_reformer"
        identity_label = "системный реформатор: умеешь держать порядок и одновременно обновлять правила"
    elif primary_key == "intuitive_depth":
        identity_key = "deep_sensor"
        identity_label = "глубокий чувствующий наблюдатель, который видит скрытые мотивы и связи"
    else:
        identity_key = "steady_transformer"
        identity_label = "устойчивый трансформатор: собираешь сложность в рабочую систему"

    if risk_key == "overcontrol_and_pressure" and secondary_key == "intuitive_depth":
        conflict_key = "control_vs_sensitivity"
        conflict_label = "между контролем, высоким стандартом и необходимостью не подавлять чувствительность"
    elif risk_key == "stability_vs_freedom_swings":
        conflict_key = "stability_vs_freedom"
        conflict_label = "между безопасной базой и желанием резко менять траекторию"
    elif risk_key == "emotional_withdrawal":
        conflict_key = "depth_vs_distance"
        conflict_label = "между потребностью в глубине и привычкой уходить в дистанцию или молчание"
    else:
        conflict_key = "vision_vs_grounding"
        conflict_label = "между большим образом, интуицией и требованием к конкретике"

    identity_vector = {
        "key": identity_key,
        "label": identity_label,
        "score": _score_to_int(
            (
                primary_strength.get("score", 55)
                + secondary_strength.get("score", primary_strength.get("score", 55))
            )
            / 2
        ),
        "evidence": [
            *(primary_strength.get("evidence", [])[:2]),
            *(secondary_strength.get("evidence", [])[:2]),
        ][:4],
    }
    core_conflict = {
        "key": conflict_key,
        "label": conflict_label,
        "score": _score_to_int(primary_risk.get("score", 55)),
        "evidence": primary_risk.get("evidence", [])[:4],
    }

    drive_labels = {
        "structured_ambition": "мастерство, результат и высокий стандарт",
        "intuitive_depth": "смысл, эмоциональная правда и чувствительность к невидимому",
        "independent_innovation": "свобода, эксперимент и право идти своим маршрутом",
        "resilient_influence": "влияние, глубина и работа со сложностью",
    }
    dominant_drives = []
    for strength in strengths[:3]:
        dominant_drives.append(
            {
                "key": strength.get("key"),
                "label": drive_labels.get(strength.get("key"), strength.get("label")),
                "score": strength.get("score", 50),
                "evidence": strength.get("evidence", [])[:3],
            }
        )
    if not dominant_drives:
        dominant_drives.append(
            {
                "key": "steady_growth",
                "label": "рост через устойчивость и последовательность",
                "score": 50,
                "evidence": [],
            }
        )

    if identity_key == "structured_sensitive_strategist":
        metaphor_label = "высокая опорная башня с внутренним радаром глубины"
        metaphor_keywords = ["каркас", "высота", "скрытая чувствительность"]
    elif identity_key == "system_reformer":
        metaphor_label = "диспетчер сложной системы, который обновляет правила без потери каркаса"
        metaphor_keywords = ["система", "обновление", "маршрут"]
    elif identity_key == "deep_sensor":
        metaphor_label = "тихий глубинный локатор, который считывает то, что другим не видно"
        metaphor_keywords = ["глубина", "наблюдение", "смысл"]
    else:
        metaphor_label = "человек-каркас, который собирает кризис в рабочую форму"
        metaphor_keywords = ["сборка", "давление", "форма"]

    map_metaphor_seed = {
        "key": f"{identity_key}_seed",
        "label": metaphor_label,
        "keywords": metaphor_keywords,
        "evidence": [
            *(identity_vector.get("evidence", [])[:2]),
            *(core_conflict.get("evidence", [])[:2]),
        ][:4],
    }

    life_story_map = {
        "structured_sensitive_strategist": "сюжет жизни часто строится так: внешне держать каркас, внутри всё время сверяться с тонкими сигналами и скрытыми подводными течениями",
        "system_reformer": "сюжет жизни часто строится так: входить в уже существующую систему, видеть её слабое место и постепенно обновлять правила изнутри",
        "deep_sensor": "сюжет жизни часто строится так: сначала долго считывать глубину и мотив, а потом говорить только то, что реально меняет смысл происходящего",
        "steady_transformer": "сюжет жизни часто строится так: брать сложный, перегретый или запутанный материал и превращать его в рабочую форму",
    }
    conflict_manifestation_map = {
        "control_vs_sensitivity": "внутренний конфликт проявляется в жизни как спор между высоким стандартом и живой чувствительностью: хочется быть сильным и собранным, но нельзя гасить тонкость ради эффективности",
        "stability_vs_freedom": "внутренний конфликт проявляется как качели между опорой и резким разворотом: сначала строить базу, а потом хотеть сбросить её одним движением",
        "depth_vs_distance": "внутренний конфликт проявляется как чередование потребности в глубине и привычки отходить на дистанцию, когда связь становится слишком реальной",
        "vision_vs_grounding": "внутренний конфликт проявляется как напряжение между большим образом, интуицией и необходимостью приземлять всё в срок, ритм и факт",
    }
    triggers_map = {
        "control_vs_sensitivity": ["жёсткий дедлайн", "оценка со стороны", "ощущение, что надо держать лицо"],
        "stability_vs_freedom": ["долгое однообразие", "ощущение клетки", "внезапно открывшаяся новая возможность"],
        "depth_vs_distance": ["слишком близкий разговор", "ожидание эмоциональной прозрачности", "страх показать уязвимость"],
        "vision_vs_grounding": ["красивый большой план без критериев", "неопределенность сроков", "слишком много смыслов и мало формы"],
    }
    sabotage_map = {
        "control_vs_sensitivity": "самосаботаж здесь в том, что контроль начинает подменять контакт с собой и лишает силу живого ресурса",
        "stability_vs_freedom": "самосаботаж здесь в крайностях: либо слишком держать, либо слишком резко ломать",
        "depth_vs_distance": "самосаботаж здесь в том, что потребность в глубине выражается не словами, а исчезновением или молчаливым отступлением",
        "vision_vs_grounding": "самосаботаж здесь в том, что большой образ не получает режима и начинает размывать решение",
    }
    compensation_map = {
        "control_vs_sensitivity": "компенсация идёт через ещё большую собранность, жёсткость и отказ от слабости",
        "stability_vs_freedom": "компенсация идёт через резкий поворот, чтобы не чувствовать накопленное внутреннее сжатие",
        "depth_vs_distance": "компенсация идёт через самоизоляцию, независимость и образ человека, которому никто не нужен",
        "vision_vs_grounding": "компенсация идёт через вдохновляющий образ вместо конкретного следующего шага",
    }
    action_map = {
        "structured_sensitive_strategist": "лучший режим действия — строить каркас, но оставлять внутри него живую обратную связь от тела, чувств и среды",
        "system_reformer": "лучший режим действия — менять не всё сразу, а поэтапно, сохраняя рабочую опору и право на корректировку",
        "deep_sensor": "лучший режим действия — сначала назвать главное скрытое напряжение, потом переводить его в простой и точный шаг",
        "steady_transformer": "лучший режим действия — не бороться со сложностью лоб в лоб, а собирать её в форму, которую можно удерживать долго",
    }

    core_life_story = {
        "key": f"{identity_key}_life_story",
        "label": life_story_map.get(identity_key, identity_label),
        "evidence": identity_vector.get("evidence", [])[:4],
    }
    life_manifestations = [
        {
            "domain": "work",
            "label": (
                "в работе это даёт роль человека, который держит структуру и собирает смысл, даже если другие уже теряют нить"
                if identity_key in {"structured_sensitive_strategist", "steady_transformer"}
                else "в работе это даёт роль человека, который меняет систему или считывает то, что не лежит на поверхности"
            ),
            "evidence": identity_vector.get("evidence", [])[:3],
        },
        {
            "domain": "relationships",
            "label": (
                "в близости это создаёт потребность одновременно в глубине и в возможности не терять автономию"
                if conflict_key in {"depth_vs_distance", "stability_vs_freedom"}
                else "в близости это создаёт запрос на связь, где можно быть и сильным, и живым, не теряя одну часть ради другой"
            ),
            "evidence": core_conflict.get("evidence", [])[:3],
        },
        {
            "domain": "stress",
            "label": conflict_manifestation_map.get(conflict_key, core_conflict.get("label", "")),
            "evidence": core_conflict.get("evidence", [])[:3],
        },
    ]
    inner_conflict_dynamics = {
        "key": f"{conflict_key}_dynamics",
        "label": conflict_manifestation_map.get(conflict_key, core_conflict.get("label", "")),
        "triggers": triggers_map.get(conflict_key, []),
        "evidence": core_conflict.get("evidence", [])[:4],
    }
    self_sabotage_pattern = {
        "key": f"{conflict_key}_self_sabotage",
        "label": sabotage_map.get(conflict_key, core_conflict.get("label", "")),
        "evidence": core_conflict.get("evidence", [])[:4],
    }
    compensation_pattern = {
        "key": f"{conflict_key}_compensation",
        "label": compensation_map.get(conflict_key, identity_vector.get("label", "")),
        "evidence": [
            *(identity_vector.get("evidence", [])[:2]),
            *(core_conflict.get("evidence", [])[:2]),
        ][:4],
    }
    what_to_do = {
        "items": [
            action_map.get(identity_key, "держать смысл и форму одновременно"),
            "переводить внутреннее напряжение в задачу, разговор или конкретный ритм",
            "замечать, где конфликт уже начался, до того как он превратится в судьбу дня или отношений",
        ],
        "evidence": [
            *(identity_vector.get("evidence", [])[:2]),
            *(core_conflict.get("evidence", [])[:2]),
        ][:4],
    }
    what_not_to_do = {
        "items": [
            "не строить жизнь только вокруг своей сильной стороны, выдавливая противоположный полюс",
            "не ждать, что конфликт исчезнет сам, если его долго не называть",
            "не принимать пик внутреннего напряжения за окончательную правду о себе",
        ],
        "evidence": core_conflict.get("evidence", [])[:3],
    }
    best_mode_of_action = {
        "key": f"{identity_key}_best_mode",
        "label": action_map.get(identity_key, identity_vector.get("label", "")),
        "evidence": identity_vector.get("evidence", [])[:4],
    }
    scene_seeds = [
        {
            "title": "внутренняя сцена",
            "seed": conflict_manifestation_map.get(conflict_key, core_conflict.get("label", "")),
        },
        {
            "title": "жизненная сцена",
            "seed": life_story_map.get(identity_key, identity_vector.get("label", "")),
        },
    ]

    return {
        "version": "natal_v2_p0",
        "identity_vector": identity_vector,
        "core_conflict": core_conflict,
        "dominant_drives": dominant_drives,
        "map_metaphor_seed": map_metaphor_seed,
        "core_life_story": core_life_story,
        "life_manifestations": life_manifestations,
        "inner_conflict_dynamics": inner_conflict_dynamics,
        "self_sabotage_pattern": self_sabotage_pattern,
        "compensation_pattern": compensation_pattern,
        "what_to_do": what_to_do,
        "what_not_to_do": what_not_to_do,
        "best_mode_of_action": best_mode_of_action,
        "scene_seeds": scene_seeds,
        "cross_links": [
            "executive_summary.strengths_score",
            "executive_summary.risk_score",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_framework_elements_modes_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    balance = _get_balance_snapshot(facts, chart_data)

    element_rank = _rank_balance_family(balance, "elements", ["Fire", "Earth", "Air", "Water"])
    mode_rank = _rank_balance_family(balance, "modes", ["Cardinal", "Fixed", "Mutable"])

    element_labels = {
        "Fire": "Огонь: энергия старта, воля и импульс к действию",
        "Earth": "Земля: устойчивость, форма и способность опираться на реальность",
        "Air": "Воздух: контакт, идеи и интеллектуальная подвижность",
        "Water": "Вода: чувствительность, интуиция и эмоциональная глубина",
    }
    mode_labels = {
        "Cardinal": "Кардинальность: запуск, инициатива и способность открывать цикл",
        "Fixed": "Фиксированность: удержание, концентрация и инерция",
        "Mutable": "Мутабельность: адаптация, настройка и гибкость",
    }
    combo_labels = {
        ("Fire", "Cardinal"): "темперамент инициатора: быстро загораться, брать старт и вести импульсом",
        ("Earth", "Cardinal"): "темперамент системного организатора: запускать через план, задачу и конструкцию",
        ("Air", "Cardinal"): "темперамент социального стратега: начинать через идеи, контакты и переговоры",
        ("Water", "Cardinal"): "темперамент эмоционального лидера: включаться через чувство значимости и внутренний отклик",
        ("Fire", "Fixed"): "темперамент носителя воли: держать курс мощно, ярко и упрямо",
        ("Earth", "Fixed"): "темперамент стабилизатора: строить надолго, удерживать ресурс и не спешить с разворотом",
        ("Air", "Fixed"): "темперамент концептуального держателя: стоять на идее, принципе и собственной логике",
        ("Water", "Fixed"): "темперамент глубинного хранителя: долго проживать, помнить и эмоционально фиксировать важное",
        ("Fire", "Mutable"): "темперамент подвижного мотора: быстро адаптироваться, но жить с избытком искр и переключений",
        ("Earth", "Mutable"): "темперамент практичного настройщика: улучшать процессы и наводить порядок через детали",
        ("Air", "Mutable"): "темперамент коммуникационного сканера: быстро учиться, связывать и собирать сигналы",
        ("Water", "Mutable"): "темперамент тонкого эмпата: улавливать атмосферу и менять режим по внутренней погоде",
    }
    deficit_advice = {
        "Fire": "добавлять прямой старт, право хотеть и привычку действовать без долгой раскачки",
        "Earth": "добавлять режим, телесную опору, конкретные шаги и финансовую/бытовую структуру",
        "Air": "добавлять разговор, интеллектуальный обмен и возможность смотреть на себя со стороны",
        "Water": "добавлять паузу, чувствительность к состоянию и экологичный контакт с эмоцией",
        "Cardinal": "осознанно тренировать старт и способность самому открывать новый цикл",
        "Fixed": "тренировать выдержку, ритм и навык доводить начатое без лишней суеты",
        "Mutable": "тренировать гибкость, допуск к корректировке и умение менять план без краха самооценки",
    }

    for item in element_rank:
        item["label"] = element_labels.get(item["key"], item["key"])
    for item in mode_rank:
        item["label"] = mode_labels.get(item["key"], item["key"])

    dominant_element = element_rank[0] if element_rank else {"key": "Earth", "score": 0, "evidence": []}
    weakest_element = element_rank[-1] if element_rank else {"key": "Water", "score": 0, "evidence": []}
    dominant_mode = mode_rank[0] if mode_rank else {"key": "Cardinal", "score": 0, "evidence": []}
    weakest_mode = mode_rank[-1] if mode_rank else {"key": "Mutable", "score": 0, "evidence": []}

    dominant_signature = {
        "key": f"{dominant_element['key'].lower()}_{dominant_mode['key'].lower()}",
        "label": combo_labels.get(
            (dominant_element.get("key"), dominant_mode.get("key")),
            "темперамент читается через ведущую стихию и модальность карты",
        ),
        "score": _score_to_int(
            (dominant_element.get("score", 0) + dominant_mode.get("score", 0)) / 2
        ),
        "evidence": [
            *(dominant_element.get("evidence", [])[:2]),
            *(dominant_mode.get("evidence", [])[:2]),
        ][:4],
    }
    deficit_signature = {
        "key": f"{weakest_element['key'].lower()}_{weakest_mode['key'].lower()}_deficit",
        "label": (
            f"зона подпитки — {element_labels.get(weakest_element.get('key'), weakest_element.get('key')).split(':', 1)[0].lower()} "
            f"и {mode_labels.get(weakest_mode.get('key'), weakest_mode.get('key')).split(':', 1)[0].lower()}"
        ),
        "growth": (
            f"{deficit_advice.get(weakest_element.get('key'), 'добавлять недостающую стихию')}; "
            f"{deficit_advice.get(weakest_mode.get('key'), 'добавлять недостающую модальность')}"
        ),
        "evidence": [
            *(weakest_element.get("evidence", [])[:2]),
            *(weakest_mode.get("evidence", [])[:2]),
        ][:4],
    }

    if dominant_mode.get("key") == "Cardinal":
        lifestyle_label = "лучший стиль жизни — запускать циклами, но заранее собирать критерии завершения, иначе энергии будет много, а устойчивости меньше"
    elif dominant_mode.get("key") == "Fixed":
        lifestyle_label = "лучший стиль жизни — строить ритм и долгую опору, а перемены вводить дозированно, чтобы не застревать в инерции"
    else:
        lifestyle_label = "лучший стиль жизни — держать гибкий маршрут, но фиксировать опорные точки, чтобы адаптация не превращалась в распыление"

    balance_formula = {
        "key": "balance_formula",
        "label": (
            f"формула баланса: опираться на {dominant_element.get('key')} + {dominant_mode.get('key')}, "
            f"но регулярно подпитывать {weakest_element.get('key')} и {weakest_mode.get('key')}"
        ),
        "evidence": [
            dominant_signature.get("label"),
            deficit_signature.get("growth"),
        ][:4],
    }
    lifestyle_vector = {
        "key": "lifestyle_vector",
        "label": lifestyle_label,
        "evidence": [
            dominant_signature.get("label"),
            deficit_signature.get("label"),
        ][:4],
    }

    return {
        "version": "natal_v2_p4",
        "element_rank": element_rank,
        "mode_rank": mode_rank,
        "dominant_signature": dominant_signature,
        "deficit_signature": deficit_signature,
        "lifestyle_vector": lifestyle_vector,
        "balance_formula": balance_formula,
        "cross_links": [
            "executive_summary.development_focus",
            "synthesis.identity_vector",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _build_money_realization_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    balance = _get_balance_snapshot(facts, chart_data)
    earth = _balance_value(balance, "elements", "Earth")
    cardinal = _balance_value(balance, "modes", "Cardinal")

    sun = position_lookup.get("Sun")
    venus = position_lookup.get("Venus")
    mars = position_lookup.get("Mars")
    jupiter = position_lookup.get("Jupiter")
    saturn = position_lookup.get("Saturn")
    uranus = position_lookup.get("Uranus")
    neptune = position_lookup.get("Neptune")
    mc = position_lookup.get("MC")

    house2 = _build_house_snapshot(house_lookup, position_lookup, 2)
    house6 = _build_house_snapshot(house_lookup, position_lookup, 6)
    house10 = _build_house_snapshot(house_lookup, position_lookup, 10)

    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")
    saturn_neptune = _find_aspect(chart_data, "Saturn", "Neptune")
    uranus_jupiter = _find_aspect(chart_data, "Uranus", "Jupiter")
    saturn_pluto = _find_aspect(chart_data, "Saturn", "Pluto")

    career_vectors = {
        "systems_leader": _new_rank_item(
            "systems_leader",
            "реализация через систему, управленческий каркас, стандарты и репутацию",
        ),
        "network_builder": _new_rank_item(
            "network_builder",
            "реализация через сообщества, связи, аудитории и современные форматы",
        ),
        "care_container": _new_rank_item(
            "care_container",
            "реализация через полезность, поддержку, удержание и заботу о людях",
        ),
        "crisis_specialist": _new_rank_item(
            "crisis_specialist",
            "реализация через сложные задачи, трансформации и работу с риском",
        ),
    }
    money_patterns = {
        "long_cycle_accumulation": _new_rank_item(
            "long_cycle_accumulation",
            "деньги растут через длинный горизонт, дисциплину и накопление репутации",
        ),
        "networked_income": _new_rank_item(
            "networked_income",
            "доход приходит через связи, проекты с людьми и распределенные каналы",
        ),
        "service_expertise": _new_rank_item(
            "service_expertise",
            "деньги включаются через экспертизу, регулярную полезность и качество процесса",
        ),
        "shared_resources": _new_rank_item(
            "shared_resources",
            "деньги приходят через совместные ресурсы, кризисные задачи и стратегию риска",
        ),
    }
    realization_modes = {
        "disciplined_climb": _new_rank_item(
            "disciplined_climb",
            "лучший режим реализации: длинный подъем, ясный KPI и последовательный рост статуса",
        ),
        "autonomous_project_cycles": _new_rank_item(
            "autonomous_project_cycles",
            "лучший режим реализации: автономные проектные циклы и право быстро принимать решения",
        ),
        "community_platform": _new_rank_item(
            "community_platform",
            "лучший режим реализации: платформа, сеть, аудитория и совместные инициативы",
        ),
        "deep_problem_solving": _new_rank_item(
            "deep_problem_solving",
            "лучший режим реализации: разбирать сложность, кризисы и неоднозначные кейсы",
        ),
    }
    work_risks = {
        "overwork_and_rigidity": _new_rank_item(
            "overwork_and_rigidity",
            "риск: перегруз, внутренний прессинг и жесткость к себе",
        ),
        "blurred_goalposts": _new_rank_item(
            "blurred_goalposts",
            "риск: размытые критерии, идеализация проекта или плохая оценка ресурса",
        ),
        "zigzag_decisions": _new_rank_item(
            "zigzag_decisions",
            "риск: резкие развороты и доходные качели из-за импульсивных смен курса",
        ),
        "value_revisions": _new_rank_item(
            "value_revisions",
            "риск: затяжные пересмотры цены, условий и собственной ценности",
        ),
        "power_drains": _new_rank_item(
            "power_drains",
            "риск: втягиваться в тяжелые силовые игры, кризисы и чужое напряжение",
        ),
    }

    if house10:
        evidence = _format_house_snapshot(house10)
        _bump_rank(career_vectors, "systems_leader", 16, evidence)
        _bump_rank(money_patterns, "long_cycle_accumulation", 10, evidence)
        if house10.get("sign") in {"Aquarius", "Gemini", "Libra"}:
            _bump_rank(career_vectors, "network_builder", 10, evidence)
        if house10.get("sign") in {"Cancer", "Pisces"}:
            _bump_rank(career_vectors, "care_container", 10, evidence)
        if house10.get("sign") in {"Scorpio"}:
            _bump_rank(career_vectors, "crisis_specialist", 10, evidence)
    if house2:
        evidence = _format_house_snapshot(house2)
        _bump_rank(money_patterns, "long_cycle_accumulation", 8, evidence)
        ruler_house = (house2.get("ruler_position") or {}).get("h")
        if ruler_house == 11:
            _bump_rank(money_patterns, "networked_income", 14, evidence)
        if ruler_house == 8:
            _bump_rank(money_patterns, "shared_resources", 14, evidence)
        if ruler_house in {6, 10}:
            _bump_rank(money_patterns, "service_expertise", 12, evidence)
    if house6:
        evidence = _format_house_snapshot(house6)
        _bump_rank(realization_modes, "disciplined_climb", 8, evidence)
        ruler_house = (house6.get("ruler_position") or {}).get("h")
        if ruler_house in {10, 11}:
            _bump_rank(realization_modes, "community_platform", 10, evidence)
        if ruler_house in {8, 12}:
            _bump_rank(realization_modes, "deep_problem_solving", 10, evidence)
        if ruler_house in {1, 9}:
            _bump_rank(realization_modes, "autonomous_project_cycles", 10, evidence)

    if _house_in(sun, {10}) or _house_in(saturn, {10}) or _house_in(mc, {10}):
        evidence = _format_position_evidence(sun) or _format_position_evidence(saturn) or _format_position_evidence(mc)
        _bump_rank(career_vectors, "systems_leader", 16, evidence)
        _bump_rank(realization_modes, "disciplined_climb", 12, evidence)
        _bump_rank(work_risks, "overwork_and_rigidity", 12, evidence)
    if earth >= 35:
        evidence = _format_balance_evidence(balance, "elements", "Earth")
        _bump_rank(career_vectors, "systems_leader", 10, evidence)
        _bump_rank(money_patterns, "long_cycle_accumulation", 10, evidence)
        _bump_rank(realization_modes, "disciplined_climb", 8, evidence)
    if cardinal >= 45:
        evidence = _format_balance_evidence(balance, "modes", "Cardinal")
        _bump_rank(realization_modes, "disciplined_climb", 6, evidence)
        _bump_rank(work_risks, "zigzag_decisions", 6, evidence)
    if _house_in(venus, {11}) or _sign_in(venus, {"Aquarius", "Gemini", "Libra"}):
        evidence = _format_position_evidence(venus)
        _bump_rank(career_vectors, "network_builder", 12, evidence)
        _bump_rank(money_patterns, "networked_income", 14, evidence)
        _bump_rank(realization_modes, "community_platform", 12, evidence)
    if _sign_in(jupiter, {"Cancer", "Pisces"}) or _house_in(jupiter, {4, 12}):
        evidence = _format_position_evidence(jupiter)
        _bump_rank(career_vectors, "care_container", 12, evidence)
        _bump_rank(money_patterns, "service_expertise", 8, evidence)
    if _house_in(mars, {8}) or _house_in(position_lookup.get("Pluto"), {7, 8}):
        evidence = _format_position_evidence(mars) or _format_position_evidence(position_lookup.get("Pluto"))
        _bump_rank(career_vectors, "crisis_specialist", 14, evidence)
        _bump_rank(money_patterns, "shared_resources", 12, evidence)
        _bump_rank(realization_modes, "deep_problem_solving", 10, evidence)
        _bump_rank(work_risks, "power_drains", 10, evidence)
    if saturn_pluto and saturn_pluto.get("t") in {"sextile", "trine", "conjunction"}:
        evidence = _format_aspect_evidence(saturn_pluto)
        _bump_rank(career_vectors, "crisis_specialist", 8, evidence)
        _bump_rank(realization_modes, "deep_problem_solving", 8, evidence)
    if sun_neptune or saturn_neptune:
        evidence = _format_aspect_evidence(sun_neptune) or _format_aspect_evidence(saturn_neptune)
        _bump_rank(work_risks, "blurred_goalposts", 16, evidence)
    if uranus_jupiter and _is_tense(uranus_jupiter):
        evidence = _format_aspect_evidence(uranus_jupiter)
        _bump_rank(work_risks, "zigzag_decisions", 16, evidence)
        _bump_rank(realization_modes, "autonomous_project_cycles", 8, evidence)
    if venus and venus.get("r"):
        evidence = _format_position_evidence(venus)
        _bump_rank(work_risks, "value_revisions", 14, evidence)

    career_vector = _pick_primary_ranked(
        career_vectors,
        fallback_key="systems_leader",
        fallback_label="реализация через систему, управленческий каркас, стандарты и репутацию",
        fallback_evidence=[
            _format_house_snapshot(house10),
            _format_position_evidence(saturn),
        ],
    )
    money_pattern = _pick_primary_ranked(
        money_patterns,
        fallback_key="long_cycle_accumulation",
        fallback_label="деньги растут через длинный горизонт, дисциплину и накопление репутации",
        fallback_evidence=[
            _format_house_snapshot(house2),
            _format_position_evidence(venus),
        ],
    )
    realization_mode = _pick_primary_ranked(
        realization_modes,
        fallback_key="disciplined_climb",
        fallback_label="лучший режим реализации: длинный подъем, ясный KPI и последовательный рост статуса",
        fallback_evidence=[
            _format_house_snapshot(house6),
            _format_position_evidence(sun),
        ],
    )
    work_risk_flags = _finalize_ranked(work_risks, limit=3)

    return {
        "version": "natal_v2_p0",
        "career_vector": career_vector,
        "money_pattern": money_pattern,
        "work_risk_flags": work_risk_flags,
        "realization_mode": realization_mode,
        "cross_links": [
            "executive_summary.money_theme",
            "synthesis.identity_vector",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _build_love_intimacy_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    venus = position_lookup.get("Venus")
    mars = position_lookup.get("Mars")
    moon = position_lookup.get("Moon")
    saturn = position_lookup.get("Saturn")
    pluto = position_lookup.get("Pluto")
    uranus = position_lookup.get("Uranus")

    house5 = _build_house_snapshot(house_lookup, position_lookup, 5)
    house7 = _build_house_snapshot(house_lookup, position_lookup, 7)
    house8 = _build_house_snapshot(house_lookup, position_lookup, 8)

    venus_mars = _find_aspect(chart_data, "Venus", "Mars")
    moon_uranus = _find_aspect(chart_data, "Moon", "Uranus")
    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")

    attachment_styles = {
        "freedom_then_depth": _new_rank_item(
            "freedom_then_depth",
            "привязанность строится через свободу и дружескую базу, но внутри нужна очень глубокая близость",
        ),
        "soft_private_bonding": _new_rank_item(
            "soft_private_bonding",
            "чувства раскрываются мягко: через безопасность, приватность и неспешность",
        ),
        "steady_tested_commitment": _new_rank_item(
            "steady_tested_commitment",
            "близость проходит через проверку временем, надежностью и зрелыми рамками",
        ),
        "idealized_merge": _new_rank_item(
            "idealized_merge",
            "есть тяга к слиянию и идеалу, поэтому важно отличать реального человека от фантазии",
        ),
    }
    partnership_needs_candidates = {
        "friendship_clarity_loyalty": _new_rank_item(
            "friendship_clarity_loyalty",
            "нужны дружеская база, честный разговор и лояльность без игр",
        ),
        "safety_time_privacy": _new_rank_item(
            "safety_time_privacy",
            "нужны бережный темп, эмоциональная безопасность и право на тишину",
        ),
        "shared_future_and_work": _new_rank_item(
            "shared_future_and_work",
            "нужны общая цель, уважение к амбиции и партнерская надежность",
        ),
        "passion_and_depth": _new_rank_item(
            "passion_and_depth",
            "нужны сексуальная честность, глубина и доверие в уязвимости",
        ),
    }
    conflict_styles = {
        "silent_accumulation_then_surge": _new_rank_item(
            "silent_accumulation_then_surge",
            "конфликтный стиль: копить напряжение внутри, а потом выдавать его резко и мощно",
        ),
        "direct_and_principled": _new_rank_item(
            "direct_and_principled",
            "конфликтный стиль: говорить прямо, но на принципах и высоком стандарте",
        ),
        "detach_then_recalibrate": _new_rank_item(
            "detach_then_recalibrate",
            "конфликтный стиль: сначала отстраниться, охладить эмоцию и только потом обсуждать",
        ),
        "control_and_loyalty_tests": _new_rank_item(
            "control_and_loyalty_tests",
            "конфликтный стиль: проверять границы, верность и устойчивость партнера",
        ),
    }
    risk_flags = {
        "distance_instead_of_request": _new_rank_item(
            "distance_instead_of_request",
            "риск: уходить в дистанцию и молчание вместо прямой просьбы",
        ),
        "hot_cold_pattern": _new_rank_item(
            "hot_cold_pattern",
            "риск: режим то близко, то далеко, если свобода и глубина не согласованы",
        ),
        "idealization_then_disappointment": _new_rank_item(
            "idealization_then_disappointment",
            "риск: видеть идеал и позже сталкиваться с разочарованием",
        ),
        "fear_of_vulnerability": _new_rank_item(
            "fear_of_vulnerability",
            "риск: путать близость с потерей контроля и потому долго не раскрывать уязвимость",
        ),
    }

    if _sign_in(venus, {"Aquarius", "Gemini", "Libra"}) or _house_in(venus, {11}):
        evidence = _format_position_evidence(venus)
        _bump_rank(attachment_styles, "freedom_then_depth", 16, evidence)
        _bump_rank(partnership_needs_candidates, "friendship_clarity_loyalty", 14, evidence)
        _bump_rank(conflict_styles, "detach_then_recalibrate", 12, evidence)
        _bump_rank(risk_flags, "hot_cold_pattern", 10, evidence)
        _bump_rank(risk_flags, "distance_instead_of_request", 8, evidence)
    if _house_in(mars, {8}) or _house_in(pluto, {7, 8}):
        evidence = _format_position_evidence(mars) or _format_position_evidence(pluto)
        _bump_rank(attachment_styles, "freedom_then_depth", 14, evidence)
        _bump_rank(partnership_needs_candidates, "passion_and_depth", 14, evidence)
        _bump_rank(conflict_styles, "control_and_loyalty_tests", 10, evidence)
        _bump_rank(risk_flags, "fear_of_vulnerability", 12, evidence)
    if _sign_in(moon, {"Cancer", "Scorpio", "Pisces"}) or _house_in(moon, {12}):
        evidence = _format_position_evidence(moon)
        _bump_rank(attachment_styles, "soft_private_bonding", 18, evidence)
        _bump_rank(partnership_needs_candidates, "safety_time_privacy", 16, evidence)
        _bump_rank(conflict_styles, "silent_accumulation_then_surge", 14, evidence)
        _bump_rank(risk_flags, "distance_instead_of_request", 12, evidence)
    if _house_in(saturn, {7, 8, 10}) or _sign_in(saturn, {"Capricorn", "Aquarius"}):
        evidence = _format_position_evidence(saturn)
        _bump_rank(attachment_styles, "steady_tested_commitment", 12, evidence)
        _bump_rank(partnership_needs_candidates, "shared_future_and_work", 10, evidence)
        _bump_rank(conflict_styles, "direct_and_principled", 10, evidence)
        _bump_rank(risk_flags, "fear_of_vulnerability", 8, evidence)
    if house5:
        _bump_rank(attachment_styles, "soft_private_bonding", 6, _format_house_snapshot(house5))
    if house7:
        evidence = _format_house_snapshot(house7)
        _bump_rank(partnership_needs_candidates, "shared_future_and_work", 6, evidence)
        _bump_rank(partnership_needs_candidates, "friendship_clarity_loyalty", 6, evidence)
    if house8:
        evidence = _format_house_snapshot(house8)
        _bump_rank(partnership_needs_candidates, "passion_and_depth", 10, evidence)
        _bump_rank(risk_flags, "fear_of_vulnerability", 6, evidence)
    if venus_mars and _is_harmonious(venus_mars):
        evidence = _format_aspect_evidence(venus_mars)
        _bump_rank(attachment_styles, "freedom_then_depth", 8, evidence)
        _bump_rank(partnership_needs_candidates, "friendship_clarity_loyalty", 6, evidence)
        _bump_rank(partnership_needs_candidates, "passion_and_depth", 6, evidence)
    if moon_uranus:
        evidence = _format_aspect_evidence(moon_uranus)
        _bump_rank(conflict_styles, "detach_then_recalibrate", 8, evidence)
        _bump_rank(risk_flags, "hot_cold_pattern", 12, evidence)
    if sun_neptune:
        evidence = _format_aspect_evidence(sun_neptune)
        _bump_rank(attachment_styles, "idealized_merge", 12, evidence)
        _bump_rank(risk_flags, "idealization_then_disappointment", 16, evidence)
    if venus and venus.get("r"):
        evidence = _format_position_evidence(venus)
        _bump_rank(risk_flags, "distance_instead_of_request", 10, evidence)
        _bump_rank(risk_flags, "hot_cold_pattern", 8, evidence)

    attachment_style = _pick_primary_ranked(
        attachment_styles,
        fallback_key="soft_private_bonding",
        fallback_label="чувства раскрываются мягко: через безопасность, приватность и неспешность",
        fallback_evidence=[
            _format_position_evidence(venus),
            _format_position_evidence(moon),
        ],
    )
    partnership_needs = _pick_primary_ranked(
        partnership_needs_candidates,
        fallback_key="friendship_clarity_loyalty",
        fallback_label="нужны дружеская база, честный разговор и лояльность без игр",
        fallback_evidence=[
            _format_house_snapshot(house7),
            _format_position_evidence(venus),
        ],
    )
    needs_map = {
        "friendship_clarity_loyalty": ["дружеская база", "честный разговор", "лояльность без игр"],
        "safety_time_privacy": ["бережный темп", "эмоциональная безопасность", "право на тишину"],
        "shared_future_and_work": ["общая цель", "уважение к амбиции", "надежность"],
        "passion_and_depth": ["сексуальная честность", "глубина", "доверие в уязвимости"],
    }
    partnership_needs["needs"] = needs_map.get(partnership_needs.get("key"), [])[:3]

    conflict_style = _pick_primary_ranked(
        conflict_styles,
        fallback_key="direct_and_principled",
        fallback_label="конфликтный стиль: говорить прямо, но на принципах и высоком стандарте",
        fallback_evidence=[
            _format_position_evidence(mars),
            _format_position_evidence(saturn),
        ],
    )
    intimacy_risk_flags = _finalize_ranked(risk_flags, limit=3)

    attachment_key = attachment_style.get("key", "")
    needs_key = partnership_needs.get("key", "")
    conflict_key = conflict_style.get("key", "")
    top_intimacy_risk = intimacy_risk_flags[0] if intimacy_risk_flags else {}
    risk_key = top_intimacy_risk.get("key", "")

    relationship_manifestation_map = {
        "freedom_then_depth": [
            "притяжение чаще начинается с ощущения воздуха, дружбы, интеллектуального контакта или ощущения, что рядом можно быть собой",
            "по-настоящему важно не поверхностное общение, а момент, когда за свободой появляется настоящая глубина и доверие",
            "если свобода и глубина не согласованы, включается сценарий то вместе, то на расстоянии",
        ],
        "soft_private_bonding": [
            "любовь раскрывается не под давлением, а в тихой приватной атмосфере, где можно не спешить",
            "близость становится настоящей там, где есть эмоциональная безопасность и право не объяснять всё мгновенно",
            "при перегрузе отношениям вредят не конфликты сами по себе, а накопленное молчание",
        ],
        "steady_tested_commitment": [
            "любовь читается через надёжность, выдержку и уважение к времени, а не только через вспышку",
            "привязанность крепнет, когда другой выдерживает дистанцию, сроки и реальные обязательства",
            "если зрелые рамки путаются с холодом, близость начинает идти через проверки на прочность",
        ],
        "idealized_merge": [
            "отношения легко поднимаются до уровня большого образа, фантазии и сильного притяжения",
            "любовь особенно цепляет, когда кажется, что найдено идеальное совпадение по смыслу или спасению",
            "главный риск — заметить реального человека слишком поздно, уже после эмоционального вложения",
        ],
    }
    triggers_map = {
        "distance_instead_of_request": ["неясные договорённости", "ощущение, что надо просить слишком много", "эмоциональная небезопасность"],
        "hot_cold_pattern": ["слишком быстрый темп", "страх потерять свободу", "ощущение, что связь стала слишком обязательной"],
        "idealization_then_disappointment": ["сильная химия без проверки реальности", "слияние на раннем этапе", "обещания без опоры на поступки"],
        "fear_of_vulnerability": ["слишком глубокая близость", "тема доверия, секса или зависимости", "необходимость показать слабое место"],
    }
    sabotage_map = {
        "distance_instead_of_request": "самосаботаж в любви идёт через молчание и дистанцию вместо прямой просьбы о нужном",
        "hot_cold_pattern": "самосаботаж идёт через качели приближения и отдаления, когда связь уже важна, но ещё страшно закрепить её формой",
        "idealization_then_disappointment": "самосаботаж идёт через быстрое наделение связи слишком большим смыслом до реальной проверки её качества",
        "fear_of_vulnerability": "самосаботаж идёт через контроль, проверку партнёра или удержание глубины на пороге, не давая ей стать взаимной",
    }
    compensation_map = {
        "distance_instead_of_request": "компенсация выглядит как образ самостоятельного человека, которому якобы ничего не нужно",
        "hot_cold_pattern": "компенсация выглядит как рационализация: сначала приблизиться, потом резко охладить всё ради чувства контроля",
        "idealization_then_disappointment": "компенсация выглядит как вера, что сама химия и сильное чувство решат то, что ещё не подтверждено поступками",
        "fear_of_vulnerability": "компенсация выглядит как проверки на верность, силу и устойчивость вместо прямого доверия",
    }
    action_map = {
        "freedom_then_depth": "лучший режим любви — сначала договариваться о воздухе и границах, а потом уже углублять связь",
        "soft_private_bonding": "лучший режим любви — медленный темп, приватность и ясное право на бережную паузу без наказания",
        "steady_tested_commitment": "лучший режим любви — выдерживать ритм, слово и поступок, не заменяя это сухой дистанцией",
        "idealized_merge": "лучший режим любви — держать чувство и реальность рядом: проверять образ поступками и временем",
    }

    relationship_manifestations = [
        {
            "phase": "attraction",
            "label": relationship_manifestation_map.get(attachment_key, [attachment_style.get("label", "")])[0],
            "evidence": attachment_style.get("evidence", [])[:3],
        },
        {
            "phase": "bonding",
            "label": relationship_manifestation_map.get(attachment_key, ["", partnership_needs.get("label", "")])[1],
            "evidence": partnership_needs.get("evidence", [])[:3],
        },
        {
            "phase": "stress",
            "label": relationship_manifestation_map.get(attachment_key, ["", "", conflict_style.get("label", "")])[2],
            "evidence": [
                *(conflict_style.get("evidence", [])[:2]),
                *(top_intimacy_risk.get("evidence", [])[:2]),
            ][:4],
        },
    ]
    relationship_triggers = {
        "key": f"{risk_key}_triggers",
        "items": triggers_map.get(risk_key, []),
        "evidence": top_intimacy_risk.get("evidence", [])[:4],
    }
    self_sabotage_pattern = {
        "key": f"{risk_key}_self_sabotage",
        "label": sabotage_map.get(risk_key, top_intimacy_risk.get("label", "")),
        "evidence": top_intimacy_risk.get("evidence", [])[:4],
    }
    compensation_pattern = {
        "key": f"{risk_key}_compensation",
        "label": compensation_map.get(risk_key, conflict_style.get("label", "")),
        "evidence": [
            *(conflict_style.get("evidence", [])[:2]),
            *(top_intimacy_risk.get("evidence", [])[:2]),
        ][:4],
    }
    what_to_do = {
        "items": [
            action_map.get(attachment_key, attachment_style.get("label", "")),
            f"прямо обозначать потребность в {', '.join(partnership_needs.get('needs', [])[:2])}" if partnership_needs.get("needs") else partnership_needs.get("label", ""),
            "замечать триггер раньше, чем он превратится в дистанцию, проверку или резкое охлаждение",
        ][:4],
        "evidence": [
            *(attachment_style.get("evidence", [])[:2]),
            *(partnership_needs.get("evidence", [])[:2]),
        ][:4],
    }
    what_not_to_do = {
        "items": [
            "не требовать глубины без оговорённых границ и темпа",
            "не путать самозащиту с зрелой дистанцией",
            "не принимать химию за гарантию совместимости без проверки реальностью",
        ],
        "evidence": top_intimacy_risk.get("evidence", [])[:3],
    }
    best_mode_of_action = {
        "key": f"{attachment_key or 'attachment'}_best_mode",
        "label": action_map.get(attachment_key, attachment_style.get("label", "")),
        "evidence": [
            *(attachment_style.get("evidence", [])[:2]),
            *(partnership_needs.get("evidence", [])[:2]),
        ][:4],
    }
    scene_seeds = [
        {
            "title": "сцена сближения",
            "seed": relationship_manifestation_map.get(attachment_key, [attachment_style.get("label", "")])[0],
        },
        {
            "title": "сцена конфликта",
            "seed": (
                f"{conflict_style.get('label')}; риск сверху обычно включается через {', '.join(triggers_map.get(risk_key, [])[:2])}"
            ),
        },
    ]

    return {
        "version": "natal_v2_p0",
        "attachment_style": attachment_style,
        "partnership_needs": partnership_needs,
        "conflict_style": conflict_style,
        "intimacy_risk_flags": intimacy_risk_flags,
        "relationship_manifestations": relationship_manifestations,
        "relationship_triggers": relationship_triggers,
        "self_sabotage_pattern": self_sabotage_pattern,
        "compensation_pattern": compensation_pattern,
        "what_to_do": what_to_do,
        "what_not_to_do": what_not_to_do,
        "best_mode_of_action": best_mode_of_action,
        "scene_seeds": scene_seeds,
        "cross_links": [
            "executive_summary.relationship_theme",
            "synthesis.core_conflict",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_final_synthesis_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    executive_pack = _build_executive_summary_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    synthesis_pack = _build_synthesis_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    money_pack = _build_money_realization_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )
    love_pack = _build_love_intimacy_insight_pack(
        facts, chart_data, position_lookup, house_lookup
    )

    top_resource = (executive_pack.get("strengths_score") or [{}])[0]
    top_conflict = synthesis_pack.get("core_conflict") or (executive_pack.get("risk_score") or [{}])[0]
    career_vector = money_pack.get("career_vector") or {}
    realization_mode = money_pack.get("realization_mode") or {}
    attachment_style = love_pack.get("attachment_style") or {}
    partnership_needs = love_pack.get("partnership_needs") or {}
    best_mode_of_action = executive_pack.get("best_mode_of_action") or {}

    resource_key = top_resource.get("key")
    conflict_key = top_conflict.get("key")
    career_key = career_vector.get("key")
    realization_key = realization_mode.get("key")
    attachment_key = attachment_style.get("key")
    needs_key = partnership_needs.get("key")

    resource_motto_map = {
        "structured_ambition": "строй опору",
        "intuitive_depth": "слушай глубину",
        "independent_innovation": "обновляй маршрут",
        "resilient_influence": "держи сложность в форме",
    }
    conflict_motto_map = {
        "control_vs_sensitivity": "не цементируй себя контролем",
        "stability_vs_freedom": "не ломай базу ради свободы",
        "depth_vs_distance": "не уходи в дистанцию",
        "vision_vs_grounding": "приземляй образ в факты",
    }
    resource_integration_map = {
        "structured_ambition": "твоя сила максимальна, когда каркас остается живым, а не жестким",
        "intuitive_depth": "твоя сила максимальна, когда чувствительность получает форму, а не туман",
        "independent_innovation": "твоя сила максимальна, когда свобода обновляет систему, а не сжигает опору",
        "resilient_influence": "твоя сила максимальна, когда давление превращается в рычаг, а не в постоянный режим жизни",
    }
    conflict_integration_map = {
        "control_vs_sensitivity": "контроль не должен душить чувствительность",
        "stability_vs_freedom": "поворот должен строиться поверх базы",
        "depth_vs_distance": "глубина не должна уходить в молчаливую дистанцию",
        "vision_vs_grounding": "большой образ должен получать критерии, срок и форму",
    }
    conflict_action_map = {
        "control_vs_sensitivity": "Сначала называй перегруз и потребность, а уже потом ужесточай план",
        "stability_vs_freedom": "Не разворачивай маршрут рывком, пока не собраны база, ритм и запас ресурса",
        "depth_vs_distance": "Начинай важный разговор до того, как уязвимость уйдет в молчание",
        "vision_vs_grounding": "Ставь рядом с интуицией критерии, сроки и проверку реальностью",
    }
    work_anchor_map = {
        "systems_leader": "держи систему, стандарт и длинный горизонт",
        "network_builder": "делай ставку на среду, связи и аудиторию",
        "care_container": "опирайся на полезность, качество и удержание",
        "crisis_specialist": "заходи в сложные кейсы, где другим тяжело",
    }
    work_mode_map = {
        "disciplined_climb": "с ясным ритмом и накоплением статуса",
        "autonomous_project_cycles": "через короткие автономные циклы",
        "community_platform": "через платформу, сеть и совместные инициативы",
        "deep_problem_solving": "через разбор сложных и неоднозначных задач",
    }
    love_anchor_map = {
        "freedom_then_depth": "сначала договаривайся о воздухе и границах, а потом углубляй связь",
        "soft_private_bonding": "сохраняй медленный безопасный темп",
        "steady_tested_commitment": "показывай надежность делом и выдерживай ритм",
        "idealized_merge": "проверяй сильное чувство временем и поступками",
    }
    love_needs_map = {
        "friendship_clarity_loyalty": "с честными договоренностями и лояльностью без игр",
        "safety_time_privacy": "с правом на паузу и эмоциональную безопасность",
        "shared_future_and_work": "с общей целью и уважением к надежности",
        "passion_and_depth": "с доверием к уязвимости и глубине",
    }

    def _merge_focus_line(primary: str, secondary: str) -> str:
        primary = (primary or "").strip()
        secondary = (secondary or "").strip()
        if not primary:
            return secondary
        if not secondary:
            return primary
        if secondary.startswith(("с ", "через ")):
            return f"{primary} {secondary}"
        return f"{primary} и {secondary}"

    work_line = _merge_focus_line(
        work_anchor_map.get(career_key, _format_insight_value(career_vector)),
        work_mode_map.get(realization_key, _format_insight_value(realization_mode)),
    )
    love_line = _merge_focus_line(
        love_anchor_map.get(attachment_key, _format_insight_value(attachment_style)),
        love_needs_map.get(needs_key, _format_insight_value(partnership_needs)),
    )
    work_line = _compose_fact_first_fragment(work_line, career_vector, realization_mode, limit=1)
    love_line = _compose_fact_first_fragment(love_line, attachment_style, partnership_needs, limit=1)
    angle_anchor = _extract_named_anchor(career_vector, realization_mode, names=("asc", "mc", "⬆️", "🏔️"))
    best_mode_fragment = _normalize_executive_fragment(
        _format_insight_value(best_mode_of_action),
        [r"^лучший режим действия\s*[—:-]\s*"],
    )
    resource_fragment = _normalize_executive_fragment(
        _format_insight_value(top_resource),
        [],
    )

    motto_core = "; ".join(
        part
        for part in [
            resource_fragment
            or resource_motto_map.get(resource_key, "собирай свою сильную сторону в действие"),
            f"режим карты — {best_mode_fragment}"
            if best_mode_fragment
            else conflict_motto_map.get(conflict_key, "не отдавай глубину хаосу"),
        ]
        if part
    )
    integration_label = "; ".join(
        part
        for part in [
            _compose_fact_first_fragment(
                resource_integration_map.get(resource_key, top_resource.get("label", "")),
                top_resource,
                limit=1,
            ),
            _compose_fact_first_fragment(
                conflict_integration_map.get(conflict_key, top_conflict.get("label", "")),
                top_conflict,
                limit=1,
            ),
        ]
        if part
    )
    advice_parts = []
    if best_mode_fragment:
        advice_parts.append(f"Зрелый ход этой карты — {best_mode_fragment}")
    advice_parts.append(
        conflict_action_map.get(
            conflict_key,
            "Не отдавай главный внутренний конфликт автопилоту: переводи его в ясное решение",
        )
    )
    bridge_parts = []
    if work_line:
        bridge_parts.append(f"в работе {work_line}")
    if love_line:
        bridge_parts.append(f"в близости {love_line}")
    if bridge_parts:
        advice_parts.append("; ".join(bridge_parts))
    advice_text = " ".join(
        _clean_sentence(part)
        for part in advice_parts
        if str(part or "").strip()
    ).strip()
    integration_key = "_".join(
        part for part in [resource_key or "resource", conflict_key or "conflict"] if part
    )

    integration = {
        "key": integration_key,
        "label": integration_label,
        "evidence": [
            *(top_resource.get("evidence", [])[:2]),
            *(top_conflict.get("evidence", [])[:2]),
            *(best_mode_of_action.get("evidence", [])[:1] if best_mode_of_action else []),
            *(career_vector.get("evidence", [])[:1] if career_vector else []),
            *(attachment_style.get("evidence", [])[:1] if attachment_style else []),
            *(partnership_needs.get("evidence", [])[:1] if partnership_needs else []),
        ][:6],
    }
    sun_anchor = _extract_named_anchor(
        top_resource,
        top_conflict,
        best_mode_of_action,
        integration,
        names=("солнце", "☀️"),
    )
    moon_anchor = _extract_named_anchor(
        top_resource,
        top_conflict,
        best_mode_of_action,
        integration,
        names=("луна", "🌙"),
    )
    if not sun_anchor and "солнце" in integration_label.lower():
        sun_anchor = "☀️ Солнце"
    if not moon_anchor and "луна" in integration_label.lower():
        moon_anchor = "🌙 Луна"
    motto_details = [part for part in [sun_anchor, moon_anchor, angle_anchor] if part]
    motto_label = "; ".join(part for part in [motto_core, *motto_details] if part)
    top_conflict_vs_top_resource = {
        "resource": top_resource,
        "conflict": top_conflict,
        "integration": integration,
    }
    closing_bridge = {
        "key": f"{integration_key}_bridge",
        "label": "; ".join(
            part
            for part in [
                f"В работе - {work_line}" if work_line else "",
                f"В близости - {love_line}" if love_line else "",
            ]
            if part
        ),
        "work_line": work_line,
        "love_line": love_line,
        "evidence": [
            *(career_vector.get("evidence", [])[:2] if career_vector else []),
            *(realization_mode.get("evidence", [])[:1] if realization_mode else []),
            *(attachment_style.get("evidence", [])[:2] if attachment_style else []),
            *(partnership_needs.get("evidence", [])[:1] if partnership_needs else []),
        ][:5],
    }
    applied_cross_links = [
        {"path": "executive_summary.strengths_score", "label": top_resource.get("label", "")},
        {"path": "synthesis.core_conflict", "label": top_conflict.get("label", "")},
        {"path": "money_realization.career_vector", "label": career_vector.get("label", "")},
        {"path": "money_realization.realization_mode", "label": realization_mode.get("label", "")},
        {"path": "love_intimacy.attachment_style", "label": attachment_style.get("label", "")},
        {"path": "love_intimacy.partnership_needs", "label": partnership_needs.get("label", "")},
    ]
    integration_focus = {
        "key": f"{integration_key}_focus",
        "label": integration_label,
        "closing_bridge": closing_bridge.get("label", ""),
        "evidence": integration.get("evidence", [])[:6],
    }
    final_motto_seed = {
        "key": f"{integration_key}_motto",
        "label": motto_label,
        "score": _score_to_int(
            (
                top_resource.get("score", 55)
                + top_conflict.get("score", 55)
                + career_vector.get("score", 55)
                + attachment_style.get("score", 55)
            )
            / 4
        ),
        "evidence": integration.get("evidence", [])[:4],
    }
    one_sentence_advice = {
        "key": f"{integration_key}_advice",
        "label": advice_text,
        "text": advice_text,
        "evidence": [
            *(integration.get("evidence", [])[:4]),
            *(_collect_fact_anchor_evidence(best_mode_of_action, career_vector, attachment_style, limit=2)),
        ][:5],
    }

    return {
        "version": "natal_v2_p0",
        "final_motto_seed": final_motto_seed,
        "one_sentence_advice": one_sentence_advice,
        "sun_vector": {"label": sun_anchor} if sun_anchor else {},
        "moon_vector": {"label": moon_anchor} if moon_anchor else {},
        "asc_mc_axis": {"label": angle_anchor} if angle_anchor else {},
        "top_conflict_vs_top_resource": top_conflict_vs_top_resource,
        "integration_focus": integration_focus,
        "closing_bridge": closing_bridge,
        "applied_cross_links": [item for item in applied_cross_links if item.get("label")],
        "cross_links": [
            "executive_summary.strengths_score",
            "synthesis.core_conflict",
            "money_realization.career_vector",
            "money_realization.realization_mode",
            "love_intimacy.attachment_style",
            "love_intimacy.partnership_needs",
        ],
    }


def _build_house_tenants(chart_data: dict) -> Dict[int, List[str]]:
    tenants: Dict[int, List[str]] = {house: [] for house in range(1, 13)}
    allowed = set(PLANET_ROLE_HINTS.keys()) | {"Lilith"}
    for position in chart_data.get("positions", []):
        house = position.get("house")
        name = _normalize_point_name(position.get("key") or position.get("name"))
        if isinstance(house, int) and 1 <= house <= 12 and name in allowed:
            tenants[house].append(name)
    return tenants


def _normalize_dispositor_summary(summary: Any) -> str:
    if isinstance(summary, list):
        parts = [str(item).strip() for item in summary if str(item).strip()]
        return "; ".join(parts)
    if summary is None:
        return ""
    cleaned = re.sub(r"\s+", " ", str(summary)).strip()
    return cleaned


def _normalize_fixed_star_record(star: Any) -> Dict[str, Any]:
    if not isinstance(star, dict):
        return {"name": str(star).strip(), "point": None, "orb": None}
    orb = star.get("orb")
    try:
        orb = round(float(orb), 1)
    except (TypeError, ValueError):
        orb = None
    point = _normalize_point_name(
        star.get("point") or star.get("planet") or star.get("raw_point") or star.get("body") or star.get("target")
    )
    return {
        "name": (star.get("name") or star.get("star") or "Fixed star").strip(),
        "point": point,
        "orb": orb,
        "sign": star.get("sign"),
    }


def _format_planet_name_list(names: List[str], limit: int = 4) -> str:
    return ", ".join(RU_PLANET_NAMES.get(name, name) for name in names[:limit])


def _build_dispositor_graph(position_lookup: Dict[str, dict]) -> Dict[str, Any]:
    planets = [planet for planet in MAJOR_DISPOSITOR_PLANETS if planet in position_lookup]
    links: Dict[str, str] = {}
    for planet in planets:
        sign = (position_lookup.get(planet) or {}).get("s")
        ruler = SIGN_RULER_MAP.get(sign)
        if ruler in planets:
            links[planet] = ruler

    inbound = {planet: 0 for planet in planets}
    for target in links.values():
        if target in inbound:
            inbound[target] += 1

    chains: Dict[str, Dict[str, Any]] = {}
    loops_seen: set[tuple[str, ...]] = set()
    loops: List[List[str]] = []
    for planet in planets:
        chain: List[str] = []
        current = planet
        while current in links and current not in chain:
            chain.append(current)
            current = links[current]
        loop: List[str] = []
        if current in chain:
            loop = chain[chain.index(current):]
            loop_key = tuple(loop)
            if loop_key not in loops_seen:
                loops_seen.add(loop_key)
                loops.append(loop)
        chains[planet] = {
            "chain": chain,
            "loop": loop,
        }
    return {
        "links": links,
        "inbound": inbound,
        "chains": chains,
        "loops": loops,
    }


def _build_dispositor_office_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    graph = _build_dispositor_graph(position_lookup)
    links = graph.get("links", {})
    inbound = graph.get("inbound", {})
    chains = graph.get("chains", {})
    loops = graph.get("loops", [])

    office_map = []
    for planet in MAJOR_DISPOSITOR_PLANETS:
        if planet not in position_lookup or planet not in links:
            continue
        reports_to = links.get(planet)
        report_position = position_lookup.get(reports_to)
        office_map.append(
            {
                "planet": planet,
                "planet_label": RU_PLANET_NAMES.get(planet, planet),
                "sign": position_lookup[planet].get("s"),
                "reports_to": reports_to,
                "reports_to_label": RU_PLANET_NAMES.get(reports_to, reports_to),
                "reports_to_sign": (report_position or {}).get("s"),
                "reports_to_house": (report_position or {}).get("h"),
            }
        )

    power_centers = []
    for planet in sorted(
        inbound.keys(),
        key=lambda key: (
            inbound.get(key, 0),
            any(key in loop for loop in loops),
        ),
        reverse=True,
    ):
        evidence = [
            _format_position_evidence(position_lookup.get(planet)),
        ]
        directs = [src for src, dst in links.items() if dst == planet]
        if directs:
            evidence.append(
                f"напрямую собирает: {_format_planet_name_list(directs)}"
            )
        if any(planet in loop for loop in loops):
            evidence.append("входит в конечный диспозиторный контур")
        power_centers.append(
            {
                "planet": planet,
                "label": RU_PLANET_NAMES.get(planet, planet),
                "score": _score_to_int(45 + inbound.get(planet, 0) * 12 + (18 if any(planet in loop for loop in loops) else 0)),
                "evidence": [item for item in evidence if item][:4],
            }
        )
    power_centers = power_centers[:3]

    final_bosses = []
    for loop in loops:
        if not loop:
            continue
        if len(loop) == 1:
            boss = loop[0]
            final_bosses.append(
                {
                    "type": "domicile",
                    "label": f"{RU_PLANET_NAMES.get(boss, boss)} держит кабинет у себя",
                    "planets": loop,
                    "evidence": [_format_position_evidence(position_lookup.get(boss))],
                }
            )
        elif len(loop) == 2:
            p1, p2 = loop
            final_bosses.append(
                {
                    "type": "mutual_reception",
                    "label": f"взаимная рецепция {RU_PLANET_NAMES.get(p1, p1)} и {RU_PLANET_NAMES.get(p2, p2)}",
                    "planets": loop,
                    "evidence": [
                        _format_position_evidence(position_lookup.get(p1)),
                        _format_position_evidence(position_lookup.get(p2)),
                    ][:4],
                }
            )
        else:
            final_bosses.append(
                {
                    "type": "loop",
                    "label": "замкнутый управленческий контур",
                    "planets": loop,
                    "evidence": [_format_planet_name_list(loop)],
                }
            )

    focus_map = {
        "Sun": "ядро и воля",
        "Moon": "эмоции и безопасность",
        "Mercury": "мышление и решения",
        "Venus": "ценность и связи",
        "Mars": "действие и конфликт",
    }
    decision_chains = []
    for planet, focus in focus_map.items():
        chain_info = chains.get(planet) or {}
        chain = chain_info.get("chain") or []
        if not chain:
            continue
        decision_chains.append(
            {
                "focus": focus,
                "planet": planet,
                "chain": chain,
                "chain_labels": [RU_PLANET_NAMES.get(item, item) for item in chain],
                "final_loop": chain_info.get("loop") or [],
                "evidence": [
                    _format_position_evidence(position_lookup.get(item))
                    for item in chain[:2]
                    if position_lookup.get(item)
                ][:4],
            }
        )

    top_center = power_centers[0] if power_centers else {}
    secondary_center = power_centers[1] if len(power_centers) > 1 else {}
    office_metaphor_seed = {
        "key": "office_hierarchy_seed",
        "label": (
            f"главный кабинет у {top_center.get('label', 'ключевой планеты')}, "
            f"а соседний центр влияния у {secondary_center.get('label', 'второго узла управления')}"
            if secondary_center
            else f"главный кабинет у {top_center.get('label', 'ключевой планеты')}"
        ),
        "evidence": [
            *(top_center.get("evidence", [])[:2] if top_center else []),
            *(secondary_center.get("evidence", [])[:1] if secondary_center else []),
        ][:4],
    }

    return {
        "version": "natal_v2_p1",
        "engine_summary": (
            (chart_data.get("dispositor_summary") or {}).get("summary")
            or _normalize_dispositor_summary(chart_data.get("dispositors"))
        ),
        "office_map": office_map,
        "power_centers": power_centers,
        "final_bosses": final_bosses,
        "decision_chains": decision_chains,
        "office_metaphor_seed": office_metaphor_seed,
        "cross_links": [
            "synthesis.identity_vector",
            "money_realization.career_vector",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _describe_house_item(
    house_number: int,
    house_lookup: Dict[int, dict],
    position_lookup: Dict[str, dict],
    house_tenants: Dict[int, List[str]],
) -> Optional[Dict[str, Any]]:
    snapshot = _build_house_snapshot(house_lookup, position_lookup, house_number)
    if not snapshot:
        return None

    sign = snapshot.get("sign")
    ruler = snapshot.get("ruler")
    ruler_position = snapshot.get("ruler_position") or {}
    sign_hint = SIGN_STYLE_HINTS.get(sign, {})
    tenants = house_tenants.get(house_number, [])
    occupant_roles = [PLANET_ROLE_HINTS.get(name, name) for name in tenants[:3]]
    occupant_labels = [_format_planet_name_list(tenants)] if tenants else []

    theme = (
        f"{HOUSE_DOMAIN_MAP.get(house_number, 'тема дома')} "
        f"через {sign_hint.get('tone', 'свой природный ритм')}"
    )

    plus_parts = [sign_hint.get("plus", "ресурс дома")]
    if ruler_position.get("h") in {1, 4, 7, 10}:
        plus_parts.append("тема дома видна и влияет на маршрут напрямую")
    if any(name in tenants for name in ["Sun", "Venus", "Jupiter", "ASC", "MC"]):
        plus_parts.append("есть дополнительная видимость или поддержка изнутри дома")

    minus_parts = [sign_hint.get("minus", "теневая сторона дома")]
    if ruler_position.get("h") in {8, 12}:
        minus_parts.append("тема легко уходит в скрытое напряжение или откладывание")
    if any(name in tenants for name in ["Saturn", "Mars", "Pluto", "Neptune"]):
        minus_parts.append("внутри дома есть точка давления, борьбы или размывания")

    trigger = (
        f"активируется через темы {HOUSE_DOMAIN_MAP.get(ruler_position.get('h'), 'дома управителя')}"
        if ruler_position.get("h")
        else "активируется, когда дом затрагивает базовую жизненную тему"
    )
    if tenants:
        trigger += f"; внутри дома это особенно заметно через {_format_planet_name_list(tenants)}"

    growth_vector = sign_hint.get("growth", "учиться удерживать дом в зрелом режиме")
    if ruler_position.get("h"):
        growth_vector += f"; связывать это с темой {HOUSE_DOMAIN_MAP.get(ruler_position.get('h'), 'дома управителя')}"

    evidence = [
        _format_house_snapshot(snapshot),
        _format_position_evidence(ruler_position),
        (
            f"планеты в доме: {_format_planet_name_list(tenants)}"
            if tenants
            else "дом без планет, опора идет через управителя"
        ),
    ]

    return {
        "house": house_number,
        "domain": HOUSE_DOMAIN_MAP.get(house_number),
        "cusp_sign": sign,
        "ruler": ruler,
        "ruler_house": ruler_position.get("h"),
        "ruler_sign": ruler_position.get("s"),
        "occupants": tenants,
        "theme": theme,
        "plus": "; ".join(part for part in plus_parts if part),
        "minus": "; ".join(part for part in minus_parts if part),
        "trigger": trigger,
        "growth_vector": growth_vector,
        "ruler_story": _format_house_snapshot(snapshot),
        "occupant_roles": occupant_roles,
        "evidence": [item for item in evidence if item][:4],
    }


def _build_balance_wheel_insight_pack(
    section_id: str,
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    house_numbers = [1, 2, 3, 4, 5, 6] if section_id == "balance_wheel_1_6" else [7, 8, 9, 10, 11, 12]
    house_tenants = _build_house_tenants(chart_data)
    house_pack = []
    activation = []
    sensitive = []

    for house_number in house_numbers:
        item = _describe_house_item(
            house_number,
            house_lookup,
            position_lookup,
            house_tenants,
        )
        if not item:
            continue
        house_pack.append(item)
        score = len(item.get("occupants", []))
        if item.get("ruler_house") in {1, 4, 7, 10}:
            score += 1
        activation.append((house_number, score))
        if item.get("ruler_house") in {8, 12} or any(
            occupant in item.get("occupants", [])
            for occupant in ["Saturn", "Mars", "Pluto", "Neptune", "Lilith"]
        ):
            sensitive.append(house_number)

    activation.sort(key=lambda item: (item[1], -item[0]), reverse=True)
    zone_summary = {
        "dominant_houses": [item[0] for item in activation[:2] if item[1] > 0],
        "sensitive_houses": sensitive[:2],
        "label": (
            f"самая активная зона: дома {', '.join(str(item[0]) for item in activation[:2] if item[1] > 0)}"
            if any(item[1] > 0 for item in activation[:2])
            else "зона читается в основном через управителей, а не через скопления планет"
        ),
    }

    return {
        "version": "natal_v2_p1",
        "house_pack": house_pack,
        "zone_summary": zone_summary,
        "cross_links": [
            "executive_summary.strengths_score",
            "money_realization.career_vector" if section_id == "balance_wheel_1_6" else "love_intimacy.attachment_style",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value)
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result


def _format_year_delta(delta_years: float) -> str:
    if delta_years >= 0:
        return f"через {delta_years:.1f} лет"
    return f"{abs(delta_years):.1f} лет назад"


def _describe_age_cycle(age_years: float, cycle_years: float, cycle_name: str) -> Dict[str, Any]:
    cycle_index = int(age_years // cycle_years)
    phase_fraction = (age_years / cycle_years) - cycle_index
    if phase_fraction < 0.25:
        phase_label = "старт нового витка"
    elif phase_fraction < 0.5:
        phase_label = "набор инерции и расширение"
    elif phase_fraction < 0.75:
        phase_label = "проверка маршрута и перенастройка"
    else:
        phase_label = "сборка результатов и подготовка к новому перезапуску"
    next_return_age = (cycle_index + 1) * cycle_years
    return {
        "cycle": cycle_name,
        "cycle_index": cycle_index + 1,
        "phase_label": phase_label,
        "age_years": round(age_years, 1),
        "years_to_next_return": round(max(0.0, next_return_age - age_years), 1),
    }


def _build_cycle_markers(age_years: float) -> List[Dict[str, Any]]:
    markers: List[Dict[str, Any]] = []
    cycle_specs = [
        ("return", "возврат Сатурна", 29.46, 0.0),
        ("opposition", "оппозиция Сатурна", 29.46, 14.73),
        ("return", "возврат Юпитера", 11.86, 0.0),
        ("return", "возврат Узлов", 18.6, 0.0),
        ("opposition", "оппозиция Узлов", 18.6, 9.3),
    ]
    for marker_type, label, cycle_years, offset in cycle_specs:
        index = 0
        while True:
            age_at = offset + cycle_years * index
            if age_at <= 0:
                index += 1
                continue
            if age_at > age_years + 15:
                break
            markers.append(
                {
                    "type": marker_type,
                    "label": label,
                    "age_at": round(age_at, 1),
                    "delta_years": round(age_at - age_years, 1),
                }
            )
            index += 1
    markers.sort(key=lambda item: abs(item.get("delta_years", 0.0)))
    return markers[:5]


def _build_time_cycles_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
    client: Optional[dict],
    forecast_window: Optional[dict],
) -> Dict[str, Any]:
    birth_dt = _parse_iso_datetime((client or {}).get("birth_date"))
    current_dt = _parse_iso_datetime((forecast_window or {}).get("start"))
    age_years = 0.0
    if birth_dt and current_dt:
        age_years = max(0.0, (current_dt - birth_dt).total_seconds() / (365.2425 * 24 * 3600))

    saturn = position_lookup.get("Saturn")
    jupiter = position_lookup.get("Jupiter")
    node = position_lookup.get("North Node") or position_lookup.get("True Node")

    saturn_phase = _describe_age_cycle(age_years, 29.46, "Saturn")
    jupiter_phase = _describe_age_cycle(age_years, 11.86, "Jupiter")
    node_phase = _describe_age_cycle(age_years, 18.6, "Nodes")
    cycle_markers = _build_cycle_markers(age_years)
    top_marker = cycle_markers[0] if cycle_markers else {}

    saturn_focus = HOUSE_DOMAIN_MAP.get((saturn or {}).get("h"), "темы зрелости и рамок")
    jupiter_focus = HOUSE_DOMAIN_MAP.get((jupiter or {}).get("h"), "темы роста и расширения")
    node_focus = HOUSE_DOMAIN_MAP.get((node or {}).get("h"), "темы вектора роста")

    if top_marker and abs(top_marker.get("delta_years", 99.0)) <= 1.5:
        summary_label = (
            f"сейчас активно окно {top_marker.get('label')}: период требует "
            f"переоценить {saturn_focus.lower()} и связать это с {jupiter_focus.lower()}"
        )
        summary_key = "active_marker_window"
    else:
        summary_label = (
            f"текущий период читается как {saturn_phase.get('phase_label')} по Сатурну "
            f"на фоне фазы '{jupiter_phase.get('phase_label')}' по Юпитеру"
        )
        summary_key = "age_phase_summary"

    maturity_cycle_summary = {
        "key": summary_key,
        "label": summary_label,
        "score": _score_to_int(100 - abs(top_marker.get("delta_years", 3.0)) * 18 if top_marker else 58),
        "evidence": [
            f"возраст {age_years:.1f} лет",
            (
                f"ближайший маркер: {top_marker.get('label')} ({_format_year_delta(top_marker.get('delta_years', 0.0))})"
                if top_marker
                else None
            ),
            _format_position_evidence(saturn),
            _format_position_evidence(jupiter),
        ][:4],
    }

    saturn_jupiter_phase = {
        "saturn": {
            **saturn_phase,
            "focus": saturn_focus,
            "evidence": [_format_position_evidence(saturn)],
        },
        "jupiter": {
            **jupiter_phase,
            "focus": jupiter_focus,
            "evidence": [_format_position_evidence(jupiter)],
        },
        "node": {
            **node_phase,
            "focus": node_focus,
            "evidence": [_format_position_evidence(node)],
        },
    }

    growth_tension = {
        "key": "saturn_jupiter_node_tension",
        "label": (
            f"главное напряжение роста сейчас между {saturn_focus.lower()}, "
            f"{jupiter_focus.lower()} и требованием не терять {node_focus.lower()}"
        ),
        "score": _score_to_int(60 + (12 if top_marker and abs(top_marker.get("delta_years", 99.0)) <= 2.0 else 0)),
        "evidence": [
            _format_position_evidence(saturn),
            _format_position_evidence(jupiter),
            _format_position_evidence(node),
        ][:4],
    }

    current_age = {
        "years": round(age_years, 1),
        "as_of": current_dt.isoformat() if current_dt else None,
    }

    return {
        "version": "natal_v2_p1",
        "current_age": current_age,
        "cycle_markers": cycle_markers,
        "maturity_cycle_summary": maturity_cycle_summary,
        "saturn_jupiter_phase": saturn_jupiter_phase,
        "growth_tension": growth_tension,
        "cross_links": [
            "executive_summary.development_focus",
            "synthesis.core_conflict",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _build_axes_truths_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    house_tenants = _build_house_tenants(chart_data)
    axis_specs = [
        (1, 7, "identity_vs_partner", "ASC-DSC"),
        (4, 10, "private_base_vs_public_role", "IC-MC"),
        (2, 8, "ownership_vs_merging", "2-8"),
        (5, 11, "self_expression_vs_collective", "5-11"),
    ]
    axis_polarities = []
    axis_tasks = []
    tension_scores = []

    for left_house, right_house, axis_key, axis_label in axis_specs:
        left = _build_house_snapshot(house_lookup, position_lookup, left_house)
        right = _build_house_snapshot(house_lookup, position_lookup, right_house)
        if not left or not right:
            continue
        left_hint = SIGN_STYLE_HINTS.get(left.get("sign"), {})
        right_hint = SIGN_STYLE_HINTS.get(right.get("sign"), {})
        left_ruler = left.get("ruler_position") or {}
        right_ruler = right.get("ruler_position") or {}

        your_truth = (
            f"твой полюс тянет к режиму '{left_hint.get('tone', 'естественный ритм')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get(left_house, 'этой оси').lower()}"
        )
        partner_truth = (
            f"противоположный полюс требует '{right_hint.get('tone', 'свою правду')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get(right_house, 'ответной оси').lower()}"
        )
        task = (
            f"{left_hint.get('growth', 'собирать свой полюс в зрелую форму')} "
            f"и дать место теме {HOUSE_DOMAIN_MAP.get(right_house, 'противоположного дома').lower()}"
        )
        evidence = [
            _format_house_snapshot(left),
            _format_house_snapshot(right),
            _format_position_evidence(left_ruler),
            _format_position_evidence(right_ruler),
        ]
        sensitivity = (
            len(house_tenants.get(left_house, []))
            + len(house_tenants.get(right_house, []))
            + (1 if left_ruler.get("h") in {8, 12} else 0)
            + (1 if right_ruler.get("h") in {8, 12} else 0)
        )
        axis_polarities.append(
            {
                "axis": axis_key,
                "axis_label": axis_label,
                "your_truth": your_truth,
                "partner_truth": partner_truth,
                "task": task,
                "evidence": [item for item in evidence if item][:4],
            }
        )
        axis_tasks.append(
            {
                "axis": axis_key,
                "axis_label": axis_label,
                "task": task,
            }
        )
        tension_scores.append((axis_key, axis_label, sensitivity, evidence))

    tension_scores.sort(key=lambda item: item[2], reverse=True)
    dominant_axis_tension = {
        "axis": tension_scores[0][0] if tension_scores else "identity_vs_partner",
        "axis_label": tension_scores[0][1] if tension_scores else "ASC-DSC",
        "label": (
            f"самая чувствительная ось сейчас — {tension_scores[0][1]}"
            if tension_scores
            else "самая чувствительная ось определяется через базовые полярности карты"
        ),
        "score": _score_to_int(45 + (tension_scores[0][2] * 10 if tension_scores else 0)),
        "evidence": [item for item in (tension_scores[0][3] if tension_scores else []) if item][:4],
    }

    return {
        "version": "natal_v2_p2",
        "axis_polarities": axis_polarities,
        "axis_tasks": axis_tasks,
        "dominant_axis_tension": dominant_axis_tension,
        "cross_links": [
            "synthesis.core_conflict",
            "balance_wheel_1_6.house_pack",
            "balance_wheel_7_12.house_pack",
        ],
    }


def _build_aspects_beginner_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    aspect_templates = {
        "conjunction": {
            "anchor": "две функции карты работают как единый контур",
            "resource": "дает цельность, концентрацию и мощный общий вектор",
            "shadow": "сливает темы вместе, из-за чего сложнее отделять одно от другого",
            "key": "учиться различать роли, даже когда они спаяны",
        },
        "opposition": {
            "anchor": "две части психики стоят друг напротив друга и требуют баланса",
            "resource": "дает объемный взгляд и способность видеть обе стороны",
            "shadow": "дает качели, проекции и чувство внутреннего раздвоения",
            "key": "не выбирать один полюс насмерть, а строить мост между ними",
        },
        "square": {
            "anchor": "внутреннее трение заставляет действовать через напряжение",
            "resource": "дает мотор, выносливость и способность пробивать сложное",
            "shadow": "дает внутренний перегрев, конфликтность и давление на себя",
            "key": "переводить трение в задачу и ритм, а не в самоуничтожение",
        },
        "trine": {
            "anchor": "энергия между функциями течет естественно и без лишнего усилия",
            "resource": "дает врожденный талант и естественный ресурс",
            "shadow": "можно привыкнуть и не развивать то, что и так дается легко",
            "key": "осознанно капитализировать легкость, а не только полагаться на нее",
        },
        "sextile": {
            "anchor": "между функциями есть рабочая возможность, которую нужно включать действием",
            "resource": "дает навык, который хорошо собирается практикой",
            "shadow": "без инициативы аспект спит и не работает на полную",
            "key": "регулярно включать этот канал делом, а не ждать автоматизма",
        },
    }
    selected = sorted(chart_data.get("aspects", []), key=lambda item: item.get("orb", 99))[:6]
    aspect_cards = []
    for raw_aspect in selected:
        aspect = _compact_aspect_fact(raw_aspect)
        template = aspect_templates.get(aspect.get("t"), aspect_templates["sextile"])
        p1 = RU_PLANET_NAMES.get(aspect.get("p1"), aspect.get("p1") or "")
        p2 = RU_PLANET_NAMES.get(aspect.get("p2"), aspect.get("p2") or "")
        role1 = PLANET_ROLE_HINTS.get(aspect.get("p1"), aspect.get("p1") or "")
        role2 = PLANET_ROLE_HINTS.get(aspect.get("p2"), aspect.get("p2") or "")
        aspect_cards.append(
            {
                "aspect": f"{p1} {RU_ASPECTS.get(aspect.get('t'), aspect.get('t') or '')} {p2}",
                "orb": aspect.get("o"),
                "anchor": template["anchor"],
                "scenario": f"сюжет строится вокруг темы '{role1}' в связке с темой '{role2}'",
                "resource": template["resource"],
                "shadow": template["shadow"],
                "key": template["key"],
                "evidence": [_format_aspect_evidence(aspect)],
            }
        )

    return {
        "version": "natal_v2_p2",
        "aspect_cards": aspect_cards,
        "selection_rule": "взяты самые точные мажорные аспекты по орбису",
        "cross_links": [
            "synthesis.core_conflict",
            "executive_summary.strengths_score",
            "executive_summary.risk_score",
        ],
    }


def _build_nodes_growth_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    north = _get_point(position_lookup, "North Node", "True Node")
    south = _get_point(position_lookup, "South Node")
    south_hint = SIGN_STYLE_HINTS.get((south or {}).get("s"), {})
    north_hint = SIGN_STYLE_HINTS.get((north or {}).get("s"), {})
    south_domain = HOUSE_DOMAIN_MAP.get((south or {}).get("h"), "знакомой жизненной темы")
    north_domain = HOUSE_DOMAIN_MAP.get((north or {}).get("h"), "новой жизненной темы")

    node_drivers = []
    for pair in [("Sun", north), ("Moon", north), ("Saturn", north)]:
        planet_name, node_point = pair
        if not node_point:
            continue
        aspect = _find_aspect(chart_data, planet_name, node_point.get("p", node_point.get("name", "True Node")))
        if aspect:
            node_drivers.append(
                {
                    "planet": planet_name,
                    "aspect": _format_aspect_evidence(aspect),
                    "meaning": f"рост цепляется за тему '{PLANET_ROLE_HINTS.get(planet_name, planet_name)}'",
                }
            )

    south_node_habit = {
        "key": "south_node_habit",
        "label": (
            f"автоматически тянуться к режиму '{south_hint.get('tone', 'привычного способа')}' "
            f"в теме {south_domain.lower()}"
        ),
        "risk": south_hint.get("minus", "застревать в знакомом сценарии"),
        "evidence": [_format_position_evidence(south)],
    }
    north_node_direction = {
        "key": "north_node_direction",
        "label": (
            f"вектор роста — осваивать '{north_hint.get('growth', 'новый взрослый способ')}' "
            f"в теме {north_domain.lower()}"
        ),
        "mission": north_hint.get("growth", "двигаться в сторону нового сценария"),
        "evidence": [_format_position_evidence(north)],
    }
    bridge_task = {
        "key": "node_bridge_task",
        "label": (
            f"не выбрасывать опыт {south_domain.lower()}, а перевести его в более зрелую форму "
            f"ради задач {north_domain.lower()}"
        ),
        "evidence": [
            _format_position_evidence(south),
            _format_position_evidence(north),
            *(driver.get("aspect") for driver in node_drivers[:2]),
        ][:4],
    }

    return {
        "version": "natal_v2_p2",
        "south_node_habit": south_node_habit,
        "north_node_direction": north_node_direction,
        "bridge_task": bridge_task,
        "node_drivers": node_drivers,
        "cross_links": [
            "executive_summary.development_focus",
            "time_cycles.growth_tension",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_mercury_mind_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    mercury = _get_point(position_lookup, "Mercury")
    moon = _get_point(position_lookup, "Moon")
    saturn = _get_point(position_lookup, "Saturn")
    uranus = _get_point(position_lookup, "Uranus")

    mercury_moon = _find_aspect(chart_data, "Mercury", "Moon")
    mercury_saturn = _find_aspect(chart_data, "Mercury", "Saturn")
    mercury_uranus = _find_aspect(chart_data, "Mercury", "Uranus")

    thinking_candidates = {
        "structured_analyst": _new_rank_item(
            "structured_analyst",
            "мышление структурное: собираешь данные в каркас, категории и выводы",
        ),
        "intuitive_reader": _new_rank_item(
            "intuitive_reader",
            "мышление считывает подтекст, атмосферу и неочевидные сигналы",
        ),
        "unconventional_scanner": _new_rank_item(
            "unconventional_scanner",
            "мышление быстро сканирует систему и любит нестандартные ходы",
        ),
    }
    processing_modes = {
        "step_by_step_verification": _new_rank_item(
            "step_by_step_verification",
            "режим обработки: сначала собрать опору и логику, потом говорить",
        ),
        "jump_then_refine": _new_rank_item(
            "jump_then_refine",
            "режим обработки: сначала увидеть ход, потом доточить и проверить",
        ),
        "emotional_filtering": _new_rank_item(
            "emotional_filtering",
            "режим обработки: мысль сильно фильтруется текущим эмоциональным состоянием",
        ),
    }
    cognitive_risks = {
        "overcontrol_and_rumination": _new_rank_item(
            "overcontrol_and_rumination",
            "ловушка: перегружать мысль контролем, проверками и внутренней критикой",
        ),
        "abrupt_jumps": _new_rank_item(
            "abrupt_jumps",
            "ловушка: резкие скачки, отстраненность и разрыв между идеей и объяснением",
        ),
        "mood_bias": _new_rank_item(
            "mood_bias",
            "ловушка: мысль сильнее обычного окрашивается настроением и внутренней погодой",
        ),
    }

    if _sign_in(mercury, {"Capricorn", "Virgo", "Taurus"}):
        evidence = _format_position_evidence(mercury)
        _bump_rank(thinking_candidates, "structured_analyst", 16, evidence)
        _bump_rank(processing_modes, "step_by_step_verification", 12, evidence)
    if mercury_saturn:
        evidence = _format_aspect_evidence(mercury_saturn)
        _bump_rank(thinking_candidates, "structured_analyst", 12, evidence)
        _bump_rank(processing_modes, "step_by_step_verification", 10, evidence)
        _bump_rank(cognitive_risks, "overcontrol_and_rumination", 14, evidence)
    if _sign_in(mercury, {"Aquarius", "Gemini", "Sagittarius"}) or mercury_uranus:
        evidence = _format_position_evidence(mercury) or _format_aspect_evidence(mercury_uranus)
        _bump_rank(thinking_candidates, "unconventional_scanner", 14, evidence)
        _bump_rank(processing_modes, "jump_then_refine", 12, evidence)
        _bump_rank(cognitive_risks, "abrupt_jumps", 12, evidence)
    if _sign_in(mercury, {"Cancer", "Scorpio", "Pisces"}) or mercury_moon:
        evidence = _format_position_evidence(mercury) or _format_aspect_evidence(mercury_moon)
        _bump_rank(thinking_candidates, "intuitive_reader", 12, evidence)
        _bump_rank(processing_modes, "emotional_filtering", 12, evidence)
        _bump_rank(cognitive_risks, "mood_bias", 12, evidence)
    if _house_in(moon, {8, 12}):
        evidence = _format_position_evidence(moon)
        _bump_rank(processing_modes, "emotional_filtering", 8, evidence)
        _bump_rank(cognitive_risks, "mood_bias", 8, evidence)

    thinking_style = _pick_primary_ranked(
        thinking_candidates,
        fallback_key="structured_analyst",
        fallback_label="мышление структурное: собираешь данные в каркас, категории и выводы",
        fallback_evidence=[_format_position_evidence(mercury)],
    )
    processing_mode = _pick_primary_ranked(
        processing_modes,
        fallback_key="step_by_step_verification",
        fallback_label="режим обработки: сначала собрать опору и логику, потом говорить",
        fallback_evidence=[_format_position_evidence(mercury)],
    )
    mind_keys = {
        "key": "mind_key",
        "label": (
            "лучший ключ — сначала назвать структуру мысли, затем добавить интуитивный слой"
            if thinking_style.get("key") == "structured_analyst"
            else "лучший ключ — переводить быстрые инсайты в понятный алгоритм и язык"
        ),
        "evidence": [
            *(thinking_style.get("evidence", [])[:2]),
            *(processing_mode.get("evidence", [])[:2]),
        ][:4],
    }

    return {
        "version": "natal_v2_p2",
        "thinking_style": thinking_style,
        "processing_mode": processing_mode,
        "cognitive_risks": _finalize_ranked(cognitive_risks, limit=3),
        "mind_keys": mind_keys,
        "cross_links": [
            "synthesis.identity_vector",
            "executive_summary.risk_score",
            "shadow_trauma.compensation_modes",
        ],
    }


def _build_shadow_trauma_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    chiron = _get_point(position_lookup, "Chiron")
    lilith = _get_point(position_lookup, "Lilith", "Mean Apogee")
    moon = _get_point(position_lookup, "Moon")
    saturn = _get_point(position_lookup, "Saturn")
    pluto = _get_point(position_lookup, "Pluto")

    chiron_hint = SIGN_STYLE_HINTS.get((chiron or {}).get("s"), {})
    lilith_hint = SIGN_STYLE_HINTS.get((lilith or {}).get("s"), {})

    chiron_pattern = {
        "anchor": (
            f"уязвимость в теме {HOUSE_DOMAIN_MAP.get((chiron or {}).get('h'), 'личной боли').lower()} "
            f"через сюжет '{chiron_hint.get('tone', 'тонкой настройки')}'"
        ),
        "scenario": "болевая точка включается там, где хочется сразу быть сильным и безошибочным",
        "resource": chiron_hint.get("growth", "в боли спрятан навык настройки и исцеления"),
        "shadow": chiron_hint.get("minus", "есть риск застревать в уязвимости и защите"),
        "key": "работать с уязвимостью как с настройкой, а не как с дефектом",
        "evidence": [_format_position_evidence(chiron)],
    }
    lilith_pattern = {
        "anchor": (
            f"теневая сила в теме {HOUSE_DOMAIN_MAP.get((lilith or {}).get('h'), 'теневой зоны').lower()} "
            f"через сюжет '{lilith_hint.get('tone', 'сырой силы')}'"
        ),
        "scenario": "искушение — брать власть, уходить в крайность или проверять мир на прочность",
        "resource": lilith_hint.get("plus", "внутри есть raw-энергия и смелость видеть неудобное"),
        "shadow": lilith_hint.get("minus", "крайности, борьба за контроль или разрушительная резкость"),
        "key": "переводить сырую силу в осознанные границы и выбор",
        "evidence": [_format_position_evidence(lilith)],
    }

    pain_points = [
        {
            "label": f"боль чаще всего цепляет тему {HOUSE_DOMAIN_MAP.get((chiron or {}).get('h'), 'уязвимости').lower()}",
            "evidence": [_format_position_evidence(chiron)],
        },
        {
            "label": f"теневое напряжение особенно видно в теме {HOUSE_DOMAIN_MAP.get((lilith or {}).get('h'), 'контроля').lower()}",
            "evidence": [_format_position_evidence(lilith)],
        },
    ]
    compensation_modes = []
    if saturn:
        compensation_modes.append(
            {
                "key": "saturn_control",
                "label": "компенсация через самоконтроль, сжатие и внутренний прессинг",
                "evidence": [_format_position_evidence(saturn)],
            }
        )
    if pluto:
        compensation_modes.append(
            {
                "key": "pluto_control",
                "label": "компенсация через контроль, силовую проверку и нежелание быть слабым",
                "evidence": [_format_position_evidence(pluto)],
            }
        )
    if moon:
        compensation_modes.append(
            {
                "key": "moon_retreat",
                "label": "компенсация через уход в молчание, закрытие или проживание боли в одиночку",
                "evidence": [_format_position_evidence(moon)],
            }
        )

    integration_task = {
        "key": "shadow_integration",
        "label": "зрелая задача — признать и боль, и темную силу, не отдавая управление ни стыду, ни контролю",
        "evidence": [
            _format_position_evidence(chiron),
            _format_position_evidence(lilith),
            _format_position_evidence(saturn),
            _format_position_evidence(pluto),
        ][:4],
    }

    return {
        "version": "natal_v2_p2",
        "chiron_pattern": chiron_pattern,
        "lilith_pattern": lilith_pattern,
        "pain_points": pain_points,
        "compensation_modes": compensation_modes[:3],
        "integration_task": integration_task,
        "cross_links": [
            "executive_summary.risk_score",
            "mercury_mind.cognitive_risks",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_core_triad_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    asc = _get_point(position_lookup, "ASC")
    sun = _get_point(position_lookup, "Sun")
    moon = _get_point(position_lookup, "Moon")

    asc_hint = SIGN_STYLE_HINTS.get((asc or {}).get("s"), {})
    sun_hint = SIGN_STYLE_HINTS.get((sun or {}).get("s"), {})
    moon_hint = SIGN_STYLE_HINTS.get((moon or {}).get("s"), {})

    sun_moon = _find_aspect(chart_data, "Sun", "Moon")
    sun_asc = _find_aspect(chart_data, "Sun", "ASC")
    moon_asc = _find_aspect(chart_data, "Moon", "ASC")
    sun_saturn = _find_aspect(chart_data, "Sun", "Saturn")
    sun_neptune = _find_aspect(chart_data, "Sun", "Neptune")

    asc_mask = {
        "key": "asc_mask",
        "label": (
            f"во внешний мир ты входишь через режим '{asc_hint.get('tone', 'естественной самоподачи')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get((asc or {}).get('h'), 'личной подачи').lower()}"
        ),
        "growth": asc_hint.get("growth", "делать подачу зрелой и управляемой"),
        "evidence": [
            _format_position_evidence(asc),
            _format_aspect_evidence(sun_asc),
            _format_aspect_evidence(moon_asc),
        ][:4],
    }
    solar_drive = {
        "key": "solar_drive",
        "label": (
            f"воля и чувство направления включаются через '{sun_hint.get('plus', 'ядро воли')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get((sun or {}).get('h'), 'самореализации').lower()}"
        ),
        "risk": sun_hint.get("minus", "есть риск перегнуть волю или контроль"),
        "evidence": [
            _format_position_evidence(sun),
            _format_aspect_evidence(sun_saturn),
            _format_aspect_evidence(sun_neptune),
        ][:4],
    }
    lunar_need = {
        "key": "lunar_need",
        "label": (
            f"эмоциональная база просит '{moon_hint.get('plus', 'эмоциональной опоры')}' "
            f"в теме {HOUSE_DOMAIN_MAP.get((moon or {}).get('h'), 'внутренней безопасности').lower()}"
        ),
        "risk": moon_hint.get("minus", "есть риск уходить в крайности настроения"),
        "evidence": [
            _format_position_evidence(moon),
            _format_aspect_evidence(sun_moon),
            _format_aspect_evidence(moon_asc),
        ][:4],
    }

    sun_element = SIGN_ELEMENT_MAP.get((sun or {}).get("s"))
    moon_element = SIGN_ELEMENT_MAP.get((moon or {}).get("s"))
    asc_element = SIGN_ELEMENT_MAP.get((asc or {}).get("s"))

    if _is_tense(sun_moon):
        conflict_key = "will_vs_feelings"
        conflict_label = "ядро личности и эмоции спорят напрямую: воля тянет в один режим, чувства требуют другого темпа"
        conflict_evidence = [_format_aspect_evidence(sun_moon)]
    elif sun_saturn:
        conflict_key = "high_standard_pressure"
        conflict_label = "ядро карты собрано через высокий стандарт и ответственность, поэтому мягкость к себе дается не сразу"
        conflict_evidence = [
            _format_aspect_evidence(sun_saturn),
            _format_position_evidence(sun),
        ]
    elif sun_neptune:
        conflict_key = "clarity_vs_blur"
        conflict_label = "между потребностью держать курс и тягой уходить в идеал, атмосферу или расплывчатый образ"
        conflict_evidence = [
            _format_aspect_evidence(sun_neptune),
            _format_position_evidence(moon),
        ]
    elif sun_element and moon_element and sun_element != moon_element:
        conflict_key = "outer_plan_vs_inner_flow"
        conflict_label = "внешний курс и внутренний ритм собраны из разных стихий, поэтому важно не требовать от себя одной скорости всегда"
        conflict_evidence = [
            _format_position_evidence(sun),
            _format_position_evidence(moon),
        ]
    else:
        conflict_key = "mask_vs_need"
        conflict_label = "главная настройка в том, чтобы маска, воля и чувства не жили тремя разными траекториями"
        conflict_evidence = [
            _format_position_evidence(asc),
            _format_position_evidence(sun),
            _format_position_evidence(moon),
        ]

    triad_conflict = {
        "key": conflict_key,
        "label": conflict_label,
        "score": _score_to_int(
            58
            + (12 if _is_tense(sun_moon) else 0)
            + (8 if sun_saturn else 0)
            + (6 if sun_neptune else 0)
        ),
        "evidence": [item for item in conflict_evidence if item][:4],
    }

    integration_parts = [
        asc_hint.get("growth"),
        sun_hint.get("growth"),
        moon_hint.get("growth"),
    ]
    if asc_element and sun_element and asc_element == sun_element:
        integration_label = "внешняя подача и воля уже говорят на одном языке; задача — добавить туда эмоциональную честность и регулярную самонастройку"
    elif moon_element and sun_element and moon_element == sun_element:
        integration_label = "ядро и чувства близки по природе; задача — чтобы внешняя маска не мешала этой внутренней согласованности"
    else:
        integration_label = "сборка ядра идет через согласование трех скоростей: как входишь, чего хочешь и что тебе реально нужно для опоры"

    triad_integration = {
        "key": "triad_integration",
        "label": integration_label,
        "steps": [part for part in integration_parts if part][:3],
        "evidence": [
            _format_position_evidence(asc),
            _format_position_evidence(sun),
            _format_position_evidence(moon),
        ][:4],
    }

    return {
        "version": "natal_v2_p3",
        "asc_mask": asc_mask,
        "solar_drive": solar_drive,
        "lunar_need": lunar_need,
        "triad_conflict": triad_conflict,
        "triad_integration": triad_integration,
        "cross_links": [
            "synthesis.identity_vector",
            "executive_summary.development_focus",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_configurations_geometry_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    pattern_templates = {
        "T-square": {
            "geometry": "две точки стоят в оппозиции и стягиваются в третью как в точку давления и сборки",
            "gift": "дает мотор, выносливость и способность расти через напряжение",
            "risk": "можно жить в режиме вечной внутренней тревоги, конфликта и перегрева",
            "question": "куда уходит лишнее напряжение и какую задачу ты пытаешься продавить любой ценой",
            "key": "искать устойчивый канал разрядки и превращать давление в ритм, а не в хаос",
        },
        "Т-квадрат": {
            "geometry": "две точки стоят в оппозиции и стягиваются в третью как в точку давления и сборки",
            "gift": "дает мотор, выносливость и способность расти через напряжение",
            "risk": "можно жить в режиме вечной внутренней тревоги, конфликта и перегрева",
            "question": "куда уходит лишнее напряжение и какую задачу ты пытаешься продавить любой ценой",
            "key": "искать устойчивый канал разрядки и превращать давление в ритм, а не в хаос",
        },
        "Grand Trine": {
            "geometry": "три точки связаны легким потоком и образуют устойчивый контур таланта",
            "gift": "дает врожденный ресурс, интуитивную согласованность и ощущение естественного дара",
            "risk": "легкость может усыплять и откладывать развитие того, что и так получается",
            "question": "как превратить врожденную легкость в осознанный навык и капитал",
            "key": "не полагаться только на дар, а строить на нем дисциплину и форму",
        },
        "Большой тригон": {
            "geometry": "три точки связаны легким потоком и образуют устойчивый контур таланта",
            "gift": "дает врожденный ресурс, интуитивную согласованность и ощущение естественного дара",
            "risk": "легкость может усыплять и откладывать развитие того, что и так получается",
            "question": "как превратить врожденную легкость в осознанный навык и капитал",
            "key": "не полагаться только на дар, а строить на нем дисциплину и форму",
        },
        "Grand Cross": {
            "geometry": "четыре точки держат напряжение по двум осям и не дают расслабиться без осознанной структуры",
            "gift": "дает огромную живучесть, объем и способность держать несколько фронтов сразу",
            "risk": "можно привыкнуть жить только через давление и кризисную мобилизацию",
            "question": "где ты подменяешь ясную стратегию постоянной обороной или атакой",
            "key": "собирать оси в систему приоритетов, а не пытаться тащить все одновременно",
        },
        "Большой крест": {
            "geometry": "четыре точки держат напряжение по двум осям и не дают расслабиться без осознанной структуры",
            "gift": "дает огромную живучесть, объем и способность держать несколько фронтов сразу",
            "risk": "можно привыкнуть жить только через давление и кризисную мобилизацию",
            "question": "где ты подменяешь ясную стратегию постоянной обороной или атакой",
            "key": "собирать оси в систему приоритетов, а не пытаться тащить все одновременно",
        },
        "Yod": {
            "geometry": "две точки сходятся в острую вершину и создают чувство тонкой настройки или судьбоносного прицела",
            "gift": "дает специфический талант и способность видеть тонкие корректировки маршрута",
            "risk": "можно жить в режиме хронической неудовлетворенности и ожидания идеального попадания",
            "question": "какая вершина карты требует не паники, а точной настройки и терпения",
            "key": "относиться к конфигурации как к маршруту настройки, а не как к приговору",
        },
        "Йод": {
            "geometry": "две точки сходятся в острую вершину и создают чувство тонкой настройки или судьбоносного прицела",
            "gift": "дает специфический талант и способность видеть тонкие корректировки маршрута",
            "risk": "можно жить в режиме хронической неудовлетворенности и ожидания идеального попадания",
            "question": "какая вершина карты требует не паники, а точной настройки и терпения",
            "key": "относиться к конфигурации как к маршруту настройки, а не как к приговору",
        },
        "Kite": {
            "geometry": "легкий ресурсный контур получает направляющую ось и возможность превратить талант в траекторию",
            "gift": "дает шанс направить врожденный дар в видимую задачу и результат",
            "risk": "часть ресурса может уходить в расфокус, если ось не проживается осознанно",
            "question": "куда именно просится твой природный талант, если дать ему направление",
            "key": "связывать легкость, цель и дисциплину, чтобы талант не распылялся",
        },
        "Кайт": {
            "geometry": "легкий ресурсный контур получает направляющую ось и возможность превратить талант в траекторию",
            "gift": "дает шанс направить врожденный дар в видимую задачу и результат",
            "risk": "часть ресурса может уходить в расфокус, если ось не проживается осознанно",
            "question": "куда именно просится твой природный талант, если дать ему направление",
            "key": "связывать легкость, цель и дисциплину, чтобы талант не распылялся",
        },
    }

    configuration_cards = []
    for pattern in chart_data.get("patterns", []):
        points = [
            _normalize_point_name(point)
            for point in (pattern.get("point_keys") or pattern.get("points", []))
        ]
        template = pattern_templates.get(pattern.get("type"), {
            "geometry": "в карте есть связанная фигура, которая собирает несколько тем в общий сценарий",
            "gift": "она дает дополнительную структурность и видимый повторяющийся сюжет",
            "risk": "если ее не осознавать, одна и та же сцепка будет повторяться слишком автоматически",
            "question": "какой общий паттерн ты проживаешь снова и снова",
            "key": "сначала назвать повторяющийся узор, а затем выбрать взрослый способ его проживать",
        })
        point_evidence = [
            _format_position_evidence(position_lookup.get(point))
            for point in points[:3]
            if position_lookup.get(point)
        ]
        configuration_cards.append(
            {
                "type": pattern.get("type") or "Конфигурация",
                "points": points,
                "points_label": _format_planet_name_list(points, limit=6),
                "geometry": template["geometry"],
                "gift": template["gift"],
                "risk": template["risk"],
                "question": template["question"],
                "key": template["key"],
                "evidence": [
                    f"точки конфигурации: {_format_planet_name_list(points, limit=6)}",
                    *point_evidence,
                ][:4],
            }
        )

    dominant_pattern = configuration_cards[0] if configuration_cards else None
    absence_summary = {
        "key": "no_major_configurations",
        "label": "жестких конфигураций в карте не видно: основные сюжеты читаются через отдельные аспекты и оси, а не через большую геометрию",
    }

    return {
        "version": "natal_v2_p3",
        "configuration_cards": configuration_cards,
        "dominant_pattern": dominant_pattern,
        "absence_summary": absence_summary,
        "cross_links": [
            "aspects_beginner.aspect_cards",
            "synthesis.core_conflict",
            "final_synthesis.top_conflict_vs_top_resource",
        ],
    }


def _build_vertex_fate_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    vertex = _get_point(position_lookup, "Vertex")
    venus = _get_point(position_lookup, "Venus")
    mars = _get_point(position_lookup, "Mars")
    moon = _get_point(position_lookup, "Moon")
    dsc = _get_point(position_lookup, "DSC")

    vertex_sign = (vertex or {}).get("s")
    vertex_hint = SIGN_STYLE_HINTS.get(vertex_sign, {})
    vertex_house = (vertex or {}).get("h")
    vertex_domain = HOUSE_DOMAIN_MAP.get(vertex_house, "сюжетных встреч")
    vertex_ruler = SIGN_RULER_MAP.get(vertex_sign)
    vertex_ruler_position = position_lookup.get(vertex_ruler) if vertex_ruler else None

    encounter_triggers = [
        {
            "key": "vertex_house_trigger",
            "label": f"сюжетные встречи включаются через тему {vertex_domain.lower()}",
            "evidence": [_format_position_evidence(vertex)],
        }
    ]
    if vertex_ruler_position:
        encounter_triggers.append(
            {
                "key": "vertex_ruler_trigger",
                "label": (
                    f"сценарий чаще приходит через тему "
                    f"{HOUSE_DOMAIN_MAP.get(vertex_ruler_position.get('h'), 'дома управителя').lower()}"
                ),
                "evidence": [
                    _format_position_evidence(vertex_ruler_position),
                    _format_position_evidence(vertex),
                ][:4],
            }
        )
    if _house_in(venus, {5, 7, 8}) or _house_in(mars, {5, 7, 8}) or _house_in(moon, {5, 7, 8, 12}):
        encounter_triggers.append(
            {
                "key": "relationship_house_trigger",
                "label": "важные встречи цепляют романтический, партнерский или глубинно-эмоциональный контур карты",
                "evidence": [
                    _format_position_evidence(venus),
                    _format_position_evidence(mars),
                    _format_position_evidence(moon),
                ][:4],
            }
        )

    vertex_signature = {
        "key": "vertex_signature",
        "label": (
            f"Вертекс показывает встречи в режиме '{vertex_hint.get('tone', 'особого притяжения')}' "
            f"через тему {vertex_domain.lower()}"
        ),
        "lesson": vertex_hint.get("growth", "учиться проживать встречи осознанно, а не как чистый рок"),
        "evidence": [
            _format_position_evidence(vertex),
            _format_position_evidence(vertex_ruler_position),
        ][:4],
    }

    if vertex_sign in {"Libra", "Taurus"} or _house_in(venus, {7, 11}):
        vector_key = "relational_mirror"
        vector_label = "сюжетные встречи часто приходят через зеркало отношений, договоренностей и вопроса равновесия"
        vector_evidence = [
            _format_position_evidence(vertex),
            _format_position_evidence(venus),
            _format_position_evidence(dsc),
        ]
    elif vertex_sign in {"Scorpio", "Sagittarius"} or _house_in(mars, {8}):
        vector_key = "transformative_encounter"
        vector_label = "важные встречи несут заряд поворота, риска и глубокой внутренней перестройки"
        vector_evidence = [
            _format_position_evidence(vertex),
            _format_position_evidence(mars),
            _format_position_evidence(moon),
        ]
    else:
        vector_key = "meaningful_alliance"
        vector_label = "сюжетные люди включают не только чувства, но и смену курса, роли или способа видеть себя"
        vector_evidence = [
            _format_position_evidence(vertex),
            _format_position_evidence(vertex_ruler_position),
            _format_position_evidence(dsc),
        ]

    relationship_vector = {
        "key": vector_key,
        "label": vector_label,
        "evidence": [item for item in vector_evidence if item][:4],
    }
    fated_lesson = {
        "key": "vertex_fated_lesson",
        "label": (
            f"главный урок Вертекса — {vertex_hint.get('growth', 'не путать притяжение с зрелым выбором')} "
            f"и связывать это с темой {HOUSE_DOMAIN_MAP.get((vertex_ruler_position or {}).get('h'), vertex_domain).lower()}"
        ),
        "evidence": [
            _format_position_evidence(vertex),
            _format_position_evidence(vertex_ruler_position),
            _format_position_evidence(dsc),
        ][:4],
    }

    return {
        "version": "natal_v2_p3",
        "vertex_signature": vertex_signature,
        "encounter_triggers": encounter_triggers[:3],
        "relationship_vector": relationship_vector,
        "fated_lesson": fated_lesson,
        "cross_links": [
            "love_intimacy.partnership_needs",
            "axes_truths.dominant_axis_tension",
            "final_synthesis.one_sentence_advice",
        ],
    }


def _build_outer_planet_vector(
    planet_name: str,
    chart_data: dict,
    position_lookup: Dict[str, dict],
) -> Dict[str, Any]:
    position = _get_point(position_lookup, planet_name)
    hint = SIGN_STYLE_HINTS.get((position or {}).get("s"), {})
    domain = HOUSE_DOMAIN_MAP.get((position or {}).get("h"), "долгого жизненного сюжета")
    contacts = []
    for target in ["Sun", "Moon", "Saturn"]:
        aspect = _find_aspect(chart_data, planet_name, target)
        if aspect:
            contacts.append(aspect)

    base_label = (
        f"{RU_PLANET_NAMES.get(planet_name, planet_name)} включает тему {domain.lower()} "
        f"через режим '{hint.get('tone', 'долгого влияния')}'"
    )
    if planet_name == "Uranus":
        gift = "дар: запускать обновление, освобождать маршрут и видеть нестандартный ход"
        risk = "риск: резкие повороты, нетерпение к ограничениям и скачкообразные решения"
    elif planet_name == "Neptune":
        gift = "дар: усиливать интуицию, воображение и чувствительность к смыслу и атмосфере"
        risk = "риск: идеализация, туман критериев и потеря границ"
    else:
        gift = "дар: проходить через кризис, глубину и собирать силу из сложных сюжетов"
        risk = "риск: контроль, силовые игры и жизнь через крайние режимы"

    if any(_is_tense(contact) for contact in contacts):
        risk += "; напряженные связи с личными точками усиливают ощущение внутреннего давления"
    if any(_is_harmonious(contact) for contact in contacts):
        gift += "; есть рабочий канал, через который высшая планета легче встраивается в личную жизнь"

    return {
        "planet": planet_name,
        "label": base_label,
        "gift": gift,
        "risk": risk,
        "key": hint.get("growth", "делать влияние этой планеты осознанным и управляемым"),
        "evidence": [
            _format_position_evidence(position),
            *(_format_aspect_evidence(contact) for contact in contacts[:2]),
        ][:4],
    }


def _build_stars_transuranus_insight_pack(
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
) -> Dict[str, Any]:
    uranus_vector = _build_outer_planet_vector("Uranus", chart_data, position_lookup)
    neptune_vector = _build_outer_planet_vector("Neptune", chart_data, position_lookup)
    pluto_vector = _build_outer_planet_vector("Pluto", chart_data, position_lookup)

    outer_contacts = []
    for pair in [("Sun", "Uranus"), ("Sun", "Neptune"), ("Saturn", "Neptune"), ("Saturn", "Pluto")]:
        aspect = _find_aspect(chart_data, pair[0], pair[1])
        if aspect:
            outer_contacts.append(aspect)

    collective_story = {
        "key": "collective_story",
        "label": (
            "высшие планеты собирают карту в сюжет, где обновление, идеал и глубинная сила постоянно влияют на жизненный курс"
            if outer_contacts
            else "высшие планеты работают фоном: их темы важны не как событие, а как долгий стиль взросления"
        ),
        "evidence": [
            *(_format_aspect_evidence(aspect) for aspect in outer_contacts[:3]),
            uranus_vector.get("label"),
        ][:4],
    }

    fixed_star_hooks = []
    for star in chart_data.get("fixed_stars", [])[:3]:
        normalized_star = _normalize_fixed_star_record(star)
        name = normalized_star.get("name") or "Fixed star"
        point = normalized_star.get("point")
        orb = normalized_star.get("orb")
        fixed_star_hooks.append(
            {
                "name": name,
                "point": point,
                "label": (
                    f"если использовать fixed stars, {name} цепляется за "
                    f"{RU_PLANET_NAMES.get(point, point or 'точку карты')}"
                ),
                "evidence": [
                    (
                        f"{name} ~ {RU_PLANET_NAMES.get(point, point or 'точка карты')} "
                        f"(orb {orb}°)"
                        if orb is not None
                        else f"{name} ~ {RU_PLANET_NAMES.get(point, point or 'точка карты')}"
                    )
                ],
            }
        )

    return {
        "version": "natal_v2_p3",
        "uranus_vector": uranus_vector,
        "neptune_vector": neptune_vector,
        "pluto_vector": pluto_vector,
        "collective_story": collective_story,
        "fixed_star_hooks": fixed_star_hooks,
        "cross_links": [
            "executive_summary.risk_score",
            "aspects_beginner.aspect_cards",
            "time_cycles.growth_tension",
        ],
    }


def _build_natal_section_insight_pack(
    section_id: str,
    facts: dict,
    chart_data: dict,
    position_lookup: Dict[str, dict],
    house_lookup: Dict[int, dict],
    client: Optional[dict] = None,
    forecast_window: Optional[dict] = None,
) -> Optional[Dict[str, Any]]:
    if section_id == "executive_summary":
        return _build_executive_summary_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "framework_elements_modes":
        return _build_framework_elements_modes_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "synthesis":
        return _build_synthesis_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "money_realization":
        return _build_money_realization_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "love_intimacy":
        return _build_love_intimacy_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "final_synthesis":
        return _build_final_synthesis_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "dispositor_office":
        return _build_dispositor_office_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id in {"balance_wheel_1_6", "balance_wheel_7_12"}:
        return _build_balance_wheel_insight_pack(
            section_id, facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "time_cycles":
        return _build_time_cycles_insight_pack(
            facts,
            chart_data,
            position_lookup,
            house_lookup,
            client,
            forecast_window,
        )
    if section_id == "axes_truths":
        return _build_axes_truths_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "aspects_beginner":
        return _build_aspects_beginner_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "nodes_growth":
        return _build_nodes_growth_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "mercury_mind":
        return _build_mercury_mind_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "shadow_trauma":
        return _build_shadow_trauma_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "core_triad":
        return _build_core_triad_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "configurations_geometry":
        return _build_configurations_geometry_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "vertex_fate":
        return _build_vertex_fate_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    if section_id == "stars_transuranus":
        return _build_stars_transuranus_insight_pack(
            facts, chart_data, position_lookup, house_lookup
        )
    return None


def build_section_context(section_id: str, global_context: dict, chart_data: dict) -> dict:
    """
    # PURPOSE: Build a section-specific context pack to keep natal prompts compact.
    # INPUT: section_id, global_context, chart_data.
    # OUTPUT: Trimmed context dict for the current section.
    # CONTEXT: Used only for natal LLM sections; other report types keep the global context.
    """

    context = copy.deepcopy(global_context)
    client = context.get("client", {})
    report_type = client.get("report_type")
    if report_type in {"week_forecast", "month_forecast"}:
        return _build_forecast_prompt_context(context)
    if report_type != "natal_master":
        return context

    if section_id in {"input_frame", "technical_appendix"}:
        return context

    rule = NATAL_SECTION_CONTEXT_RULES.get(section_id)
    if rule is None and section_id not in NATAL_SECTION_IDS and section_id != "executive_summary":
        return context
    rule = copy.deepcopy(rule or DEFAULT_NATAL_SECTION_CONTEXT_RULE)

    facts = context.get("facts", {})
    position_names = _unique_preserve_order(rule.get("positions", []))
    house_numbers = _unique_preserve_order(rule.get("houses", []))
    aspect_points = _unique_preserve_order(rule.get("aspect_points", position_names))
    aspect_limit = int(rule.get("aspect_limit", 0) or 0)

    position_lookup = _build_position_lookup(facts, chart_data)
    house_lookup = _build_house_lookup(facts, chart_data)

    filtered_facts: Dict[str, Any] = {
        "v": facts.get("v", "facts_v1"),
        "tz": facts.get("tz", "UTC"),
        "pos": [copy.deepcopy(position_lookup[name]) for name in position_names if name in position_lookup],
        "houses": [copy.deepcopy(house_lookup[number]) for number in house_numbers if number in house_lookup],
        "aspects": _collect_section_aspects(chart_data, aspect_points, aspect_limit),
    }
    if rule.get("include_balance") and facts.get("balance") is not None:
        filtered_facts["balance"] = copy.deepcopy(facts.get("balance"))
    if facts.get("_truncated"):
        filtered_facts["_truncated"] = True

    trimmed_context: Dict[str, Any] = {
        "client": copy.deepcopy(client),
        "forecast_window": copy.deepcopy(context.get("forecast_window", {})),
        "facts": filtered_facts,
        "section_context": {
            "section_id": section_id,
            "focus": rule.get("focus"),
            "relevant_points": position_names,
            "relevant_houses": house_numbers,
        },
    }

    chart_pack = _build_section_chart_pack(rule, chart_data)
    if chart_pack:
        trimmed_context["chart"] = chart_pack

    if rule.get("include_patterns"):
        patterns = _collect_section_patterns(chart_data, position_names)
        if patterns:
            trimmed_context["section_context"]["patterns"] = patterns

    if rule.get("include_balance") and facts.get("balance") is not None:
        trimmed_context["section_context"]["balance"] = copy.deepcopy(facts.get("balance"))

    if section_id in {"balance_wheel_1_6", "balance_wheel_7_12"}:
        trimmed_context["section_context"]["house_context"] = format_house_context(chart_data)

    if section_id in FACTS_FIRST_INSIGHT_PACK_SECTION_IDS:
        insight_pack = _build_natal_section_insight_pack(
            section_id,
            filtered_facts,
            chart_data,
            position_lookup,
            house_lookup,
            client,
            context.get("forecast_window", {}),
        )
        if insight_pack:
            trimmed_context["section_context"]["insight_pack"] = insight_pack

    return trimmed_context


def build_report_context(payload: Any, chart_data: dict) -> dict:
    """
    # START_CONTRACT: FN-BUILD-REPORT-CONTEXT
    # purpose: Assemble canonical prompt/runtime context for report generation and resume flows.
    # inputs: report payload plus canonical chart_data dictionary.
    # returns: context dict for semantic blocks, llm orchestration, and fallback rendering.
    # side_effects: emits context assembly and forecast semantic-layer logs.
    # errors: suppresses forecast enrichment failures into logs while preserving base context output.
    # END_CONTRACT: FN-BUILD-REPORT-CONTEXT
    """
    
    # START_BLOCK: FORECAST_WINDOW_RESOLUTION
    # Determine forecast timezone (current location > birth location > UTC)
    forecast_tz = (
        payload.solar_current_timezone 
        or payload.birth_timezone 
        or "UTC"
    )
    
    forecast_window = build_forecast_window(payload.report_type, forecast_tz)
    _workflow_log(
        "info",
        "report.workflow.context_forecast_window",
        fn="build_report_context",
        contract="FN-BUILD-REPORT-CONTEXT",
        block="FORECAST_WINDOW_RESOLUTION",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
        forecast_timezone=forecast_tz,
    )
    # END_BLOCK: FORECAST_WINDOW_RESOLUTION

    # START_BLOCK: CLIENT_PROFILE_NORMALIZATION
    # Clean client name (remove text in parentheses)
    clean_name = payload.client_name
    clean_name = re.sub(r'\s*\(.*?\)', '', clean_name)
    clean_name = re.sub(r'\s*\[.*?\]', '', clean_name)
    clean_name = clean_name.strip()
    _workflow_log(
        "info",
        "report.workflow.context_client_name_cleaned",
        fn="build_report_context",
        contract="FN-BUILD-REPORT-CONTEXT",
        block="CLIENT_PROFILE_NORMALIZATION",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
        original=payload.client_name,
        cleaned=clean_name,
    )

    # Inferred gender
    gender = infer_gender(clean_name)
    
    # Base context
    display_birth_date = payload.birth_date
    if (
        payload.birth_date
        and payload.birth_timezone
        and payload.report_type not in ["horary", "horary_answer"]
    ):
        display_birth_date = normalize_datetime_input(
            payload.birth_date,
            payload.birth_timezone,
            assume_local=False,
        )

    display_partner_birth_date = payload.partner_birth_date
    if payload.partner_birth_date and payload.partner_birth_timezone:
        display_partner_birth_date = normalize_datetime_input(
            payload.partner_birth_date,
            payload.partner_birth_timezone,
            assume_local=False,
        )

    context = {
        "client": {
            "name": clean_name,
            "gender": "женский" if gender == "female" else "мужской",
            "note": payload.client_note,
            "question": getattr(payload, "question", None) or payload.client_note,
            "birth_date": display_birth_date,
            "birth_location": payload.birth_location,
            "birth_lat": payload.birth_lat,
            "birth_lon": payload.birth_lon,
            "birth_timezone": payload.birth_timezone,
            "birth_place_id": payload.birth_place_id,
            "birth_time_known": getattr(payload, "birth_time_known", True),
            "report_type": payload.report_type,
        },
        "partner": {
            "name": payload.partner_name,
            "birth_date": display_partner_birth_date,
            "birth_location": payload.partner_birth_location,
            "birth_lat": payload.partner_birth_lat,
            "birth_lon": payload.partner_birth_lon,
            "birth_timezone": payload.partner_birth_timezone,
            "birth_place_id": payload.partner_birth_place_id,
        },
        "solar": {
            "current_location": payload.solar_current_location,
            "current_lat": payload.solar_current_lat,
            "current_lon": payload.solar_current_lon,
            "current_timezone": payload.solar_current_timezone,
            "current_place_id": payload.solar_current_place_id,
            "next_location": payload.solar_next_location,
            "next_lat": payload.solar_next_lat,
            "next_lon": payload.solar_next_lon,
            "next_timezone": payload.solar_next_timezone,
            "next_place_id": payload.solar_next_place_id,
        },
        "forecast_window": forecast_window,
        "facts": get_chart_facts_json(chart_data)
    }

    # END_BLOCK: CLIENT_PROFILE_NORMALIZATION

    # START_BLOCK: FACTS_CONTEXT_TRIM
    # Optimization: context size control for free models
    # If facts JSON is too large, it can trigger 402 on OpenRouter free accounts
    facts_json = json.dumps(context["facts"])
    if len(facts_json) > 3000:
        _workflow_log(
            "info",
            "report.workflow.context_facts_truncated",
            fn="build_report_context",
            contract="FN-BUILD-REPORT-CONTEXT",
            block="FACTS_CONTEXT_TRIM",
            report_id=getattr(payload, "report_id", None),
            report_type=getattr(payload, "report_type", None),
            original_len=len(facts_json),
        )
        # Simple truncation of aspects if too many
        if len(context["facts"].get("aspects", [])) > 10:
            context["facts"]["aspects"] = context["facts"]["aspects"][:10]
            context["facts"]["_truncated"] = True

    # Optimization: for horary, we don't need the full 'chart' object anymore
    # because 'facts' contains all essentials.
    if payload.report_type not in ["horary", "horary_answer"]:
        context["chart"] = chart_data

    # END_BLOCK: FACTS_CONTEXT_TRIM

    # START_BLOCK: FORECAST_SEMANTIC_LAYER
    # Inject detailed forecast data
    if payload.report_type in ["year_forecast", "week_forecast", "month_forecast", "ten_year_forecast"]:
        try:
            engine = StelliumEngine()
            house_system = engine_utils.resolve_house_system(payload.house_system)
            
            clean_birth_date = payload.birth_date
            if "+" in clean_birth_date:
                clean_birth_date = clean_birth_date.split("+")[0]
            
            location_input = payload.birth_location
            if payload.birth_lat is not None and payload.birth_lon is not None:
                location_input = {
                    "latitude": payload.birth_lat,
                    "longitude": payload.birth_lon,
                    "name": payload.birth_location or payload.client_name,
                }
                
            natal_chart = engine.create_natal_chart(
                payload.client_name,
                clean_birth_date,
                location_input,
                house_system,
            )
            
            forecast_loc = payload.solar_current_location or payload.birth_location
            
            if payload.report_type == "year_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                    target_year = start_dt.year
                except:
                    target_year = datetime.now(timezone.utc).year
                    
                context["year_forecast_data"] = engine.calculate_forecast_year_data(
                    natal_chart,
                    target_year,
                    forecast_loc
                )
                
            elif payload.report_type == "week_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                except:
                    start_dt = datetime.now(timezone.utc)
                    
                context["week_forecast_data"] = engine.calculate_forecast_week_data(
                    natal_chart,
                    start_dt,
                    forecast_loc
                )
                try:
                    context["month_forecast_data"] = engine.calculate_forecast_month_data(
                        natal_chart,
                        start_dt,
                        forecast_loc
                    )
                except Exception as exc:
                    _workflow_log(
                        "warning",
                        "report.workflow.context_week_brief_layer_partial",
                        fn="build_report_context",
                        contract="FN-BUILD-REPORT-CONTEXT",
                        block="FORECAST_SEMANTIC_LAYER",
                        report_id=getattr(payload, "report_id", None),
                        report_type=getattr(payload, "report_type", None),
                        layer="month_forecast_data",
                        error=str(exc),
                    )
                try:
                    context["year_forecast_data"] = engine.calculate_forecast_year_data(
                        natal_chart,
                        start_dt.year,
                        forecast_loc
                    )
                except Exception as exc:
                    _workflow_log(
                        "warning",
                        "report.workflow.context_week_brief_layer_partial",
                        fn="build_report_context",
                        contract="FN-BUILD-REPORT-CONTEXT",
                        block="FORECAST_SEMANTIC_LAYER",
                        report_id=getattr(payload, "report_id", None),
                        report_type=getattr(payload, "report_type", None),
                        layer="year_forecast_data",
                        error=str(exc),
                    )
                context["week_brief_seed"] = _build_week_brief_seed_bundle(context)
                
            elif payload.report_type == "month_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                except:
                    start_dt = datetime.now(timezone.utc)
                    
                context["month_forecast_data"] = engine.calculate_forecast_month_data(
                    natal_chart,
                    start_dt,
                    forecast_loc
                )

            elif payload.report_type == "ten_year_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                    start_year = start_dt.year
                except:
                    start_year = datetime.now(timezone.utc).year
                    
                context["decade_forecast_data"] = engine.calculate_forecast_decade_data(
                    natal_chart,
                    start_year,
                    forecast_loc
                )

        except Exception as exc:
            _workflow_log(
                "error",
                "report.workflow.context_forecast_error",
                fn="build_report_context",
                contract="FN-BUILD-REPORT-CONTEXT",
                block="FORECAST_SEMANTIC_LAYER",
                report_id=getattr(payload, "report_id", None),
                report_type=getattr(payload, "report_type", None),
                error=str(exc),
            )

    _workflow_log(
        "info",
        "report.workflow.context_ready",
        fn="build_report_context",
        contract="FN-BUILD-REPORT-CONTEXT",
        block="FORECAST_SEMANTIC_LAYER",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
        keys=sorted(context.keys()),
    )
    # END_BLOCK: FORECAST_SEMANTIC_LAYER
    return context
# #END_BLOCK_WORKFLOW_CONTEXT


# #START_BLOCK_WORKFLOW_SECTIONS
def initialize_report_chunks(
    report: Report,
    section_specs: List[SectionSpec],
    db: Session,
    reset: bool = False,
) -> dict:
    """
    # START_CONTRACT: FN-SAVE-SECTION-PAYLOAD
    # purpose: Ensure persisted section payload/chunk placeholders exist before generation or resume.
    # inputs: report row, section specs, db session, reset flag.
    # returns: mapping of section_id to ReportChunk rows.
    # side_effects: mutates chunk rows and emits admin/workflow queue logs.
    # errors: propagates database persistence failures.
    # END_CONTRACT: FN-SAVE-SECTION-PAYLOAD
    """

    if reset:
        # START_BLOCK: CHUNK_RESET
        db.query(ReportChunk).filter(ReportChunk.report_id == report.id).delete()
        db.flush()
        _workflow_log(
            "info",
            "report.workflow.queue_reset",
            fn="initialize_report_chunks",
            contract="FN-SAVE-SECTION-PAYLOAD",
            block="CHUNK_RESET",
            report=report,
            stage="reset",
            reset=True,
            section_total=len(section_specs),
            bridge="admin_resume_checkout",
        )
        # END_BLOCK: CHUNK_RESET

    chunks = {
        chunk.section: chunk
        for chunk in db.query(ReportChunk)
        .filter(ReportChunk.report_id == report.id)
        .all()
    }

    # START_BLOCK: CHUNK_UPSERT
    for index, spec in enumerate(section_specs):
        chunk = chunks.get(spec.section_id)
        if chunk:
            if reset:
                chunk.content = ""
                chunk.status = "pending"
                chunk.error_message = None
                chunk.error_at = None
            chunk.order_index = index
        else:
            chunk = ReportChunk(
                report_id=report.id,
                section=spec.section_id,
                content="",
                status="pending",
                order_index=index,
            )
            db.add(chunk)
        chunks[spec.section_id] = chunk

    # END_BLOCK: CHUNK_UPSERT
    # START_BLOCK: CHUNK_STATUS_SUMMARY
    _workflow_log(
        "info",
        "report.workflow.queue_initialized",
        fn="initialize_report_chunks",
        contract="FN-SAVE-SECTION-PAYLOAD",
        block="CHUNK_STATUS_SUMMARY",
        report=report,
        stage="initialized",
        reset=reset,
        section_total=len(section_specs),
        pending=sum(1 for chunk in chunks.values() if chunk.status == "pending"),
        running=sum(1 for chunk in chunks.values() if chunk.status == "in_progress"),
        error=sum(1 for chunk in chunks.values() if chunk.status in {"failed", "error"}),
    )
    # END_BLOCK: CHUNK_STATUS_SUMMARY

    return chunks
# #END_BLOCK_WORKFLOW_SECTIONS


async def generate_section_content(
    spec: SectionSpec,
    context: dict,
    chart_data: dict,
    llm_client: Optional[LLMClient],
    fallback_models: List[str],
    retry_attempts: int,
    use_template: bool
) -> SectionResult:
    """
    # START_CONTRACT: FN-ENQUEUE-REPORT-GENERATION
    # purpose: Produce a single section payload through static override, llm generation, or fallback policy.
    # inputs: section spec, section/global context, chart data, llm client config, retry/fallback settings.
    # returns: SectionResult with normalized content and usage metrics.
    # side_effects: emits section generation trace logs aligned with workflow/admin monitoring.
    # errors: propagates non-fallback generation failures to caller.
    # END_CONTRACT: FN-ENQUEUE-REPORT-GENERATION
    """
    import time
    start_t = time.perf_counter()
    _workflow_log(
        "info",
        "report.workflow.section_generation_start",
        fn="generate_section_content",
        contract="FN-ENQUEUE-REPORT-GENERATION",
        block="SECTION_STATIC_OVERRIDE",
        report_id=context.get("report_id") or context.get("client", {}).get("report_id"),
        section_id=spec.section_id,
        title=spec.title,
    )

    # START_BLOCK: SECTION_STATIC_OVERRIDE
    # 1. Static Overrides
    if spec.section_id == "input_frame":
        _workflow_log(
            "info",
            "report.workflow.section_static_override",
            fn="generate_section_content",
            contract="FN-ENQUEUE-REPORT-GENERATION",
            block="SECTION_STATIC_OVERRIDE",
            report_id=context.get("report_id") or context.get("client", {}).get("report_id"),
            section="input_frame",
            section_id=spec.section_id,
        )
        
        blocks = []
        
        # 1. Intro Callout
        intro_text = SECTION_INTROS.get("input_frame", "")
        if intro_text:
            blocks.append({
                "type": "callout",
                "variant": "info",
                "title": "Паспорт карты",
                "content": intro_text
            })
            
        # 2. Client Data
        c = context.get("client", {})
        birth_time_known = c.get("birth_time_known", True)
        
        # House System Localization
        hs_raw = str(chart_data.get("house_system") or "Placidus")
        if not birth_time_known:
            hs_display = "Космограмма (без домов)"
        elif "Whole" in hs_raw: hs_display = "Цельнознаковая"
        elif "Placidus" in hs_raw: hs_display = "Плацидус"
        elif "Equal" in hs_raw: hs_display = "Равнодомная"
        elif "Koch" in hs_raw: hs_display = "Кох"
        elif "Regio" in hs_raw: hs_display = "Региомонтан"
        elif "Porph" in hs_raw: hs_display = "Порфирий"
        else: hs_display = hs_raw

        # Date Formatting
        tz = c.get("birth_timezone") or "UTC"
        display_date = c.get('birth_date') or "-"
        
        if display_date != "-":
            try:
                clean_iso = display_date.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_iso)
                if dt.tzinfo and tz != "UTC":
                    dt = dt.astimezone(ZoneInfo(tz))
                
                if birth_time_known:
                    display_date = dt.strftime("%d.%m.%Y %H:%M")
                else:
                    display_date = dt.strftime("%d.%m.%Y (время неизв.)")
                
                if tz == "UTC" and birth_time_known:
                    display_date = f"{display_date} (UTC)"
            except Exception:
                pass

        blocks.append({
            "type": "header",
            "level": 3,
            "text": "Данные рождения"
        })
        
        blocks.append({
            "type": "key_value",
            "items": [
                {"key": "Кверент", "value": c.get('name') or "Unknown"},
                {"key": "Дата", "value": display_date},
                {"key": "Место", "value": c.get('birth_location') or "-"},
                {"key": "Часовой пояс", "value": tz if birth_time_known else "-"},
                {"key": "Дома", "value": hs_display}
            ]
        })
        
        # Check for High Latitude switch
        lat = c.get("birth_lat")
        if birth_time_known and lat and abs(lat) >= 60.0 and "Whole" in str(hs_raw):
             blocks.append({
                "type": "callout",
                "variant": "warning",
                "title": "⚠️ Особенности расчета",
                "content": f"Место рождения находится в высоких широтах ({lat:.2f}°). Система домов автоматически переключена на «Полнознаковую» (Whole Sign), так как стандартная система Плацидус не работает корректно за полярным кругом."
            })

        # 3. Planets Table Preparation
        positions = chart_data.get("positions", [])
        
        angles_data = []
        planets_data = []
        
        for p in positions:
            name_raw = p["name"]
            if name_raw in ["RAMC", "Zero"]: continue
            
            name_ru = RU_PLANETS_FULL.get(name_raw, name_raw)
            sign_ru = RU_SIGNS.get(p["sign"], p["sign"])
            house = str(p.get("house", "-")) if birth_time_known else "-"
            
            deg = int(p["sign_degree"])
            minute = int((p["sign_degree"] - deg) * 60)
            deg_str = f"{deg}°{minute:02d}'"
            
            retro = "R" if p.get("is_retrograde") else ""
            
            # Row: [Name, Sign, House, Degree, Retro]
            row = [name_ru, sign_ru, house, deg_str, retro]
            
            if name_raw in ["ASC", "MC", "DSC", "IC", "Vertex", "Part of Fortune"]:
                angles_data.append(row)
            else:
                planets_data.append(row)

        # 4. Render Tables
        if angles_data and birth_time_known:
             blocks.append({
                "type": "header",
                "level": 3,
                "text": "Угловые точки"
            })
             # Angles usually don't have Retro, so we use 4 columns
             blocks.append({
                "type": "table",
                "columns": [
                    {"header": "Точка", "width": "35%"},
                    {"header": "Знак", "width": "25%"},
                    {"header": "Дом", "width": "15%", "align": "center"},
                    {"header": "Град.", "width": "25%", "align": "right", "nowrap": True}
                ],
                "rows": [row[:4] for row in angles_data]
            })

        if planets_data:
            blocks.append({
                "type": "header",
                "level": 3,
                "text": "Планеты"
            })
            
            has_retro = any(row[4] for row in planets_data)
            p_cols = [
                {"header": "Планета", "width": "35%"},
                {"header": "Знак", "width": "25%"},
            ]
            if birth_time_known:
                p_cols.append({"header": "Дом", "width": "15%", "align": "center"})
            
            p_cols.append({"header": "Град.", "width": "25%", "align": "right", "nowrap": True})
            
            final_rows = []
            if has_retro:
                p_cols.append({"header": "R", "width": "30px", "align": "center"})
                if birth_time_known:
                    final_rows = planets_data
                else:
                    # Filter out house column (index 2)
                    final_rows = [[r[0], r[1], r[3], r[4]] for r in planets_data]
            else:
                if birth_time_known:
                    final_rows = [row[:4] for row in planets_data]
                else:
                    # Filter out house column (index 2)
                    final_rows = [[r[0], r[1], r[3]] for r in planets_data]

            blocks.append({
                "type": "table",
                "columns": p_cols,
                "rows": final_rows
            })
            
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=json.dumps(blocks, ensure_ascii=False))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id == "horary_00_passport":
        logger.info("gen.content.static", section="horary_00_passport")
        c = context.get("client", {})
        question = c.get("question") or c.get("note") or "Вопрос не указан"
        dt_str = chart_data.get("datetime_local") or chart_data.get("datetime_utc")
        
        dt_display = dt_str
        try:
            if dt_str:
                if dt_str.endswith("Z"): dt_str = dt_str[:-1]
                dt_val = datetime.fromisoformat(dt_str)
                
                # Timezone conversion
                tz_name = chart_data.get("location", {}).get("timezone")
                if tz_name:
                    if dt_val.tzinfo is None:
                        dt_val = dt_val.replace(tzinfo=timezone.utc)
                    dt_val = dt_val.astimezone(ZoneInfo(tz_name))
                
                dt_display = dt_val.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass
            
        loc = chart_data.get("location", {}).get("name", "Неизвестно")
        
        blocks = [
            {"type": "header", "level": 2, "text": "Паспорт вопроса"},
            {
                "type": "key_value",
                "items": [
                    {"key": "Вопрос", "value": question},
                    {"key": "Дата и время", "value": dt_display},
                    {"key": "Место", "value": loc},
                ],
            },
        ]
        content = json.dumps(blocks, ensure_ascii=False)
        logger.info("gen.content.passport.result", content_len=len(content), content_preview=content[:50])
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=content)
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id == "horary_00_technical":
        h = chart_data.get("horary", {})
        if not h:
             res = SectionResult(section_id=spec.section_id, title=spec.title, content=json.dumps([{"type": "paragraph", "text": "_Нет данных хорара._"}], ensure_ascii=False))
             res.duration_ms = int((time.perf_counter() - start_t) * 1000)
             return res

        blocks = []
        
        # 1. Scenario
        adapter_name = h.get('adapter_name', 'Не определен')
        blocks.append({"type": "header", "level": 2, "text": f"🧩 Сценарий: {adapter_name}"})
        
        # 2. Roles
        roles = h.get("roles", {})
        if roles:
            blocks.append({"type": "header", "level": 3, "text": "🎭 Сигнификаторы (Роли)"})
            
            priority = ["querent", "quesited", "opponent", "judge", "law", "verdict", "money", "wallet", "fine", "profit", "job", "partner", "moon"]
            sorted_keys = sorted(roles.keys(), key=lambda k: priority.index(k) if k in priority else 99)
            
            role_names_ru = {
                "querent": "Кверент (Ты)", "quesited": "Квестит (Вопрос)", "opponent": "Оппонент",
                "judge": "Судья/Власть", "law": "Закон", "verdict": "Итог дела", "money": "Деньги",
                "wallet": "Твой кошелек", "fine": "Штраф/Потери", "profit": "Выгода",
                "job": "Работа", "partner": "Партнер", "moon": "Луна"
            }
            
            rows = []
            for key in sorted_keys:
                r = roles[key]
                role_name = role_names_ru.get(key, key.capitalize())
                planet = r.get('planet_ru', '-')
                house = str(r.get('house', '-'))
                desc = r.get('description', '')
                rows.append([role_name, planet, house, desc])
            
            blocks.append({
                "type": "table",
                "columns": [
                    {"header": "Роль", "width": "25%"},
                    {"header": "Планета", "width": "20%"},
                    {"header": "Дом", "width": "15%", "align": "center"},
                    {"header": "Описание", "width": "40%"}
                ],
                "rows": rows
            })

        # 3. Radicality
        rad = h.get("radicality", {})
        if rad:
            score = rad.get('score', '?')
            try:
                score_val = float(score)
            except: 
                score_val = 0
                
            blocks.append({"type": "rating", "value": score_val, "max": 10, "label": "🛡️ Радикальность"})
            
            issues = rad.get('issues', [])
            warnings = rad.get('warnings', [])
            
            if issues:
                blocks.append({
                    "type": "callout", 
                    "variant": "error", 
                    "title": "Проблемы радикальности",
                    "content": "\n".join([f"• {i}" for i in issues])
                })
            
            if warnings:
                blocks.append({
                    "type": "callout", 
                    "variant": "warning", 
                    "title": "Предупреждения",
                    "content": "\n".join([f"• {w}" for w in warnings])
                })
                
            if not issues and not warnings:
                blocks.append({
                    "type": "callout", 
                    "variant": "success", 
                    "title": "Карта радикальна",
                    "content": "Суждение надежно, можно приступать к анализу."
                })

        res = SectionResult(section_id=spec.section_id, title=spec.title, content=json.dumps(blocks, ensure_ascii=False))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id == "technical_appendix":
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=format_technical_appendix(chart_data))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    if spec.section_id in {"executive_summary", "final_synthesis"}:
        insight_pack = (context.get("section_context") or {}).get("insight_pack")
        if insight_pack:
            content = build_section_validation_fallback_content(spec, context)
            res = SectionResult(section_id=spec.section_id, title=spec.title, content=content)
            res.duration_ms = int((time.perf_counter() - start_t) * 1000)
            return res

    # 2. Template Mode
    if use_template:
        if spec.section_id == "week_strategy":
            content = _render_week_strategy_content(context)
        elif spec.section_id in {"month_full_forecast", "month_theme"}:
            content = _render_month_forecast_content(context)
        else:
            content = build_section_template_content(spec)
        res = SectionResult(section_id=spec.section_id, title=spec.title, content=inject_planet_emojis(content))
        res.duration_ms = int((time.perf_counter() - start_t) * 1000)
        return res

    # 3. LLM Generation
    effective_spec = spec
    if spec.section_id in ["balance_wheel_1_6", "balance_wheel_7_12"]:
        structured_house_pack = (
            (context.get("section_context", {}).get("insight_pack") or {}).get("house_pack")
        )
        if structured_house_pack:
            house_ctx = json.dumps(structured_house_pack, ensure_ascii=False)
            new_prompt = (
                spec.prompt
                + "\n\n### СТРУКТУРНЫЙ HOUSE PACK ДЛЯ АНАЛИЗА (ИСПОЛЬЗУЙ КАК ОСНОВУ, НЕ ВЫХОДИ ЗА НЕГО):\n"
                + house_ctx
            )
        else:
            house_ctx = (
                context.get("section_context", {}).get("house_context")
                or context.get("houses_summary")
                or format_house_context(chart_data)
            )
            new_prompt = spec.prompt + f"\n\n### ДАННЫЕ ПО ДОМАМ ДЛЯ АНАЛИЗА (ИСПОЛЬЗУЙ ИХ!):\n{house_ctx}\n\nОписывай каждый дом, учитывая знак куспида, положение управителя и планеты внутри."
        effective_spec = SectionSpec(
            section_id=spec.section_id,
            title=spec.title,
            prompt=new_prompt,
            max_tokens=spec.max_tokens
        )

    result = await asyncio.to_thread(
        generate_section_with_retries,
        effective_spec,
        context,
        primary_client=llm_client,
        fallback_models=fallback_models,
        max_attempts=retry_attempts,
    )
    
    raw = result.content
    
    # JSON Cleanup: Strip code blocks if present
    if raw:
        import re
        # Find content between ```json and ```
        match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
        else:
            # Fallback: find content between ``` and ```
            match = re.search(r"```\s*(.*?)\s*```", raw, re.DOTALL)
            if match:
                raw = match.group(1).strip()

    if spec.section_id == "week_strategy" and context.get("week_forecast_data"):
        raw = _render_week_strategy_content(context, llm_content=raw)
    if spec.section_id in {"month_full_forecast", "month_theme"} and context.get("month_forecast_data"):
        raw = _render_month_forecast_content(context, llm_content=raw)

    # 4. Intro Injection (JSON-safe)
    intro = SECTION_INTROS.get(spec.section_id)
    if intro and raw and raw.strip().startswith("["):
        try:
            blocks = json.loads(raw)
            if isinstance(blocks, list):
                # Prepend intro block
                blocks.insert(0, {
                    "type": "paragraph",
                    "text": intro.strip()
                })
                raw = json.dumps(blocks, ensure_ascii=False)
        except:
            # If parsing fails, we can't safely inject. 
            # But generate_section_with_retries should guarantee valid JSON if valid.
            pass
        
    # END_BLOCK: SECTION_STATIC_OVERRIDE
    # START_BLOCK: SECTION_LLM_GENERATION
    result.content = inject_planet_emojis(raw)
    result.duration_ms = int((time.perf_counter() - start_t) * 1000)
    _workflow_log(
        "info",
        "report.workflow.section_generation_complete",
        fn="generate_section_content",
        contract="FN-ENQUEUE-REPORT-GENERATION",
        block="SECTION_LLM_GENERATION",
        report_id=context.get("report_id") or context.get("client", {}).get("report_id"),
        section_id=spec.section_id,
        duration_ms=result.duration_ms,
    )
    # END_BLOCK: SECTION_LLM_GENERATION
    return result

# #START_BLOCK_WORKFLOW_GENERATION
async def generate_report_sections(
    report: Report,
    payload: Any,
    db: Session,
    *,
    llm_client: Optional[LLMClient],
    llm_mode: Optional[str] = None,
    reset_chunks: bool,
    raise_on_error: bool,
    run: Optional[ReportRun] = None,
) -> tuple[list, dict]:
    """
    # START_CONTRACT: FN-HANDLE-GENERATION-RESULT
    # purpose: Orchestrate full report generation, persistence, fallback handling, and ready notification.
    # inputs: report row, payload, db session, llm config, reset flag, error policy, optional run row.
    # returns: generated section results and chart_data for downstream rendering/export.
    # side_effects: mutates report/chunks/run state, emits admin/workflow logs, schedules telegram delivery.
    # errors: propagates unrecoverable generation failures when raise_on_error is enabled.
    # END_CONTRACT: FN-HANDLE-GENERATION-RESULT
    """

    # START_BLOCK: GENERATION_PREPARE
    section_specs = build_section_specs(payload)
    total_expected = len(section_specs)
    
    chunk_map = initialize_report_chunks(
        report, section_specs, db, reset=reset_chunks
    )
    report.status = "in_progress"
    report.error_message = None
    report.error_at = None
    db.commit()

    chart_data = build_chart_data(payload)
    context = build_report_context(payload, chart_data)
    effective_mode = (llm_mode or "openrouter").strip().lower()
    use_template = effective_mode in {"fallback", "local", "mock", "stub"}
    
    if not use_template and llm_client is None:
        raise ValueError("LLM client is required for this llm_mode.")
        
    retry_attempts = resolve_llm_retry_attempts()
    fallback_models = []
    if effective_mode in {"openrouter", "cheap"}:
        fallback_models = resolve_llm_fallback_chain()
    
    _workflow_log(
        "info",
        "report.workflow.generation_start",
        fn="generate_report_sections",
        contract="FN-HANDLE-GENERATION-RESULT",
        block="GENERATION_PREPARE",
        report=report,
        mode=effective_mode,
        sections_total=total_expected,
        fallback_chain=fallback_models,
    )
    # END_BLOCK: GENERATION_PREPARE

    # Semaphore for rate limiting (OpenRouter limit or CLI concurrency control)
    semaphore = asyncio.Semaphore(resolve_llm_concurrency(effective_mode))

    # Track successes and usage
    success_count = 0
    fallback_count = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_total_tokens = 0

    # Helper for single section processing
    # START_BLOCK: GENERATION_PARALLEL_SECTIONS
    async def process_section(spec: SectionSpec, index: int) -> SectionResult:
        nonlocal success_count, fallback_count, total_prompt_tokens, total_completion_tokens, total_total_tokens
        async with semaphore:
            # Throttle for OpenRouter (free tier is rate-limited)
            if effective_mode == "openrouter":
                await asyncio.sleep(resolve_openrouter_throttle_seconds())
            
            chunk = chunk_map.get(spec.section_id)
            if chunk:
                chunk.status = "in_progress"
                chunk.error_message = None
                chunk.error_at = None
                chunk.order_index = index
                db.commit()

            # CONTEXT ANONYMIZATION + SECTION PACK
            section_context = copy.deepcopy(build_section_context(spec.section_id, context, chart_data))
            if spec.section_id != "input_frame":
                section_context["client"]["name"] = "Ты"
                section_context["client"]["note"] = ""

            result = None
            try:
                result = await generate_section_content(
                    spec,
                    section_context,
                    chart_data,
                    llm_client,
                    fallback_models,
                    retry_attempts,
                    use_template
                )
                
                content = result.content
                usage = result.usage

                if usage:
                    total_prompt_tokens += usage.get("prompt_tokens", 0)
                    total_completion_tokens += usage.get("completion_tokens", 0)
                    total_total_tokens += usage.get("total_tokens", 0)

                if chunk:
                    chunk.content = content
                    chunk.status = "completed"
                    db.commit()
                
                # If content contains error callout, it's a soft fallback
                if "Ошибка генерации" in content:
                    fallback_count += 1
                    _workflow_log(
                        "info",
                        "report.workflow.section_fallback_content",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="GENERATION_PARALLEL_SECTIONS",
                        report=report,
                        stage="fallback_content",
                        section_id=spec.section_id,
                        run_id=str(run.id) if run else None,
                        fallback=True,
                    )
                else:
                    success_count += 1
                
                _workflow_log(
                    "info",
                    "report.workflow.section_done",
                    fn="generate_report_sections",
                    contract="FN-HANDLE-GENERATION-RESULT",
                    block="GENERATION_PARALLEL_SECTIONS",
                    report=report,
                    section_id=spec.section_id,
                    duration_ms=getattr(result, "duration_ms", 0),
                    status="completed",
                )
                    
                return result
            except Exception as exc:
                error_msg = str(exc)
                # Check if we should fail hard or fallback
                allow_fallback = not raise_on_error or should_fallback_on_llm_error(exc)
                if isinstance(exc, LLMContentValidationError):
                    # Validation errors are also allowed to fallback
                    allow_fallback = True
                
                _workflow_log(
                    "error",
                    "report.workflow.section_error",
                    fn="generate_report_sections",
                    contract="FN-HANDLE-GENERATION-RESULT",
                    block="GENERATION_PARALLEL_SECTIONS",
                    report=report,
                    section_id=spec.section_id,
                    error=error_msg,
                    exc_type=type(exc).__name__,
                    allow_fallback=allow_fallback,
                    stage="section_error",
                    run_id=str(run.id) if run else None,
                )

                if allow_fallback:
                    if isinstance(exc, LLMContentValidationError):
                        fb_content = inject_planet_emojis(
                            build_section_validation_fallback_content(spec, section_context)
                        )
                    else:
                        fb_content = inject_planet_emojis(build_section_fallback_content(spec, section_context))
                    fallback_count += 1
                    _workflow_log(
                        "info",
                        "report.workflow.section_fallback_applied",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="GENERATION_PARALLEL_SECTIONS",
                        report=report,
                        stage="fallback_applied",
                        section_id=spec.section_id,
                        run_id=str(run.id) if run else None,
                        fallback=True,
                    )
                    if chunk:
                        chunk.content = fb_content
                        chunk.status = "completed" # Mark completed with error content
                        chunk.error_message = error_msg
                        chunk.error_at = datetime.now(timezone.utc)
                        db.commit()
                    return SectionResult(section_id=spec.section_id, title=spec.title, content=fb_content)
                else:
                    if chunk:
                        chunk.status = "failed"
                        chunk.error_message = error_msg
                        chunk.error_at = datetime.now(timezone.utc)
                        db.commit()
                    raise exc

    # Split sections: Independent vs Final
    independent_specs = [s for s in section_specs if s.section_id != "final_synthesis"]
    final_spec = next((s for s in section_specs if s.section_id == "final_synthesis"), None)
    
    # Run independent in parallel
    tasks = [process_section(spec, i) for i, spec in enumerate(independent_specs)]
    
    generated_sections = []
    failed = False
    
    try:
        results = await asyncio.gather(*tasks)
        generated_sections.extend(results)
    except Exception as e:
        failed = True
        report.status = "failed"
        report.error_message = str(e)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        if raise_on_error: raise e
        return [], {}

    # END_BLOCK: GENERATION_PARALLEL_SECTIONS

    # START_BLOCK: GENERATION_FINAL_SYNTHESIS
    # Run Final Synthesis if others succeeded
    if final_spec and not failed:
        try:
            res = await process_section(final_spec, len(independent_specs))
            generated_sections.append(res)
        except Exception as e:
            if raise_on_error: raise e

    # END_BLOCK: GENERATION_FINAL_SYNTHESIS

    # START_BLOCK: GENERATION_FINALIZE
    # HARD CHECK: Minimum successful sections
    # For natal_master (approx 18 sections), we expect at least 5 to consider it "usable"
    # For others (1-3 sections), we expect at least 1.
    min_required = 1
    if report.report_type == "natal_master":
        min_required = 5
    
    total_ok = success_count + fallback_count
    # Single-section forecast/report lanes remain usable when deterministic fallback content
    # was applied; natal keeps a stricter threshold because broad fallback-only output is not
    # sufficient for that surface.
    usable_count = total_ok if report.report_type != "natal_master" else success_count
    
    # Update Run stats if provided
    if run:
        run.prompt_tokens = total_prompt_tokens
        run.completion_tokens = total_completion_tokens
        run.total_tokens = total_total_tokens
        # Estimated cost: very rough heuristic for GPT-4.1-Nano
        # $0.05 / 1M tokens? Let's use a conservative placeholder or 0 for now
        # until we have real pricing logic.
        run.estimated_cost = Decimal(str(round(total_total_tokens * 0.0000001, 4)))
        db.commit()

    _workflow_log(
        "info",
        "report.workflow.generation_stats",
        fn="generate_report_sections",
        contract="FN-HANDLE-GENERATION-RESULT",
        block="GENERATION_FINALIZE",
        report=report,
        success=success_count,
        fallback=fallback_count,
        total=total_expected,
        min_required=min_required,
        total_ok=total_ok,
        usable=usable_count,
    )
    _workflow_log(
        "info",
        "report.workflow.generation_complete",
        fn="generate_report_sections",
        contract="FN-HANDLE-GENERATION-RESULT",
        block="GENERATION_FINALIZE",
        report=report,
        stage="generation_complete",
        run_id=str(run.id) if run else None,
        success=success_count,
        fallback=fallback_count,
        usable=usable_count,
        pending=sum(1 for chunk in chunk_map.values() if chunk.status == "pending"),
        running=sum(1 for chunk in chunk_map.values() if chunk.status == "in_progress"),
        error=sum(1 for chunk in chunk_map.values() if chunk.status in {"failed", "error"}),
    )

    if usable_count < min_required and not use_template:
        report.status = "failed"
        report.error_message = (
            f"Generation failed: only {usable_count}/{total_expected} sections usable "
            f"(min {min_required})."
        )
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        _workflow_log(
            "error",
            "report.workflow.failed_threshold",
            fn="generate_report_sections",
            contract="FN-HANDLE-GENERATION-RESULT",
            block="GENERATION_FINALIZE",
            report=report,
            success=success_count,
            fallback=fallback_count,
            usable=usable_count,
        )
    else:
        report.status = "completed"
        if fallback_count:
            report.error_message = (
                f"Partial generation: {fallback_count} of {total_expected} sections used fallback content."
            )
            report.error_at = datetime.now(timezone.utc)
        else:
            report.error_message = None
            report.error_at = None
        db.commit()
        
        # END_BLOCK: GENERATION_FINALIZE

        # START_BLOCK: REPORT_READY_NOTIFY
        # Notification Logic
        if report.user_id:
            user = db.query(User).filter(User.id == report.user_id).first()
            if user and user.telegram_id:
                report_names = {
                    "natal_master": "Твой Натальный разбор",
                    "year_forecast": "Твой Альманах 2026",
                    "week_forecast": "Прогноз на неделю",
                    "month_forecast": "Прогноз на месяц",
                    "ten_year_forecast": "Прогноз на 10 лет",
                    "solar_return": "Твой Соляр",
                    "horary_answer": "Ответ на твой вопрос",
                }
                report_name = report_names.get(report.report_type, "Твой отчет")
                fallback_msg = f"✨ {report_name} готов! Заходи в приложение, чтобы прочитать его. 📂"
                messages: list[str] = []
                try:
                    chunks = (
                        db.query(ReportChunk)
                        .filter(ReportChunk.report_id == report.id)
                        .order_by(ReportChunk.order_index.asc(), ReportChunk.created_at.asc())
                        .all()
                    )
                    messages = render_report_chunks_to_messages(chunks, title=report_name)
                except Exception as exc:
                    _workflow_log(
                        "error",
                        "report.workflow.notify_render_failed",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="REPORT_READY_NOTIFY",
                        report=report,
                        error=str(exc),
                    )

                if messages:
                    _workflow_log(
                        "info",
                        "report.workflow.notify_report_ready",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="REPORT_READY_NOTIFY",
                        report=report,
                        delivery="chunked_messages",
                        message_total=len(messages),
                        bridge="resume_checkout_ready",
                    )
                    asyncio.create_task(
                        _send_report_delivery_messages(user.telegram_id, messages)
                    )
                else:
                    _workflow_log(
                        "info",
                        "report.workflow.notify_report_ready",
                        fn="generate_report_sections",
                        contract="FN-HANDLE-GENERATION-RESULT",
                        block="REPORT_READY_NOTIFY",
                        report=report,
                        delivery="single_fallback_message",
                        bridge="resume_checkout_ready",
                    )
                    asyncio.create_task(send_bot_notification(user.telegram_id, fallback_msg))
        # END_BLOCK: REPORT_READY_NOTIFY

    return generated_sections, chart_data
# #END_BLOCK_WORKFLOW_GENERATION
