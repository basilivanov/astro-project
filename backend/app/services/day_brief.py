"""DayBrief aggregation helpers for /api/day/brief."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable


DOMAIN_KEYS = ("energy", "work", "relationships", "focus")
CATEGORY_WEIGHTS = {
    "fast_transits": 0.35,
    "lunar_windows": 0.25,
    "slow_background": 0.20,
    "natal_sensitivity": 0.15,
    "rare_boosters": 0.05,
}
BASELINE_SCORE = 55
BENEFIC_TRANSITS = {"Venus", "Jupiter", "Sun"}
CHALLENGING_TRANSITS = {"Mars", "Saturn", "Pluto", "Uranus", "Neptune"}
NATAL_DOMAIN_MAP = {
    "Sun": "work",
    "MC": "work",
    "Mercury": "focus",
    "Mars": "energy",
    "ASC": "energy",
    "Moon": "relationships",
    "Venus": "relationships",
}
FOCUS_KEY_DOMAIN = {
    "money_admin": "work",
    "relationship": "relationships",
    "rest": "energy",
    "launch": "focus",
}
HOUSE_DOMAIN_MAP = {
    1: "energy",
    2: "work",
    3: "focus",
    6: "work",
    7: "relationships",
    10: "work",
    11: "relationships",
    12: "energy",
}
BEST_USE_TEMPLATES = {
    "work": "Собрать рабочий фронт короткими циклами и подтвердить условия.",
    "relationships": "Говорить напрямую и согревать контакт без длинных намеков.",
    "energy": "Дать телу и графику понятный ритм без хаотичных рывков.",
    "focus": "Закрыть глубокую задачу без отвлечений и шороха чатов.",
}
RISK_TEMPLATES = {
    "work": "Срывы рождаются из поспешных обещаний и спора за дедлайн.",
    "relationships": "Лишний нажим ломает мягкий контакт и вызывает обиды.",
    "energy": "Перегрев и бессонные окна быстро обнуляют запас сил.",
    "focus": "Шум и параллельные чаты украдут концентрацию.",
}
WINDOW_FOCUS = {
    "work": "рабочие договоренности",
    "relationships": "личные разговоры",
    "energy": "поддержку тела и режима",
    "focus": "глубокий фокус",
}
DAY_TYPE_THRESHOLDS = (
    (75, "push"),
    (65, "balance"),
    (57, "deep_focus"),
    (50, "caution"),
)


@dataclass
class FactorRecord:
    id: str
    label: str
    explanation: str
    domain: str
    signal: float
    category: str


def _empty_scores() -> dict[str, float]:
    return {key: 0.0 for key in DOMAIN_KEYS}


def _domain_for_natal(point: str) -> str:
    return NATAL_DOMAIN_MAP.get(point, "focus")


def _effect_from_aspect(aspect_type: str, transit: str) -> float:
    aspect_type = (aspect_type or "").lower()
    if "тригон" in aspect_type or "секстиль" in aspect_type:
        return 1.0
    if "квадрат" in aspect_type or "оппоз" in aspect_type:
        return -1.0
    if "соедин" in aspect_type:
        if transit in BENEFIC_TRANSITS:
            return 0.8
        if transit in CHALLENGING_TRANSITS:
            return -0.8
        return 0.3
    return 0.2


def _normalize_scores(values: dict[str, float], *, cap: float) -> dict[str, float]:
    normalized = {}
    for key, value in values.items():
        normalized[key] = max(-1.0, min(1.0, value / cap))
    return normalized


def _light_to_signal(light: Any) -> float:
    normalized = str(light or "").lower()
    if normalized == "green":
        return 0.8
    if normalized == "yellow":
        return 0.1
    if normalized == "red":
        return -0.8
    return 0.0


def _parse_local_dt(facts: dict[str, Any]) -> datetime:
    raw = facts.get("local_dt") or ""
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return datetime.now(timezone.utc)


def _score_fast_transits(facts: dict[str, Any]) -> tuple[dict[str, float], list[FactorRecord]]:
    hits = [hit for hit in (facts.get("fast_hits") or []) if isinstance(hit, dict)]
    if not hits:
        return _empty_scores(), []
    contributions = _empty_scores()
    factors: list[FactorRecord] = []
    for idx, hit in enumerate(hits[:5]):
        domain = _domain_for_natal(str(hit.get("natal")))
        transit = str(hit.get("transit"))
        effect = _effect_from_aspect(str(hit.get("type")), transit)
        orb = abs(float(hit.get("orb", 1.0)))
        intensity = 1.0 - min(orb / 2.0, 0.85)
        signal = effect * intensity
        contributions[domain] += signal
        label = hit.get("summary") or f"{transit} → {hit.get('natal')}"
        factors.append(
            FactorRecord(
                id=f"fast_transit_{idx}",
                label=label,
                explanation=f"Быстрый транзит {transit} к {hit.get('natal')} ощущается сегодня сильнее обычного.",
                domain=domain,
                signal=signal,
                category="fast_transits",
            )
        )
    return _normalize_scores(contributions, cap=3.5), factors


def _phase_bias(phase: str) -> dict[str, float]:
    lookup = {
        "новолуние": {"focus": 0.9, "work": 0.7, "energy": 0.3},
        "растущ": {"work": 0.8, "focus": 0.6, "relationships": 0.2},
        "полнолуние": {"relationships": 0.6, "energy": -0.4, "work": -0.3},
        "убывающ": {"focus": 0.5, "relationships": 0.4, "energy": -0.2},
    }
    lowered = (phase or "").lower()
    for key, mapping in lookup.items():
        if key in lowered:
            return mapping
    return {"focus": 0.3, "relationships": 0.2}


def _build_windows(
    now_local: datetime,
    dominant_domain: str,
    phase: str,
    void_flag: bool,
    moon_sign: str,
) -> list[dict[str, Any]]:
    base = now_local.replace(hour=7, minute=30, second=0, microsecond=0)
    slots = [
        ("Утро", 7, 11),
        ("День", 11, 16),
        ("Вечер", 16, 20),
    ]
    windows = []
    for label, start_hour, end_hour in slots:
        start = base.replace(hour=start_hour)
        end = base.replace(hour=end_hour)
        wtype = "soft"
        if label == "Утро":
            wtype = "best" if "раст" in phase.lower() or "новолу" in phase.lower() else "soft"
        if label == "День" and void_flag:
            wtype = "caution"
        if label == "Вечер":
            wtype = "caution" if void_flag or "полнолу" in phase.lower() else "soft"
        focus = WINDOW_FOCUS.get(dominant_domain, "главные задачи")
        reason = f"Луна в {moon_sign or 'текущем знаке'} поддерживает {focus}."
        if wtype == "caution":
            reason = "Поздняя Луна просит не форсировать и держать буфер."
        windows.append(
            {
                "label": label,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "type": wtype,
                "focus": focus,
                "explanation": reason,
            }
        )
    return windows


def _score_lunar_dynamics(facts: dict[str, Any]) -> tuple[dict[str, float], list[dict[str, Any]], list[FactorRecord]]:
    contributions = _empty_scores()
    factors: list[FactorRecord] = []
    phase = str(facts.get("moon_phase") or "")
    for domain, value in _phase_bias(phase).items():
        contributions[domain] += value
        factors.append(
            FactorRecord(
                id=f"lunar_phase_{domain}",
                label=f"{phase or 'Луна'}",
                explanation=f"Фаза Луны смещает фокус к сфере «{WINDOW_FOCUS.get(domain, domain)}».",
                domain=domain,
                signal=value,
                category="lunar_windows",
            )
        )

    traffic = facts.get("traffic_lights") or {}
    contributions["energy"] += _light_to_signal(traffic.get("health")) * 0.6
    contributions["work"] += _light_to_signal(traffic.get("money")) * 0.5
    contributions["relationships"] += _light_to_signal(traffic.get("love")) * 0.5

    day_context = (facts.get("week_data") or {}).get("days") or []
    moon_context = day_context[0].get("moon") if day_context and isinstance(day_context[0], dict) else {}
    void_flag = bool((moon_context or {}).get("void_of_course"))
    if void_flag:
        contributions["work"] -= 0.9
        contributions["focus"] -= 0.7
        factors.append(
            FactorRecord(
                id="lunar_void",
                label="Void of course",
                explanation="Поздняя Луна без курса: оставь буфер и не дави на сроки.",
                domain="focus",
                signal=-0.9,
                category="lunar_windows",
            )
        )

    dominant_domain = max(contributions, key=lambda key: contributions[key])
    windows = _build_windows(
        _parse_local_dt(facts),
        dominant_domain,
        phase,
        void_flag,
        (moon_context or {}).get("sign") or facts.get("moon_sign") or "",
    )
    return _normalize_scores(contributions, cap=3.0), windows, factors


def _score_slow_background(facts: dict[str, Any]) -> tuple[dict[str, float], list[FactorRecord]]:
    contributions = _empty_scores()
    factors: list[FactorRecord] = []
    month_data = facts.get("month_data") or {}
    status = str(month_data.get("status") or "YELLOW").upper()
    if status == "GREEN":
        delta = 0.9
    elif status == "RED":
        delta = -0.8
    else:
        delta = 0.2
    contributions["work"] += delta
    contributions["focus"] += delta * 0.6
    factors.append(
        FactorRecord(
            id="month_status",
            label=f"Месячный статус {status}",
            explanation="Медленный фон месяца окрашивает рабочий сценарий дня.",
            domain="work",
            signal=delta,
            category="slow_background",
        )
    )

    year_data = facts.get("year_data") or {}
    profection = (year_data.get("profection") or {}).get("house")
    profection_domain = HOUSE_DOMAIN_MAP.get(profection)
    if profection_domain:
        contributions[profection_domain] += 0.6
        factors.append(
            FactorRecord(
                id="profection_house",
                label=f"Активен дом {profection}",
                explanation="Годовой управитель периода подчёркивает эту сферу недели.",
                domain=profection_domain,
                signal=0.6,
                category="slow_background",
            )
        )

    months = year_data.get("months") or []
    try:
        now_month = _parse_local_dt(facts).month
    except Exception:
        now_month = None
    if now_month:
        month_entry = next((m for m in months if m.get("month") == now_month), None)
        if month_entry:
            status = str(month_entry.get("status") or "YELLOW").upper()
            delta = 0.7 if status == "GREEN" else (-0.7 if status == "RED" else 0.1)
            contributions["relationships"] += delta * 0.5
            contributions["energy"] += delta * 0.3
            factors.append(
                FactorRecord(
                    id="month_anchor",
                    label=f"Фаза месяца {status}",
                    explanation="Сценарий месяца даёт долгий фон для эмоциональной реакции.",
                    domain="relationships",
                    signal=delta,
                    category="slow_background",
                )
            )

    return _normalize_scores(contributions, cap=3.0), factors


def _score_natal_sensitivity(facts: dict[str, Any]) -> tuple[dict[str, float], list[FactorRecord]]:
    contributions = _empty_scores()
    factors: list[FactorRecord] = []
    semantic = facts.get("semantic_layer") or {}
    focus_key = semantic.get("focus_key")
    domain = FOCUS_KEY_DOMAIN.get(focus_key, "focus")
    signal = 0.8
    contributions[domain] += signal
    factors.append(
        FactorRecord(
            id="focus_key",
            label=f"Активный фокус: {focus_key or 'general'}",
            explanation="Натальная чувствительность к этой сфере повышена, поэтому сигнал громче.",
            domain=domain,
            signal=signal,
            category="natal_sensitivity",
        )
    )

    fast_hits = facts.get("fast_hits") or []
    natal_counts = _empty_scores()
    for hit in fast_hits:
        domain = _domain_for_natal(str(hit.get("natal")))
        natal_counts[domain] += 1
    dominant = max(natal_counts, key=lambda key: natal_counts[key])
    if natal_counts[dominant] > 0:
        contributions[dominant] += 0.5
        factors.append(
            FactorRecord(
                id="natal_activation",
                label=f"Активирована точка {dominant}",
                explanation="Несколько транзитов попадают в одну и ту же область натала.",
                domain=dominant,
                signal=0.5,
                category="natal_sensitivity",
            )
        )

    return _normalize_scores(contributions, cap=2.0), factors


def _score_rare_boosters(facts: dict[str, Any]) -> tuple[dict[str, float], list[FactorRecord]]:
    contributions = _empty_scores()
    factors: list[FactorRecord] = []
    hits = facts.get("fast_hits") or []
    for idx, hit in enumerate(hits):
        transit = str(hit.get("transit"))
        aspect = str(hit.get("type"))
        if transit in {"Jupiter", "Sun"} and ("Тригон" in aspect or "Секстиль" in aspect):
            domain = _domain_for_natal(str(hit.get("natal")))
            signal = 1.0
            contributions[domain] += signal
            factors.append(
                FactorRecord(
                    id=f"rare_booster_{idx}",
                    label=f"{transit} усиливает {hit.get('natal')}",
                    explanation="Редкий усилитель подтверждён: можно позволить себе смелый шаг в этой сфере.",
                    domain=domain,
                    signal=signal,
                    category="rare_boosters",
                )
            )
    return _normalize_scores(contributions, cap=1.5), factors


def _decorate_factors(records: Iterable[FactorRecord]) -> list[dict[str, Any]]:
    decorated = []
    for idx, record in enumerate(records):
        weight = CATEGORY_WEIGHTS.get(record.category, 0.0)
        decorated.append(
            {
                "id": record.id or f"factor_{record.category}_{idx}",
                "label": record.label,
                "explanation": record.explanation,
                "domain": record.domain,
                "impact": round(abs(record.signal) * weight, 3),
                "polarity": "positive" if record.signal >= 0 else "negative",
                "source": record.category,
            }
        )
    return decorated


def _resolve_day_type(scores: dict[str, int]) -> str:
    avg = sum(scores.values()) / len(scores)
    for threshold, label in DAY_TYPE_THRESHOLDS:
        if avg >= threshold:
            return label
    return "recovery"


def _build_best_and_risks(scores: dict[str, int], windows: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    deltas = {key: scores[key] - BASELINE_SCORE for key in DOMAIN_KEYS}
    positives = sorted([(k, v) for k, v in deltas.items() if v > 3], key=lambda item: item[1], reverse=True)
    negatives = sorted([(k, v) for k, v in deltas.items() if v < -3], key=lambda item: item[1])
    best = positives[:2] or sorted(deltas.items(), key=lambda item: item[1], reverse=True)[:1]
    risks = negatives[:2] or sorted(deltas.items(), key=lambda item: item[1])[:1]

    window_lookup = {window["type"]: window for window in windows}
    best_window = window_lookup.get("best") or (windows[0] if windows else None)
    caution_window = window_lookup.get("caution") or (windows[-1] if windows else None)

    best_uses = []
    for domain, _ in best:
        base = BEST_USE_TEMPLATES.get(domain, "Сделать главное и не распыляться.")
        if best_window:
            best_uses.append(
                f"{base} Лучше всего в окне {best_window['label']} ({best_window['focus']})."
            )
        else:
            best_uses.append(base)

    risk_lines = []
    for domain, _ in risks:
        base = RISK_TEMPLATES.get(domain, "Главный риск — поспешить и потерять ясность.")
        if caution_window:
            risk_lines.append(
                f"{base} В окне {caution_window['label']} держи буфер и не жги сроки."
            )
        else:
            risk_lines.append(base)

    return best_uses, risk_lines


def _build_summary(facts: dict[str, Any], scores: dict[str, int], best_uses: list[str], risks: list[str]) -> dict[str, Any]:
    semantic = facts.get("semantic_layer") or {}
    headline = semantic.get("headline") or "День просит собранности и одну главную ставку."
    worst = min(scores, key=scores.get)
    best = max(scores, key=scores.get)
    subhead = (
        f"Главный фокус — {WINDOW_FOCUS.get(best, 'главные задачи')}. "
        f"Риск: {WINDOW_FOCUS.get(worst, 'лишний шум')} требует буфера."
    )
    day_type = _resolve_day_type(scores)
    return {
        "headline": headline,
        "subhead": subhead,
        "day_type": day_type,
    }


def _build_explainability(facts: dict[str, Any], factors: list[dict[str, Any]], user: Any | None) -> dict[str, Any]:
    personalization_level = facts.get("personalization_level", "anonymous")
    meta = facts.get("meta") or {}
    base = 0.45
    if personalization_level.startswith("personalized"):
        base += 0.2
    if facts.get("fast_hits"):
        base += 0.15
    has_precise_time = bool(user and getattr(user, "birth_time", None) and getattr(user, "birth_time_known", True))
    if has_precise_time:
        base += 0.05
    if len(factors) >= 4:
        base += 0.05
    if meta.get("fallback_mode"):
        base -= 0.15
    confidence = round(max(0.35, min(0.95, base)), 2)
    return {
        "confidence": confidence,
        "uses_precise_birth_time": has_precise_time,
        "factors_considered": len(factors),
        "personalization_level": personalization_level,
    }


def build_day_brief_payload(facts: dict[str, Any], *, user: Any | None = None) -> dict[str, Any]:
    fast_scores, fast_factors = _score_fast_transits(facts)
    lunar_scores, windows, lunar_factors = _score_lunar_dynamics(facts)
    slow_scores, slow_factors = _score_slow_background(facts)
    natal_scores, natal_factors = _score_natal_sensitivity(facts)
    rare_scores, rare_factors = _score_rare_boosters(facts)

    category_signals = {
        "fast_transits": fast_scores,
        "lunar_windows": lunar_scores,
        "slow_background": slow_scores,
        "natal_sensitivity": natal_scores,
        "rare_boosters": rare_scores,
    }
    scores = {key: float(BASELINE_SCORE) for key in DOMAIN_KEYS}
    for category, signals in category_signals.items():
        weight = CATEGORY_WEIGHTS[category]
        for domain in DOMAIN_KEYS:
            scores[domain] += weight * 100 * signals.get(domain, 0.0)
    int_scores = {domain: int(max(0, min(100, round(value)))) for domain, value in scores.items()}

    factors = _decorate_factors(
        fast_factors + lunar_factors + slow_factors + natal_factors + rare_factors
    )
    factors.sort(key=lambda item: item["impact"], reverse=True)

    best_uses, risks = _build_best_and_risks(int_scores, windows)
    summary = _build_summary(facts, int_scores, best_uses, risks)
    explainability = _build_explainability(facts, factors, user)

    response = {
        "summary": summary,
        "scores": int_scores,
        "windows": windows,
        "best_uses": best_uses,
        "risks": risks,
        "personalized_factors": factors[:8],
        "explainability": explainability,
    }
    return response


def build_day_brief_fallback(now_utc: datetime) -> dict[str, Any]:
    now_local = now_utc.astimezone(timezone.utc)
    fallback_facts = {
        "local_dt": now_local.isoformat(),
        "moon_phase": "Растущая",
        "moon_sign": "Луна",
        "traffic_lights": {"health": "yellow", "money": "yellow", "love": "yellow"},
        "week_data": {"days": [{"moon": {"sign": "Луна", "phase": "Растущая", "void_of_course": False}}]},
        "semantic_layer": {
            "headline": "День про аккуратный ход и подтверждение главного решения.",
            "focus_key": "money_admin",
        },
        "personalization_level": "anonymous",
        "meta": {"fallback_mode": True},
        "fast_hits": [],
    }
    return build_day_brief_payload(fallback_facts, user=None)
