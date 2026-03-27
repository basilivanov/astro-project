# ############################################################################
# AI_HEADER: MODULE_WEEK_MAP
# ROLE: Build aggregated WeekMap artifact (theme/thesis/day map/domains/factors/actions/risks).
# DEPENDENCIES: stellium_engine, aggregation_weights, forecast_semantics.
# GRACE_ANCHORS: [WEEK_MAP_PIPELINE]
# ############################################################################

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from stellium_engine import StelliumEngine

from ..logging_utils import get_correlation_ids, log_grace_event
from .aggregation_weights import apply_weighted_factors
from .forecast_semantics import build_week_forecast_semantic_layer
from .personalized_daily import (
    _create_natal_chart,
    _resolve_forecast_location,
    _resolve_local_now,
    _resolve_location_label,
    _resolve_timezone,
)
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
    "Овен": "Овен",
    "Телец": "Телец",
    "Близ": "Близнецы",
    "Близнецы": "Близнецы",
    "Рак": "Рак",
    "Лев": "Лев",
    "Дева": "Дева",
    "Весы": "Весы",
    "Скорп": "Скорпион",
    "Скорпион": "Скорпион",
    "Стрел": "Стрелец",
    "Стрелец": "Стрелец",
    "Козер": "Козерог",
    "Козерог": "Козерог",
    "Водол": "Водолей",
    "Водолей": "Водолей",
    "Рыбы": "Рыбы",
}

MODULE_ID = "M-WEEK-MAP"


def _log_week_map(level: str, event: str, *, fn: str, block: str, **fields: Any) -> None:
    context = get_correlation_ids()
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        block=block,
        correlation_id=context.get("correlation_id"),
        trace_id=context.get("trace_id"),
        correlation_source=context.get("correlation_source"),
        **fields,
    )


def _resolve_week_start(now_local: datetime) -> datetime:
    weekday = now_local.weekday()
    return now_local.replace(hour=5, minute=0, second=0, microsecond=0) - timedelta(days=weekday)


def _normalize_domain_scores(domain_raw: dict[str, Any]) -> dict[str, Any]:
    scores = {}
    for key in ("work", "relationships", "energy", "focus"):
        scores[key] = max(0, min(100, int(domain_raw.get(key, 60))))
    return scores


def _translate_weekday_to_ru(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    return EN_WEEKDAY_TO_RU.get(raw, raw)


def _format_short_date_label(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw).strftime("%d.%m")
    except ValueError:
        return raw


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


def _normalize_moon_sign_label(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return MOON_SIGN_ALIASES.get(raw, raw)


def _summarize_week_events(day: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for ingress in (day.get("ingresses") or [])[:2]:
        text = str(ingress or "").strip()
        if text:
            items.append(text)
    for aspect in (day.get("aspects") or [])[:3]:
        transit = str(aspect.get("transit") or "").strip()
        natal = str(aspect.get("natal") or "").strip()
        aspect_label = str(aspect.get("aspect") or "").strip()
        if transit and natal and aspect_label:
            items.append(f"{transit} {aspect_label} {natal}")
    return items


def _normalize_week_day_payload(day: dict[str, Any]) -> dict[str, Any]:
    source = dict(day or {})
    moon = source.get("moon") or {}
    events = [
        str(item).strip()
        for item in (source.get("events") or _summarize_week_events(source))
        if str(item).strip()
    ]
    traffic_light = str(source.get("traffic_light") or "").strip().upper() or "YELLOW"
    return {
        "date": source.get("date"),
        "date_label": source.get("date_label") or _format_short_date_label(source.get("date")),
        "weekday_ru": source.get("weekday_ru") or _translate_weekday_to_ru(source.get("weekday")),
        "traffic_light": traffic_light,
        "traffic_desc": source.get("traffic_desc") or _default_week_traffic_desc(traffic_light),
        "tension_score": _coerce_float(source.get("tension_score")),
        "moon": {
            "sign": _normalize_moon_sign_label(moon.get("sign")),
            "phase": moon.get("phase"),
            "void_of_course": bool(moon.get("void_of_course")),
        },
        "events": events,
    }


def _normalize_week_summary(week_data: dict[str, Any], days: list[dict[str, Any]]) -> dict[str, Any]:
    source = dict((week_data or {}).get("summary") or {})
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
        "status_label": source.get("status_label") or traffic_light,
    }


def _build_day_card(day: dict[str, Any]) -> dict[str, Any]:
    events = [str(item).strip() for item in (day.get("events") or []) if str(item).strip()]
    return {
        "date": day.get("date"),
        "weekday": day.get("weekday_ru") or day.get("weekday"),
        "score": day.get("tension_score"),
        "mode": day.get("traffic_light"),
        "headline": day.get("traffic_desc"),
        "best_for": events[:2],
        "avoid": events[2:4],
    }


def _build_factor_inputs(summary: dict[str, Any], week_data: dict[str, Any]) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    semantic_layer = week_data.get("semantic_layer") or {}
    avg_tension = summary.get("avg_tension") or 0.0
    factors.extend(
        [
            {
                "category": "slow_background",
                "label": "Периодический фон",
                "weight": avg_tension,
                "confidence": 0.9,
                "explanation": semantic_layer.get("tension"),
            },
            {
                "category": "period_theme",
                "label": "Тема недели",
                "weight": 1.0,
                "confidence": 1.0,
                "explanation": semantic_layer.get("headline"),
            },
        ]
    )

    day_hits = week_data.get("days") or []
    if day_hits:
        top_day = max(day_hits, key=lambda item: (item.get("traffic_light") == "GREEN", -(item.get("tension_score") or 0)))
        slow_day = max(day_hits, key=lambda item: (item.get("traffic_light") == "RED", item.get("tension_score") or 0))
        factors.append(
            {
                "category": "weekly_triggers",
                "label": f"Точные включения: {top_day.get('date_label') or top_day.get('date')}",
                "weight": 0.7,
                "confidence": 0.8,
                "explanation": ", ".join((top_day.get("events") or [])[:2]),
            }
        )
        factors.append(
            {
                "category": "day_decomposition",
                "label": f"Слабое место: {slow_day.get('date_label') or slow_day.get('date')}",
                "weight": (slow_day.get("tension_score") or 1.0),
                "confidence": 0.7,
                "explanation": ", ".join((slow_day.get("events") or [])[:2]),
            },
        )

    rare_hits = [event for day in day_hits for event in (day.get("events") or []) if "стат" in str(event).lower()]
    if rare_hits:
        factors.append(
            {
                "category": "rare_boosters",
                "label": "Редкие усилители",
                "weight": 0.6,
                "confidence": 0.9,
                "explanation": "; ".join(rare_hits[:3]),
            }
        )
    return factors


def build_week_map(now_utc: datetime, user: Optional[Any]) -> dict[str, Any]:
    """Assemble the aggregated WeekMap artifact."""

    fn = "build_week_map"
    now = now_utc if isinstance(now_utc, datetime) else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    tz = _resolve_timezone(user)
    local_now = _resolve_local_now(now, tz)
    week_start = _resolve_week_start(local_now)
    location_label = _resolve_location_label(None, user)
    _log_week_map(
        "info",
        "week_map.entry",
        fn=fn,
        block="CONTEXT",
        timezone=tz,
        location=location_label,
    )

    engine = StelliumEngine()
    if not user or not getattr(user, "birth_date", None) or not getattr(user, "birth_place", None):
        raise ValueError("WeekMap requires authenticated profile with birth date and place")
    natal_chart = _create_natal_chart(engine, user)

    forecast_location = _resolve_forecast_location(user, location_label)
    week_data = engine.calculate_forecast_week_data(natal_chart, week_start, forecast_location)
    days = [_normalize_week_day_payload(day) for day in week_data.get("days", [])]
    summary = _normalize_week_summary(week_data, days)
    semantic_layer = build_week_forecast_semantic_layer(summary, days)
    week_data["semantic_layer"] = semantic_layer

    factors = _build_factor_inputs(summary, {"days": days, "semantic_layer": semantic_layer})
    weighted = apply_weighted_factors("week_map", factors, top_n=5)

    domains = _normalize_domain_scores(
        {
            "work": 70 if summary.get("traffic_light") == "GREEN" else 55,
            "relationships": 60,
            "energy": 65,
            "focus": 58,
        }
    )

    payload = {
        "timezone": tz,
        "location": location_label,
        "week_start": week_start.date().isoformat(),
        "theme": semantic_layer.get("headline"),
        "thesis": semantic_layer.get("practical_move"),
        "day_cards": [_build_day_card(day) for day in days],
        "domains": domains,
        "major_factors": weighted["top_factors"],
        "actions": [semantic_layer.get("practical_move"), semantic_layer.get("negotiation")],
        "risks": [semantic_layer.get("friction"), semantic_layer.get("tension")],
        "deep_sections": ["strategy", "domains", "timeline"],
        "explainability": {
            "total_score": weighted["total_score"],
            "confidence": 0.85,
            "used_exact_birth_time": bool(getattr(user, "birth_time_known", True)),
            "pipeline": weighted["pipeline"],
        },
    }

    _log_week_map(
        "info",
        "week_map.ready",
        fn=fn,
        block="ASSEMBLY",
        day_cards=len(payload["day_cards"]),
        top_factor=payload["major_factors"][0]["label"] if payload["major_factors"] else None,
    )
    return payload


__all__ = ["build_week_map"]
