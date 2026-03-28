# ############################################################################
# AI_HEADER: MODULE_AGGREGATION_WEIGHTS
# ROLE: Provide reusable weighting helper for DayBrief/WeekMap factors with explainability context.
# DEPENDENCIES: None (pure math helpers over supplied factor descriptors).
# GRACE_ANCHORS: [AGGREGATION_PIPELINE]
# ############################################################################

"""
Deterministic helper for applying canonical weight tables to heterogeneous factor inputs.

Stage 4 introduces v2 calibration tables that adjust impact by:
- source family
- rarity bucket
- confidence
- timing precision

The module keeps the public `apply_weighted_factors(profile, factors, top_n=...)`
contract stable so day/week payload builders can adopt v2 weights without wider API
changes.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


DAY_BRIEF_WEIGHT_TABLE = {
    "fast_transits": 0.35,
    "lunar_windows": 0.25,
    "slow_background": 0.20,
    "natal_sensitivity": 0.15,
    "rare_boosters": 0.05,
}


WEEK_MAP_WEIGHT_TABLE = {
    "slow_background": 0.30,
    "weekly_triggers": 0.25,
    "period_theme": 0.20,
    "day_decomposition": 0.15,
    "rare_boosters": 0.10,
}


WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "day_brief": DAY_BRIEF_WEIGHT_TABLE,
    "week_map": WEEK_MAP_WEIGHT_TABLE,
}


WEIGHT_PROFILE_VERSIONS: dict[str, str] = {
    "day_brief": "v2",
    "week_map": "v2",
}


FAMILY_MULTIPLIERS: dict[str, float] = {
    "fast_transits": 1.08,
    "lunar_windows": 0.96,
    "slow_background": 0.92,
    "natal_sensitivity": 1.02,
    "rare_boosters": 1.18,
    "weekly_triggers": 1.04,
    "period_theme": 0.95,
    "day_decomposition": 0.98,
}


RARITY_MULTIPLIERS: dict[str, float] = {
    "common": 0.96,
    "uncommon": 1.0,
    "rare": 1.08,
    "signature": 1.15,
}


TIMING_PRECISION_MULTIPLIERS: dict[str, float] = {
    "broad": 0.9,
    "approximate": 0.97,
    "day": 1.0,
    "exact": 1.06,
}


DEFAULT_RARITY = "uncommon"
DEFAULT_TIMING_PRECISION = "day"


def _normalize_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_key(value: Any, *, default: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized or default


def _extract_rarity(raw_factor: dict[str, Any]) -> str:
    metadata = raw_factor.get("metadata") if isinstance(raw_factor.get("metadata"), dict) else {}
    rarity = (
        raw_factor.get("rarity")
        or raw_factor.get("rarity_bucket")
        or metadata.get("rarity")
        or metadata.get("rarity_bucket")
    )
    rarity_key = _normalize_key(rarity, default=DEFAULT_RARITY)
    return rarity_key if rarity_key in RARITY_MULTIPLIERS else DEFAULT_RARITY


def _extract_timing_precision(raw_factor: dict[str, Any]) -> str:
    metadata = raw_factor.get("metadata") if isinstance(raw_factor.get("metadata"), dict) else {}
    precision = (
        raw_factor.get("timing_precision")
        or raw_factor.get("timing")
        or metadata.get("timing_precision")
        or metadata.get("timing")
    )
    precision_key = _normalize_key(precision, default=DEFAULT_TIMING_PRECISION)
    return precision_key if precision_key in TIMING_PRECISION_MULTIPLIERS else DEFAULT_TIMING_PRECISION


def _family_multiplier(raw_factor: dict[str, Any], category: str) -> float:
    family = _normalize_key(raw_factor.get("family") or category, default=category)
    return FAMILY_MULTIPLIERS.get(family, 1.0)


def _susceptibility_multiplier(raw_factor: dict[str, Any]) -> float:
    susceptibility = _normalize_float(raw_factor.get("susceptibility_multiplier"), default=1.0)
    return max(0.7, min(1.35, susceptibility or 1.0))


def _build_support_trace(raw_factor: dict[str, Any], *, category: str, impact: float) -> dict[str, Any]:
    metadata = raw_factor.get("metadata") if isinstance(raw_factor.get("metadata"), dict) else {}
    supporting_factors = raw_factor.get("supporting_factors") or metadata.get("supporting_factors") or []
    source_models = raw_factor.get("source_models") or metadata.get("source_models") or []
    return {
        "factor_id": raw_factor.get("id"),
        "category": category,
        "impact": round(impact, 4),
        "family": _normalize_key(raw_factor.get("family") or category, default=category),
        "rarity": _extract_rarity(raw_factor),
        "timing_precision": _extract_timing_precision(raw_factor),
        "supporting_factors": supporting_factors,
        "source_models": source_models,
        "source": raw_factor.get("source") or "deterministic",
    }


def apply_weighted_factors(
    profile: str,
    factors: Iterable[dict[str, Any]],
    *,
    top_n: int = 4,
) -> dict[str, Any]:
    """Apply profile-specific weights to heterogeneous factor inputs."""

    profile_key = profile.strip().lower()
    if profile_key not in WEIGHT_PROFILES:
        raise ValueError(f"Unknown weight profile: {profile}")

    table = WEIGHT_PROFILES[profile_key]
    normalized: List[dict[str, Any]] = []
    category_totals: Dict[str, float] = {key: 0.0 for key in table}

    for raw_factor in factors:
        category = str(raw_factor.get("category") or "").strip()
        if category not in table:
            continue

        base_weight = max(0.0, _normalize_float(raw_factor.get("weight"), default=1.0))
        confidence = max(0.0, min(1.0, _normalize_float(raw_factor.get("confidence"), default=1.0)))
        family_multiplier = _family_multiplier(raw_factor, category)
        rarity = _extract_rarity(raw_factor)
        rarity_multiplier = RARITY_MULTIPLIERS[rarity]
        timing_precision = _extract_timing_precision(raw_factor)
        timing_multiplier = TIMING_PRECISION_MULTIPLIERS[timing_precision]
        susceptibility_multiplier = _susceptibility_multiplier(raw_factor)

        impact = (
            base_weight
            * table[category]
            * confidence
            * family_multiplier
            * rarity_multiplier
            * timing_multiplier
            * susceptibility_multiplier
        )
        category_totals[category] += impact

        enriched = dict(raw_factor)
        enriched.update(
            {
                "category": category,
                "weight": round(base_weight, 4),
                "confidence": round(confidence, 3),
                "impact": round(impact, 4),
                "weight_profile_version": WEIGHT_PROFILE_VERSIONS[profile_key],
                "family_multiplier": round(family_multiplier, 3),
                "rarity": rarity,
                "rarity_multiplier": round(rarity_multiplier, 3),
                "timing_precision": timing_precision,
                "timing_multiplier": round(timing_multiplier, 3),
                "susceptibility_multiplier": round(susceptibility_multiplier, 3),
                "support_trace": _build_support_trace(raw_factor, category=category, impact=impact),
            }
        )
        normalized.append(enriched)

    normalized.sort(key=lambda item: item["impact"], reverse=True)
    total_score = sum(category_totals.values())
    if top_n < 1:
        top_n = 1

    top_factors: List[dict[str, Any]] = []
    reliability_support: List[dict[str, Any]] = []
    for factor in normalized[:top_n]:
        impact_pct = 0.0 if total_score <= 0 else (factor["impact"] / total_score) * 100
        enriched_factor = dict(factor)
        enriched_factor["impact_pct"] = round(impact_pct, 1)
        top_factors.append(enriched_factor)
        reliability_support.append(dict(factor.get("support_trace") or {}))

    pipeline = [
        {
            "category": category,
            "weight_share": round(weight, 2),
            "impact": round(category_totals.get(category, 0.0), 4),
            "weight_profile_version": WEIGHT_PROFILE_VERSIONS[profile_key],
        }
        for category, weight in table.items()
    ]

    return {
        "profile": profile_key,
        "weight_profile_version": WEIGHT_PROFILE_VERSIONS[profile_key],
        "total_score": round(total_score, 4),
        "factors": normalized,
        "top_factors": top_factors,
        "category_totals": category_totals,
        "pipeline": pipeline,
        "reliability_support": reliability_support,
    }


__all__ = [
    "apply_weighted_factors",
    "DAY_BRIEF_WEIGHT_TABLE",
    "WEEK_MAP_WEIGHT_TABLE",
    "WEIGHT_PROFILE_VERSIONS",
]
