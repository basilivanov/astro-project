"""Week-owned seed helpers for WeekBrief assembly and prompt context."""

# ############################################################################
# AI_HEADER: MODULE_WEEK_BRIEF_SEED
# ROLE: Own Week seed bundle assembly, normalization, and block parsing outside report orchestration internals.
# DEPENDENCIES: backend.app.services.forecast_semantics
# GRACE_ANCHORS: [WEEK_BRIEF_SEED_HELPERS]
# ############################################################################

# START_MODULE_CONTRACT: M-WEEK-BRIEF-SEED
# purpose: Provide Week-owned seed normalization helpers shared by WeekBrief assembly and report workflow prompt-context preparation.
# owns:
#   - backend/app/services/week_brief_seed.py
# inputs:
#   - week forecast context dictionaries and raw week chunk content
# outputs:
#   - normalized Week seed bundles, normalized day and summary payloads, and parsed JSON block lists
# dependencies:
#   - backend.app.services.forecast_semantics.build_week_forecast_semantic_layer
# invariants:
#   - Week seed normalization semantics stay aligned with the pre-extraction behavior
#   - WeekBrief and prompt-context assembly consume the same Week-owned helper boundary
# non_goals:
#   - changing Week scoring, payload contracts, or report orchestration responsibilities
# END_MODULE_CONTRACT: M-WEEK-BRIEF-SEED

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from typing import Any

from .forecast_semantics import build_week_forecast_semantic_layer


# START_BLOCK: WEEK_BRIEF_SEED_HELPERS
RU_SIGNS = {
    "Aries": "Овен ♈",
    "Taurus": "Телец ♉",
    "Gemini": "Близнецы ♊",
    "Cancer": "Рак ♋",
    "Leo": "Лев ♌",
    "Virgo": "Дева ♍",
    "Libra": "Весы ♎",
    "Scorpio": "Скорпион ♏",
    "Sagittarius": "Стрелец ♐",
    "Capricorn": "Козерог ♑",
    "Aquarius": "Водолей ♒",
    "Pisces": "Рыбы ♓",
}

RU_SIGNS_PLAIN = {
    sign: value.split(" ", 1)[0]
    for sign, value in RU_SIGNS.items()
}

RU_PLANETS_FULL = {
    "Sun": "☀️ Солнце",
    "Moon": "🌙 Луна",
    "Mercury": "☿ Меркурий",
    "Venus": "♀️ Венера",
    "Mars": "♂️ Марс",
    "Jupiter": "♃ Юпитер",
    "Saturn": "♄ Сатурн",
    "Uranus": "♅ Уран",
    "Neptune": "♆ Нептун",
    "Pluto": "♇ Плутон",
    "Chiron": "⚷ Хирон",
    "Lilith": "⚸ Лилит",
    "Selena": "🌟 Селена",
    "North Node": "☊ Сев. Узел",
    "South Node": "☋ Южн. Узел",
    "Mean Apogee": "⚸ Лилит",
    "True Node": "☊ Сев. Узел",
    "Part of Fortune": "⊗ Парс Фортуны",
    "ASC": "⬆️ ASC",
    "MC": "🏔️ MC",
    "DSC": "⬇️ DSC",
    "IC": "🏠 IC",
    "Vertex": "✴️ Вертекс",
    "Ceres": "Церера",
    "Pallas": "Паллада",
    "Juno": "Юнона",
    "Vesta": "Веста",
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


def _coerce_float(value: Any) -> float | None:
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


def normalize_week_day_payload(day: dict[str, Any]) -> dict[str, Any]:
    source = copy.deepcopy(day or {})
    moon = source.get("moon", {}) or {}
    moon_sign = _normalize_moon_sign_label(moon.get("sign"))
    moon_phase = str(moon.get("phase") or "").strip()
    events = [
        str(item).strip()
        for item in (source.get("events") or _summarize_week_events(source))
        if str(item).strip()
    ]
    traffic_light = str(source.get("traffic_light") or "").strip().upper() or "YELLOW"
    return {
        "date": source.get("date"),
        "date_label": str(source.get("date_label") or "").strip() or _format_short_date_label(source.get("date")),
        "weekday_ru": str(source.get("weekday_ru") or "").strip() or _translate_weekday_to_ru(source.get("weekday")),
        "traffic_light": traffic_light,
        "traffic_desc": str(source.get("traffic_desc") or "").strip() or _default_week_traffic_desc(traffic_light),
        "tension_score": _coerce_float(source.get("tension_score")),
        "moon": {
            "sign": moon_sign,
            "phase": moon_phase,
            "void_of_course": bool(moon.get("void_of_course")),
        },
        "moon_label": str(source.get("moon_label") or "").strip()
        or ", ".join(part for part in [moon_sign, moon_phase] if part),
        "events": events,
    }


def normalize_week_summary(week_data: dict[str, Any], days: list[dict[str, Any]]) -> dict[str, Any]:
    source = copy.deepcopy((week_data or {}).get("summary") or {})
    avg_tension = _coerce_float(source.get("avg_tension"))
    if avg_tension is None and days:
        scores = [item.get("tension_score") for item in days if item.get("tension_score") is not None]
        if scores:
            avg_tension = sum(scores) / len(scores)
    traffic_light = str(source.get("traffic_light") or source.get("status_label") or "").strip().upper()
    if traffic_light not in {"RED", "YELLOW", "GREEN"}:
        tension = avg_tension if avg_tension is not None else 0.0
        if tension >= 1.5:
            traffic_light = "RED"
        elif tension >= 0.3:
            traffic_light = "YELLOW"
        else:
            traffic_light = "GREEN"
    return {
        "traffic_light": traffic_light,
        "avg_tension": round(avg_tension, 1) if avg_tension is not None else None,
        "status_label": str(source.get("status_label") or traffic_light).strip() or traffic_light,
    }


def build_week_brief_seed_bundle(context: dict[str, Any]) -> dict[str, Any]:
    week_data = copy.deepcopy(context.get("week_forecast_data") or {})
    days = [normalize_week_day_payload(day) for day in week_data.get("days", [])[:7]]
    summary = normalize_week_summary(week_data, days)
    semantic_layer = week_data.get("semantic_layer")
    if not isinstance(semantic_layer, dict) or not semantic_layer:
        semantic_layer = build_week_forecast_semantic_layer(summary, days)

    month_data = copy.deepcopy(context.get("month_forecast_data") or {})
    year_data = copy.deepcopy(context.get("year_forecast_data") or {})
    return {
        "forecast_window": copy.deepcopy(context.get("forecast_window") or {}),
        "summary": summary,
        "days": days,
        "semantic_layer": semantic_layer,
        "month_forecast_data": month_data,
        "year_forecast_data": year_data,
        "slow_background": {
            "profection": copy.deepcopy(year_data.get("profection") or {}),
            "solar_return": copy.deepcopy(year_data.get("solar_return") or {}),
            "solar_arcs": copy.deepcopy((year_data.get("solar_arcs") or [])[:6]),
            "long_transits": copy.deepcopy((month_data.get("major_transits") or [])[:6]),
            "retrogrades": copy.deepcopy((month_data.get("retrogrades") or [])[:4]),
            "lunations": copy.deepcopy((month_data.get("lunations") or [])[:3]),
        },
    }


def parse_json_block_list(content: Any) -> list[dict[str, Any]]:
    text = str(content or "").strip()
    if not text:
        return []
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*```$", "", text).strip()
    try:
        data = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]
# END_BLOCK: WEEK_BRIEF_SEED_HELPERS


__all__ = [
    "build_week_brief_seed_bundle",
    "normalize_week_day_payload",
    "normalize_week_summary",
    "parse_json_block_list",
]
