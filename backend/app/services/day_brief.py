"""DayBrief assembly for the daily feed surface."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Iterable

from pydantic import ValidationError

from ..logging_utils import get_correlation_ids, log_grace_event
from .aggregation_weights import DAY_BRIEF_WEIGHT_TABLE, apply_weighted_factors
from .day_brief_types import ImpactLevel, SignalSource
from .day_brief_validators import serialize_day_brief, validate_day_brief_payload
from .forecast_semantics import build_daily_forecast_semantic_layer
from .personal_susceptibility import attach_susceptibility, build_susceptibility_profile, calibration_entrypoints
from .forecast_factor_pipeline import build_normalized_factors, build_semantic_layer_from_factors, preprocess_factors_for_ranking, select_explainability_factors


MODULE_NAME = "M-DAY-BRIEF-SERVICE"
DAY_BRIEF_PROMPT_VERSION = "day_brief_prompt_v2"
DOMAIN_KEYS = ("energy", "money", "love", "focus")
DOMAIN_ALIASES = {
    "energy": {"energy", "health", "tonus"},
    "money": {"money", "work_money", "work", "career"},
    "love": {"love", "relationship", "relationships"},
    "focus": {"focus", "launch", "strategy"},
}
CATEGORY_WEIGHTS = DAY_BRIEF_WEIGHT_TABLE
BASELINE_SCORE = 55
BENEFIC_TRANSITS = {"Venus", "Jupiter", "Sun"}
CHALLENGING_TRANSITS = {"Mars", "Saturn", "Pluto", "Uranus", "Neptune"}
NATAL_DOMAIN_MAP = {
    "Sun": "money",
    "MC": "money",
    "Mercury": "focus",
    "Mars": "energy",
    "ASC": "energy",
    "Moon": "love",
    "Venus": "love",
}
FOCUS_KEY_DOMAIN = {
    "money_admin": "money",
    "relationship": "love",
    "rest": "energy",
    "launch": "focus",
}
HOUSE_DOMAIN_MAP = {
    1: "energy",
    2: "money",
    3: "focus",
    6: "money",
    7: "love",
    10: "money",
    11: "love",
    12: "energy",
}
BEST_USE_TEMPLATES = {
    "money": "Собрать рабочий или денежный вопрос коротким и чистым циклом.",
    "love": "Сказать главное прямо и без давления, сохранив мягкий тон.",
    "energy": "Выстроить день так, чтобы ритм поддерживал тело, а не спорил с ним.",
    "focus": "Закрыть одну глубокую задачу и не распыляться на шум.",
}
RISK_TEMPLATES = {
    "money": "Поспешные обещания и спор за условия быстро создают лишнюю цену ошибки.",
    "love": "Резкий тон ломает контакт быстрее, чем сама тема разговора.",
    "energy": "Перегрев и попытка тащить всё сразу быстро съедают ресурс.",
    "focus": "Шум, параллельные чаты и поспешные ответы крадут главный ход дня.",
}
WINDOW_FOCUS = {
    "money": "рабочие договоренности",
    "love": "важные разговоры",
    "energy": "режим и телесный ритм",
    "focus": "глубокий фокус",
}
SCORE_TITLES = {
    "energy": "Тонус",
    "money": "Работа и деньги",
    "love": "Чувства",
    "focus": "Фокус",
}
SUPPORTING_FACTOR_DOMAIN_LABELS = {
    "energy": "Ресурс дня",
    "money": "Рабочий контекст",
    "love": "Контакт и тон",
    "focus": "Фокус дня",
}
SUPPORTING_FACTOR_BLOCKLIST_PREFIXES = (
    "traffic:",
    "semantic:",
)
SUPPORTING_FACTOR_BLOCKLIST_LABELS = {
    "Рабочий контекст",
    "Контакт и тон",
    "Ресурс дня",
    "Фокус дня",
}
DAY_TYPE_THRESHOLDS = (
    (75, "push"),
    (65, "balance"),
    (57, "deep_focus"),
    (50, "caution"),
)
WINDOW_TIMEFRAMES = {
    "Утро": "morning",
    "День": "day",
    "Вечер": "evening",
}
FACTOR_CATEGORY_MAP = {
    "fast_transits": "transit_natal",
    "lunar_windows": "lunar_timing",
    "slow_background": "background",
    "natal_sensitivity": "natal_sensitivity",
    "rare_boosters": "transit_natal",
}
DAY_FALLBACK_SUMMARY_HEADLINE = "День просит спокойного темпа, одного главного приоритета и аккуратных фиксаций."
DAY_FALLBACK_SUMMARY_GUIDE = "Лучше идти короткими циклами, держать буфер на перепроверку и не открывать лишний фронт."
DAY_FALLBACK_BEST_USE = "Собери один главный шаг, зафиксируй его письменно и не распыляй ресурс на параллельные срочности."
DAY_FALLBACK_RISK = "Избыточная скорость, резкий тон и попытка тащить всё сразу создают лишние ошибки."


@dataclass
class FactorRecord:
    id: str
    label: str
    explanation: str
    domain: str
    signal: float
    category: str | None = None


def _stable_seed(*parts: Any) -> int:
    raw = "|".join(str(part or "") for part in parts)
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)


def build_day_brief_prompt_bundle(facts: dict[str, Any], *, general_vibe: str | None = None) -> dict[str, Any]:
    semantic = _get_semantic_layer(facts)
    normalized_factors = _get_normalized_factors(facts, semantic_seed=semantic)
    local_dt = _parse_local_dt(facts)
    seed = _stable_seed(local_dt.date().isoformat(), semantic.get("focus_key"), general_vibe)
    prompt_lines = [
        f"Prompt registry: {DAY_BRIEF_PROMPT_VERSION}.",
        "Задача: собрать DayBrief строго из переданных фактов без новых сущностей и обещаний.",
        "Тон: премиальный, ясный, земной; сначала жизненная навигация, потом астрологическая причина.",
        "Контракт: headline/subhead должны быть короткими, best_uses/risks — детерминированными и проверяемыми.",
        f"Дата пользователя: {local_dt.date().isoformat()}.",
        f"Фокус дня: {semantic.get('focus_key') or 'money_admin'}.",
        f"Headline seed: {semantic.get('headline') or DAY_FALLBACK_SUMMARY_HEADLINE}",
        f"Pacing seed: {semantic.get('pacing') or DAY_FALLBACK_SUMMARY_GUIDE}",
        f"General vibe: {str(general_vibe or '').strip() or 'не задан'}.",
    ]
    return {
        "version": DAY_BRIEF_PROMPT_VERSION,
        "seed": seed,
        "model": "deterministic_repo",
        "prompt": "\n".join(prompt_lines),
    }


def build_day_brief_fallback_texts(facts: dict[str, Any], *, general_vibe: str | None = None) -> dict[str, str]:
    semantic = _get_semantic_layer(facts)
    normalized_factors = _get_normalized_factors(facts, semantic_seed=semantic)
    focus = str(semantic.get("focus_key") or "money_admin")
    headline = str(semantic.get("headline") or DAY_FALLBACK_SUMMARY_HEADLINE).strip()
    subhead = str(semantic.get("pacing") or DAY_FALLBACK_SUMMARY_GUIDE).strip()
    if general_vibe and str(general_vibe).strip():
        subhead = f"{subhead} Опора дня: {str(general_vibe).strip()[:120]}."
    best_use = {
        "money_admin": "Сначала закрой один рабочий или денежный вопрос, затем перепроверь условия и сумму шага.",
        "relationship": "Скажи главное мягко и прямо, оставив собеседнику пространство на ответ без давления.",
        "rest": "Собери день вокруг восстановления, буфера по времени и отказа от лишнего напряжения.",
        "launch": "Отдай лучший ресурс одной фокусной задаче и доведи её до видимой фиксации.",
    }.get(focus, DAY_FALLBACK_BEST_USE)
    risk = {
        "money_admin": "Не принимай предварительную договоренность за финальный результат и не форсируй цифры в спешке.",
        "relationship": "Не повышай тон и не додумывай мотивы там, где нужен один уточняющий вопрос.",
        "rest": "Не пытайся компенсировать усталость скоростью: это быстро превращает день в перегрев.",
        "launch": "Не разменивай сильное окно на суету, мелкие ответы и хаотичные переключения.",
    }.get(focus, DAY_FALLBACK_RISK)
    return {
        "headline": _clip_text(headline, fallback=DAY_FALLBACK_SUMMARY_HEADLINE, max_len=140),
        "subhead": _clip_text(subhead, fallback=DAY_FALLBACK_SUMMARY_GUIDE, max_len=220),
        "best_use": _clip_text(best_use, fallback=DAY_FALLBACK_BEST_USE, max_len=220),
        "risk": _clip_text(risk, fallback=DAY_FALLBACK_RISK, max_len=220),
    }
    category: str


def _empty_scores() -> dict[str, float]:
    return {key: 0.0 for key in DOMAIN_KEYS}


def _domain_for_natal(point: str) -> str:
    return NATAL_DOMAIN_MAP.get(point, "focus")


def _effect_from_aspect(aspect_type: str, transit: str) -> float:
    lowered = (aspect_type or "").lower()
    if "тригон" in lowered or "секстиль" in lowered:
        return 1.0
    if "квадрат" in lowered or "оппоз" in lowered:
        return -1.0
    if "соедин" in lowered:
        if transit in BENEFIC_TRANSITS:
            return 0.8
        if transit in CHALLENGING_TRANSITS:
            return -0.8
        return 0.3
    return 0.2


def _normalize_scores(values: dict[str, float], *, cap: float) -> dict[str, float]:
    return {key: max(-1.0, min(1.0, value / cap)) for key, value in values.items()}


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
        parsed = datetime.fromisoformat(str(raw))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return datetime.now(timezone.utc)


def _get_semantic_layer(facts: dict[str, Any]) -> dict[str, Any]:
    semantic = facts.get("semantic_layer")
    if isinstance(semantic, dict) and semantic:
        return semantic
    today_context = {}
    week_days = ((facts.get("week_data") or {}).get("days") or [])
    if week_days and isinstance(week_days[0], dict):
        today_context = dict(week_days[0])
    seed = build_daily_forecast_semantic_layer(
        fast_hits=facts.get("fast_hits") or [],
        traffic_lights=facts.get("traffic_lights") or {},
        day_context=today_context,
        month_data=facts.get("month_data") or {},
    )
    factors = _get_normalized_factors(facts, semantic_seed=seed)
    return build_semantic_layer_from_factors(factors, fallback=seed)


def _get_normalized_factors(facts: dict[str, Any], *, semantic_seed: dict[str, Any] | None = None):
    existing = facts.get("normalized_factors") or []
    if existing:
        factors = []
        for item in existing:
            if not isinstance(item, dict):
                continue
            try:
                from .forecast_factor_pipeline import NormalizedFactor
                factors.append(NormalizedFactor.model_validate(item))
            except Exception:
                continue
        if factors:
            return factors
    semantic_seed = semantic_seed or facts.get("semantic_layer") or {}
    return build_normalized_factors(
        fast_hits=facts.get("fast_hits") or [],
        traffic_lights=facts.get("traffic_lights") or {},
        semantic_layer=semantic_seed,
    )

def _birth_time_used(user: Any | None) -> bool:
    return bool(user and getattr(user, "birth_time", None) and getattr(user, "birth_time_known", True))


def _clip_text(value: str, *, fallback: str, max_len: int) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        text = fallback
    if len(text) <= max_len:
        return text
    trimmed = text[:max_len].rsplit(" ", 1)[0].strip()
    return trimmed or text[:max_len].strip()


def _pluralize_aspects(count: int) -> str:
    remainder_100 = count % 100
    remainder_10 = count % 10
    if 11 <= remainder_100 <= 14:
        suffix = "аспектов"
    elif remainder_10 == 1:
        suffix = "аспект"
    elif remainder_10 in {2, 3, 4}:
        suffix = "аспекта"
    else:
        suffix = "аспектов"
    return f"{count} ключевых {suffix}"


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
        try:
            orb = abs(float(hit.get("orb", 1.0)))
        except Exception:
            orb = 1.0
        intensity = 1.0 - min(orb / 2.0, 0.85)
        signal = effect * intensity
        contributions[domain] += signal
        label = str(hit.get("summary") or f"{transit} → {hit.get('natal')}").strip()
        factors.append(
            FactorRecord(
                id=f"fast_transit_{idx}",
                label=_clip_text(label, fallback="Активный транзит дня", max_len=80),
                explanation=_clip_text(
                    f"Быстрый транзит {transit} к {hit.get('natal')} сегодня звучит заметно громче обычного.",
                    fallback="Быстрый транзит даёт заметный сигнал по этой зоне дня.",
                    max_len=220,
                ),
                domain=domain,
                signal=signal,
                category="fast_transits",
            )
        )
    return _normalize_scores(contributions, cap=3.5), factors


def _phase_bias(phase: str) -> dict[str, float]:
    lookup = {
        "новолуние": {"focus": 0.9, "money": 0.7, "energy": 0.3},
        "растущ": {"money": 0.8, "focus": 0.6, "love": 0.2},
        "полнолуние": {"love": 0.6, "energy": -0.4, "money": -0.3},
        "убывающ": {"focus": 0.5, "love": 0.4, "energy": -0.2},
    }
    lowered = (phase or "").lower()
    for key, mapping in lookup.items():
        if key in lowered:
            return mapping
    return {"focus": 0.3, "love": 0.2}


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
    windows: list[dict[str, Any]] = []
    for idx, (slot_label, start_hour, end_hour) in enumerate(slots, start=1):
        start = base.replace(hour=start_hour)
        end = base.replace(hour=end_hour)
        mode = "soft"
        if slot_label == "Утро":
            mode = "best" if "раст" in phase.lower() or "новолу" in phase.lower() else "soft"
        if slot_label == "День" and void_flag:
            mode = "caution"
        if slot_label == "Вечер":
            mode = "caution" if void_flag or "полнолу" in phase.lower() else "soft"

        focus = WINDOW_FOCUS.get(dominant_domain, "главные задачи")
        if mode == "best":
            advice = f"Запускать, писать и договариваться: Луна в {moon_sign or 'актуальном знаке'} поддерживает {focus}."
            label = "Лучшее окно"
        elif mode == "caution":
            advice = "Не форсировать итоги и оставить буфер: поздний ритм дня любит перепроверку и паузу."
            label = "Осторожнее"
        else:
            advice = f"Подходит для спокойной сборки, уточнений и хода вокруг темы «{focus}»."
            label = "Мягкий ритм"

        windows.append(
            {
                "id": f"w{idx}",
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
                "label": label,
                "mode": mode,
                "advice": _clip_text(advice, fallback="Подходит для спокойного ритма и точных шагов.", max_len=200),
                "_slot_label": slot_label,
            }
        )
    return _dedupe_windows(windows, dominant_domain)


def _semantic_fingerprint(*parts: Any) -> str:
    tokens: list[str] = []
    for part in parts:
        text = str(part or "").strip().lower()
        if not text:
            continue
        cleaned = re.sub(r"[^\w\sа-яё]", " ", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            tokens.extend(token for token in cleaned.split(" ") if len(token) > 2)
    if not tokens:
        return ""
    return " ".join(list(dict.fromkeys(tokens))[:12])


WINDOW_LABEL_TAXONOMY = {
    "assembly": "Собрать ядро дня",
    "negotiation": "Согласовать и договориться",
    "review": "Проверить и сверить",
    "recovery": "Снизить темп и восстановиться",
    "focus": "Удержать глубокий фокус",
}


def _window_taxonomy_key(label: str, advice: str, explanation: str, dominant_domain: str) -> str:
    text = " ".join(part for part in (label, advice, explanation, dominant_domain) if part).lower()
    if any(token in text for token in ("соглас", "переговор", "договор", "обсужд", "контакт")):
        return "negotiation"
    if any(token in text for token in ("провер", "свер", "цифр", "документ", "пересмотр")):
        return "review"
    if any(token in text for token in ("восстанов", "пауза", "отдых", "ресурс", "мягк")):
        return "recovery"
    if any(token in text for token in ("фокус", "глуб", "концент", "одна задача")):
        return "focus"
    return "assembly"


def _dedupe_windows(windows: list[dict[str, Any]], dominant_domain: str) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    for window in windows:
        taxonomy_key = _window_taxonomy_key(
            str(window.get("label") or ""),
            str(window.get("advice") or ""),
            str(window.get("explanation") or ""),
            dominant_domain,
        )
        window["taxonomy_key"] = taxonomy_key
        window["label"] = WINDOW_LABEL_TAXONOMY[taxonomy_key]
        fingerprint = _semantic_fingerprint(taxonomy_key, window.get("advice"), window.get("explanation"))
        duplicate = next((
            item for item in deduped
            if item.get("mode") == window.get("mode")
            and item.get("start") == window.get("start")
            and item.get("end") == window.get("end")
            and _semantic_fingerprint(item.get("taxonomy_key"), item.get("advice"), item.get("explanation")) == fingerprint
        ), None)
        if duplicate:
            duplicate["_factor_ids"] = list(dict.fromkeys([*(duplicate.get("_factor_ids") or []), *(window.get("_factor_ids") or [])]))[:4]
            continue
        deduped.append(window)
    return deduped


def _score_lunar_dynamics(facts: dict[str, Any]) -> tuple[dict[str, float], list[dict[str, Any]], list[FactorRecord]]:
    contributions = _empty_scores()
    factors: list[FactorRecord] = []
    phase = str(facts.get("moon_phase") or "")
    for domain, value in _phase_bias(phase).items():
        contributions[domain] += value
        factors.append(
            FactorRecord(
                id=f"lunar_phase_{domain}",
                label=_clip_text(phase or "Лунный ритм", fallback="Лунный ритм", max_len=80),
                explanation=_clip_text(
                    f"Фаза Луны смещает внимание к сфере «{WINDOW_FOCUS.get(domain, domain)}».",
                    fallback="Лунный фон заметно меняет приоритет дня.",
                    max_len=220,
                ),
                domain=domain,
                signal=value,
                category="lunar_windows",
            )
        )

    traffic = facts.get("traffic_lights") or {}
    contributions["energy"] += _light_to_signal(traffic.get("health")) * 0.6
    contributions["money"] += _light_to_signal(traffic.get("money")) * 0.5
    contributions["love"] += _light_to_signal(traffic.get("love")) * 0.5

    day_context = (facts.get("week_data") or {}).get("days") or []
    moon_context = day_context[0].get("moon") if day_context and isinstance(day_context[0], dict) else {}
    void_flag = bool((moon_context or {}).get("void_of_course"))
    if void_flag:
        contributions["money"] -= 0.9
        contributions["focus"] -= 0.7
        factors.append(
            FactorRecord(
                id="lunar_void",
                label="Луна без курса",
                explanation="Окно без курса просит не форсировать сроки и оставить запас по времени.",
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
        str((moon_context or {}).get("sign") or facts.get("moon_sign") or ""),
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
    contributions["money"] += delta
    contributions["focus"] += delta * 0.6
    factors.append(
        FactorRecord(
            id="month_status",
            label=f"Фон месяца {status}",
            explanation="Медленный фон месяца окрашивает рабочий сценарий и темп решений.",
            domain="money",
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
                explanation="Профекционный акцент усиливает эту зону и делает её заметнее в течение дня.",
                domain=profection_domain,
                signal=0.6,
                category="slow_background",
            )
        )

    months = year_data.get("months") or []
    now_month = _parse_local_dt(facts).month
    month_entry = next((item for item in months if item.get("month") == now_month), None)
    if month_entry:
        month_status = str(month_entry.get("status") or "YELLOW").upper()
        month_delta = 0.7 if month_status == "GREEN" else (-0.7 if month_status == "RED" else 0.1)
        contributions["love"] += month_delta * 0.5
        contributions["energy"] += month_delta * 0.3
        factors.append(
            FactorRecord(
                id="month_anchor",
                label=f"Текущий месяц {month_status}",
                explanation="Фон месяца задаёт длинную эмоциональную подложку и меняет чувствительность.",
                domain="love",
                signal=month_delta,
                category="slow_background",
            )
        )
    return _normalize_scores(contributions, cap=3.0), factors


def _score_natal_sensitivity(facts: dict[str, Any]) -> tuple[dict[str, float], list[FactorRecord]]:
    contributions = _empty_scores()
    factors: list[FactorRecord] = []
    semantic = _get_semantic_layer(facts)
    normalized_factors = _get_normalized_factors(facts, semantic_seed=semantic)
    focus_key = semantic.get("focus_key")
    domain = FOCUS_KEY_DOMAIN.get(str(focus_key or ""), "focus")
    contributions[domain] += 0.8
    factors.append(
        FactorRecord(
            id="focus_key",
            label=f"Активный фокус: {focus_key or 'general'}",
            explanation="Натальная чувствительность к этой сфере повышена, поэтому сигнал слышится сильнее.",
            domain=domain,
            signal=0.8,
            category="natal_sensitivity",
        )
    )

    fast_hits = facts.get("fast_hits") or []
    natal_counts = _empty_scores()
    for hit in fast_hits:
        if isinstance(hit, dict):
            natal_counts[_domain_for_natal(str(hit.get("natal")))] += 1
    dominant = max(natal_counts, key=lambda key: natal_counts[key])
    if natal_counts[dominant] > 0:
        contributions[dominant] += 0.5
        factors.append(
            FactorRecord(
                id="natal_activation",
                label=f"Активирована зона {dominant}",
                explanation="Несколько транзитов попадают в одну и ту же область натального контура.",
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
        if not isinstance(hit, dict):
            continue
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
                    explanation="Редкий поддерживающий фактор даёт зелёный свет для точного и подготовленного шага.",
                    domain=domain,
                    signal=signal,
                    category="rare_boosters",
                )
            )
    return _normalize_scores(contributions, cap=1.5), factors


def _impact_level_from_signal(signal: float) -> ImpactLevel:
    absolute = abs(signal)
    if absolute >= 0.75:
        return ImpactLevel.high
    if absolute >= 0.4:
        return ImpactLevel.medium
    return ImpactLevel.low


def _score_status(value: int) -> str:
    if value >= 67:
        return "green"
    if value >= 45:
        return "yellow"
    return "red"


def _convert_records_for_weighting(records: Iterable[FactorRecord]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, record in enumerate(records):
        normalized.append(
            {
                "id": record.id or f"factor_{record.category}_{idx}",
                "label": record.label,
                "explanation": record.explanation,
                "domain": record.domain,
                "category": record.category,
                "weight": round(abs(record.signal), 4),
                "confidence": 0.9 if abs(record.signal) >= 0.6 else 0.75,
                "polarity": "positive" if record.signal >= 0 else "negative",
                "source": record.category,
            }
        )
    return normalized


def _source_models_for_record(record: dict[str, Any]) -> list[str]:
    category = str(record.get("category") or "")
    if category == "lunar_windows":
        return [SignalSource.lunar.value]
    if category == "fast_transits":
        return [SignalSource.transit_natal.value]
    if category == "rare_boosters":
        return [SignalSource.transit_natal.value]
    if category == "natal_sensitivity":
        return [SignalSource.transit_natal.value]
    if str(record.get("id") or "") == "profection_house":
        return [SignalSource.profections.value]
    if category == "slow_background":
        return [SignalSource.mixed.value]
    return [SignalSource.mixed.value]


def _build_explanation_astro(record: dict[str, Any]) -> str:
    label = str(record.get("label") or "").strip()
    category = str(record.get("category") or "")
    if category == "fast_transits":
        return _clip_text(
            f"Транзитный фактор «{label}» формирует один из главных дневных сигналов.",
            fallback="Транзитный фактор добавляет заметный акцент к дневной карте.",
            max_len=260,
        )
    if category == "lunar_windows":
        return "Лунный контекст задаёт тайминг и чувствительность этого участка дня."
    if category == "slow_background":
        return "Медленный фон периода усиливает этот мотив через длинные циклы и общий контекст."
    if category == "natal_sensitivity":
        return "Натальная чувствительность делает именно эту тему восприимчивее к текущим транзитам."
    return "Комбинация текущих факторов усиливает именно эту зону сценария."


def _prepare_personalized_factors(
    records: Iterable[FactorRecord],
    *,
    limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    normalized = _convert_records_for_weighting(records)
    if not normalized:
        empty_weighted = {
            "profile": "day_brief",
            "total_score": 0.0,
            "factors": [],
            "top_factors": [],
            "category_totals": {key: 0.0 for key in CATEGORY_WEIGHTS},
            "pipeline": [
                {"category": key, "weight_share": weight, "impact": 0.0}
                for key, weight in CATEGORY_WEIGHTS.items()
            ],
        }
        return [], empty_weighted, []

    susceptibility = build_susceptibility_profile(None)
    weighted = apply_weighted_factors("day_brief", attach_susceptibility(normalized, profile=susceptibility), top_n=8)
    source_lookup = {item["id"]: item for item in normalized}
    factors: list[dict[str, Any]] = []
    refs: list[dict[str, Any]] = []
    for factor in weighted["top_factors"][:limit]:
        src = source_lookup.get(factor.get("id"), {})
        impact_value = float(factor.get("impact", 0.0))
        source_models = _source_models_for_record(src)
        refs.append(
            {
                "id": factor.get("id"),
                "domain": src.get("domain"),
                "polarity": src.get("polarity", "positive"),
                "source_model": source_models[0] if source_models else SignalSource.mixed.value,
            }
        )
        factors.append(
            {
                "id": factor.get("id"),
                "label": _clip_text(str(factor.get("label") or "Ключевой фактор"), fallback="Ключевой фактор", max_len=80),
                "impact": _impact_level_from_signal(impact_value).value,
                "category": FACTOR_CATEGORY_MAP.get(str(src.get("category") or ""), str(src.get("category") or "")[:64] or None),
                "explanation_human": _clip_text(
                    str(factor.get("explanation") or src.get("explanation") or ""),
                    fallback="Этот фактор заметно влияет на сегодняшнюю траекторию дня.",
                    max_len=260,
                ),
                "explanation_astro": _build_explanation_astro(src),
                "source_models": source_models,
                "weight": round(min(1.0, abs(impact_value)), 3),
            }
        )
    return factors, weighted, refs


def _resolve_day_type(scores: dict[str, int]) -> str:
    avg = sum(scores.values()) / len(scores)
    for threshold, label in DAY_TYPE_THRESHOLDS:
        if avg >= threshold:
            return label
    return "recovery"


def _resolve_tone_tag(scores: dict[str, int], semantic: dict[str, Any], fallback_mode: bool) -> str:
    if fallback_mode:
        return "steady_fallback"
    if scores["focus"] >= 70 and scores["money"] >= 65:
        return "active_structured"
    if scores["love"] < 50:
        return "soft_boundaries"
    if scores["energy"] < 50:
        return "careful_pacing"
    if "нажим" in str(semantic.get("tension") or "").lower():
        return "precise_caution"
    return "balanced"


def _score_advice_map(semantic: dict[str, Any]) -> dict[str, str]:
    return {
        "energy": _clip_text(
            str(semantic.get("rest") or ""),
            fallback="Ресурс лучше держится на ровном темпе и паузах, чем на рывках.",
            max_len=220,
        ),
        "money": _clip_text(
            str(semantic.get("money_admin_focus") or semantic.get("negotiation") or ""),
            fallback="Рабочие и денежные вопросы лучше собирать по одному и фиксировать детали письменно.",
            max_len=220,
        ),
        "love": _clip_text(
            str(semantic.get("relationship_softness") or semantic.get("negotiation") or ""),
            fallback="Важен тон, пауза и отказ от лишнего давления в контакте.",
            max_len=220,
        ),
        "focus": _clip_text(
            str(semantic.get("pacing") or semantic.get("practical_move") or ""),
            fallback="Один главный ход сегодня работает лучше, чем распараллеливание.",
            max_len=220,
        ),
    }


def _build_score_items(scores: dict[str, int], semantic: dict[str, Any]) -> list[dict[str, Any]]:
    advice_map = _score_advice_map(semantic)
    items = []
    for key in DOMAIN_KEYS:
        why_title = _clip_text(
            str(semantic.get("score_details", {}).get(key, {}).get("title") or semantic.get("headline") or SCORE_TITLES[key]),
            fallback=SCORE_TITLES[key],
            max_len=140,
        )
        why_text = _clip_text(
            str(semantic.get("score_details", {}).get(key, {}).get("text") or advice_map[key]),
            fallback=advice_map[key],
            max_len=280,
        )
        items.append(
            {
                "key": key,
                "title": SCORE_TITLES[key],
                "value": scores[key],
                "status": _score_status(scores[key]),
                "advice": advice_map[key],
                "details": {
                    "why_title": why_title,
                    "why_text": why_text,
                    "supporting_factors": [],
                },
            }
        )
    return items


def _collect_factor_ids(factor_refs: list[dict[str, Any]], domain: str | None, polarity: str, *, limit: int = 3) -> list[str]:
    results: list[str] = []
    if domain is None:
        return results
    accepted_domains = DOMAIN_ALIASES.get(str(domain).strip().lower(), {str(domain).strip().lower()})
    for item in factor_refs:
        item_domain = str(item.get("domain") or "").strip().lower()
        if item_domain in accepted_domains and item.get("polarity") == polarity:
            factor_id = str(item.get("id"))
            if factor_id not in results:
                results.append(factor_id)
            if len(results) >= limit:
                break
    return results


def _build_supporting_factor_entries(factor_ids: list[str], factor_lookup: dict[str, dict[str, Any]], *, limit: int = 3) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for factor_id in factor_ids[:limit]:
        factor = factor_lookup.get(factor_id)
        if not factor:
            continue
        factor_id_text = str(factor.get("id") or "").strip().lower()
        impact = str(factor.get("impact") or "").strip().lower()
        raw_label = str(factor.get("label") or "").strip()
        domain = str(factor.get("domain") or "").strip().lower()
        family = str(factor.get("category") or factor.get("family") or "").strip().lower()
        human = str(factor.get("explanation_human") or "").strip()
        astro = str(factor.get("explanation_astro") or "").strip()
        if factor_id_text.startswith(SUPPORTING_FACTOR_BLOCKLIST_PREFIXES):
            continue
        if raw_label in SUPPORTING_FACTOR_BLOCKLIST_LABELS:
            continue
        if human and (human == raw_label or human.lower().startswith("светофор ")):
            human = ""
        if astro and astro.lower().startswith("светофор "):
            astro = ""
        label = raw_label
        if ":" in raw_label and domain in SUPPORTING_FACTOR_DOMAIN_LABELS:
            label = SUPPORTING_FACTOR_DOMAIN_LABELS[domain]
        elif family == "slow_background" and domain in SUPPORTING_FACTOR_DOMAIN_LABELS:
            label = SUPPORTING_FACTOR_DOMAIN_LABELS[domain]
        if not label and not human and not astro:
            continue
        value = {
            "high": "Сильный сигнал",
            "medium": "Умеренный сигнал",
            "low": "Мягкий сигнал",
        }.get(impact)
        entries.append(
            {
                "id": factor.get("id"),
                "label": label,
                "explanation_human": human or None,
                "explanation_astro": astro if astro and astro != raw_label else None,
                "impact": factor.get("impact"),
                "value": value,
            }
        )
    return entries


def _collect_local_score_factor_ids(
    factor_refs: list[dict[str, Any]],
    *,
    domain: str,
    factor_lookup: dict[str, dict[str, Any]],
    score_item: dict[str, Any],
    explainability_factors: list[dict[str, Any]] | None = None,
    limit: int = 4,
) -> list[str]:
    local_ids = _collect_factor_ids(factor_refs, domain, "positive", limit=limit)
    viable_local_ids = [factor_id for factor_id in local_ids if factor_lookup.get(factor_id)]
    if viable_local_ids:
        return viable_local_ids

    details = score_item.get("details") if isinstance(score_item.get("details"), dict) else {}
    item_text = " ".join(
        str(part or "")
        for part in (
            score_item.get("title"),
            score_item.get("advice"),
            details.get("why_title"),
            details.get("why_text"),
        )
    ).strip().lower()
    if not item_text:
        return []

    explainability_lookup = {
        str(item.get("id") or "").strip(): item
        for item in (explainability_factors or [])
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    accepted_domains = DOMAIN_ALIASES.get(str(domain).strip().lower(), {str(domain).strip().lower()})
    matches: list[str] = []
    for factor_id, factor in factor_lookup.items():
        if factor_id in matches:
            continue
        label = str(factor.get("label") or "").strip().lower()
        human = str(factor.get("explanation_human") or "").strip().lower()
        if not label and not human:
            continue

        explainability_factor = explainability_lookup.get(factor_id, {})
        related_key = str(
            explainability_factor.get("related_key")
            or explainability_factor.get("domain")
            or explainability_factor.get("key")
            or ""
        ).strip().lower()
        if related_key and related_key not in accepted_domains:
            continue

        tokens = [token for token in (label, human) if token]
        if related_key in accepted_domains:
            matches.append(factor_id)
        elif any(token in item_text for token in tokens):
            matches.append(factor_id)
        if len(matches) >= limit:
            break
    return matches


def _merge_explainability_factor_lookup(
    factor_lookup: dict[str, dict[str, Any]],
    explainability_factors: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    merged = dict(factor_lookup or {})
    for item in explainability_factors or []:
        if not isinstance(item, dict):
            continue
        factor_id = str(item.get("id") or "").strip()
        if not factor_id:
            continue
        existing = merged.get(factor_id, {})
        merged[factor_id] = {
            **existing,
            "id": factor_id,
            "label": str(item.get("label") or existing.get("label") or "").strip(),
            "domain": str(item.get("domain") or existing.get("domain") or "").strip() or None,
            "category": str(item.get("family") or existing.get("category") or "").strip() or None,
            "explanation_human": str(item.get("explanation_human") or existing.get("explanation_human") or "").strip(),
            "explanation_astro": str(item.get("explanation_astro") or existing.get("explanation_astro") or "").strip(),
            "weight": existing.get("weight") if existing.get("weight") is not None else abs(float(item.get("signal") or 0.0)),
        }
    return merged


def _build_best_and_risks(
    scores: dict[str, int],
    windows: list[dict[str, Any]],
    factor_refs: list[dict[str, Any]],
    *,
    factor_lookup: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    deltas = {key: scores[key] - BASELINE_SCORE for key in DOMAIN_KEYS}
    positives = sorted(
        [(key, value) for key, value in deltas.items() if value > 3],
        key=lambda item: item[1],
        reverse=True,
    )
    negatives = sorted(
        [(key, value) for key, value in deltas.items() if value < -3],
        key=lambda item: item[1],
    )
    best = positives[:2] or sorted(deltas.items(), key=lambda item: item[1], reverse=True)[:1]
    risks = negatives[:2] or sorted(deltas.items(), key=lambda item: item[1])[:1]

    best_window = next((window for window in windows if window["mode"] == "best"), windows[0] if windows else None)
    caution_window = next((window for window in windows if window["mode"] == "caution"), windows[-1] if windows else None)

    best_uses: list[dict[str, Any]] = []
    for idx, (domain, value) in enumerate(best, start=1):
        window = best_window or caution_window
        window_slot = str((window or {}).get("_slot_label") or "")
        text = BEST_USE_TEMPLATES.get(domain, "Сделать главное и не распыляться.")
        if window:
            text = f"{text} Лучше держать этот ход в окне «{window['label']}»."
        factor_ids = _collect_factor_ids(factor_refs, domain, "positive", limit=3)
        supporting_factors = _build_supporting_factor_entries(factor_ids, factor_lookup or {}, limit=3)
        best_uses.append(
            {
                "id": f"bu{idx}",
                "text": _clip_text(text, fallback="Сделать одно главное действие и не распыляться.", max_len=220),
                "factor_id": factor_ids[0] if factor_ids else None,
                "impact": _impact_level_from_signal(value / 10.0).value,
                "timeframe": WINDOW_TIMEFRAMES.get(window_slot, "all_day"),
                "details": {
                    "why_text": _clip_text(BEST_USE_TEMPLATES.get(domain, text), fallback=text, max_len=280),
                    "supporting_factors": supporting_factors,
                },
            }
        )

    risk_lines: list[dict[str, Any]] = []
    for idx, (domain, value) in enumerate(risks, start=1):
        window = caution_window or best_window
        window_slot = str((window or {}).get("_slot_label") or "")
        text = RISK_TEMPLATES.get(domain, "Главный риск — поспешить и потерять ясность.")
        if window:
            text = f"{text} Особенно в окне «{window['label']}»."
        factor_ids = _collect_factor_ids(factor_refs, domain, "negative", limit=3)
        supporting_factors = _build_supporting_factor_entries(factor_ids, factor_lookup or {}, limit=3)
        risk_lines.append(
            {
                "id": f"r{idx}",
                "text": _clip_text(text, fallback="Не разгонять день там, где нужна пауза.", max_len=220),
                "factor_id": factor_ids[0] if factor_ids else None,
                "impact": _impact_level_from_signal(value / 10.0).value,
                "timeframe": WINDOW_TIMEFRAMES.get(window_slot, "all_day"),
                "why_text": _clip_text(RISK_TEMPLATES.get(domain, text), fallback=text, max_len=280),
                "supporting_factors": supporting_factors,
            }
        )
    return _dedupe_action_risk_items(best_uses), _dedupe_action_risk_items(risk_lines)


def _dedupe_action_risk_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    for item in items:
        fingerprint = _semantic_fingerprint(item.get("text"), item.get("why_text"), item.get("timeframe"))
        duplicate = next((
            existing for existing in deduped
            if existing.get("timeframe") == item.get("timeframe")
            and _semantic_fingerprint(existing.get("text"), existing.get("why_text"), existing.get("timeframe")) == fingerprint
        ), None)
        if duplicate:
            merged_factor_ids = [value for value in dict.fromkeys([duplicate.get("factor_id"), item.get("factor_id")]) if value]
            if merged_factor_ids:
                duplicate["factor_id"] = merged_factor_ids[0]
            lookup = {factor.get("id"): factor for factor in [*duplicate.get("supporting_factors", []), *item.get("supporting_factors", [])] if factor.get("id")}
            merged_supporting_ids = list(dict.fromkeys(lookup.keys()))
            if len(merged_factor_ids) > 1:
                duplicate["why_text"] = _clip_text(
                    f"{duplicate.get('why_text') or duplicate.get('text') or ''} Также здесь пересекаются сигналы по близкой теме.",
                    fallback=str(duplicate.get("why_text") or duplicate.get("text") or ""),
                    max_len=280,
                )
            if merged_supporting_ids:
                duplicate["supporting_factors"] = [lookup[factor_id] for factor_id in merged_supporting_ids[:3] if factor_id in lookup]
            continue
        deduped.append(item)
    return deduped


def _build_summary(
    facts: dict[str, Any],
    scores: dict[str, int],
    *,
    fallback_mode: bool,
) -> dict[str, Any]:
    semantic = _get_semantic_layer(facts)
    normalized_factors = _get_normalized_factors(facts, semantic_seed=semantic)
    headline = _clip_text(
        str(semantic.get("headline") or ""),
        fallback="День просит собранности и одного понятного шага без лишнего разгона.",
        max_len=140,
    )
    pacing = str(semantic.get("pacing") or "").strip()
    move = str(semantic.get("practical_move") or "").strip()
    if fallback_mode and not move:
        move = "Сузь день до одного приоритета и сначала зафиксируй самое важное."
    subhead = _clip_text(
        " ".join(part for part in (pacing.capitalize() if pacing else "", move) if part),
        fallback="Лучше работают короткие циклы, ясные формулировки и спокойная фиксация деталей.",
        max_len=240,
    )
    return {
        "headline": headline,
        "subhead": subhead,
        "day_type": _resolve_day_type(scores),
        "tone": _resolve_tone_tag(scores, semantic, fallback_mode),
    }


def _build_context(facts: dict[str, Any]) -> dict[str, Any]:
    aspects_count = int(facts.get("aspects_count", 0) or 0)
    moon_sign = str(facts.get("moon_sign") or "").strip() or None
    label = None
    if moon_sign:
        label = f"Луна в {moon_sign}"
        if aspects_count:
            label = f"{label} · {_pluralize_aspects(aspects_count)}"
    return {
        "moon_sign": moon_sign,
        "moon_phase": str(facts.get("moon_phase") or "").strip() or None,
        "moon_emoji": str(facts.get("moon_emoji") or "").strip() or None,
        "aspects_count": aspects_count,
        "label": label,
    }


def _normalize_sub_end(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return None


def _build_premium_state(now_local: datetime, user: Any | None) -> dict[str, Any] | None:
    if user is None:
        return None
    sub_end = _normalize_sub_end(getattr(user, "subscription_active_until", None))
    active = bool(sub_end and sub_end > now_local.astimezone(timezone.utc))
    if active and sub_end is not None:
        seconds_left = max(0, int((sub_end - now_local.astimezone(timezone.utc)).total_seconds()))
        days_left = max(1, int((seconds_left + 86399) / 86400))
    else:
        days_left = 0
    return {
        "subscription_active": active,
        "subscription_active_until": sub_end.date().isoformat() if active and sub_end else None,
        "days_left": days_left,
        "show_upgrade_cta": not active,
        "show_resume_banner": False,
    }


def _build_cta(user: Any | None) -> dict[str, Any] | None:
    if user is None:
        return {
            "primary": {"type": "open_premium", "label": "Открыть прогнозы", "href": "/reports"},
            "secondary": {"type": "open_today", "label": "Сегодня", "href": "/"},
        }

    sub_end = _normalize_sub_end(getattr(user, "subscription_active_until", None))
    active = bool(sub_end and sub_end > datetime.now(timezone.utc))
    if active:
        return {
            "primary": {"type": "open_week", "label": "Смотреть неделю", "href": "/week"},
            "secondary": {"type": "ask_question", "label": "Задать вопрос", "href": "/question"},
        }
    return {
        "primary": {"type": "open_premium", "label": "Открыть прогнозы", "href": "/reports"},
        "secondary": {"type": "open_history", "label": "История", "href": "/reports/history"},
    }


def _build_legacy_payload(facts: dict[str, Any], general_vibe: str | None) -> dict[str, Any]:
    traffic_lights = facts.get("traffic_lights") or {}
    fast_hits = []
    for hit in facts.get("fast_hits") or []:
        if not isinstance(hit, dict):
            continue
        fast_hits.append(
            {
                "type": hit.get("type"),
                "summary": hit.get("summary"),
                "transit": hit.get("transit"),
                "natal": hit.get("natal"),
            }
        )
    return {
        "general_vibe": _clip_text(str(general_vibe or ""), fallback="", max_len=400) or None,
        "moon_sign": facts.get("moon_sign"),
        "moon_phase": facts.get("moon_phase"),
        "moon_emoji": facts.get("moon_emoji"),
        "aspects_count": int(facts.get("aspects_count", 0) or 0),
        "traffic_lights": {
            "health": traffic_lights.get("health"),
            "money": traffic_lights.get("money"),
            "love": traffic_lights.get("love"),
        },
        "fast_hits": fast_hits,
    }


def _confidence_bucket(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"


def _build_explainability(
    facts: dict[str, Any],
    weighted_metadata: dict[str, Any],
    factor_refs: list[dict[str, Any]],
    *,
    birth_time_used: bool,
    fallback_mode: bool,
    raw_factor_count: int,
) -> dict[str, Any]:
    personalization_level = str(facts.get("personalization_level") or "anonymous")
    base = 0.42
    if personalization_level.startswith("personalized"):
        base += 0.18
    if facts.get("fast_hits"):
        base += 0.12
    if birth_time_used:
        base += 0.08
    if raw_factor_count >= 6:
        base += 0.08
    elif raw_factor_count >= 3:
        base += 0.04
    if fallback_mode:
        base -= 0.12
    if not birth_time_used:
        base -= 0.03
    confidence = round(max(0.35, min(0.95, base)), 2)
    top_signal_source = factor_refs[0]["source_model"] if factor_refs else None
    factor_count = int(min(500, max(raw_factor_count, len(weighted_metadata.get("factors", [])))))
    explanation_depth = "full" if factor_count >= 6 and birth_time_used else "standard" if factor_count >= 3 else "minimal"
    return {
        "confidence": confidence,
        "birth_time_used": birth_time_used,
        "factor_count": factor_count,
        "timing_precision": "exact" if birth_time_used and not fallback_mode else "approximate",
        "top_signal_source": top_signal_source,
        "explanation_depth": explanation_depth,
    }


def _assemble_day_brief_payload(
    facts: dict[str, Any],
    *,
    user: Any | None = None,
    general_vibe: str | None = None,
) -> dict[str, Any]:
    semantic = _get_semantic_layer(facts)
    normalized_factors = _get_normalized_factors(facts, semantic_seed=semantic)
    facts = dict(facts)
    facts["semantic_layer"] = semantic

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

    raw_records = fast_factors + lunar_factors + slow_factors + natal_factors + rare_factors
    if normalized_factors:
        ranked_factors, factor_domain_meta = preprocess_factors_for_ranking(normalized_factors)
        raw_records = [FactorRecord(id=item["factor"].id, label=item["factor"].label, explanation=item["factor"].explanation_human, domain=item["factor"].domain, signal=item["score"]) for item in ranked_factors]
        for domain, meta in factor_domain_meta.items():
            int_scores[domain] = int(max(0, min(100, round(BASELINE_SCORE + (meta["signal"] * 35)))))
    birth_time_used = _birth_time_used(user)
    fallback_mode = bool((facts.get("meta") or {}).get("fallback_mode"))
    personalized_factors, weighted_meta, factor_refs = _prepare_personalized_factors(
        raw_records,
        limit=3 if fallback_mode else 5,
    )

    factor_lookup = {factor["id"]: factor for factor in personalized_factors}
    best_uses, risks = _build_best_and_risks(int_scores, windows, factor_refs, factor_lookup=factor_lookup)
    summary = _build_summary(facts, int_scores, fallback_mode=fallback_mode)
    explainability = _build_explainability(
        facts,
        weighted_meta,
        factor_refs,
        birth_time_used=birth_time_used,
        fallback_mode=fallback_mode,
        raw_factor_count=len(raw_records),
    )
    susceptibility = build_susceptibility_profile(user)
    explainability["reliability_support"] = weighted_meta.get("reliability_support", [])
    explainability["calibration"] = {
        "weight_profile_version": weighted_meta.get("weight_profile_version", "v2"),
        "susceptibility_source": susceptibility.source,
        "susceptibility_version": susceptibility.version,
        "entrypoints": calibration_entrypoints(),
    }
    if normalized_factors:
        calibrated_factors = attach_susceptibility([factor.model_dump() for factor in normalized_factors], profile=susceptibility)
        explainability["selected_factors"] = select_explainability_factors(normalized_factors, limit=5 if not fallback_mode else 3)
        explainability["selected_factors_support"] = [
            {
                "id": factor.get("id"),
                "susceptibility_multiplier": factor.get("susceptibility_multiplier", 1.0),
                "timing_precision": (factor.get("metadata") or {}).get("timing_precision", "day"),
                "rarity": (factor.get("metadata") or {}).get("rarity", "uncommon"),
            }
            for factor in calibrated_factors[: 5 if not fallback_mode else 3]
        ]
    detail_factor_lookup = _merge_explainability_factor_lookup(
        factor_lookup,
        explainability.get("selected_factors"),
    )

    score_items = _build_score_items(int_scores, semantic)
    for item in score_items:
        factor_ids = _collect_local_score_factor_ids(
            factor_refs,
            domain=str(item["key"]),
            factor_lookup=detail_factor_lookup,
            score_item=item,
            explainability_factors=explainability.get("selected_factors"),
            limit=4,
        )
        supporting_factors = _build_supporting_factor_entries(factor_ids, detail_factor_lookup, limit=4)
        why_text = item.get("details", {}).get("why_text") or item.get("advice") or "Здесь важна точная дозировка, а не простой напор."
        item["details"] = {
            "why_title": item.get("details", {}).get("why_title") or f"Почему {str(item['title']).lower()} именно такие",
            "why_text": why_text,
            "supporting_factors": supporting_factors,
            "factor_ids": factor_ids,
        } if supporting_factors or why_text else None

    now_local = _parse_local_dt(facts)
    clean_windows = []
    for window in windows:
        clean_window = {key: value for key, value in window.items() if not key.startswith("_")}
        factor_ids = list(dict.fromkeys((window.get("_factor_ids") or [])[:4]))
        supporting_factors = _build_supporting_factor_entries(factor_ids, detail_factor_lookup, limit=4)
        why_text = _clip_text(
            str(clean_window.get("explanation") or "") or f"{clean_window.get('label', 'Это окно')} лучше использовать там, где важны точная дозировка, ясный темп и одна понятная задача.",
            fallback="Это окно работает лучше, когда вы не распыляетесь и держите спокойный темп.",
            max_len=280,
        )
        clean_window["details"] = {
            "why_text": why_text,
            "supporting_factors": supporting_factors,
            "factor_ids": factor_ids,
        } if supporting_factors or why_text else None
        clean_windows.append(clean_window)

    return {
        "version": "day_brief_v1",
        "date": now_local.date().isoformat(),
        "personalization_level": str(facts.get("personalization_level") or "anonymous"),
        "fallback_mode": fallback_mode,
        "summary": summary,
        "context": _build_context(facts),
        "scores": score_items,
        "windows": clean_windows,
        "best_uses": best_uses,
        "risks": risks,
        "personalized_factors": personalized_factors,
        "explainability": explainability,
        "premium": _build_premium_state(now_local, user),
        "cta": _build_cta(user),
        "legacy": _build_legacy_payload(facts, general_vibe),
    }


def _resolve_trace_id(explicit: str | None = None) -> str | None:
    context = get_correlation_ids()
    return explicit or context.get("trace_id")


def build_day_brief_telemetry(
    payload: dict[str, Any],
    *,
    generation_mode: str | None = None,
    trace_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    model = validate_day_brief_payload(payload)
    resolved_trace_id = _resolve_trace_id(trace_id)
    return {
        "trace_id": resolved_trace_id,
        "request_id": request_id or resolved_trace_id,
        "generation_mode": generation_mode or "deterministic",
        "birth_time_used": model.explainability.birth_time_used,
        "confidence_bucket": _confidence_bucket(float(model.explainability.confidence)),
        "factor_count": model.explainability.factor_count,
    }


def _log_day_brief_event(
    level: str,
    event: str,
    *,
    fn: str,
    block: str,
    payload: dict[str, Any] | None = None,
    generation_mode: str | None = None,
    reason: str | None = None,
    error: str | None = None,
) -> None:
    if payload is None:
        return
    telemetry = build_day_brief_telemetry(payload, generation_mode=generation_mode)
    model = validate_day_brief_payload(payload)
    log_grace_event(
        level,
        event,
        module=MODULE_NAME,
        fn=fn,
        block=block,
        trace_id=telemetry["trace_id"],
        request_id=telemetry["request_id"],
        generation_mode=telemetry["generation_mode"],
        fallback_mode=model.fallback_mode,
        birth_time_used=telemetry["birth_time_used"],
        confidence_bucket=telemetry["confidence_bucket"],
        factor_count=telemetry["factor_count"],
        personalization_level=model.personalization_level,
        reason=reason,
        error=error,
    )


def build_day_brief_payload(
    facts: dict[str, Any],
    *,
    user: Any | None = None,
    general_vibe: str | None = None,
    generation_mode: str | None = None,
) -> dict[str, Any]:
    try:
        payload = serialize_day_brief(
            _assemble_day_brief_payload(
                facts,
                user=user,
                general_vibe=general_vibe,
            )
        )
        try:
            _log_day_brief_event(
                "info",
                "day_brief.built",
                fn="build_day_brief_payload",
                block="DAY_BRIEF_BUILD",
                payload=payload,
                generation_mode=generation_mode,
            )
        except Exception as exc:
            log_grace_event(
                "warning",
                "day_brief.log_failed",
                module=MODULE_NAME,
                fn="build_day_brief_payload",
                block="DAY_BRIEF_BUILD",
                generation_mode=generation_mode or "deterministic",
                personalization_level=payload.get("personalization_level"),
                fallback_mode=payload.get("fallback_mode"),
                error=str(exc),
            )
        return payload
    except ValidationError as exc:
        fallback = build_day_brief_fallback(
            _parse_local_dt(facts).astimezone(timezone.utc),
            general_vibe=general_vibe,
            generation_mode="fallback",
            reason="validation_failed",
        )
        _log_day_brief_event(
            "error",
            "day_brief.validation_failed",
            fn="build_day_brief_payload",
            block="DAY_BRIEF_VALIDATE",
            payload=fallback,
            generation_mode="fallback",
            reason="validation_failed",
            error=str(exc),
        )
        return fallback
    except Exception as exc:
        fallback = build_day_brief_fallback(
            _parse_local_dt(facts).astimezone(timezone.utc),
            general_vibe=general_vibe,
            generation_mode="fallback",
            reason="build_error",
        )
        _log_day_brief_event(
            "warning",
            "day_brief.fallback",
            fn="build_day_brief_payload",
            block="DAY_BRIEF_BUILD",
            payload=fallback,
            generation_mode="fallback",
            reason="build_error",
            error=str(exc),
        )
        return fallback


def build_day_brief_fallback(
    now_utc: datetime,
    *,
    general_vibe: str | None = None,
    generation_mode: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    now_local = now_utc.astimezone(timezone.utc)
    fallback_facts = {
        "local_dt": now_local.isoformat(),
        "moon_phase": "Растущая Луна",
        "moon_sign": "Луна",
        "moon_emoji": "🌔",
        "aspects_count": 0,
        "traffic_lights": {"health": "yellow", "money": "yellow", "love": "yellow"},
        "week_data": {"days": [{"moon": {"sign": "Луна", "phase": "Растущая Луна", "void_of_course": False}}]},
        "semantic_layer": {
            "headline": "День про аккуратный ход, короткий фокус и спокойную фиксацию главного.",
            "pacing": "Темп лучше держать короткими циклами и не открывать второй фронт без необходимости.",
            "rest": "Оставь запас по времени и не превращай усталость в спешку.",
            "money_admin_focus": "Сначала закрыть один рабочий или денежный вопрос и перепроверить детали.",
            "relationship_softness": "В разговоре полезнее мягкий тон и один прямой вопрос вместо нажима.",
            "practical_move": "Выбери один главный шаг, зафиксируй его письменно и не распыляйся на всё сразу.",
            "focus_key": "money_admin",
            "tension": "лишняя скорость и параллельные задачи",
        },
        "personalization_level": "anonymous",
        "meta": {"fallback_mode": True},
        "fast_hits": [],
        "month_data": {"status": "YELLOW"},
        "year_data": {},
    }
    payload = serialize_day_brief(_assemble_day_brief_payload(fallback_facts, user=None, general_vibe=general_vibe))
    _log_day_brief_event(
        "info",
        "day_brief.fallback",
        fn="build_day_brief_fallback",
        block="DAY_BRIEF_FALLBACK",
        payload=payload,
        generation_mode=generation_mode or "fallback",
        reason=reason or "fallback_payload",
    )
    return payload
