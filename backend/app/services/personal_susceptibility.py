from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_DOMAIN_ADJUSTMENTS = {
    "energy": 1.0,
    "money": 1.0,
    "love": 1.0,
    "focus": 1.0,
    "work_money": 1.0,
    "relationships": 1.0,
}

DEFAULT_CATEGORY_ADJUSTMENTS = {
    "fast_transits": 1.0,
    "lunar_windows": 1.0,
    "slow_background": 1.0,
    "natal_sensitivity": 1.0,
    "rare_boosters": 1.0,
    "weekly_triggers": 1.0,
    "period_theme": 1.0,
    "day_decomposition": 1.0,
}


@dataclass(frozen=True)
class SusceptibilityProfile:
    source: str
    version: str
    domain_adjustments: dict[str, float]
    category_adjustments: dict[str, float]

    def multiplier_for(self, *, domain: str | None = None, category: str | None = None) -> float:
        domain_value = self.domain_adjustments.get(str(domain or "").lower(), 1.0)
        category_value = self.category_adjustments.get(str(category or "").lower(), 1.0)
        value = domain_value * category_value
        return max(0.7, min(1.35, round(value, 3)))


def _normalize_adjustments(source: Any, defaults: dict[str, float]) -> dict[str, float]:
    payload = source if isinstance(source, dict) else {}
    normalized: dict[str, float] = {}
    for key, default in defaults.items():
        try:
            normalized[key] = float(payload.get(key, default))
        except (TypeError, ValueError):
            normalized[key] = default
    return normalized


def build_susceptibility_profile(user: Any | None) -> SusceptibilityProfile:
    raw = getattr(user, "susceptibility_profile", None) if user is not None else None
    raw = raw if isinstance(raw, dict) else {}
    return SusceptibilityProfile(
        source="user_profile" if raw else "deterministic_default",
        version=str(raw.get("version") or "v1"),
        domain_adjustments=_normalize_adjustments(raw.get("domains"), DEFAULT_DOMAIN_ADJUSTMENTS),
        category_adjustments=_normalize_adjustments(raw.get("categories"), DEFAULT_CATEGORY_ADJUSTMENTS),
    )


def attach_susceptibility(factors: list[dict[str, Any]], *, profile: SusceptibilityProfile) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for factor in factors:
        item = dict(factor)
        multiplier = profile.multiplier_for(domain=item.get("domain"), category=item.get("category") or item.get("family"))
        metadata = dict(item.get("metadata") or {})
        metadata.setdefault("susceptibility_profile_version", profile.version)
        metadata.setdefault("susceptibility_source", profile.source)
        item["metadata"] = metadata
        item["susceptibility_multiplier"] = multiplier
        enriched.append(item)
    return enriched


def calibration_entrypoints() -> dict[str, Any]:
    return {
        "feedback_sources": ["report_feedback", "admin_trace_review", "future_online_learning"],
        "storage": "users.susceptibility_profile",
        "defaults": "deterministic_v1",
        "next_step": "replace default multipliers with user feedback driven calibration jobs",
    }
