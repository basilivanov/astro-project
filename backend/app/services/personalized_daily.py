# ############################################################################
# AI_HEADER: MODULE_PERSONALIZED_DAILY
# ROLE: Build fact-first personalized daily context for /api/feed/today.
# DEPENDENCIES: stellium_engine.py, backend/app/engine_utils.py, backend/app/models.py
# GRACE_ANCHORS: [PERSONALIZED_DAILY_FACTS, PERSONALIZED_DAILY_SCORING]
# ############################################################################

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

import structlog

from stellium_engine import StelliumEngine

from .. import engine_utils
from .forecast_semantics import build_daily_forecast_semantic_layer

logger = structlog.get_logger()

_PERSONALIZED_DAILY_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}


def _emit_feed_log(event: str, **fields: Any) -> None:
    logger.info(event, **fields)

RU_PLANETS = {
    "Sun": "Солнце",
    "Moon": "Луна",
    "Mercury": "Меркурий",
    "Venus": "Венера",
    "Mars": "Марс",
    "Jupiter": "Юпитер",
    "Saturn": "Сатурн",
    "Uranus": "Уран",
    "Neptune": "Нептун",
    "Pluto": "Плутон",
    "Chiron": "Хирон",
    "True Node": "Сев. Узел",
    "North Node": "Сев. Узел",
    "South Node": "Южн. Узел",
    "ASC": "ASC",
    "MC": "MC",
}

RU_WEEKDAYS = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье",
}

FAST_TRANSITS = {"Sun", "Mercury", "Venus", "Mars"}
PERSONAL_NATAL_POINTS = {"Sun", "Moon", "Mercury", "Venus", "Mars", "ASC", "MC"}
HEALTH_POINTS = {"Sun", "Moon", "Mars", "ASC"}
MONEY_POINTS = {"Venus", "Jupiter", "Mercury", "MC", "Sun"}
LOVE_POINTS = {"Venus", "Mars", "Moon", "Sun"}
BENEFIC_TRANSITS = {"Sun", "Venus", "Jupiter"}
CHALLENGING_TRANSITS = {"Mars", "Saturn", "Uranus", "Neptune", "Pluto", "South Node"}


def _get_moon_phase_emoji(phase_angle: float) -> str:
    if phase_angle < 45:
        return "🌑"
    if phase_angle < 90:
        return "🌒"
    if phase_angle < 135:
        return "🌓"
    if phase_angle < 180:
        return "🌔"
    if phase_angle < 225:
        return "🌕"
    if phase_angle < 270:
        return "🌖"
    if phase_angle < 315:
        return "🌗"
    return "🌘"


def _get_phase_name(phase_angle: float) -> str:
    if phase_angle < 10:
        return "Новолуние"
    if phase_angle < 90:
        return "Растущая Луна"
    if phase_angle < 100:
        return "Первая четверть"
    if phase_angle < 170:
        return "Растущая Луна"
    if phase_angle < 190:
        return "Полнолуние"
    if phase_angle < 270:
        return "Убывающая Луна"
    if phase_angle < 280:
        return "Последняя четверть"
    return "Убывающая Луна"


def _translate_planet(name: str) -> str:
    return RU_PLANETS.get(name, name)


def _resolve_timezone(user: Optional[Any]) -> str:
    tz_str = getattr(user, "current_timezone", None) or getattr(user, "birth_timezone", None) or "UTC"
    try:
        ZoneInfo(tz_str)
        return tz_str
    except Exception:
        return "UTC"


def _resolve_local_now(now_utc: datetime, tz_str: str) -> datetime:
    aware_now = now_utc if now_utc.tzinfo else now_utc.replace(tzinfo=timezone.utc)
    try:
        return aware_now.astimezone(ZoneInfo(tz_str))
    except Exception:
        return aware_now.astimezone(timezone.utc)


def _resolve_transit_location(user: Optional[Any]) -> Any:
    if user and getattr(user, "current_lat", None) is not None and getattr(user, "current_lon", None) is not None:
        return {
            "latitude": user.current_lat,
            "longitude": user.current_lon,
            "name": getattr(user, "current_location", None) or getattr(user, "birth_place", None) or "Current Location",
        }
    if user and getattr(user, "birth_lat", None) is not None and getattr(user, "birth_lon", None) is not None:
        return {
            "latitude": user.birth_lat,
            "longitude": user.birth_lon,
            "name": getattr(user, "birth_place", None) or "Birth Location",
        }
    if user and getattr(user, "current_location", None):
        return user.current_location
    if user and getattr(user, "birth_place", None):
        return user.birth_place
    return "Moscow"


def _resolve_location_label(location_input: Any, user: Optional[Any]) -> str:
    if isinstance(location_input, dict):
        name = location_input.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    if isinstance(location_input, str) and location_input.strip():
        return location_input.strip()
    if user and getattr(user, "current_location", None):
        return str(user.current_location)
    if user and getattr(user, "birth_place", None):
        return str(user.birth_place)
    return "Moscow"


def _resolve_forecast_location(user: Optional[Any], location_label: str) -> str:
    if user and getattr(user, "current_location", None):
        return user.current_location
    if user and getattr(user, "birth_place", None):
        return user.birth_place
    if location_label:
        return location_label
    return "Moscow"


def _profile_fingerprint(user: Optional[Any]) -> tuple[Any, ...]:
    if not user:
        return ("anonymous",)
    return (
        getattr(user, "id", None),
        getattr(user, "birth_date", None),
        getattr(user, "birth_time", None),
        getattr(user, "birth_time_known", True),
        getattr(user, "birth_place", None),
        getattr(user, "birth_lat", None),
        getattr(user, "birth_lon", None),
        getattr(user, "birth_timezone", None),
        getattr(user, "current_location", None),
        getattr(user, "current_lat", None),
        getattr(user, "current_lon", None),
        getattr(user, "current_timezone", None),
        getattr(user, "sun_sign", None),
    )


def _build_cache_key(now_local: datetime, tz_str: str, location_label: str, user: Optional[Any]) -> tuple[Any, ...]:
    return (
        now_local.date().isoformat(),
        tz_str,
        location_label,
        *_profile_fingerprint(user),
    )


def _is_full_profile(user: Optional[Any]) -> bool:
    if not user:
        return False
    return bool(getattr(user, "birth_date", None) and getattr(user, "birth_place", None))


def _build_birth_datetime(user: Any) -> str:
    birth_date = getattr(user, "birth_date", None) or ""
    birth_time = getattr(user, "birth_time", None)
    if birth_time:
        return f"{birth_date}T{birth_time}:00"
    return birth_date


def _create_natal_chart(engine: StelliumEngine, user: Any) -> Any:
    location_input: Any = getattr(user, "birth_place", None) or "Moscow"
    if getattr(user, "birth_lat", None) is not None and getattr(user, "birth_lon", None) is not None:
        location_input = {
            "latitude": user.birth_lat,
            "longitude": user.birth_lon,
            "name": getattr(user, "birth_place", None) or getattr(user, "full_name", None) or "Birth Location",
        }

    house_system = engine_utils.resolve_house_system("placidus")
    return engine.create_natal_chart(
        getattr(user, "full_name", None) or "User",
        _build_birth_datetime(user),
        location_input,
        house_system,
        birth_time_known=getattr(user, "birth_time_known", True),
    )


def _format_aspect_hit(hit: dict[str, Any]) -> str:
    return (
        f"{_translate_planet(str(hit.get('transit')))} "
        f"{hit.get('type')} "
        f"{_translate_planet(str(hit.get('natal')))}"
    )


def _format_transit_aspect(aspect: dict[str, Any]) -> str:
    return (
        f"{_translate_planet(str(aspect.get('p1')))} "
        f"{_translate_aspect_type(str(aspect.get('type')))} "
        f"{_translate_planet(str(aspect.get('p2')))}"
    )


def _translate_aspect_type(aspect_type: str) -> str:
    mapping = {
        "conjunction": "соединение",
        "opposition": "оппозиция",
        "trine": "трин",
        "square": "квадрат",
        "sextile": "секстиль",
    }
    return mapping.get((aspect_type or "").strip().lower(), aspect_type)


def _select_fast_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = []
    for hit in hits:
        transit = str(hit.get("transit"))
        natal = str(hit.get("natal"))
        if transit not in FAST_TRANSITS:
            continue
        if natal not in PERSONAL_NATAL_POINTS:
            continue
        orb = round(float(hit.get("exact_diff", 0.0)), 2)
        filtered.append(
            {
                "transit": transit,
                "natal": natal,
                "type": str(hit.get("type")),
                "orb": orb,
                "summary": _format_aspect_hit(hit),
            }
        )
    filtered.sort(key=lambda item: item["orb"])
    return filtered[:5]


def _select_transit_day_aspects(aspects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prioritized = []
    for aspect in aspects:
        p1 = str(aspect.get("p1"))
        p2 = str(aspect.get("p2"))
        if p1 not in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}:
            continue
        if p2 not in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}:
            continue
        prioritized.append(aspect)
    prioritized.sort(key=lambda item: float(item.get("orb", 99.0)))
    return prioritized[:5]


def _week_today_context(week_data: dict[str, Any]) -> dict[str, Any]:
    days = week_data.get("days") or []
    if not days:
        return {}
    return days[0] if isinstance(days[0], dict) else {}


def _month_status_adjustment(status: Optional[str], weight: int) -> int:
    if status == "GREEN":
        return weight
    if status == "RED":
        return -weight
    return 0


def _base_score_from_weekday(day_context: dict[str, Any]) -> int:
    traffic = str(day_context.get("traffic_light") or "").upper()
    if traffic == "GREEN":
        return 70
    if traffic == "RED":
        return 40
    return 58


def _hit_effect(hit: dict[str, Any]) -> int:
    aspect_type = str(hit.get("type", ""))
    transit = str(hit.get("transit", ""))
    if "Тригон" in aspect_type or "Секстиль" in aspect_type:
        return 10
    if "Квадрат" in aspect_type or "Оппозиция" in aspect_type:
        return -12
    if "Соединение" in aspect_type:
        if transit in BENEFIC_TRANSITS:
            return 9
        if transit in CHALLENGING_TRANSITS:
            return -10
        return 3
    return 0


def _to_light(score: int) -> str:
    if score >= 67:
        return "green"
    if score >= 46:
        return "yellow"
    return "red"


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))


def _build_generic_traffic_lights(
    day_aspects: list[dict[str, Any]],
    phase_name: str,
    moon_degree: float,
) -> dict[str, str]:
    tension = sum(
        1
        for aspect in day_aspects
        if str(aspect.get("type")) in {"square", "opposition"}
    )
    support = sum(
        1
        for aspect in day_aspects
        if str(aspect.get("type")) in {"trine", "sextile"}
    )
    base = 56 + support * 5 - tension * 7
    if phase_name in {"Новолуние", "Полнолуние"}:
        base -= 4
    if moon_degree >= 28:
        base -= 3
    health = _clamp_score(base)
    money = _clamp_score(base - 2)
    love = _clamp_score(base + (4 if phase_name == "Полнолуние" else 0) - (2 if moon_degree >= 28 else 0))
    return {
        "health": _to_light(health),
        "money": _to_light(money),
        "love": _to_light(love),
    }


def _build_personalized_traffic_lights(
    fast_hits: list[dict[str, Any]],
    today_context: dict[str, Any],
    month_data: dict[str, Any],
    year_data: dict[str, Any],
    current_month: int,
) -> dict[str, str]:
    scores = {
        "health": _base_score_from_weekday(today_context),
        "money": _base_score_from_weekday(today_context),
        "love": _base_score_from_weekday(today_context),
    }

    month_status = str(month_data.get("status") or "")
    year_month_status = ""
    months = year_data.get("months") or []
    if months:
        for month_item in months:
            if not isinstance(month_item, dict):
                continue
            if int(month_item.get("month", 0) or 0) == current_month:
                year_month_status = str(month_item.get("status") or "")
                break

    shared_adjustment = _month_status_adjustment(month_status, 5) + _month_status_adjustment(year_month_status, 3)
    for key in scores:
        scores[key] += shared_adjustment

    moon_info = today_context.get("moon") or {}
    if moon_info.get("void_of_course"):
        scores["money"] -= 5
        scores["love"] -= 4

    for hit in fast_hits:
        effect = _hit_effect(hit)
        natal_point = str(hit.get("natal"))
        transit = str(hit.get("transit"))
        if natal_point in HEALTH_POINTS:
            scores["health"] += effect
            if transit == "Mars" and effect < 0:
                scores["health"] -= 3
        if natal_point in MONEY_POINTS:
            scores["money"] += effect
            if transit == "Mercury" and effect > 0:
                scores["money"] += 2
        if natal_point in LOVE_POINTS:
            scores["love"] += effect
            if transit == "Venus" and effect > 0:
                scores["love"] += 2

    return {key: _to_light(_clamp_score(value)) for key, value in scores.items()}


def _pick_month_events(month_data: dict[str, Any]) -> list[str]:
    events: list[str] = []
    for key in ("lunations", "ingresses", "major_transits", "retrogrades"):
        raw_items = month_data.get(key) or []
        for item in raw_items:
            if isinstance(item, str) and item.strip():
                events.append(item.strip())
            if len(events) >= 3:
                return events
    return events


def _summarize_year_month(year_data: dict[str, Any], current_month: int) -> str:
    months = year_data.get("months") or []
    for month_item in months:
        if not isinstance(month_item, dict):
            continue
        if int(month_item.get("month", 0) or 0) != current_month:
            continue
        status = month_item.get("status") or "YELLOW"
        aspects = month_item.get("aspects") or []
        aspect_stub = ""
        if aspects and isinstance(aspects[0], dict):
            aspect_stub = (
                f"; тон месяца задает {aspects[0].get('transit')} "
                f"{aspects[0].get('aspect')} {aspects[0].get('natal')}"
            )
        return f"Годовой фон на этот месяц: {status}{aspect_stub}"

    profection = year_data.get("profection") or {}
    house = profection.get("house")
    lord = profection.get("lord")
    if house and lord:
        return f"Годовой фон: профекция {house} дома, управитель года {lord}"
    return "Годовой фон без резкого разворота"


def _build_fact_lines(
    *,
    now_local: datetime,
    location_label: str,
    tz_str: str,
    moon_sign_ru: str,
    phase_name: str,
    fast_hits: list[dict[str, Any]],
    day_aspects: list[dict[str, Any]],
    today_context: dict[str, Any],
    month_data: dict[str, Any],
    year_data: dict[str, Any],
    sun_sign: Optional[str],
) -> list[str]:
    lines = [
        (
            f"Локальный контекст: {RU_WEEKDAYS[now_local.weekday()]}, "
            f"{now_local.strftime('%d.%m %H:%M')}, {location_label}, timezone {tz_str}."
        ),
        f"Луна дня: {moon_sign_ru}, фаза {phase_name}.",
    ]
    if sun_sign:
        lines.append(f"Базовый профиль: солнечный знак {engine_utils.translate_sign(sun_sign)}.")

    if fast_hits:
        summaries = ", ".join(hit["summary"] for hit in fast_hits[:3])
        lines.append(f"Быстрые транзиты к наталу: {summaries}.")
    elif day_aspects:
        summaries = ", ".join(_format_transit_aspect(item) for item in day_aspects[:3])
        lines.append(f"Общий фон дня: {summaries}.")

    if today_context:
        moon = today_context.get("moon") or {}
        traffic = today_context.get("traffic_desc") or today_context.get("traffic_light")
        moon_bits = []
        if moon.get("sign"):
            moon_bits.append(f"Луна недели в {moon.get('sign')}")
        if moon.get("phase"):
            moon_bits.append(f"фаза {moon.get('phase')}")
        if moon.get("void_of_course"):
            moon_bits.append("есть поздняя Луна/void of course")
        if moon_bits or traffic:
            lines.append(
                f"Контекст недели: {traffic or 'нейтрально'}"
                + (f"; {'; '.join(moon_bits)}." if moon_bits else ".")
            )

    month_events = _pick_month_events(month_data)
    month_status = month_data.get("status")
    if month_status or month_events:
        month_line = f"Контекст месяца: статус {month_status or 'YELLOW'}"
        if month_events:
            month_line += f"; ближайшие события: {', '.join(month_events)}."
        else:
            month_line += "."
        lines.append(month_line)

    lights_bits = []
    traffic_lights = today_context.get("personalized_traffic_lights") or {}
    for key in ("health", "money", "love"):
        value = traffic_lights.get(key)
        if value:
            lights_bits.append(f"{key}={value}")
    if lights_bits:
        lines.append(f"Светофоры дня: {', '.join(lights_bits)}.")

    if year_data:
        lines.append(_summarize_year_month(year_data, now_local.month) + ".")

    return lines


def _build_cache_scope(facts: dict[str, Any]) -> str:
    payload = {
        "date": facts.get("date"),
        "level": facts.get("personalization_level"),
        "timezone": facts.get("timezone"),
        "location": facts.get("location_label"),
        "aspect_summary": facts.get("aspect_summary"),
        "traffic_lights": facts.get("traffic_lights"),
        "fact_lines": facts.get("fact_lines", [])[:5],
        "semantic_layer": {
            "headline": ((facts.get("semantic_layer") or {}).get("headline") if isinstance(facts.get("semantic_layer"), dict) else ""),
            "practical_move": ((facts.get("semantic_layer") or {}).get("practical_move") if isinstance(facts.get("semantic_layer"), dict) else ""),
        },
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


# #START_BLOCK_PERSONALIZED_DAILY_FACTS
def build_personalized_daily_facts(now_utc: datetime, user: Optional[Any] = None) -> dict[str, Any]:
    tz_str = _resolve_timezone(user)
    now_local = _resolve_local_now(now_utc, tz_str)
    transit_location = _resolve_transit_location(user)
    location_label = _resolve_location_label(transit_location, user)
    cache_key = _build_cache_key(now_local, tz_str, location_label, user)
    profile_mode = "authenticated" if user else "anonymous"

    _emit_feed_log(
        "feed.entry",
        stage="facts_start",
        profile_mode=profile_mode,
        timezone=tz_str,
        location=location_label,
        local_date=now_local.date().isoformat(),
    )

    cached = _PERSONALIZED_DAILY_CACHE.get(cache_key)
    if cached:
        _emit_feed_log(
            "feed.debug",
            stage="facts_cache_hit",
            cache_scope=cached.get("cache_scope"),
            personalization_level=cached.get("personalization_level"),
            timezone=tz_str,
            location=location_label,
            profile_mode=profile_mode,
        )
        return copy.deepcopy(cached)

    engine = StelliumEngine()
    house_system = engine_utils.resolve_house_system("placidus")
    transit_chart = engine.create_transit_chart(
        now_local.strftime("%Y-%m-%d %H:%M"),
        transit_location,
        house_system,
    )

    moon = next((body for body in transit_chart.positions if getattr(body, "name", "") == "Moon"), None)
    sun = next((body for body in transit_chart.positions if getattr(body, "name", "") == "Sun"), None)
    if not moon or not sun:
        raise ValueError("Could not calculate Moon/Sun for feed context")

    phase_angle = (moon.longitude - sun.longitude) % 360
    moon_sign_ru = engine_utils.translate_sign(getattr(moon, "sign", "") or "")
    phase_name = _get_phase_name(phase_angle)
    moon_degree = round(float(moon.longitude % 30), 1)
    day_aspects = _select_transit_day_aspects(engine.find_natal_aspects(transit_chart))

    facts: dict[str, Any] = {
        "date": now_local.strftime("%d.%m.%Y"),
        "timezone": tz_str,
        "local_dt": now_local.isoformat(),
        "weekday": RU_WEEKDAYS[now_local.weekday()],
        "location_label": location_label,
        "moon_sign": moon_sign_ru,
        "moon_phase": phase_name,
        "moon_emoji": _get_moon_phase_emoji(phase_angle),
        "moon_degree": moon_degree,
        "aspect_summary": ", ".join(_format_transit_aspect(item) for item in day_aspects) or "Нет мажорных аспектов",
        "aspects_count": len(day_aspects),
        "traffic_lights": _build_generic_traffic_lights(day_aspects, phase_name, moon_degree),
        "personalization_level": "anonymous",
        "fact_lines": _build_fact_lines(
            now_local=now_local,
            location_label=location_label,
            tz_str=tz_str,
            moon_sign_ru=moon_sign_ru,
            phase_name=phase_name,
            fast_hits=[],
            day_aspects=day_aspects,
            today_context={},
            month_data={},
            year_data={},
            sun_sign=getattr(user, "sun_sign", None) if user else None,
        ),
    }
    facts["semantic_layer"] = build_daily_forecast_semantic_layer(
        fast_hits=[],
        traffic_lights=facts.get("traffic_lights"),
        day_context={},
        month_data={},
    )

    if _is_full_profile(user):
        natal_chart = _create_natal_chart(engine, user)
        fast_hits = _select_fast_hits(engine.find_transit_aspects(natal_chart, transit_chart, orb=1.2))
        forecast_location = _resolve_forecast_location(user, location_label)

        week_data: dict[str, Any] = {}
        month_data: dict[str, Any] = {}
        year_data: dict[str, Any] = {}

        try:
            week_data = engine.calculate_forecast_week_data(natal_chart, now_local, forecast_location)
        except Exception as exc:
            logger.warning("daily.personalization.week_failed", error=str(exc), location=forecast_location)

        try:
            month_data = engine.calculate_forecast_month_data(natal_chart, now_local, forecast_location)
        except Exception as exc:
            logger.warning("daily.personalization.month_failed", error=str(exc), location=forecast_location)

        try:
            year_data = engine.calculate_forecast_year_data(natal_chart, now_local.year, forecast_location)
        except Exception as exc:
            logger.warning("daily.personalization.year_failed", error=str(exc), location=forecast_location)

        today_context = _week_today_context(week_data)
        aspect_summary = ", ".join(hit["summary"] for hit in fast_hits) or facts["aspect_summary"]
        personalized_traffic_lights = _build_personalized_traffic_lights(
            fast_hits,
            today_context,
            month_data,
            year_data,
            now_local.month,
        )
        if isinstance(today_context, dict):
            today_context = copy.deepcopy(today_context)
            today_context["personalized_traffic_lights"] = personalized_traffic_lights

        facts.update(
            {
                "aspect_summary": aspect_summary,
                "aspects_count": len(fast_hits) if fast_hits else facts["aspects_count"],
                "fast_hits": fast_hits,
                "week_data": week_data,
                "month_data": month_data,
                "year_data": year_data,
                "traffic_lights": personalized_traffic_lights,
                "personalization_level": "personalized_v2",
                "fact_lines": _build_fact_lines(
                    now_local=now_local,
                    location_label=location_label,
                    tz_str=tz_str,
                    moon_sign_ru=moon_sign_ru,
                    phase_name=phase_name,
                    fast_hits=fast_hits,
                    day_aspects=day_aspects,
                    today_context=today_context,
                    month_data=month_data,
                    year_data=year_data,
                    sun_sign=getattr(user, "sun_sign", None),
                ),
                "semantic_layer": build_daily_forecast_semantic_layer(
                    fast_hits=fast_hits,
                    traffic_lights=personalized_traffic_lights,
                    day_context=today_context,
                    month_data=month_data,
                ),
            }
        )
    elif user:
        facts["personalization_level"] = "profile_light"
        logger.info(
            "daily.personalization.partial_profile",
            timezone=tz_str,
            location=location_label,
            has_birth_date=bool(getattr(user, "birth_date", None)),
            has_birth_place=bool(getattr(user, "birth_place", None)),
        )
    else:
        logger.info(
            "daily.personalization.general_fallback",
            timezone=tz_str,
            location=location_label,
        )

    facts["cache_scope"] = _build_cache_scope(facts)
    facts["cache_scope_level"] = facts.get("personalization_level")
    facts["meta"] = {
        "cache_scope": facts["cache_scope"],
        "cache_scope_level": facts.get("cache_scope_level"),
        "personalization_level": facts.get("personalization_level"),
        "timezone": facts.get("timezone"),
        "location_label": facts.get("location_label"),
        "has_fast_hits": bool(facts.get("fast_hits")),
        "fallback_mode": facts.get("personalization_level") in {"anonymous", "profile_light"},
        "fact_lines": copy.deepcopy(facts.get("fact_lines", [])[:6]),
        "traffic_lights": copy.deepcopy(facts.get("traffic_lights", {})),
    }
    fallback_mode = facts.get("personalization_level") in {"anonymous", "profile_light"}
    _emit_feed_log(
        "feed.debug",
        stage="facts_built",
        cache_scope=facts["cache_scope"],
        personalization_level=facts.get("personalization_level"),
        timezone=facts.get("timezone"),
        location=facts.get("location_label"),
        has_fast_hits=bool(facts.get("fast_hits")),
        fallback_mode=fallback_mode,
        fallback_reason=("limited_profile" if fallback_mode else None),
        prompt_path="personalized_daily_v2",
    )
    _PERSONALIZED_DAILY_CACHE[cache_key] = copy.deepcopy(facts)
    return facts


# #END_BLOCK_PERSONALIZED_DAILY_FACTS


# #START_BLOCK_PERSONALIZED_DAILY_SCORING
def summarize_personalization_for_prompt(facts: dict[str, Any]) -> dict[str, Any]:
    fact_lines = [
        line.strip()
        for line in facts.get("fact_lines", [])
        if isinstance(line, str) and line.strip()
    ]
    fallback_detail = " ".join(fact_lines[2:5]).strip()
    if not fallback_detail:
        fallback_detail = fact_lines[1] if len(fact_lines) > 1 else ""

    return {
        "level": facts.get("personalization_level", "anonymous"),
        "fact_lines": fact_lines[:6],
        "fallback_detail": fallback_detail,
        "cache_scope": facts.get("cache_scope"),
        "traffic_lights": copy.deepcopy(facts.get("traffic_lights", {})),
        "semantic_layer": copy.deepcopy(facts.get("semantic_layer", {})),
        "prompt_contract": "personalized_daily_v2",
    }


# #END_BLOCK_PERSONALIZED_DAILY_SCORING
