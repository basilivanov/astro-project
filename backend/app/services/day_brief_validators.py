"""Validation helpers for strict DayBrief DTO assembly."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from pydantic import ValidationError

from .day_brief_types import DayBrief

_DAY_HERO_KEYS = ("title", "subtitle", "day_type", "tone")
_DAY_DOMAIN_KEYS = (
    "key",
    "title",
    "score_status",
    "score",
    "status",
    "description_status",
    "description",
    "why_status",
    "why_astro_text",
    "evidence_refs",
    "text_reason_codes",
    "text_composition_mode",
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


def _copy_known_keys(payload: Mapping[str, Any] | None, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    return {key: deepcopy(payload[key]) for key in keys if key in payload}


def _repair_day_brief_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    repaired = _copy_known_keys(
        payload,
        ("version", "status", "date", "personalization_level", "hero", "domains", "premium", "cta"),
    )
    repaired["hero"] = _copy_known_keys(payload.get("hero"), _DAY_HERO_KEYS)
    domains = payload.get("domains") if isinstance(payload.get("domains"), Mapping) else {}
    repaired["domains"] = {
        key: _copy_known_keys(value, _DAY_DOMAIN_KEYS)
        for key, value in domains.items()
        if isinstance(value, Mapping)
    }
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
    return repaired


def validate_day_brief_payload(payload: Mapping[str, Any] | DayBrief) -> DayBrief:
    if isinstance(payload, DayBrief):
        return payload
    if not isinstance(payload, Mapping):
        return DayBrief.parse_obj(payload)

    # Canonical Day no longer accepts alternate versions. Unknown nested keys are repaired,
    # but a non-canonical version must fail loudly instead of slipping through legacy semantics.
    version = payload.get("version")
    if version not in (None, "day_brief_canon_v1"):
        return DayBrief.parse_obj(payload)
    try:
        return DayBrief.parse_obj(payload)
    except ValidationError:
        repaired = _repair_day_brief_payload(payload)
        return DayBrief.parse_obj(repaired)


def serialize_day_brief(payload: Mapping[str, Any] | DayBrief) -> dict[str, Any]:
    return validate_day_brief_payload(payload).dict(exclude_none=True)
