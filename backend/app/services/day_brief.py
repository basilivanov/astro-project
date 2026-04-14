"""Strict canonical DayBrief assembly for the daily feed surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any

from ..logging_utils import get_correlation_ids, log_grace_event
from .aggregation_weights import DAY_BRIEF_WEIGHT_TABLE
from .day_brief_validators import serialize_day_brief, validate_day_brief_payload
from .forecast_factor_pipeline import NormalizedFactor
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
DOMAIN_MARKER_HINTS = {
    "money": ("услов", "срок", "цен", "цифр", "договор", "обязател", "соглас"),
    "love": ("контакт", "мотив", "уточн", "реакц", "ясност", "мягк"),
    "focus": ("фокус", "вниман", "переключ", "приоритет", "контур"),
    "energy": ("ресурс", "темп", "ритм", "восстанов", "нагруз", "рывок"),
}


@dataclass
class FactorRecord:
    id: str
    label: str
    explanation: str
    domain: str
    signal: float


@dataclass
class DomainTextLayerResult:
    description_status: str
    description: str | None
    why_status: str
    why_astro_text: str | None
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    composition_mode: str = "deterministic"


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
        normalized: list[NormalizedFactor] = []
        for item in existing:
            if isinstance(item, NormalizedFactor):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(NormalizedFactor.model_validate(item))
        if normalized:
            return normalized
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


def _prepare_factor_refs(facts: dict[str, Any], normalized_factors: list[Any]) -> tuple[list[FactorRecord], list[dict[str, Any]], dict[str, Any]]:
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


def _select_domain_explainability_refs(key: str, records: list[FactorRecord], *, limit: int = 4) -> list[dict[str, Any]]:
    aliases = DOMAIN_ALIASES.get(key, {key})
    domain_records = [record for record in records if record.domain in aliases]
    if not domain_records:
        return []
    prioritized = sorted(
        domain_records,
        key=lambda record: (
            0 if _factor_personal_clause({"label": record.label}) else 1,
            -abs(record.signal),
        ),
    )
    return [
        {
            "id": record.id,
            "label": record.label,
            "domain": record.domain,
            "explanation": record.explanation,
            "signal": record.signal,
        }
        for record in prioritized[: max(1, limit)]
    ]


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


DESCRIPTION_FORBIDDEN_RE = ("дом", "аспект", "квадрат", "секстиль", "трин", "оппози", "соедин", "марс", "венер", "меркур", "луна", "солнц", "мс", "mc", "твой", "твоя", "твоё")
WHY_ANCHOR_RE = ("твой", "твоя", "твоё", "твоём", "луна", "марс", "венер", "меркур", "солнц", "мс", "mc", "дом")
WHY_CAUSAL_RE = ("поэтому", "потому", "из-за", "задаёт", "задают", "акцент", "включ", "проходит", "цепляет", "считывается", "идёт", "заметно", "реагирует")


def _domain_description(key: str, semantic: dict[str, Any]) -> str | None:
    candidates = {
        "energy": [semantic.get("rest"), semantic.get("headline")],
        "money": [semantic.get("money_admin_focus"), semantic.get("practical_move")],
        "love": [semantic.get("relationship_softness"), semantic.get("headline")],
        "focus": [semantic.get("pacing"), semantic.get("practical_move")],
    }.get(key, [])
    text = _dedupe_sentences(*[str(item or "") for item in candidates])
    text = _clip_text(text, fallback="", max_len=300)
    return text or None


def _hero_focus_overlap_tokens() -> tuple[str, ...]:
    return (
        "один главный",
        "один шаг",
        "за раз",
        "не распы",
        "коротк",
        "список дел",
        "не обещ",
        "один документ",
        "один дедлайн",
        "одно согласование",
        "один вектор",
    )


def _rewrite_focus_description(description: str | None) -> str | None:
    lowered = str(description or "").lower()
    if not lowered.strip():
        return None
    if any(token in lowered for token in _hero_focus_overlap_tokens()):
        return "Фокус дня просит удерживать один главный приоритет и сокращать лишние переключения. Не дробите внимание: один контур действий сейчас собирает результат лучше, чем параллельные рывки."
    return description


def _rewrite_money_description(description: str | None) -> str | None:
    lowered = str(description or "").lower()
    if not lowered.strip():
        return None
    if not any(token in lowered for token in ("услов", "срок", "цифр", "договор", "документ", "соглас", "обязател", "цен")):
        return "В рабочих и денежных вопросах сегодня важны условия, сроки и точные формулировки. Спокойная проверка цифр и договорённостей работает лучше, чем быстрый нажим."
    return description


def _polish_domain_description(key: str, description: str | None, hero: dict[str, Any] | None = None) -> str | None:
    next_description = description
    if key == "focus":
        hero_text = f"{hero.get('title') or ''} {hero.get('subtitle') or ''}".lower() if isinstance(hero, dict) else ""
        next_description = _rewrite_focus_description(next_description)
        focus_text = str(next_description or "").lower()
        blocked_overlap = any(token in hero_text and token in focus_text for token in _hero_focus_overlap_tokens())
        if blocked_overlap or _text_similarity(hero_text, focus_text) >= 0.34:
            next_description = "Фокус дня держится на одном главном приоритете и спокойной последовательности действий. Чем меньше лишних переключений и дробления внимания, тем легче довести результат до конца."
    if key == "money":
        next_description = _rewrite_money_description(next_description)
    return _trim_to_sentences(next_description, max_sentences=2, max_len=170) if next_description else None


def _polish_hero_copy(hero: dict[str, Any]) -> dict[str, Any]:
    title = _trim_to_sentences(hero.get("title"), max_sentences=1, max_len=72) or "Держите день собранным."
    subtitle = _trim_to_sentences(hero.get("subtitle"), max_sentences=2, max_len=150) or "Главный результат сегодня приходит через спокойный темп и один ясный вектор действий."
    hero["title"] = title
    hero["subtitle"] = subtitle
    return hero


def _domain_text_forbidden_description_reason(text: str | None) -> str | None:
    lowered = str(text or "").lower()
    if not lowered.strip():
        return "description_missing"
    if "недел" in lowered or "weekly" in lowered:
        return "description_weekly_leak"
    if any(token in lowered for token in DESCRIPTION_FORBIDDEN_RE):
        return "description_too_technical"
    return None


def _text_similarity(left: str | None, right: str | None) -> float:
    left_words = {word for word in str(left or "").lower().split() if len(word) > 3}
    right_words = {word for word in str(right or "").lower().split() if len(word) > 3}
    if not left_words or not right_words:
        return 0.0
    return len(left_words & right_words) / max(1, min(len(left_words), len(right_words)))

def _trim_to_sentences(text: str | None, *, max_sentences: int, max_len: int) -> str | None:
    raw = " ".join(str(text or "").split()).strip()
    if not raw:
        return None
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", raw) if part.strip()]
    clipped = " ".join(parts[:max_sentences]) if parts else raw
    return _clip_text(clipped, fallback="", max_len=max_len) or None


def _canonicalize_clause(text: str | None) -> str:
    lowered = str(text or "").lower()
    lowered = re.sub(r"[^а-яa-z0-9 ]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _strip_repeated_opening(text: str | None, seen: set[str]) -> str | None:
    value = _trim_to_sentences(text, max_sentences=3, max_len=240)
    if not value:
        return None
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", value) if part.strip()]
    kept: list[str] = []
    for part in parts:
        canon = _canonicalize_clause(part)
        if canon and canon in seen and len(parts) > 1:
            continue
        kept.append(part)
        if canon:
            seen.add(canon)
    return _clip_text(" ".join(kept) or value, fallback=value, max_len=240)


def _dedupe_day_surface(hero: dict[str, Any], domains: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    seen: set[str] = set()
    hero = _polish_hero_copy(hero)
    hero_title = _trim_to_sentences(hero.get("title"), max_sentences=1, max_len=72)
    hero_subtitle = _trim_to_sentences(hero.get("subtitle"), max_sentences=2, max_len=150)
    for item in [hero_title, hero_subtitle]:
        canon = _canonicalize_clause(item)
        if canon:
            seen.add(canon)
    hero["title"] = hero_title or hero.get("title")
    hero["subtitle"] = hero_subtitle or hero.get("subtitle")

    for key in DOMAIN_KEYS:
        domain = domains[key]
        description = _strip_repeated_opening(domain.get("description"), seen)
        description = _polish_domain_description(key, description, hero)
        why_text = _strip_repeated_opening(domain.get("why_astro_text"), seen)
        if description and why_text and _text_similarity(description, why_text) >= 0.72:
            why_text = None
            domain["why_status"] = "failed"
            reason_codes = list(domain.get("text_reason_codes") or [])
            if "why_duplicates_description" not in reason_codes:
                reason_codes.append("why_duplicates_description")
            domain["text_reason_codes"] = reason_codes
        if description:
            domain["description"] = description
        if why_text:
            domain["why_astro_text"] = _trim_to_sentences(why_text, max_sentences=2, max_len=220)
        elif domain.get("why_status") == "complete":
            domain["why_status"] = "failed"
            domain["why_astro_text"] = None
    return hero, domains


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
    return None


def _domain_semantic_clause(key: str, semantic: dict[str, Any]) -> str | None:
    candidates = {
        "energy": str(semantic.get("rest") or ""),
        "money": str(semantic.get("money_admin_focus") or semantic.get("practical_move") or ""),
        "love": str(semantic.get("relationship_softness") or ""),
        "focus": str(semantic.get("pacing") or semantic.get("practical_move") or ""),
    }
    clause = candidates.get(key, "")
    lowered = clause.lower()
    if not clause.strip():
        return None
    return None if "недел" in lowered or "weekly" in lowered else clause


def _domain_lunar_clause(key: str, moon_phase: str, moon_sign: str) -> str | None:
    if not (moon_phase or moon_sign):
        return None
    backdrop = " ".join(part for part in [f"Луна в {moon_sign}" if moon_sign else "", moon_phase] if part).strip()
    if not backdrop:
        return None
    return None


def _has_domain_driver_marker(key: str, text: str | None) -> bool:
    lowered = str(text or "").lower()
    if not lowered.strip():
        return False
    return any(marker in lowered for marker in DOMAIN_MARKER_HINTS.get(key, ()))


def _collect_domain_text_inputs(key: str, semantic: dict[str, Any], factor_refs: list[dict[str, Any]], facts: dict[str, Any]) -> dict[str, Any]:
    domain_refs = [
        item for item in factor_refs
        if str(item.get("domain") or "").strip().lower() in DOMAIN_ALIASES.get(key, {key})
    ]
    personal_refs = [item for item in domain_refs if _factor_personal_clause(item)]
    if personal_refs:
        domain_refs = personal_refs + [item for item in domain_refs if item not in personal_refs]
    return {
        "key": key,
        "semantic": semantic,
        "domain_refs": domain_refs,
        "facts": facts,
        "profection_house": ((facts.get("year_data") or {}).get("profection") or {}).get("house"),
        "moon_phase": str(facts.get("moon_phase") or "").strip(),
        "moon_sign": str(facts.get("moon_sign") or "").strip(),
    }


def _compose_domain_description(inputs: dict[str, Any]) -> tuple[str | None, list[str]]:
    description = _trim_to_sentences(_domain_description(str(inputs["key"]), inputs["semantic"]), max_sentences=2, max_len=220)
    reason = _domain_text_forbidden_description_reason(description)
    return (None if reason else description), ([reason] if reason else [])


def _compose_domain_why_text(inputs: dict[str, Any]) -> tuple[str | None, list[str]]:
    key = str(inputs["key"])
    semantic = inputs["semantic"]
    domain_refs = inputs["domain_refs"]
    first_factor = domain_refs[0] if domain_refs else None
    phase = str(inputs.get("moon_phase") or "").strip()
    moon_sign = str(inputs.get("moon_sign") or "").strip()
    lunar_clause = _domain_lunar_clause(key, phase, moon_sign)
    profection_house = inputs.get("profection_house")
    house_clause = None
    if isinstance(profection_house, int):
        human_house = _human_house_label(profection_house)
        if human_house and HOUSE_DOMAIN_MAP.get(profection_house) == key:
            house_clause = f"Дополнительный акцент идёт через твой {human_house}."
    factor_clause = _factor_personal_clause(first_factor) if first_factor else None
    semantic_clause = _domain_semantic_clause(key, semantic)
    text = _dedupe_sentences(factor_clause or "", house_clause or "", lunar_clause or "", semantic_clause or "")
    text = _trim_to_sentences(text, max_sentences=2, max_len=220) or ""
    reasons: list[str] = []
    lowered = text.lower()
    if not text:
        reasons.append("why_missing")
    if domain_refs and not any(_factor_personal_clause(item) for item in domain_refs) and not house_clause and not semantic_clause and not lunar_clause:
        reasons.append("why_not_personalized")
    if text and not any(token in lowered for token in WHY_CAUSAL_RE):
        reasons.append("why_missing_causal_link")
    if text and not (factor_clause or house_clause or _has_domain_driver_marker(key, text)):
        reasons.append("why_missing_domain_driver")
    return (None if reasons else text), reasons


def _build_domain_text_layers(key: str, semantic: dict[str, Any], factor_refs: list[dict[str, Any]], facts: dict[str, Any]) -> DomainTextLayerResult:
    inputs = _collect_domain_text_inputs(key, semantic, factor_refs, facts)
    description, description_reasons = _compose_domain_description(inputs)
    why_astro_text, why_reasons = _compose_domain_why_text(inputs)
    reason_codes = [*description_reasons, *why_reasons]
    if description and why_astro_text and _text_similarity(description, why_astro_text) >= 0.82:
        why_astro_text = None
        reason_codes.append("why_duplicates_description")
    return DomainTextLayerResult(
        description_status="complete" if description else "failed" if description_reasons else "missing",
        description=description,
        why_status="complete" if why_astro_text else "failed" if why_reasons or "why_duplicates_description" in reason_codes else "missing",
        why_astro_text=why_astro_text,
        evidence_refs=inputs["domain_refs"][:4],
        reason_codes=reason_codes,
        composition_mode="deterministic",
    )


def _guard_cross_domain_why_duplicates(domains: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    seen: dict[str, str] = {}
    for key in DOMAIN_KEYS:
        domain = domains[key]
        why_text = domain.get("why_astro_text")
        if domain.get("why_status") != "complete" or not why_text:
            continue
        canon = _canonicalize_clause(why_text)
        duplicate_of = next((other for other, other_text in seen.items() if _text_similarity(other_text, canon) >= 0.82), None)
        if duplicate_of and not _has_domain_driver_marker(key, why_text):
            reasons = list(domain.get("text_reason_codes") or [])
            if "why_cross_domain_duplicate" not in reasons:
                reasons.append("why_cross_domain_duplicate")
            domain["text_reason_codes"] = reasons
            domain["why_status"] = "failed"
            domain["why_astro_text"] = None
            continue
        seen[key] = canon
    return domains

def _build_day_domain(key: str, scores: dict[str, int], semantic: dict[str, Any], factor_refs: list[dict[str, Any]], facts: dict[str, Any]) -> dict[str, Any]:
    text_layers = _build_domain_text_layers(key, semantic, factor_refs, facts)
    score = scores.get(key)
    return {
        "key": key,
        "title": SCORE_TITLES[key],
        "score_status": "complete" if isinstance(score, int) else "missing",
        "score": score if isinstance(score, int) else None,
        "status": _score_status(score) if isinstance(score, int) else None,
        "description_status": text_layers.description_status,
        "description": text_layers.description,
        "why_status": text_layers.why_status,
        "why_astro_text": text_layers.why_astro_text,
        "evidence_refs": text_layers.evidence_refs,
        "text_reason_codes": text_layers.reason_codes,
        "text_composition_mode": text_layers.composition_mode,
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
    records, factor_refs, domain_meta = _prepare_factor_refs(facts, normalized_factors)
    int_scores = _normalize_scores_with_factors(facts, domain_meta)
    hero = {
        "title": _trim_to_sentences(str(semantic.get("headline") or general_vibe or ""), max_sentences=1, max_len=110) or "Сегодня лучше держать день собранным и не распылять внимание.",
        "subtitle": _trim_to_sentences(_dedupe_sentences(str(semantic.get("pacing") or ""), str(semantic.get("practical_move") or "")), max_sentences=2, max_len=190) or "Лучше работают короткие циклы, ясные формулировки и один главный шаг.",
        "day_type": _resolve_day_type(int_scores),
        "tone": _resolve_tone_tag(int_scores, semantic),
    }
    domains = {
        key: _build_day_domain(key, int_scores, semantic, _select_domain_explainability_refs(key, records), facts)
        for key in DOMAIN_KEYS
    }
    domains = _guard_cross_domain_why_duplicates(domains)
    hero, domains = _dedupe_day_surface(hero, domains)
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
        text_layer_status={
            key: {"description": domain.description_status, "why": domain.why_status}
            for key, domain in model.domains.items()
        },
        text_layer_reason_codes={
            key: getattr(domain, "text_reason_codes", [])
            for key, domain in model.domains.items()
            if getattr(domain, "text_reason_codes", [])
        },
        text_composition_mode="deterministic",
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
