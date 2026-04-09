"""Deterministic WeekBrief assembly for week forecast report detail."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

from ..logging_utils import get_correlation_ids, log_grace_event
from .aggregation_weights import apply_weighted_factors
from .forecast_factor_pipeline import NormalizedFactor, clamp_signal, make_factor, normalize_domain
from .personal_susceptibility import attach_susceptibility, build_susceptibility_profile, calibration_entrypoints
try:
    from .report_workflow import (
        _build_week_brief_seed_bundle,
        _normalize_week_day_payload,
        _normalize_week_summary,
        _parse_json_block_list,
    )
except ModuleNotFoundError:  # pragma: no cover - test env without heavy astro deps
    def _build_week_brief_seed_bundle(context: dict[str, Any]) -> dict[str, Any]:
        week_data = context.get("week_forecast_data") or {}
        return {
            "forecast_window": context.get("forecast_window") or {},
            "days": copy.deepcopy((week_data.get("days") or [])[:7]),
            "summary": copy.deepcopy(week_data.get("summary") or {}),
            "semantic_layer": copy.deepcopy(context.get("semantic_layer") or {}),
            "year_forecast_data": copy.deepcopy(context.get("year_forecast_data") or {}),
            "month_forecast_data": copy.deepcopy(context.get("month_forecast_data") or {}),
        }

    def _normalize_week_day_payload(day: dict[str, Any]) -> dict[str, Any]:
        payload = dict(day or {})
        payload.setdefault("traffic_light", "YELLOW")
        payload.setdefault("moon", {})
        payload.setdefault("events", payload.get("ingresses") or [])
        return payload

    def _normalize_week_summary(summary: dict[str, Any], _days: list[dict[str, Any]]) -> dict[str, Any]:
        payload = dict(summary or {})
        payload.setdefault("traffic_light", "YELLOW")
        payload.setdefault("avg_tension", 0.6)
        return payload

    def _parse_json_block_list(raw_content: str) -> list[dict[str, Any]]:
        try:
            parsed = json.loads(raw_content or "[]")
        except Exception:
            return []
        return parsed if isinstance(parsed, list) else []
from .week_brief_types import SignalSource
from .week_brief_validators import (
    validate_week_brief_envelope_payload,
    validate_week_brief_payload,
)


MODULE_ID = "M-WEEK-BRIEF"
WEEKDAY_CODE_MAP = {
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
    "sunday": "sun",
    "понедельник": "mon",
    "вторник": "tue",
    "среда": "wed",
    "четверг": "thu",
    "пятница": "fri",
    "суббота": "sat",
    "воскресенье": "sun",
}
FOCUS_THEME_MAP = {
    "money_admin": "Работа, договоренности и ритм",
    "relationship": "Контакт, тон и личные границы",
    "rest": "Ресурс, восстановление и буфер",
    "launch": "Запуск, фокус и системный ход",
}
FOCUS_DOMAIN_MAP = {
    "money_admin": "work_money",
    "relationship": "relationships",
    "rest": "energy",
    "launch": "focus",
}
HOUSE_DOMAIN_MAP = {
    1: "energy",
    2: "work_money",
    3: "focus",
    4: "relationships",
    5: "relationships",
    6: "energy",
    7: "relationships",
    8: "work_money",
    9: "focus",
    10: "work_money",
    11: "relationships",
    12: "energy",
}
POINT_DOMAIN_MAP = {
    "Солнце": "work_money",
    "MC": "work_money",
    "ASC": "energy",
    "Марс": "energy",
    "Луна": "relationships",
    "Венера": "relationships",
    "Меркурий": "focus",
    "Юпитер": "focus",
}
DOMAIN_TITLES = {
    "work_money": "Работа и деньги",
    "relationships": "Отношения",
    "energy": "Энергия",
    "focus": "Фокус",
}
DOMAIN_HEADLINES = {
    "work_money": "Неделя показывает, насколько хорошо собран рабочий контур.",
    "relationships": "Тон и формат разговора сейчас влияют на результат сильнее обычного.",
    "energy": "Ресурс держится на ритме, а не на одном сильном рывке.",
    "focus": "Лучше всего едут задачи, где понятен следующий конкретный шаг.",
}
GENERIC_BEST_USES = (
    "Сузь неделю до одной главной линии и держи решения привязанными к ней.",
    "Фиксируй договоренности письменно, чтобы не тратить ресурс на повторные согласования.",
)
GENERIC_RISKS = (
    "Не принимай промежуточную ясность за окончательный результат.",
    "Не трать сильные дни на шум и параллельные срочности.",
)


@dataclass
class WeekSectionSeed:
    id: str
    slug: str
    title: str
    summary: str
    factor_ids: list[str] = field(default_factory=list)
    domain: str = "focus"
    source: str = "deterministic"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class _FactorSeed:
    factor: NormalizedFactor
    profile_category: str
    dto_category: str
    source_models: list[str]
    confidence: float
    section_slug: str = "overview"

    @property
    def id(self) -> str:
        return self.factor.id

    @property
    def label(self) -> str:
        return self.factor.label

    @property
    def explanation_human(self) -> str:
        return self.factor.explanation_human

    @property
    def explanation_astro(self) -> str:
        return self.factor.explanation_astro

    @property
    def domain(self) -> str:
        return self.factor.domain

    @property
    def weight(self) -> float:
        return self.factor.weight

    @property
    def signal(self) -> float:
        return self.factor.signal


def _log_week_brief(level: str, event: str, *, report: Any | None = None, **fields: Any) -> None:
    context = get_correlation_ids()
    payload = {key: value for key, value in fields.items() if value is not None}
    if report is not None:
        payload["report_id"] = str(report.id)
        payload["report_type"] = getattr(report, "report_type", None)
        payload["report_status"] = getattr(report, "status", None)
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn="build_week_brief_payload",
        block="ASSEMBLY",
        correlation_id=context.get("correlation_id"),
        trace_id=context.get("trace_id"),
        correlation_source=context.get("correlation_source"),
        **payload,
    )


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


def _weighted_factor_payloads(records: list[_FactorSeed]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return _assemble_week_top_layer(records, limit=5)
def _build_domain_scores(
    seed: dict[str, Any],
    factor_records: list[_FactorSeed],
    day_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    semantic_layer = seed.get("semantic_layer") or {}
    summary = seed.get("summary") or {}
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    scores = {
        "work_money": 55,
        "relationships": 55,
        "energy": 55,
        "focus": 55,
    }
    traffic = str(summary.get("traffic_light") or "YELLOW").upper()
    if traffic == "GREEN":
        scores["work_money"] += 8
        scores["focus"] += 10
        scores["energy"] += 4
        scores["relationships"] += 4
    elif traffic == "RED":
        scores["energy"] -= 10
        scores["work_money"] -= 6
        scores["focus"] -= 6
        scores["relationships"] -= 4

    dominant_domain = FOCUS_DOMAIN_MAP.get(focus_key, "focus")
    scores[dominant_domain] += 9

    for card in day_cards:
        mode = str(card.get("mode") or "").lower()
        if mode == "green":
            scores[dominant_domain] += 2
            scores["focus"] += 1
        elif mode == "red":
            scores["energy"] -= 2
            scores["focus"] -= 1

    for record in factor_records:
        impact = int(round(record.weight * 12))
        if record.signal < 0:
            scores[record.domain] -= impact
        else:
            scores[record.domain] += impact

    domains: list[dict[str, Any]] = []
    for key in ("work_money", "relationships", "energy", "focus"):
        value = max(0, min(100, int(scores[key])))
        domains.append(
            {
                "key": key,
                "title": DOMAIN_TITLES[key],
                "status": _domain_status(value),
                "value": value,
                "headline": _domain_headline(key, value, focus_key)[:100],
                "advice": _domain_advice(key, value, semantic_layer)[:220],
            }
        )
    return domains


def _confidence_bucket(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.6:
        return "medium"
    return "low"


def _build_explainability(
    seed: dict[str, Any],
    weighted: dict[str, Any],
    factor_count: int,
    *,
    birth_time_used: bool,
    fallback_mode: bool,
    chunk_parse_degraded: bool,
) -> dict[str, Any]:
    confidence = 0.52
    if seed.get("days"):
        confidence += 0.12
    if seed.get("year_forecast_data") or seed.get("month_forecast_data"):
        confidence += 0.1
    if factor_count >= 5:
        confidence += 0.08
    if birth_time_used:
        confidence += 0.06
    if fallback_mode:
        confidence -= 0.16
    if chunk_parse_degraded:
        confidence -= 0.08
    confidence = round(max(0.35, min(0.94, confidence)), 2)

    top_factors = weighted.get("top_factors") or []
    top_signal_source = SignalSource.mixed.value
    if top_factors:
        top_signal_source = _signal_source_for_models(top_factors[0].get("source_models") or [])

    return {
        "confidence": confidence,
        "birth_time_used": bool(birth_time_used),
        "factor_count": factor_count,
        "timing_precision": "exact" if seed.get("days") else "approximate",
        "top_signal_source": top_signal_source,
        "explanation_depth": "full" if factor_count >= 5 else "standard",
        "reliability_support": [
            str(item.get("label") or item.get("factor_id") or "").strip()
            for item in (weighted.get("reliability_support", []) or [])
            if isinstance(item, dict) and str(item.get("label") or item.get("factor_id") or "").strip()
        ],
        "calibration": {
            "weight_profile_version": weighted.get("weight_profile_version", "v2"),
            "susceptibility_source": "deterministic_default",
            "susceptibility_version": "v1",
            "entrypoints": calibration_entrypoints(),
        },
    }


def _render_chunk_markdown(blocks: list[dict[str, Any]], raw_content: str) -> tuple[str, str | None, bool]:
    if not blocks:
        return raw_content.strip() or "Секция доступна в исходном виде.", None, True

    lines: list[str] = []
    summary: str | None = None
    degraded = False
    for block in blocks:
        block_type = str(block.get("type") or "").strip().lower()
        if block_type == "header":
            level = int(block.get("level") or 2)
            text = str(block.get("text") or "").strip()
            if text:
                lines.append(f"{'#' * max(1, min(6, level))} {text}")
        elif block_type == "paragraph":
            text = str(block.get("text") or "").strip()
            if text:
                lines.append(text)
                if summary is None:
                    summary = text[:240]
        elif block_type == "callout":
            title = str(block.get("title") or "").strip()
            content = str(block.get("content") or "").strip()
            if title or content:
                label = f"**{title}**" if title else ""
                lines.append(": ".join(part for part in [label, content] if part))
                if summary is None and content:
                    summary = content[:240]
        elif block_type == "list":
            items = [str(item).strip() for item in (block.get("items") or []) if str(item).strip()]
            lines.extend(f"- {item}" for item in items)
            if summary is None and items:
                summary = items[0][:240]
        elif block_type == "key_value":
            items = [item for item in (block.get("items") or []) if isinstance(item, dict)]
            for item in items:
                key = str(item.get("key") or "").strip()
                value = str(item.get("value") or "").strip()
                if key or value:
                    lines.append(f"- **{key}**: {value}".strip())
            if summary is None and items:
                first = items[0]
                summary = f"{first.get('key')}: {first.get('value')}"[:240]
        elif block_type == "traffic_lights":
            items = block.get("items") or {}
            if isinstance(items, dict):
                normalized_items = []
                for key in ("money", "health", "love"):
                    value = str(items.get(key) or "").strip()
                    if value:
                        normalized_items.append(f"{key}: {value}")
                if normalized_items:
                    lines.append("Срезы недели:")
                    lines.extend(f"- {item}" for item in normalized_items)
                    if summary is None:
                        summary = f"Срезы недели: {', '.join(normalized_items)}"[:240]
                else:
                    degraded = True
            else:
                degraded = True
        else:
            degraded = True
    markdown = "\n\n".join(line for line in lines if line).strip() or raw_content.strip()
    return markdown, summary, degraded


def _chunk_title(section: str, blocks: list[dict[str, Any]]) -> str:
    for block in blocks:
        if str(block.get("type") or "").strip().lower() == "header":
            text = str(block.get("text") or "").strip()
            if text:
                return text[:80]
    return section.replace("_", " ").strip().title()[:80] or "Секция"


def _section_seed_title(seed: WeekSectionSeed) -> str:
    title = str(seed.title or "").strip()
    return title[:80] or seed.slug.replace("_", " ").strip().title()[:80] or "Секция"


def _section_seed_markdown(seed: WeekSectionSeed, factor_records: list[_FactorSeed]) -> str:
    lines: list[str] = [f"# {_section_seed_title(seed)}", str(seed.summary or "").strip()]
    indexed_records = {record.id: record for record in factor_records}
    ordered_records = [indexed_records[factor_id] for factor_id in seed.factor_ids if factor_id in indexed_records]
    for record in ordered_records[:4]:
        detail = str(record.explanation_human or record.explanation_astro or "").strip()
        if not detail:
            continue
        lines.append(f"- {record.label}: {detail}")
    return "\n\n".join(part for part in lines if part).strip()


def _build_seed_deep_sections(
    section_seeds: list[WeekSectionSeed],
    factor_records: list[_FactorSeed],
) -> list[dict[str, Any]]:
    deep_sections: list[dict[str, Any]] = []
    for order, section_seed in enumerate(section_seeds):
        deep_sections.append(
            {
                "id": section_seed.id,
                "slug": section_seed.slug[:64],
                "title": _section_seed_title(section_seed),
                "summary": str(section_seed.summary or "").strip()[:240],
                "body_markdown": _section_seed_markdown(section_seed, factor_records),
                "is_primary": order == 0,
                "order": order,
            }
        )
    return deep_sections[:16]


def _build_deep_sections(chunks: Iterable[Any]) -> tuple[list[dict[str, Any]], bool]:
    deep_sections: list[dict[str, Any]] = []
    degraded = False
    for order, chunk in enumerate(sorted(chunks, key=lambda item: int(getattr(item, "order_index", 0)))):
        section = str(getattr(chunk, "section", "") or "").strip()
        if not section or section == "input_frame":
            continue
        raw_content = str(getattr(chunk, "content", "") or "").strip()
        blocks = _parse_json_block_list(raw_content)
        markdown, summary, section_degraded = _render_chunk_markdown(blocks, raw_content)
        degraded = degraded or section_degraded or str(getattr(chunk, "status", "") or "").lower() != "completed"
        deep_sections.append(
            {
                "id": f"deep_{section}",
                "slug": section[:64],
                "title": _chunk_title(section, blocks),
                "summary": summary,
                "body_markdown": markdown,
                "is_primary": section == "week_strategy" or order == 0,
                "order": order,
            }
        )
    return deep_sections[:16], degraded


def _merge_seed_with_chunk_sections(
    seed_sections: list[dict[str, Any]],
    chunk_sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not seed_sections:
        return chunk_sections[:16]

    chunk_by_slug = {
        str(section.get("slug") or "").strip(): section
        for section in chunk_sections
        if str(section.get("slug") or "").strip()
    }
    merged: list[dict[str, Any]] = []
    for seed_section in seed_sections:
        merged_section = copy.deepcopy(seed_section)
        chunk_section = chunk_by_slug.get(str(seed_section.get("slug") or "").strip())
        if chunk_section:
            chunk_body = str(chunk_section.get("body_markdown") or "").strip()
            if chunk_body and not _looks_like_placeholder_markdown(chunk_body):
                merged_section["body_markdown"] = chunk_body
            chunk_title = str(chunk_section.get("title") or "").strip()
            if chunk_title and not _looks_like_placeholder_text(chunk_title):
                merged_section["title"] = chunk_title[:80]
            chunk_summary = str(chunk_section.get("summary") or "").strip()
            if chunk_summary and not _looks_like_placeholder_text(chunk_summary):
                merged_section["summary"] = chunk_summary[:240]
        merged.append(merged_section)
    return merged[:16]


def _build_day_cards(seed: dict[str, Any]) -> list[dict[str, Any]]:
    semantic_layer = seed.get("semantic_layer") or {}
    factor_records = [record for record in (seed.get("factor_records") or []) if getattr(record, "id", None)]
    indexed_records = {str(record.id): record for record in factor_records if getattr(record, "id", None)}
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    start, _end = _week_window(seed)
    cards: list[dict[str, Any]] = []
    for index in range(7):
        source = (seed.get("days") or [None] * 7)[index] if index < len(seed.get("days") or []) else None
        current_date = start + timedelta(days=index)
        normalized = _normalize_week_day_payload(source or {"date": current_date.isoformat(), "weekday": current_date.strftime("%A"), "traffic_light": "YELLOW"})
        best_for, avoid = _build_day_actions(normalized, focus_key)
        headline = _build_day_headline(normalized, focus_key)[:100]
        lead = ". ".join(part for part in [headline, f"Опора дня — {best_for[0]}" if best_for else None] if part)[:180] or None
        practical = best_for[:2] if best_for else avoid[:1]
        factor_ids = [record.id for record in factor_records[index:index + 2] if getattr(record, "id", None)][:4]
        ordered_records = [indexed_records[factor_id] for factor_id in factor_ids if factor_id in indexed_records]
        detail_supporting_factors = _build_supporting_factor_entries(ordered_records, factor_ids, limit=3)
        why_title = "Почему день так звучит" if detail_supporting_factors else None
        why_parts = [lead]
        if best_for:
            why_parts.append(f"Лучше ставить на {best_for[0].lower()}.")
        if avoid:
            why_parts.append(f"Снижайте риск через режим без {avoid[0].lower()}.")
        why_text = " ".join(part.strip() for part in why_parts if part and str(part).strip())[:280] or None
        supporting_factors = [
            {
                "label": "Лучше направить в",
                "explanation_human": best_for[0] if best_for else "Спокойный ритм и проверяемые шаги дадут лучший результат.",
                "value": f"{_score_day_card(normalized)}/100",
            },
            {
                "label": "Стоит снизить",
                "explanation_human": avoid[0] if avoid else "Избегайте резких решений без подтверждения.",
                "value": str(normalized.get("traffic_light") or "YELLOW").lower(),
            },
        ]
        cards.append(
            {
                "id": f"week-day-{current_date.isoformat()}",
                "date": _safe_date(normalized.get("date"), default=current_date).isoformat(),
                "weekday": _weekday_code(normalized, current_date),
                "mode": str(normalized.get("traffic_light") or "YELLOW").lower(),
                "score": _score_day_card(normalized),
                "headline": headline,
                "lead": lead,
                "practical": practical[:3],
                "supporting_factors": supporting_factors[:3],
                "details": {
                    "why_text": why_text,
                    "why_title": why_title,
                    "supporting_factors": detail_supporting_factors,
                },
                "factor_ids": factor_ids,
                "best_for": best_for[:4],
                "avoid": avoid[:4],
                "peak_window_label": None if (normalized.get("moon") or {}).get("void_of_course") else "до 14:00",
            }
        )
    return cards


def _resolve_week_type(summary: dict[str, Any], day_cards: list[dict[str, Any]], semantic_layer: dict[str, Any]) -> str:
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    green_days = sum(1 for day in day_cards if day.get("mode") == "green")
    red_days = sum(1 for day in day_cards if day.get("mode") == "red")
    traffic = str(summary.get("traffic_light") or "YELLOW").upper()
    if focus_key == "rest":
        return "recovery"
    if red_days >= 2 or traffic == "RED":
        return "caution" if green_days < 2 else "transition"
    if green_days >= 4 and focus_key in {"launch", "money_admin"}:
        return "push"
    if focus_key == "launch":
        return "deep_work"
    if green_days and red_days:
        return "transition"
    return "balance"


def _build_summary(seed: dict[str, Any], day_cards: list[dict[str, Any]]) -> dict[str, Any]:
    summary = seed.get("summary") or {}
    semantic_layer = seed.get("semantic_layer") or {}
    focus_key = str(semantic_layer.get("focus_key") or "money_admin")
    traffic = str(summary.get("traffic_light") or "YELLOW").upper()
    green_days = sum(1 for item in day_cards if item.get("mode") == "green")
    red_days = sum(1 for item in day_cards if item.get("mode") == "red")

    headline = {
        "GREEN": "Неделя дает ход тем шагам, которые уже готовы к реальному движению.",
        "YELLOW": "Неделя просит точного ритма, коротких проверок и ясных договоренностей.",
        "RED": "Неделя требует взрослой сборки, буфера и отказа от лишнего фронта.",
    }.get(traffic, "Неделя просит точного ритма, коротких проверок и ясных договоренностей.")
    if semantic_layer.get("headline"):
        headline = str(semantic_layer.get("headline")).strip()

    subhead = " ".join(
        part.strip()
        for part in [
            str(semantic_layer.get("pacing") or "").strip(),
            str(semantic_layer.get("negotiation") or "").strip(),
        ]
        if part and str(part).strip()
    )
    if not subhead:
        subhead = "Лучший результат даст одна опорная линия недели и отказ от лишней суеты."

    if red_days >= 2:
        subhead += " Красные дни лучше вести без силового нажима."
    elif green_days >= 3:
        subhead += " Сильные дни стоит использовать для видимых шагов и фиксаций."

    return {
        "headline": headline[:160],
        "subhead": subhead[:300],
        "week_type": _resolve_week_type(summary, day_cards, semantic_layer),
        "theme": FOCUS_THEME_MAP.get(focus_key, "Темп, приоритеты и ясные шаги")[:80],
    }


def _build_premium(user: Any | None, *, report_status: str) -> dict[str, Any] | None:
    if user is None:
        return None
    now = datetime.now(timezone.utc)
    active_until = getattr(user, "subscription_active_until", None)
    if isinstance(active_until, datetime) and active_until.tzinfo is None:
        active_until = active_until.replace(tzinfo=timezone.utc)
    active = bool(active_until and active_until > now)
    days_left = max((active_until - now).days, 0) if active and active_until else None
    return {
        "subscription_active": active,
        "subscription_active_until": active_until.date().isoformat() if active_until else None,
        "days_left": days_left if active else 0 if active_until else None,
        "show_upgrade_cta": not active,
        "show_resume_banner": report_status == "in_progress",
    }


def _build_cta(report: Any) -> dict[str, Any]:
    report_id = str(getattr(report, "id", "") or "").strip()
    return {
        "primary": {
            "type": "open_report",
            "label": "Открыть разбор",
            "href": f"/read/{report_id}",
        },
        "secondary": {
            "type": "open_history",
            "label": "К истории",
            "href": "/reports",
        },
    }


def _report_ref(report: Any) -> dict[str, Any]:
    generated_at = getattr(report, "updated_at", None) or getattr(report, "created_at", None)
    generated = generated_at.isoformat() if isinstance(generated_at, datetime) else None
    return {
        "report_id": str(getattr(report, "id", "")),
        "report_type": "week_forecast",
        "source_status": str(getattr(report, "status", "") or "unknown"),
        "generated_at": generated,
    }


def _build_seed(context: dict[str, Any]) -> dict[str, Any]:
    if context.get("week_brief_seed"):
        return copy.deepcopy(context["week_brief_seed"])
    return _build_week_brief_seed_bundle(context)


def _build_week_brief_fallback(
    *,
    report: Any,
    payload: Any | None,
    context: dict[str, Any],
    chunks: Iterable[Any],
    user: Any | None,
) -> dict[str, Any]:
    seed = _build_seed(context) if context else {}
    start, end = _week_window(seed, report=report)
    deep_sections, degraded = _build_deep_sections(chunks)
    fallback_day_cards = _build_day_cards(
        {
            **seed,
            "days": [],
            "summary": seed.get("summary") or {"traffic_light": "YELLOW", "avg_tension": 0.6},
            "semantic_layer": seed.get("semantic_layer")
            or {
                "focus_key": "money_admin",
                "headline": "Неделя лучше идет через спокойный ритм и одну опорную линию.",
                "pacing": "Лучше не распыляться и заранее оставлять буфер на перепроверку.",
                "negotiation": "Фиксируй ключевые договоренности сразу после разговора.",
                "rest": "Не геройствуй там, где можно замедлиться и проверить вводные.",
            },
        }
    )
    factors = [
        {
            "id": "fallback_background",
            "label": "Безопасный fallback недели",
            "impact": "medium",
            "category": "background",
            "explanation_human": "Даже без полного набора сигналов неделя лучше всего собирается через один главный трек и короткие проверки.",
            "explanation_astro": "Часть расчетов недоступна, поэтому brief собран из минимального устойчивого слоя.",
            "source_models": [SignalSource.mixed.value],
            "weight": 0.45,
        }
    ]
    explainability = {
        "confidence": 0.4,
        "birth_time_used": bool(payload and getattr(payload, "birth_time_known", True)),
        "factor_count": 1,
        "timing_precision": "approximate",
        "top_signal_source": SignalSource.mixed.value,
        "explanation_depth": "minimal",
    }
    return {
        "version": "week_brief_v1",
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "personalization_level": "personalized_v2" if payload else "anonymous",
        "fallback_mode": True,
        "status": _map_report_status(getattr(report, "status", None)),
        "summary": {
            "headline": "Неделя требует спокойного ритма, ясных приоритетов и коротких подтверждений.",
            "subhead": "Полный слой прогноза сейчас частично недоступен, поэтому держись одной рабочей линии и не разгоняй лишний фронт.",
            "week_type": "transition",
            "theme": "Приоритеты, ритм и проверка деталей",
        },
        "day_cards": fallback_day_cards,
        "domains": [
            {
                "key": key,
                "title": DOMAIN_TITLES[key],
                "status": "yellow",
                "value": 55,
                "headline": DOMAIN_HEADLINES[key][:100],
                "advice": "Иди по шагам и не принимай промежуточный результат за финальный.",
            }
            for key in ("work_money", "relationships", "energy", "focus")
        ],
        "best_uses": _format_action_items(list(GENERIC_BEST_USES), prefix="best"),
        "risks": _format_action_items(list(GENERIC_RISKS), prefix="risk"),
        "major_factors": factors,
        "deep_sections": deep_sections,
        "explainability": explainability,
        "premium": _build_premium(user, report_status=_map_report_status(getattr(report, "status", None))),
        "cta": _build_cta(report),
        "report_ref": _report_ref(report),
    }


def build_week_brief_payload(
    *,
    report: Any,
    payload: Any | None,
    context: dict[str, Any] | None,
    chunks: Iterable[Any],
    user: Any | None = None,
    llm_model: str | None = None,
) -> dict[str, Any]:
    safe_context = copy.deepcopy(context or {})
    try:
        seed = _build_seed(safe_context)
        summary = seed.get("summary") or _normalize_week_summary(
            safe_context.get("week_forecast_data") or {},
            [_normalize_week_day_payload(day) for day in (safe_context.get("week_forecast_data") or {}).get("days", [])[:7]],
        )
        seed["summary"] = summary
        day_cards = _build_day_cards(seed)
        factor_records = _build_factor_seeds(seed)
        section_seeds = _build_week_section_seeds(seed, factor_records)
        major_factors, weighted = _weighted_factor_payloads(factor_records)
        seed_deep_sections = _build_seed_deep_sections(section_seeds, factor_records)
        chunk_deep_sections, chunk_parse_degraded = _build_deep_sections(chunks)
        deep_sections = _merge_seed_with_chunk_sections(seed_deep_sections, chunk_deep_sections)
        best_day = max(day_cards, key=lambda item: int(item.get("score", 0)), default=None)
        worst_day = min(day_cards, key=lambda item: int(item.get("score", 0)), default=None)
        fallback_mode = bool(not seed.get("days") or not deep_sections)
        explainability = _build_explainability(
            seed,
            weighted,
            len(factor_records),
            birth_time_used=bool(payload and getattr(payload, "birth_time_known", True)),
            fallback_mode=fallback_mode,
            chunk_parse_degraded=chunk_parse_degraded,
        )
        week_start, week_end = _week_window(seed, report=report)
        domains = _enrich_domains(_build_domain_scores(seed, factor_records, day_cards), factor_records)
        best_uses = _enrich_action_items(_build_best_uses(seed.get("semantic_layer") or {}, best_day), factor_records, kind="best")
        risks = _enrich_action_items(_build_risks(seed.get("semantic_layer") or {}, worst_day), factor_records, kind="risk")
        result = {
            "version": "week_brief_v1",
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "personalization_level": "personalized_v2" if payload else "anonymous",
            "fallback_mode": fallback_mode,
            "status": _map_report_status(getattr(report, "status", None)),
            "summary": _build_summary(seed, day_cards),
            "day_cards": day_cards,
            "domains": domains,
            "best_uses": best_uses,
            "risks": risks,
            "major_factors": major_factors,
            "deep_sections": deep_sections,
            "explainability": explainability,
            "premium": _build_premium(user, report_status=_map_report_status(getattr(report, "status", None))),
            "cta": _build_cta(report),
            "report_ref": _report_ref(report),
        }
        validated = validate_week_brief_payload(result)
        if validated["fallback_mode"]:
            _log_week_brief(
                "info",
                "week_brief_fallback_triggered",
                report=report,
                factor_count=validated["explainability"]["factor_count"],
                week_brief_llm_model=llm_model or "deterministic",
                week_brief_fallback_mode=True,
                chunk_parse_degraded=chunk_parse_degraded,
                week_brief_confidence_bucket=_confidence_bucket(validated["explainability"]["confidence"]),
            )
        _log_week_brief(
            "info",
            "week_brief_built",
            report=report,
            factor_count=validated["explainability"]["factor_count"],
            week_brief_llm_model=llm_model or "deterministic",
            week_brief_fallback_mode=validated["fallback_mode"],
            chunk_parse_degraded=chunk_parse_degraded,
            week_brief_confidence_bucket=_confidence_bucket(validated["explainability"]["confidence"]),
        )
        return validated
    except Exception as exc:
        _log_week_brief(
            "warning",
            "week_brief_validation_failed",
            report=report,
            error=str(exc),
            week_brief_llm_model=llm_model or "deterministic",
        )
        fallback = validate_week_brief_payload(
            _build_week_brief_fallback(
                report=report,
                payload=payload,
                context=safe_context,
                chunks=chunks,
                user=user,
            )
        )
        _log_week_brief(
            "info",
            "week_brief_fallback_triggered",
            report=report,
            factor_count=fallback["explainability"]["factor_count"],
            week_brief_llm_model=llm_model or "deterministic",
            week_brief_fallback_mode=True,
            chunk_parse_degraded=True,
            week_brief_confidence_bucket=_confidence_bucket(fallback["explainability"]["confidence"]),
        )
        _log_week_brief(
            "info",
            "week_brief_built",
            report=report,
            factor_count=fallback["explainability"]["factor_count"],
            week_brief_llm_model=llm_model or "deterministic",
            week_brief_fallback_mode=True,
            chunk_parse_degraded=True,
            week_brief_confidence_bucket=_confidence_bucket(fallback["explainability"]["confidence"]),
        )
        return fallback


def build_week_brief_envelope(
    *,
    report: Any,
    week_brief: dict[str, Any] | None = None,
    retry_after_seconds: int = 3,
) -> dict[str, Any]:
    status = _map_report_status(getattr(report, "status", None))
    payload = {
        "status": status,
        "data": week_brief if status == "ready" else None,
        "message": None,
        "retry_after_seconds": retry_after_seconds if status == "in_progress" else None,
    }
    if status == "in_progress":
        payload["message"] = "Week brief is still building."
    if status == "error":
        payload["message"] = str(getattr(report, "error_message", "") or "Week brief could not be fully assembled.")
    return validate_week_brief_envelope_payload(payload)


__all__ = [
    "build_week_brief_envelope",
    "build_week_brief_payload",
]
