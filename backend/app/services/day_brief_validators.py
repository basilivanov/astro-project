"""Validation helpers for DayBrief DTO assembly."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from pydantic import ValidationError

from .day_brief_types import DayBrief


_SUMMARY_KEYS = ("headline", "subhead", "day_type", "tone")
_CONTEXT_KEYS = ("moon_sign", "moon_phase", "moon_emoji", "aspects_count", "label")
_EXPLAINABILITY_KEYS = (
    "confidence",
    "birth_time_used",
    "factor_count",
    "timing_precision",
    "top_signal_source",
    "explanation_depth",
    "reliability_support",
    "calibration",
    "selected_factors",
    "selected_factors_support",
)
_LEGACY_KEYS = (
    "general_vibe",
    "moon_sign",
    "moon_phase",
    "moon_emoji",
    "aspects_count",
    "traffic_lights",
    "fast_hits",
)
_DAY_SCORE_KEYS = ("key", "title", "value", "status", "advice")
_DAY_WINDOW_KEYS = ("id", "start", "end", "label", "mode", "advice")
_ACTION_RISK_KEYS = ("id", "text", "factor_id", "impact", "timeframe")
_PERSONALIZED_FACTOR_KEYS = (
    "id",
    "label",
    "impact",
    "category",
    "explanation_human",
    "explanation_astro",
    "source_models",
    "weight",
)
_PREMIUM_KEYS = (
    "subscription_active",
    "subscription_active_until",
    "days_left",
    "show_upgrade_cta",
    "show_resume_banner",
)
_CTA_LINK_KEYS = ("type", "label", "href")
_CTA_KEYS = ("primary", "secondary")
_TRAFFIC_LIGHT_KEYS = ("health", "money", "love")
_FAST_HIT_KEYS = ("type", "summary", "transit", "natal")


def _copy_known_keys(payload: Mapping[str, Any] | None, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    return {key: deepcopy(payload[key]) for key in keys if key in payload}


def _repair_day_brief_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    repaired = _copy_known_keys(
        payload,
        (
            "version",
            "date",
            "personalization_level",
            "fallback_mode",
            "summary",
            "context",
            "scores",
            "windows",
            "best_uses",
            "risks",
            "personalized_factors",
            "explainability",
            "premium",
            "cta",
            "legacy",
        ),
    )
    repaired["summary"] = _copy_known_keys(payload.get("summary"), _SUMMARY_KEYS)
    repaired["context"] = _copy_known_keys(payload.get("context"), _CONTEXT_KEYS)
    repaired["scores"] = [
        _copy_known_keys(item, _DAY_SCORE_KEYS)
        for item in (payload.get("scores") if isinstance(payload.get("scores"), list) else [])
        if isinstance(item, Mapping)
    ]
    repaired["windows"] = [
        _copy_known_keys(item, _DAY_WINDOW_KEYS)
        for item in (payload.get("windows") if isinstance(payload.get("windows"), list) else [])
        if isinstance(item, Mapping)
    ]
    repaired["best_uses"] = [
        _copy_known_keys(item, _ACTION_RISK_KEYS)
        for item in (payload.get("best_uses") if isinstance(payload.get("best_uses"), list) else [])
        if isinstance(item, Mapping)
    ]
    repaired["risks"] = [
        _copy_known_keys(item, _ACTION_RISK_KEYS)
        for item in (payload.get("risks") if isinstance(payload.get("risks"), list) else [])
        if isinstance(item, Mapping)
    ]
    repaired["personalized_factors"] = [
        _copy_known_keys(item, _PERSONALIZED_FACTOR_KEYS)
        for item in (payload.get("personalized_factors") if isinstance(payload.get("personalized_factors"), list) else [])
        if isinstance(item, Mapping)
    ]
    repaired["explainability"] = _copy_known_keys(payload.get("explainability"), _EXPLAINABILITY_KEYS)
    if "premium" in repaired:
        premium = _copy_known_keys(payload.get("premium"), _PREMIUM_KEYS)
        repaired["premium"] = premium or None
    if "cta" in repaired:
        cta = _copy_known_keys(payload.get("cta"), _CTA_KEYS)
        if "primary" in cta:
            cta["primary"] = _copy_known_keys(cta.get("primary"), _CTA_LINK_KEYS)
        if "secondary" in cta:
            cta["secondary"] = _copy_known_keys(cta.get("secondary"), _CTA_LINK_KEYS)
        repaired["cta"] = cta
    if "legacy" in repaired:
        legacy = _copy_known_keys(payload.get("legacy"), _LEGACY_KEYS)
        if "traffic_lights" in legacy:
            legacy["traffic_lights"] = _copy_known_keys(legacy.get("traffic_lights"), _TRAFFIC_LIGHT_KEYS)
        legacy["fast_hits"] = [
            _copy_known_keys(item, _FAST_HIT_KEYS)
            for item in (legacy.get("fast_hits") if isinstance(legacy.get("fast_hits"), list) else [])
            if isinstance(item, Mapping)
        ]
        repaired["legacy"] = legacy
    return repaired


def validate_day_brief_payload(payload: Mapping[str, Any] | DayBrief) -> DayBrief:
    if isinstance(payload, DayBrief):
        return payload
    try:
        return DayBrief.model_validate(payload)
    except ValidationError:
        repaired = _repair_day_brief_payload(payload)
        return DayBrief.model_validate(repaired)


def serialize_day_brief(payload: Mapping[str, Any] | DayBrief) -> dict[str, Any]:
    return validate_day_brief_payload(payload).model_dump(mode="json", exclude_none=True)
