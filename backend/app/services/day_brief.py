"""Strict canonical DayBrief assembly for the daily feed surface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..logging_utils import get_correlation_ids, log_grace_event
from .aggregation_weights import DAY_BRIEF_WEIGHT_TABLE
from .day_brief_validators import serialize_day_brief, validate_day_brief_payload
from .forecast_factor_pipeline import build_normalized_factors, preprocess_factors_for_ranking

MODULE_NAME = "M-DAY-BRIEF-SERVICE"
DOMAIN_KEYS = ("energy", "money", "love", "focus")
DOMAIN_ALIASES = {
    "energy": {"energy", "health", "tonus"},
    "money": {"money", "work_money", "work", "career"},
    "love": {"love", "relationship", "relationships"},
    "focus": {"focus", "launch", "strategy"},
}
CATEGORY_WEIGHTS = DAY_BRIEF_WEIGHT_TABLE
BASELINE_SCORE = 55
SCORE_TITLES = {
    "energy": "Тонус",
    "money": "Работа и деньги",
    "love": "Чувства",
    "focus": "Фокус",
}
DAY_TYPE_THRESHOLDS = (
    (75, "push"),
    (65, "balance"),
    (57, "deep_focus"),
    (50, "caution"),
)
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


@dataclass
class FactorRecord:
    id: str
    label: str
    explanation: str
    domain: str
    signal: float


def _clip_text(value: str, *, fallback: str, max_len: int) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        text = fallback
    if len(text) <= max_len:
        return text
    trimmed = text[:max_len].rsplit(" ", 1)[0].strip()
    return trimmed or text[:max_len].strip()


def _parse_local_dt(facts: dict[str, Any]) -> datetime:
    raw = facts.get("local_dt") or ""
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _get_semantic_layer(facts: dict[str, Any]) -> dict[str, Any]:
    semantic = facts.get("semantic_layer")
    if isinstance(semantic, dict) and semantic:
        return semantic
    return {
        "headline": "День про короткий фокус, спокойный темп и взрослое отношение к приоритетам.",
        "pacing": "Лучше идти короткими циклами и не открывать лишние фронты.",
        "rest": "Ресурс держится лучше, если не прожимать день первым рывком.",
        "money_admin_focus": "Рабочие и денежные вопросы лучше закрывать по одному и сразу фиксировать детали.",
        "relationship_softness": "В контакте сегодня полезнее мягкость, точность и пауза перед ответом.",
        "practical_move": "Выбери один главный шаг и закрепи результат письменно.",
    }


def _get_normalized_factors(facts: dict[str, Any], *, semantic_seed: dict[str, Any] | None = None) -> list[Any]:
    existing = facts.get("normalized_factors")
    if isinstance(existing, list) and existing:
        return existing
    return build_normalized_factors(
        fast_hits=facts.get("fast_hits") or [],
        traffic_lights=facts.get("traffic_lights") or {},
        semantic_layer=semantic_seed or _get_semantic_layer(facts),
    )


def _score_status(value: int) -> str:
    if value >= 67:
        return "green"
    if value >= 45:
        return "yellow"
    return "red"


def _resolve_day_type(scores: dict[str, int]) -> str:
    avg = sum(scores.values()) / len(scores)
    for threshold, label in DAY_TYPE_THRESHOLDS:
        if avg >= threshold:
            return label
    return "recovery"


def _resolve_tone_tag(scores: dict[str, int], semantic: dict[str, Any]) -> str:
    if scores["focus"] >= 70 and scores["money"] >= 65:
        return "active_structured"
    if scores["love"] < 50:
        return "soft_boundaries"
    if scores["energy"] < 50:
        return "careful_pacing"
    if "нажим" in str(semantic.get("tension") or "").lower():
        return "precise_caution"
    return "balanced"


def _prepare_factor_refs(facts: dict[str, Any], normalized_factors: list[Any]) -> tuple[list[FactorRecord], list[dict[str, Any]]]:
    if normalized_factors:
        ranked_factors, factor_domain_meta = preprocess_factors_for_ranking(normalized_factors)
        records = [
            FactorRecord(
                id=item["factor"].id,
                label=item["factor"].label,
                explanation=item["factor"].explanation_human,
                domain=item["factor"].domain,
                signal=item["score"],
            )
            for item in ranked_factors
        ]
        refs = [
            {
                "id": record.id,
                "label": record.label,
                "domain": record.domain,
                "explanation": record.explanation,
                "signal": record.signal,
            }
            for record in records[:4]
        ]
        domain_meta = {domain: meta for domain, meta in factor_domain_meta.items()}
        return records, refs, domain_meta
    return [], [], {}


def _base_scores(facts: dict[str, Any]) -> dict[str, int]:
    traffic = facts.get("traffic_lights") or {}
    mapping = {"green": 74, "yellow": 56, "red": 38}
    scores = {
        "energy": mapping.get(str(traffic.get("health") or "").lower(), BASELINE_SCORE),
        "money": mapping.get(str(traffic.get("money") or "").lower(), BASELINE_SCORE),
        "love": mapping.get(str(traffic.get("love") or "").lower(), BASELINE_SCORE),
        "focus": BASELINE_SCORE,
    }
    return scores


def _dedupe_sentences(*parts: str) -> str:
    seen: list[str] = []
    for part in parts:
        normalized = " ".join(str(part or "").split()).strip()
        if normalized and normalized not in seen:
            seen.append(normalized)
    return " ".join(seen)


def _human_house_label(value: int | None) -> str | None:
    labels = {
        1: "1-й дом тела и личной инициативы",
        2: "2-й дом денег и личной цены вопроса",
        3: "3-й дом мыслей, контактов и коротких решений",
        4: "4-й дом опоры и внутренней устойчивости",
        5: "5-й дом чувств, симпатии и живого отклика",
        6: "6-й дом работы, режима и повседневных задач",
        7: "7-й дом партнёрства и контакта",
        8: "8-й дом общей цены решений и напряжения",
        9: "9-й дом смысла и расширения горизонта",
        10: "10-й дом карьеры и решений",
        11: "11-й дом друзей, команды и общих планов",
        12: "12-й дом восстановления и тихой внутренней работы",
    }
    return labels.get(value)


def _domain_description(key: str, semantic: dict[str, Any]) -> str | None:
    candidates = {
        "energy": [semantic.get("rest"), semantic.get("headline")],
        "money": [semantic.get("money_admin_focus"), semantic.get("practical_move")],
        "love": [semantic.get("relationship_softness"), semantic.get("headline")],
        "focus": [semantic.get("pacing"), semantic.get("practical_move")],
    }.get(key, [])
    text = _dedupe_sentences(*[str(item or "") for item in candidates])
    text = _clip_text(text, fallback="", max_len=300)
    if "недел" in text.lower() or "weekly" in text.lower():
        return None
    return text or None


def _factor_personal_clause(record: dict[str, Any]) -> str | None:
    label = str(record.get("label") or "").strip()
    if not label:
        return None
    lowered = label.lower()
    if "venus" in lowered or "венер" in lowered:
        return f"Сегодня это особенно заметно через твою Венеру: {label}."
    if "mercur" in lowered or "меркур" in lowered:
        return f"Тон дня цепляет твой Меркурий: {label}."
    if "mars" in lowered or "марс" in lowered:
        return f"Импульс дня проходит через твой Марс: {label}."
    if "moon" in lowered or "луна" in lowered:
        return f"Эмоциональный фон считывается через твою Луну: {label}."
    if "sun" in lowered or "солнц" in lowered:
        return f"Сейчас заметно включается твоё Солнце: {label}."
    if "mc" in lowered or "мс" in lowered:
        return f"Это отражается на твоём МС и теме решений: {label}."
    return f"Один из ключевых астрологических акцентов дня — {label}."


def _domain_why_text(key: str, semantic: dict[str, Any], factor_refs: list[dict[str, Any]], facts: dict[str, Any]) -> str | None:
    domain_refs = [
        item for item in factor_refs
        if str(item.get("domain") or "").strip().lower() in DOMAIN_ALIASES.get(key, {key})
    ]
    first_factor = domain_refs[0] if domain_refs else None
    phase = str(facts.get("moon_phase") or "").strip()
    moon_sign = str(facts.get("moon_sign") or "").strip()
    lunar_clause = None
    if phase or moon_sign:
        lunar_bits = [bit for bit in [f"Луна в {moon_sign}" if moon_sign else "", phase] if bit]
        if lunar_bits:
            lunar_clause = f"Фон дня задают {' '.join(lunar_bits)}, поэтому сфера реагирует заметнее обычного."
    profection_house = ((facts.get("year_data") or {}).get("profection") or {}).get("house")
    house_clause = None
    if isinstance(profection_house, int):
        human_house = _human_house_label(profection_house)
        if human_house and HOUSE_DOMAIN_MAP.get(profection_house) == key:
            house_clause = f"Дополнительный акцент идёт через твой {human_house}."
    factor_clause = _factor_personal_clause(first_factor) if first_factor else None
    semantic_clause = {
        "energy": str(semantic.get("rest") or ""),
        "money": str(semantic.get("money_admin_focus") or semantic.get("practical_move") or ""),
        "love": str(semantic.get("relationship_softness") or ""),
        "focus": str(semantic.get("pacing") or semantic.get("practical_move") or ""),
    }.get(key, "")
    sanitized_semantic_clause = semantic_clause if "недел" not in semantic_clause.lower() and "weekly" not in semantic_clause.lower() else ""
    text = _dedupe_sentences(factor_clause or "", house_clause or "", lunar_clause or "", sanitized_semantic_clause)
    text = _clip_text(text, fallback="", max_len=400)
    return text or None


def _build_day_domain(key: str, scores: dict[str, int], semantic: dict[str, Any], factor_refs: list[dict[str, Any]], facts: dict[str, Any]) -> dict[str, Any]:
    description = _domain_description(key, semantic)
    why_astro_text = _domain_why_text(key, semantic, factor_refs, facts)
    score = scores.get(key)
    domain_refs = [item for item in factor_refs if str(item.get("domain") or "").strip().lower() in DOMAIN_ALIASES.get(key, {key})]
    return {
        "key": key,
        "title": SCORE_TITLES[key],
        "score_status": "complete" if isinstance(score, int) else "missing",
        "score": score if isinstance(score, int) else None,
        "status": _score_status(score) if isinstance(score, int) else None,
        "description_status": "complete" if description else "missing",
        "description": description,
        "why_status": "complete" if why_astro_text else "missing",
        "why_astro_text": why_astro_text,
        "evidence_refs": domain_refs[:4],
    }


def _resolve_payload_status(domains: dict[str, dict[str, Any]]) -> str:
    if all(item.get("score_status") == "failed" for item in domains.values()):
        return "failed"
    if all(
        item.get("score_status") == "complete"
        and item.get("description_status") == "complete"
        and item.get("why_status") == "complete"
        for item in domains.values()
    ):
        return "complete"
    return "partial"


def _normalize_scores_with_factors(facts: dict[str, Any], domain_meta: dict[str, Any]) -> dict[str, int]:
    scores = _base_scores(facts)
    for domain, meta in domain_meta.items():
        scores[domain] = int(max(0, min(100, round(BASELINE_SCORE + (float(meta.get("signal", 0.0)) * 35)))))
    return scores


def _build_premium_state(now_local: datetime, user: Any | None) -> dict[str, Any] | None:
    if user is None:
        return None
    sub_end = getattr(user, "subscription_active_until", None)
    if isinstance(sub_end, datetime):
        if sub_end.tzinfo is None:
            sub_end = sub_end.replace(tzinfo=timezone.utc)
        active = sub_end > now_local.astimezone(timezone.utc)
    else:
        active = False
    days_left = max(1, int((sub_end - now_local.astimezone(timezone.utc)).total_seconds() / 86400) + 1) if active and sub_end else 0
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
    sub_end = getattr(user, "subscription_active_until", None)
    active = isinstance(sub_end, datetime) and (sub_end if sub_end.tzinfo else sub_end.replace(tzinfo=timezone.utc)) > datetime.now(timezone.utc)
    if active:
        return {
            "primary": {"type": "open_week", "label": "Смотреть неделю", "href": "/week"},
            "secondary": {"type": "ask_question", "label": "Задать вопрос", "href": "/question"},
        }
    return {
        "primary": {"type": "open_premium", "label": "Открыть прогнозы", "href": "/reports"},
        "secondary": {"type": "open_history", "label": "История", "href": "/reports/history"},
    }


def _assemble_day_brief_payload(
    facts: dict[str, Any],
    *,
    user: Any | None = None,
    general_vibe: str | None = None,
) -> dict[str, Any]:
    semantic = _get_semantic_layer(facts)
    normalized_factors = _get_normalized_factors(facts, semantic_seed=semantic)
    _records, factor_refs, domain_meta = _prepare_factor_refs(facts, normalized_factors)
    int_scores = _normalize_scores_with_factors(facts, domain_meta)
    hero = {
        "title": _clip_text(str(semantic.get("headline") or general_vibe or ""), fallback="Сегодня лучше держать день собранным и не распылять внимание.", max_len=140),
        "subtitle": _clip_text(_dedupe_sentences(str(semantic.get("pacing") or ""), str(semantic.get("practical_move") or "")), fallback="Лучше работают короткие циклы, ясные формулировки и один главный шаг.", max_len=240),
        "day_type": _resolve_day_type(int_scores),
        "tone": _resolve_tone_tag(int_scores, semantic),
    }
    domains = {key: _build_day_domain(key, int_scores, semantic, factor_refs, facts) for key in DOMAIN_KEYS}
    now_local = _parse_local_dt(facts)
    return {
        "version": "day_brief_canon_v1",
        "status": _resolve_payload_status(domains),
        "date": now_local.date().isoformat(),
        "personalization_level": str(facts.get("personalization_level") or "anonymous"),
        "hero": hero,
        "domains": domains,
        "premium": _build_premium_state(now_local, user),
        "cta": _build_cta(user),
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
    complete_domains = sum(
        1
        for domain in model.domains.values()
        if domain.score_status == "complete" and domain.description_status == "complete" and domain.why_status == "complete"
    )
    return {
        "trace_id": resolved_trace_id,
        "request_id": request_id or resolved_trace_id,
        "generation_mode": generation_mode or "deterministic",
        "birth_time_used": False,
        "confidence_bucket": "high" if complete_domains == 4 else "medium" if complete_domains >= 2 else "low",
        "factor_count": sum(len(domain.evidence_refs) for domain in model.domains.values()),
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
        status=model.status,
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
            status=payload.get("status"),
            error=str(exc),
        )
    return payload
