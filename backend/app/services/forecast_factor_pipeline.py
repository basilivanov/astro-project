from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel, Field


DOMAIN_KEYS = ("energy", "money", "love", "focus")
DEFAULT_DOMAIN = "focus"
TRANSIT_DOMAIN_MAP = {
    "Sun": "money",
    "MC": "money",
    "Mercury": "focus",
    "Mars": "energy",
    "ASC": "energy",
    "Moon": "love",
    "Venus": "love",
    "Jupiter": "money",
    "Saturn": "focus",
}
FOCUS_KEY_DOMAIN = {
    "money_admin": "money",
    "relationship": "love",
    "rest": "energy",
    "launch": "focus",
}


class NormalizedFactor(BaseModel):
    id: str
    family: str
    category: str
    domain: str = Field(default=DEFAULT_DOMAIN)
    label: str
    explanation_human: str
    explanation_astro: str = ""
    signal: float = 0.0
    weight: float = 1.0
    source: str = "deterministic"
    metadata: dict[str, Any] = Field(default_factory=dict)


def clamp_signal(value: Any, *, cap: float = 1.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        numeric = 0.0
    return max(-cap, min(cap, numeric))


def normalize_domain(value: Any, *, fallback: str = DEFAULT_DOMAIN) -> str:
    domain = str(value or fallback).lower().strip()
    return domain if domain in DOMAIN_KEYS else fallback


def make_factor(
    *,
    factor_id: str,
    family: str,
    label: str,
    explanation_human: str,
    explanation_astro: str = "",
    domain: str | None = None,
    signal: float = 0.0,
    weight: float = 1.0,
    category: str | None = None,
    source: str = "deterministic",
    metadata: dict[str, Any] | None = None,
) -> NormalizedFactor:
    resolved_family = str(family or "misc").strip() or "misc"
    return NormalizedFactor(
        id=str(factor_id),
        family=resolved_family,
        category=str(category or resolved_family),
        domain=normalize_domain(domain),
        label=str(label or factor_id),
        explanation_human=str(explanation_human or label),
        explanation_astro=str(explanation_astro or ""),
        signal=clamp_signal(signal),
        weight=max(0.0, float(weight)),
        source=str(source or "deterministic"),
        metadata=dict(metadata or {}),
    )


def factor_from_fast_hit(hit: dict[str, Any]) -> NormalizedFactor | None:
    if not isinstance(hit, dict):
        return None
    transit = str(hit.get("transit") or "").strip()
    natal = str(hit.get("natal") or "").strip()
    aspect_type = str(hit.get("type") or "").strip()
    summary = str(hit.get("summary") or "").strip()
    if not (transit or natal or summary):
        return None
    signal = -0.75 if any(token in aspect_type.lower() for token in ("квадрат", "оппози")) else 0.7
    domain = normalize_domain(TRANSIT_DOMAIN_MAP.get(natal) or TRANSIT_DOMAIN_MAP.get(transit))
    label = summary or " ".join(part for part in (transit, aspect_type, natal) if part).strip()
    explanation_astro = label
    explanation_human = str(hit.get("interpretation") or hit.get("summary") or label)
    return make_factor(
        factor_id=f"fast:{transit}:{natal}:{aspect_type}",
        family="fast_transits",
        category="transit_natal",
        domain=domain,
        label=label,
        explanation_human=explanation_human,
        explanation_astro=explanation_astro,
        signal=signal,
        metadata={"orb": hit.get("orb") or hit.get("exact_diff")},
    )


def factors_from_fast_hits(hits: Iterable[dict[str, Any]]) -> list[NormalizedFactor]:
    return [factor for factor in (factor_from_fast_hit(hit) for hit in hits or []) if factor is not None]


def factors_from_traffic_lights(traffic_lights: dict[str, Any], semantic_layer: dict[str, Any] | None = None) -> list[NormalizedFactor]:
    semantic_layer = semantic_layer or {}
    signal_map = {"green": 0.75, "yellow": 0.1, "red": -0.8}
    factors: list[NormalizedFactor] = []
    for domain in DOMAIN_KEYS:
        status = str((traffic_lights or {}).get(domain) or "").lower().strip()
        if not status:
            continue
        human = str(semantic_layer.get("practical_move") or semantic_layer.get("headline") or f"{domain} требует аккуратного режима.")
        factors.append(
            make_factor(
                factor_id=f"traffic:{domain}",
                family="lunar_windows",
                category="lunar_timing",
                domain=domain,
                label=f"{domain}:{status}",
                explanation_human=human,
                explanation_astro=f"Светофор {domain}: {status}",
                signal=signal_map.get(status, 0.0),
            )
        )
    return factors


def factors_from_semantic_layer(semantic_layer: dict[str, Any]) -> list[NormalizedFactor]:
    if not isinstance(semantic_layer, dict) or not semantic_layer:
        return []
    focus_key = str(semantic_layer.get("focus_key") or "").strip()
    domain = normalize_domain(FOCUS_KEY_DOMAIN.get(focus_key))
    return [
        make_factor(
            factor_id=f"semantic:{focus_key or 'headline'}",
            family="slow_background",
            category="background",
            domain=domain,
            label=str(semantic_layer.get("headline") or "Тема дня"),
            explanation_human=str(semantic_layer.get("practical_move") or semantic_layer.get("pacing") or "Собери день вокруг одного смыслового трека."),
            explanation_astro=str(semantic_layer.get("friction") or semantic_layer.get("tone") or ""),
            signal=0.45,
            metadata={"focus_key": focus_key},
        )
    ]


def build_normalized_factors(
    *,
    fast_hits: Iterable[dict[str, Any]] | None = None,
    traffic_lights: dict[str, Any] | None = None,
    semantic_layer: dict[str, Any] | None = None,
) -> list[NormalizedFactor]:
    semantic_layer = semantic_layer or {}
    factors = [
        *factors_from_fast_hits(fast_hits or []),
        *factors_from_traffic_lights(traffic_lights or {}, semantic_layer),
        *factors_from_semantic_layer(semantic_layer),
    ]
    unique: list[NormalizedFactor] = []
    seen: set[str] = set()
    for factor in factors:
        if factor.id in seen:
            continue
        seen.add(factor.id)
        unique.append(factor)
    return unique


def preprocess_factors_for_ranking(factors: Iterable[NormalizedFactor], *, weights: dict[str, float] | None = None) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    weights = weights or {}
    ranked: list[dict[str, Any]] = []
    domain_totals = {key: 0.0 for key in DOMAIN_KEYS}
    for factor in factors:
        weight = factor.weight * float(weights.get(factor.family, 1.0))
        score = clamp_signal(factor.signal * weight)
        domain_totals[factor.domain] += score
        ranked.append({"factor": factor, "score": score, "abs_score": abs(score)})
    ranked.sort(key=lambda item: (item["abs_score"], item["score"]), reverse=True)
    meta = {domain: {"signal": clamp_signal(total), "raw": total} for domain, total in domain_totals.items()}
    return ranked, meta


def select_explainability_factors(factors: Iterable[NormalizedFactor], *, limit: int = 5) -> list[dict[str, Any]]:
    ranked, _ = preprocess_factors_for_ranking(factors)
    selected: list[dict[str, Any]] = []
    for item in ranked[: max(0, limit)]:
        factor = item["factor"]
        selected.append(
            {
                "id": factor.id,
                "label": factor.label,
                "domain": factor.domain,
                "family": factor.family,
                "signal": round(item["score"], 3),
                "explanation_human": factor.explanation_human,
                "explanation_astro": factor.explanation_astro,
            }
        )
    return selected


def build_semantic_layer_from_factors(factors: Iterable[NormalizedFactor], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = dict(fallback or {})
    ranked, meta = preprocess_factors_for_ranking(factors)
    top = ranked[0]["factor"] if ranked else None
    if top is None:
        return fallback
    merged = dict(fallback)
    merged.update(
        {
            "headline": fallback.get("headline") or top.label,
            "practical_move": fallback.get("practical_move") or top.explanation_human,
            "tone": fallback.get("tone") or top.explanation_astro or top.explanation_human,
            "focus_key": fallback.get("focus_key") or top.metadata.get("focus_key") or top.domain,
            "factor_domains": {key: value["signal"] for key, value in meta.items()},
        }
    )
    return merged
