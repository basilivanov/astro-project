"""WeekBrief normalization and deterministic factor seed helpers."""

# ############################################################################
# AI_HEADER: MODULE_WEEK_BRIEF_NORMALIZATION
# ROLE: Normalize dates, text, day cards, section seeds, and factor seeds.
# DEPENDENCIES: week_brief_foundation, forecast_factor_pipeline, personal_susceptibility.
# GRACE_ANCHORS: [WEEK_BRIEF_NORMALIZATION]
# ############################################################################

# START_MODULE_CONTRACT: M-WEEK-BRIEF-NORMALIZATION
# purpose: Convert week seed data into stable normalized day, domain, section, and factor intermediates.
# owns:
#   - backend/app/services/week_brief_normalization.py
# inputs:
#   - week seed bundle, semantic layer, day payloads, and normalized factor records
# outputs:
#   - normalized day cards, factor records, section seeds, and action/domain helpers
# invariants:
#   - deterministic fallback wording and factor weights remain unchanged
# non_goals:
#   - changing API envelope or validation contracts
# END_MODULE_CONTRACT: M-WEEK-BRIEF-NORMALIZATION

# START_MODULE_MAP: M-WEEK-BRIEF-NORMALIZATION
# public_entrypoints:
#   - _build_factor_seeds -> deterministic factor extraction
#   - _build_day_cards -> normalized seven-day card assembly
#   - _build_week_section_seeds -> deterministic deep section seeds
# semantic_blocks:
#   - WEEK_BRIEF_NORMALIZATION: date/text/chunk/factor seed normalization helpers
# owned_tests:
#   - tests/test_week_brief_service.py
# adjacent_modules:
#   - backend/app/services/week_brief_foundation.py
#   - backend/app/services/week_brief_assembly.py
# END_MODULE_MAP: M-WEEK-BRIEF-NORMALIZATION

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

from .forecast_factor_pipeline import NormalizedFactor, clamp_signal, make_factor, normalize_domain
from .personal_susceptibility import attach_susceptibility, build_susceptibility_profile, calibration_entrypoints
from .week_brief_foundation import *
from . import week_brief_foundation as _foundation
globals().update({name: getattr(_foundation, name) for name in dir(_foundation) if name.startswith("_") and not name.startswith("__")})

# START_BLOCK: WEEK_BRIEF_NORMALIZATION
def _safe_date(value: Any, *, default: date) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raw = str(value or "").strip()
    if raw:
        try:
            return datetime.fromisoformat(raw).date()
        except ValueError:
            pass
    return default


def _safe_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _map_report_status(report_status: Any) -> str:
    normalized = str(report_status or "").strip().lower()
    if normalized in {"completed", "done", "ready"}:
        return "ready"
    if normalized in {"failed", "error"}:
        return "error"
    return "in_progress"


def _week_window(seed: dict[str, Any], *, report: Any | None = None) -> tuple[date, date]:
    days = seed.get("days") or []
    if days:
        start = _safe_date(days[0].get("date"), default=date.today())
        end = _safe_date(days[-1].get("date"), default=start + timedelta(days=6))
        return start, end
    forecast_window = seed.get("forecast_window") or {}
    start_dt = _safe_datetime((forecast_window or {}).get("start"))
    if start_dt is None and report is not None:
        start_dt = getattr(report, "created_at", None)
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    start = start_dt.date()
    return start, start + timedelta(days=6)


def _weekday_code(day: dict[str, Any], current_date: date) -> str:
    raw = str(day.get("weekday") or day.get("weekday_ru") or "").strip().lower()
    if raw in WEEKDAY_CODE_MAP:
        return WEEKDAY_CODE_MAP[raw]
    return ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][current_date.weekday()]


def _is_hard_aspect(text: str) -> bool:
    lowered = text.lower()
    return "квадрат" in lowered or "оппозиц" in lowered or "шторм" in lowered


def _signal_source_for_models(models: Iterable[str]) -> str:
    normalized = [str(item).strip() for item in models if str(item).strip()]
    if not normalized:
        return SignalSource.mixed.value
    if len(normalized) == 1:
        return normalized[0]
    return SignalSource.mixed.value


def _score_day_card(day: dict[str, Any]) -> int:
    status = str(day.get("traffic_light") or "YELLOW").upper()
    tension = float(day.get("tension_score") or 0.0)
    base = {"GREEN": 78, "YELLOW": 60, "RED": 38}.get(status, 60)
    if status == "GREEN":
        base += max(0, int((0.5 - tension) * 6))
    elif status == "RED":
        base -= max(0, int((tension - 1.5) * 8))
    else:
        base -= max(0, int(tension * 3))
    if (day.get("moon") or {}).get("void_of_course"):
        base -= 4
    return max(0, min(100, base))


def _build_day_headline(day: dict[str, Any], focus_key: str) -> str:
    status = str(day.get("traffic_light") or "YELLOW").upper()
    events = [str(item).strip() for item in (day.get("events") or []) if str(item).strip()]
    if events:
        event_line = events[0]
        if len(event_line) <= 96 and not _looks_like_raw_astro_phrase(event_line):
            return event_line
    if status == "GREEN":
        return {
            "money_admin": "Лучший день для фиксации и договоренностей",
            "relationship": "Хороший день для прямого и теплого разговора",
            "rest": "День с более мягким темпом и понятным ресурсом",
            "launch": "День для запуска и ключевого хода",
        }.get(focus_key, "День для заметного продвижения")
    if status == "RED":
        return "День требует буфера и сокращения лишнего"
    return "День лучше вести спокойно и по шагам"


def _moon_context_tokens(day: dict[str, Any]) -> tuple[str | None, str | None]:
    moon = day.get("moon") or {}
    sign = str(moon.get("sign") or "").strip()
    phase = str(moon.get("phase") or "").strip()
    return (sign or None, phase or None)


def _dedupe_keep_order(items: Iterable[str], *, limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = re.sub(r"\s+", " ", str(item or "")).strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
        if len(result) >= limit:
            break
    return result


def _looks_like_raw_astro_phrase(value: str) -> bool:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    lowered = text.lower()
    if not text:
        return False
    astro_tokens = (
        "квадрат",
        "соединение",
        "оппози",
        "секстиль",
        "тригон",
        "нептун",
        "плутон",
        "сатурн",
        "юпитер",
        "венера",
        "меркурий",
        "марс",
        "луна",
        "солнце",
        " asc",
        " mc",
    )
    return any(token in lowered for token in astro_tokens) or bool(re.search(r"\b\d{1,2}\.\d{1,2}\b", text))


def _sanitize_user_hint(value: str | None, *, fallback: str | None = None) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" .,-–—")
    if not text or _looks_like_raw_astro_phrase(text):
        return fallback
    return text[:96]


def _looks_like_placeholder_text(value: str) -> bool:
    text = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    if not text:
        return True
    return any(token in text for token in ("week_strategy", "week_timing", "week_background", "section ", "раздел ", "placeholder", "todo"))


def _looks_like_placeholder_markdown(value: str) -> bool:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return True
    return _looks_like_placeholder_text(text) or text.startswith("{") or text.startswith("[") or len(text) < 24


def _build_day_actions(day: dict[str, Any], focus_key: str) -> tuple[list[str], list[str]]:
    status = str(day.get("traffic_light") or "YELLOW").upper()
    moon_label = str(day.get("moon_label") or "").strip()
    moon_sign, moon_phase = _moon_context_tokens(day)
    events = [str(item).strip() for item in (day.get("events") or []) if str(item).strip()]
    best_for = {
        "money_admin": ["согласование", "фиксация условий"],
        "relationship": ["разговор по существу", "мягкая обратная связь"],
        "rest": ["замедление ритма", "буфер по времени"],
        "launch": ["запуск", "фокусная задача"],
    }.get(focus_key, ["главный приоритет"])
    avoid = {
        "money_admin": ["размытые обещания", "лишний фронт"],
        "relationship": ["давление на ответ", "домысливание"],
        "rest": ["перегрев", "гонка без пауз"],
        "launch": ["распыление", "мелкая суета"],
    }.get(focus_key, ["спешка"])

    event_hints: list[str] = []
    risk_hints: list[str] = []
    for event in events[:2]:
        lowered = event.lower()
        if "->" in event:
            event_hints.append(event)
            continue
        if _is_hard_aspect(lowered):
            risk_hints.append(event)
        elif not _looks_like_raw_astro_phrase(event):
            event_hints.append(event)

    moon_hints = [item for item in (_sanitize_user_hint(moon_sign), _sanitize_user_hint(moon_phase)) if item]

    if status == "GREEN":
        moon_label = _sanitize_user_hint(moon_label)
        if moon_label:
            moon_hints.append(moon_label)
        return (
            _dedupe_keep_order([*best_for, *event_hints, *moon_hints], limit=4),
            _dedupe_keep_order([*avoid, *risk_hints], limit=3),
        )
    if status == "RED":
        return (
            _dedupe_keep_order(["один приоритет", "проверка вводных", *moon_hints], limit=4),
            _dedupe_keep_order([*risk_hints, *avoid, "жесткий спор", "перегруз"], limit=4),
        )
    if (day.get("moon") or {}).get("void_of_course"):
        avoid = ["жесткое решение", "обещания без ответа"] + avoid
    return (
        _dedupe_keep_order([*best_for, *event_hints, *moon_hints], limit=4),
        _dedupe_keep_order([*risk_hints, *avoid], limit=4),
    )


def _domain_status(value: int) -> str:
    if value >= 70:
        return "green"
    if value >= 50:
        return "yellow"
    return "red"


def _domain_headline(domain_key: str, value: int, focus_key: str) -> str:
    if domain_key == FOCUS_DOMAIN_MAP.get(focus_key):
        return "Это главный рабочий контур недели: здесь больше всего смысла держать внимание."
    if value < 50:
        return "Здесь неделя просит мягкости, буфера и дополнительной проверки."
    return DOMAIN_HEADLINES[domain_key]


def _domain_advice(domain_key: str, value: int, semantic_layer: dict[str, Any]) -> str:
    if domain_key == "work_money":
        if value >= 70:
            return str(semantic_layer.get("money_admin_focus") or "Двигай рабочие и денежные вопросы короткими подтверждаемыми циклами.")
        return "Проверяй сроки, цену решения и договоренности до того, как ускоряться."
    if domain_key == "relationships":
        return str(semantic_layer.get("relationship_softness") or "Сохраняй прямой тон и не дави на скорость ответа.")
    if domain_key == "energy":
        return str(semantic_layer.get("rest") or "Держи режим и не сжигай запас сил на лишнем фронте.")
    return str(semantic_layer.get("pacing") or "Собери главный трек недели и не дроби внимание.")


def _format_action_items(items: list[str], *, prefix: str) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for index, text in enumerate(items):
        normalized = re.sub(r"\s+", " ", str(text or "")).strip()
        if len(normalized) < 8:
            continue
        prepared.append(
            {
                "id": f"{prefix}_{index + 1}",
                "text": normalized[:220],
                "impact": "high" if index == 0 else "medium",
                "timeframe": "all_week",
            }
        )
    return prepared


def _build_best_uses(semantic_layer: dict[str, Any], best_day: dict[str, Any] | None) -> list[dict[str, Any]]:
    items = [
        str(semantic_layer.get("practical_move") or ""),
        str(semantic_layer.get("negotiation") or semantic_layer.get("money_admin_focus") or ""),
    ]
    if best_day is not None:
        label = str(best_day.get("date") or best_day.get("weekday") or "").strip()
        if label:
            best_hint = _sanitize_user_hint(
                ((best_day.get("best_for") or [None])[0]),
                fallback="спокойные договоренности и шаги с проверяемым результатом",
            )
            items.append(f"Ставь на {label} задачи, где важны {best_hint}.")
    items.extend(GENERIC_BEST_USES)
    return _format_action_items(items, prefix="best")[:4]


def _build_risks(semantic_layer: dict[str, Any], worst_day: dict[str, Any] | None) -> list[dict[str, Any]]:
    items = [
        str(semantic_layer.get("friction") or ""),
        str(semantic_layer.get("tension") or ""),
    ]
    if worst_day is not None:
        label = str(worst_day.get("date") or worst_day.get("weekday") or "").strip()
        if label:
            avoid_hint = _sanitize_user_hint(
                ((worst_day.get("avoid") or [None])[0]),
                fallback="лишний нажим и решения без перепроверки",
            )
            items.append(f"На {label} снизь {avoid_hint}: это даст меньше шума и ошибок.")
    items.extend(GENERIC_RISKS)
    return _format_action_items(items, prefix="risk")[:4]


def _build_supporting_factor_entries(factor_records: list[_FactorSeed], factor_ids: list[str], *, limit: int = 3) -> list[dict[str, Any]]:
    indexed = {record.id: record for record in factor_records}
    entries: list[dict[str, Any]] = []
    for factor_id in factor_ids[:limit]:
        record = indexed.get(factor_id)
        if record is None:
            continue
        entries.append(
            {
                "label": record.label[:80],
                "explanation_human": record.explanation_human[:220],
                "explanation_astro": record.explanation_astro[:220] if record.explanation_astro else None,
                "value": record.domain,
            }
        )
    return entries


def _top_factor_ids_for_domain(
    factor_records: list[_FactorSeed],
    domain: str,
    *,
    polarity: str | None = None,
    limit: int = 3,
) -> list[str]:
    filtered = [record for record in factor_records if record.domain == domain]
    if polarity == "positive":
        filtered = [record for record in filtered if record.signal >= 0]
    elif polarity == "negative":
        filtered = [record for record in filtered if record.signal < 0]
    ordered = sorted(filtered, key=lambda item: abs(item.signal) * max(item.weight, 0.1), reverse=True)
    return [record.id for record in ordered[:limit]]


def _enrich_action_items(items: list[dict[str, Any]], factor_records: list[_FactorSeed], *, kind: str) -> list[dict[str, Any]]:
    positive_domains = ("work_money", "focus", "relationships", "energy")
    negative_domains = ("energy", "focus", "work_money", "relationships")
    enriched: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        domain = positive_domains[index % len(positive_domains)] if kind == "best" else negative_domains[index % len(negative_domains)]
        factor_ids = _top_factor_ids_for_domain(factor_records, domain, polarity="positive" if kind == "best" else "negative", limit=3)
        supporting_factors = _build_supporting_factor_entries(factor_records, factor_ids, limit=3)
        why_text = (
            f"Эта рекомендация держится на домене «{DOMAIN_TITLES.get(domain, domain)}»: неделя здесь лучше отвечает на конкретные, дозированные шаги."
            if kind == "best"
            else f"Этот риск заметнее в домене «{DOMAIN_TITLES.get(domain, domain)}»: лишний нажим и шум быстрее сбивают недельный ритм."
        )
        enriched.append(
            {
                **item,
                "factor_id": item.get("factor_id") or (factor_ids[0] if factor_ids else None),
                "why_text": why_text[:280],
                "supporting_factors": supporting_factors,
            }
        )
    return enriched


def _enrich_domains(domains: list[dict[str, Any]], factor_records: list[_FactorSeed]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for domain in domains:
        key = str(domain.get("key") or "focus")
        factor_ids = _top_factor_ids_for_domain(factor_records, key, limit=3)
        enriched.append(
            {
                **domain,
                "why_text": f"Оценка домена собрана из повторяющихся недельных сигналов, а не из одного случайного пика: смотрите на устойчивые факторы ниже."[:280],
                "supporting_factors": _build_supporting_factor_entries(factor_records, factor_ids, limit=3),
            }
        )
    return enriched


def _factor_domain_from_text(text: str, *, fallback: str = "focus") -> str:
    for point, domain in POINT_DOMAIN_MAP.items():
        if point.lower() in text.lower():
            return domain
    return fallback


def _make_week_factor_seed(
    *,
    factor_id: str,
    family: str,
    profile_category: str,
    dto_category: str,
    label: str,
    explanation_human: str,
    explanation_astro: str = "",
    domain: str = "focus",
    signal: float = 0.0,
    weight: float = 1.0,
    confidence: float = 0.8,
    source_models: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    section_slug: str = "overview",
) -> _FactorSeed:
    return _FactorSeed(
        factor=make_factor(
            factor_id=factor_id,
            family=family,
            category=dto_category,
            domain=normalize_domain(domain),
            label=label,
            explanation_human=explanation_human,
            explanation_astro=explanation_astro,
            signal=clamp_signal(signal),
            weight=weight,
            source="deterministic",
            metadata=metadata or {},
        ),
        profile_category=profile_category,
        dto_category=dto_category,
        source_models=list(source_models or [SignalSource.mixed.value]),
        confidence=confidence,
        section_slug=section_slug,
    )


def _build_factor_seeds(seed: dict[str, Any]) -> list[_FactorSeed]:
    summary = seed.get("summary") or {}
    days = seed.get("days") or []
    semantic_layer = seed.get("semantic_layer") or {}
    year_data = seed.get("year_forecast_data") or {}
    month_data = seed.get("month_forecast_data") or {}
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    focus_domain = FOCUS_DOMAIN_MAP.get(focus_key, "focus")
    seeds: list[_FactorSeed] = [
        _make_week_factor_seed(
            factor_id="week:theme_anchor",
            family="slow_background",
            profile_category="period_theme",
            dto_category="background",
            label=str(semantic_layer.get("headline") or FOCUS_THEME_MAP.get(focus_key, "Тема недели")),
            explanation_human=str(semantic_layer.get("practical_move") or "Неделя лучше всего собирается вокруг одной опорной линии."),
            explanation_astro=str(semantic_layer.get("pacing") or "Общий недельный ритм задает темп решений."),
            domain=focus_domain,
            signal=0.9,
            weight=1.0,
            confidence=0.95,
            source_models=[SignalSource.mixed.value],
            metadata={"focus_key": focus_key},
            section_slug="overview",
        )
    ]

    green_days = [day for day in days if str(day.get("traffic_light") or "").upper() == "GREEN"]
    red_days = [day for day in days if str(day.get("traffic_light") or "").upper() == "RED"]
    if green_days:
        best_day = max(green_days, key=_score_day_card)
        best_label = str(best_day.get("date") or best_day.get("date_label") or "лучший день")
        best_events = ", ".join((best_day.get("events") or [])[:2]).strip()
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:best_day:{best_label}",
                family="fast_transits",
                profile_category="weekly_triggers",
                dto_category="transit_natal",
                label=f"Сильное окно недели: {best_label}",
                explanation_human=f"Лучше всего двигать видимые шаги, договоренности и фиксации ближе к {best_label}.",
                explanation_astro=best_events or str(best_day.get("traffic_desc") or "День собирается мягче обычного."),
                domain=focus_domain,
                signal=0.7,
                weight=0.8,
                confidence=0.85,
                source_models=[SignalSource.transit_natal.value],
                metadata={"day": best_label, "kind": "best_day"},
                section_slug="timing",
            )
        )
    if red_days:
        worst_day = max(red_days, key=lambda item: float(item.get("tension_score") or 0.0))
        worst_label = str(worst_day.get("date") or worst_day.get("date_label") or "напряженный день")
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:worst_day:{worst_label}",
                family="fast_transits",
                profile_category="day_decomposition",
                dto_category="transit_natal",
                label=f"Точка трения: {worst_label}",
                explanation_human=f"На {worst_label} важно сократить фронт, оставить буфер и не идти в жесткий нажим.",
                explanation_astro=", ".join((worst_day.get("events") or [])[:2]) or str(worst_day.get("traffic_desc") or ""),
                domain="energy",
                signal=-0.8,
                weight=0.85,
                confidence=0.85,
                source_models=[SignalSource.transit_natal.value],
                metadata={"day": worst_label, "kind": "worst_day"},
                section_slug="timing",
            )
        )

    profection = year_data.get("profection") or {}
    profection_house = profection.get("house")
    if profection_house:
        prof_domain = HOUSE_DOMAIN_MAP.get(int(profection_house), focus_domain)
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:profection:{profection_house}",
                family="slow_background",
                profile_category="slow_background",
                dto_category="profections",
                label=f"Активен дом {profection_house}",
                explanation_human=f"Годовой фон усиливает темы дома {profection_house}, поэтому неделя чувствительна к выбору приоритетов в этой зоне.",
                explanation_astro=f"Профекция {profection_house} дома, управитель года: {profection.get('lord') or 'не уточнен'}.",
                domain=prof_domain,
                signal=0.6,
                weight=0.82,
                confidence=0.9,
                source_models=[SignalSource.profections.value],
                metadata={"house": profection_house},
                section_slug="background",
            )
        )

    solar_return = year_data.get("solar_return") or {}
    if solar_return:
        sr_domain = HOUSE_DOMAIN_MAP.get(int(solar_return.get("sun_house") or 10), focus_domain)
        seeds.append(
            _make_week_factor_seed(
                factor_id="week:solar_return",
                family="slow_background",
                profile_category="slow_background",
                dto_category="solar",
                label=f"Соляр акцентирует дом {solar_return.get('sun_house') or 10}",
                explanation_human="Сюжет недели опирается на солярный вектор: заметнее всего работают решения в видимой и структурной зоне.",
                explanation_astro=f"Соляр ASC в {solar_return.get('asc_sign') or 'неизвестном'}; Солнце в доме {solar_return.get('sun_house') or 10}.",
                domain=sr_domain,
                signal=0.55,
                weight=0.78,
                confidence=0.84,
                source_models=[SignalSource.solar.value],
                metadata={"sun_house": solar_return.get("sun_house")},
                section_slug="background",
            )
        )

    for index, entry in enumerate((year_data.get("solar_arcs") or [])[:2]):
        direction = str(entry.get("direction") or "Дуга").strip()
        natal = str(entry.get("natal") or "").strip()
        label = " ".join(part for part in [direction, natal] if part).strip() or f"Солярная дуга {index + 1}"
        domain = _factor_domain_from_text(label, fallback=focus_domain)
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:solar_arc:{index}",
                family="slow_background",
                profile_category="rare_boosters",
                dto_category="directions",
                label=label[:80],
                explanation_human=f"Редкий фоновый усилитель подчеркивает тему '{label.lower()}' в течение недели.",
                explanation_astro=f"Солярная дуга: {direction} к {natal}, орб {entry.get('orb') or 'н/д'}.",
                domain=domain,
                signal=0.42,
                weight=0.66,
                confidence=0.74,
                source_models=[SignalSource.directions.value],
                metadata={"orb": entry.get("orb")},
                section_slug="background",
            )
        )

    for index, transit in enumerate((month_data.get("major_transits") or [])[:3]):
        transit_text = str(transit or "").strip()
        if not transit_text:
            continue
        signal = -0.58 if _is_hard_aspect(transit_text) else 0.48
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:major_transit:{index}",
                family="fast_transits",
                profile_category="weekly_triggers",
                dto_category="transit_transit",
                label=transit_text[:80],
                explanation_human=(
                    "Этот транзит делает неделю чувствительнее к трению и требует более аккуратных решений."
                    if signal < 0
                    else "Этот транзит помогает продвинуть то, что уже готово и собрано."
                ),
                explanation_astro=transit_text[:260],
                domain=_factor_domain_from_text(transit_text, fallback=focus_domain),
                signal=signal,
                weight=0.68,
                confidence=0.78,
                source_models=[SignalSource.transit_transit.value],
                metadata={"kind": "major_transit"},
                section_slug="timing",
            )
        )

    for index, ingress in enumerate((month_data.get("ingresses") or [])[:2]):
        ingress_text = str(ingress or "").strip()
        if not ingress_text:
            continue
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:ingress:{index}",
                family="fast_transits",
                profile_category="weekly_triggers",
                dto_category="transit_transit",
                label=ingress_text[:80],
                explanation_human="Смена знака или контекста сдвигает темп недели и помогает обновить подход.",
                explanation_astro=ingress_text[:260],
                domain=_factor_domain_from_text(ingress_text, fallback=focus_domain),
                signal=0.36,
                weight=0.54,
                confidence=0.72,
                source_models=[SignalSource.transit_transit.value],
                metadata={"kind": "ingress"},
                section_slug="timing",
            )
        )

    for index, retro in enumerate((month_data.get("retrogrades") or [])[:2]):
        retro_text = str(retro or "").strip()
        if not retro_text:
            continue
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:retrograde:{index}",
                family="slow_background",
                profile_category="day_decomposition",
                dto_category="transit_transit",
                label=retro_text[:80],
                explanation_human="Ретроградный фон просит пересматривать вводные и не спешить с окончательными выводами.",
                explanation_astro=retro_text[:260],
                domain="focus",
                signal=-0.44,
                weight=0.52,
                confidence=0.7,
                source_models=[SignalSource.transit_transit.value],
                metadata={"kind": "retrograde"},
                section_slug="timing",
            )
        )

    for index, lunation in enumerate((month_data.get("lunations") or [])[:2]):
        lunation_text = str(lunation or "").strip()
        if not lunation_text:
            continue
        seeds.append(
            _make_week_factor_seed(
                factor_id=f"week:lunation:{index}",
                family="lunar_windows",
                profile_category="weekly_triggers",
                dto_category="lunar_timing",
                label=lunation_text[:80],
                explanation_human="Лунация отмечает кульминацию и помогает увидеть, что уже созрело для фиксации.",
                explanation_astro=lunation_text[:260],
                domain=focus_domain,
                signal=0.4,
                weight=0.58,
                confidence=0.75,
                source_models=[SignalSource.lunar.value],
                metadata={"kind": "lunation"},
                section_slug="timing",
            )
        )

    avg_tension = float(summary.get("avg_tension") or 0.0)
    if avg_tension >= 1.0:
        seeds.append(
            _make_week_factor_seed(
                factor_id="week:tension_anchor",
                family="slow_background",
                profile_category="day_decomposition",
                dto_category="background",
                label="Неделя просит больше буфера",
                explanation_human="Средний уровень напряжения выше обычного, поэтому устойчивость сейчас важнее скорости.",
                explanation_astro=f"Среднее напряжение недели: {avg_tension:.2f}.",
                domain="energy",
                signal=-0.7,
                weight=min(1.0, avg_tension / 2.0),
                confidence=0.9,
                source_models=[SignalSource.mixed.value],
                metadata={"avg_tension": avg_tension},
                section_slug="overview",
            )
        )
    return seeds


def _build_week_section_seeds(seed: dict[str, Any], factor_records: list[_FactorSeed]) -> list[WeekSectionSeed]:
    semantic_layer = seed.get("semantic_layer") or {}
    grouped: dict[str, list[_FactorSeed]] = {}
    for record in factor_records:
        grouped.setdefault(record.section_slug or "overview", []).append(record)

    titles = {
        "overview": "Каркас недели",
        "timing": "Окна и триггеры",
        "background": "Фоновый слой",
    }
    summaries = {
        "overview": str(semantic_layer.get("headline") or "Главная линия недели собрана из устойчивых факторов."),
        "timing": str(semantic_layer.get("practical_move") or "Неделю лучше вести через короткие окна и подтверждаемые шаги."),
        "background": str(semantic_layer.get("pacing") or "Фоновый слой задает темп и приоритеты недели."),
    }

    section_seeds: list[WeekSectionSeed] = []
    for order, slug in enumerate(("overview", "timing", "background")):
        records = grouped.get(slug) or []
        if not records:
            continue
        dominant = max(records, key=lambda item: abs(item.signal) * max(item.weight, 0.1))
        factor_ids = [record.id for record in sorted(records, key=lambda item: abs(item.signal) * max(item.weight, 0.1), reverse=True)[:4]]
        section_seeds.append(
            WeekSectionSeed(
                id=f"section:{slug}",
                slug=slug,
                title=titles[slug],
                summary=summaries[slug][:240],
                factor_ids=factor_ids,
                domain=dominant.domain,
                source=dominant.factor.source,
                metadata={"order": order, "factor_count": len(records)},
            )
        )
    return section_seeds


def _assemble_week_top_layer(
    factor_records: list[_FactorSeed],
    *,
    limit: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    susceptibility = build_susceptibility_profile(None)
    weighted = apply_weighted_factors(
        "week_map",
        attach_susceptibility([
            {
                "id": record.id,
                "category": record.profile_category,
                "label": record.label,
                "weight": abs(record.weight),
                "confidence": record.confidence,
                "domain": record.domain,
                "dto_category": record.dto_category,
                "explanation_human": record.explanation_human,
                "explanation_astro": record.explanation_astro,
                "source_models": record.source_models,
                "signal": record.signal,
                "family": record.factor.family,
            }
            for record in factor_records
        ], profile=susceptibility),
        top_n=limit,
    )
    by_id = {record.id: record for record in factor_records}
    payloads: list[dict[str, Any]] = []
    for factor in weighted.get("top_factors", []):
        source = by_id.get(str(factor.get("id") or ""))
        if source is None:
            continue
        payloads.append(
            {
                "id": source.id,
                "label": source.label[:80],
                "impact": "high" if abs(source.signal) >= 0.7 else "medium" if abs(source.signal) >= 0.45 else "low",
                "category": source.dto_category,
                "explanation_human": source.explanation_human[:260],
                "explanation_astro": source.explanation_astro[:260],
                "source_models": source.source_models,
                "weight": round(min(1.0, factor.get("impact_pct", 0.0) / 100.0 + 0.2), 3),
            }
        )
    payloads.sort(key=lambda item: (0 if item.get("id") == "week:theme_anchor" else 1, -float(item.get("weight") or 0.0), str(item.get("id") or "")))
    return payloads[:limit], weighted


# END_BLOCK: WEEK_BRIEF_NORMALIZATION
