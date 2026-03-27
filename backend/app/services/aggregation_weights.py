# ############################################################################
# AI_HEADER: MODULE_AGGREGATION_WEIGHTS
# ROLE: Provide reusable weighting helper for DayBrief/WeekMap factors with explainability context.
# DEPENDENCIES: None (pure math helpers over supplied factor descriptors).
# GRACE_ANCHORS: [AGGREGATION_PIPELINE]
# ############################################################################

"""
Deterministic helper for applying canonical weight tables to heterogeneous factor inputs.

The module exposes `apply_weighted_factors`, which normalizes raw factor intensity per
profile ("day_brief" or "week_map"), enforces percentage budgets from Task.md, and returns
explainability-ready payloads (sorted factors, per-category impact, pipeline trace).
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


def _normalize_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def apply_weighted_factors(
    profile: str,
    factors: Iterable[dict[str, Any]],
    *,
    top_n: int = 4,
) -> dict[str, Any]:
    """Apply profile-specific weights to heterogeneous factor inputs.

    Args:
        profile: "day_brief" or "week_map" (see Task.md contracts).
        factors: Iterable of dicts with at least `category`, `label`, `weight` fields.
        top_n: Number of explainability-ready factors to return.

    Returns:
        Dict containing total score, enriched factor list, top factors and category pipeline.
    """

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

        base_weight = max(0.0, _normalize_float(raw_factor.get("weight")))
        confidence = max(0.0, min(1.0, _normalize_float(raw_factor.get("confidence"), default=1.0)))
        impact = base_weight * table[category] * confidence
        category_totals[category] += impact

        enriched = dict(raw_factor)
        enriched.update(
            {
                "category": category,
                "weight": round(base_weight, 4),
                "confidence": round(confidence, 3),
                "impact": round(impact, 4),
            }
        )
        normalized.append(enriched)

    normalized.sort(key=lambda item: item["impact"], reverse=True)
    total_score = sum(category_totals.values())
    if top_n < 1:
        top_n = 1

    top_factors: List[dict[str, Any]] = []
    for factor in normalized[:top_n]:
        impact_pct = 0.0 if total_score <= 0 else (factor["impact"] / total_score) * 100
        enriched_factor = dict(factor)
        enriched_factor["impact_pct"] = round(impact_pct, 1)
        top_factors.append(enriched_factor)

    pipeline = [
        {
            "category": category,
            "weight_share": round(weight, 2),
            "impact": round(category_totals.get(category, 0.0), 4),
        }
        for category, weight in table.items()
    ]

    return {
        "profile": profile_key,
        "total_score": round(total_score, 4),
        "factors": normalized,
        "top_factors": top_factors,
        "category_totals": category_totals,
        "pipeline": pipeline,
    }


__all__ = ["apply_weighted_factors", "DAY_BRIEF_WEIGHT_TABLE", "WEEK_MAP_WEIGHT_TABLE"]
