"""Validation helpers for DayBrief DTO assembly."""

from __future__ import annotations

from typing import Any, Mapping

from .day_brief_types import DayBrief


def validate_day_brief_payload(payload: Mapping[str, Any] | DayBrief) -> DayBrief:
    if isinstance(payload, DayBrief):
        return payload
    return DayBrief.model_validate(payload)


def serialize_day_brief(payload: Mapping[str, Any] | DayBrief) -> dict[str, Any]:
    return validate_day_brief_payload(payload).model_dump(mode="json", exclude_none=True)
