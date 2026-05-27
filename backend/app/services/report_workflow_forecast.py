# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_FORECAST
# ROLE: Week forecast rendering and report forecast helper facade.
# DEPENDENCIES: forecast_semantics.py, week_brief_seed.py, report_workflow_content.py
# GRACE_ANCHORS: [FORECAST_WINDOW, WEEK_FORECAST_RENDERING, FORECAST_FALLBACK]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-FORECAST
# purpose: Render week forecast content and expose forecast fallback/prompt helpers for report workflow.
# inputs:
#   - Report context dictionaries with week/month forecast data
#   - compact chart facts for deterministic fallback rendering
# outputs:
#   - JSON block strings and prompt-context dictionaries
# trace_obligations:
#   - Pure helper module; workflow caller retains module/block/report_id logging attribution
# invariants:
#   - Week/month fallback copy and JSON schemas remain stable across extraction
# non_goals:
#   - Does not own generation lifecycle, chunk persistence, or notifications
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-FORECAST

# START_MODULE_MAP: M-REPORT-WORKFLOW-FORECAST
# entrypoints:
#   - build_forecast_window -> FORECAST_WINDOW
#   - _render_week_strategy_content -> WEEK_FORECAST_RENDERING
#   - build_section_fallback_content -> FORECAST_FALLBACK
# END_MODULE_MAP: M-REPORT-WORKFLOW-FORECAST

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from ..llm.orchestrator import SectionSpec
from .forecast_semantics import build_week_forecast_semantic_layer
from .report_workflow_content import cleanup_content_artifacts
from .report_workflow_forecast_month import (
    RU_MONTH_NAMES,
    _build_month_campaign_arc,
    _build_month_central_task,
    _build_month_event_cards,
    _build_month_forecast_prompt_context,
    _build_month_phase_cards,
    _build_month_status_summary,
    _format_month_window_label,
    _render_month_forecast_content,
)
from .week_brief_seed import (
    build_week_brief_seed_bundle as build_week_brief_seed_bundle_owned,
    normalize_week_day_payload as normalize_week_day_payload_owned,
    normalize_week_summary as normalize_week_summary_owned,
    parse_json_block_list as parse_json_block_list_owned,
)

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

# START_BLOCK: FORECAST_WINDOW
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
# END_BLOCK: FORECAST_WINDOW

# START_BLOCK: WEEK_FORECAST_NORMALIZATION
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
# END_BLOCK: WEEK_FORECAST_NORMALIZATION

# START_BLOCK: WEEK_FORECAST_RENDERING
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
# END_BLOCK: WEEK_FORECAST_RENDERING

# START_BLOCK: FORECAST_FALLBACK
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
# END_BLOCK: FORECAST_FALLBACK
