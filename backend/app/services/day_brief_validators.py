"""Validation helpers for strict DayBrief DTO assembly."""

# ############################################################################
# AI_HEADER: MODULE_DAY_BRIEF_VALIDATORS
# ROLE: Repair and validate canonical DayBrief DTO payloads without widening business semantics.
# DEPENDENCIES: pydantic, backend.app.services.day_brief_types.
# GRACE_ANCHORS: [DAY_BRIEF_VALIDATOR_KEYS, DAY_BRIEF_VALIDATOR_REPAIR, DAY_BRIEF_VALIDATOR_ENTRYPOINTS]
# ############################################################################

# START_MODULE_CONTRACT: M-DAY-BRIEF-SERVICE
# purpose: Validate canonical DayBrief payloads and trim unknown nested keys without contract drift.
# owns:
#   - backend/app/services/day_brief_validators.py
# inputs:
#   - mapping payloads or DayBrief model instances
# outputs:
#   - validated DayBrief models
#   - serialized canonical DayBrief dict payloads
# dependencies:
#   - backend.app.services.day_brief_types.DayBrief
# side_effects:
#   - none; validation and repair are pure transformations
# invariants:
#   - non-canonical DayBrief versions fail loudly
#   - unknown nested keys may be dropped, but required canonical keys remain enforced
# non_goals:
#   - changing DayBrief DTO semantics
#   - accepting legacy alternate versions
# END_MODULE_CONTRACT: M-DAY-BRIEF-SERVICE

# START_MODULE_MAP: M-DAY-BRIEF-SERVICE
# public_entrypoints:
#   - validate_day_brief_payload
#   - serialize_day_brief
# semantic_blocks:
#   - DAY_BRIEF_VALIDATOR_KEYS: canonical nested key allowlists
#   - DAY_BRIEF_VALIDATOR_REPAIR: bounded nested repair helpers
#   - DAY_BRIEF_VALIDATOR_ENTRYPOINTS: exported validation and serialization contracts
# owned_tests:
#   - tests/test_day_brief.py
#   - tests/test_day_brief_schema.py
# adjacent_modules:
#   - backend/app/services/day_brief.py
#   - backend/app/services/day_brief_types.py
# END_MODULE_MAP: M-DAY-BRIEF-SERVICE

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from pydantic import ValidationError

from .day_brief_types import DayBrief

# START_BLOCK: DAY_BRIEF_VALIDATOR_KEYS
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
# END_BLOCK: DAY_BRIEF_VALIDATOR_KEYS


# START_BLOCK: DAY_BRIEF_VALIDATOR_REPAIR
def _copy_known_keys(payload: Mapping[str, Any] | None, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    return {key: deepcopy(payload[key]) for key in keys if key in payload}

# START_CONTRACT: FN-REPAIR-DAY-BRIEF-PAYLOAD
# purpose: Strip unknown nested keys while preserving canonical DayBrief fields.
# inputs:
#   - payload: mapping candidate for canonical DayBrief validation
# returns: repaired payload constrained to known DayBrief keys
# invariants:
#   - never introduces new keys
#   - never upgrades non-canonical version values
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
# END_CONTRACT: FN-REPAIR-DAY-BRIEF-PAYLOAD
# END_BLOCK: DAY_BRIEF_VALIDATOR_REPAIR


# START_BLOCK: DAY_BRIEF_VALIDATOR_ENTRYPOINTS
# START_CONTRACT: FN-VALIDATE-DAY-BRIEF-PAYLOAD
# purpose: Validate canonical DayBrief payloads and apply bounded repair on unknown nested keys.
# inputs:
#   - payload: mapping or DayBrief model candidate
# returns: validated DayBrief model
# invariants:
#   - alternate versions are rejected
#   - required canonical fields remain enforced after repair
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
# END_CONTRACT: FN-VALIDATE-DAY-BRIEF-PAYLOAD


# START_CONTRACT: FN-SERIALIZE-DAY-BRIEF
# purpose: Serialize a validated DayBrief payload into the canonical wire shape.
# inputs:
#   - payload: mapping or DayBrief model candidate
# returns: canonical dict excluding None values
def serialize_day_brief(payload: Mapping[str, Any] | DayBrief) -> dict[str, Any]:
    return validate_day_brief_payload(payload).dict(exclude_none=True)
# END_CONTRACT: FN-SERIALIZE-DAY-BRIEF
# END_BLOCK: DAY_BRIEF_VALIDATOR_ENTRYPOINTS
