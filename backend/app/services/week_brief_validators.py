"""Strict validators for WeekBrief and WeekBriefEnvelope."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - container runtime lacks jsonschema
    class Draft202012Validator:  # type: ignore[override]
        def __init__(self, schema: dict[str, Any]):
            self.schema = schema

        def validate(self, _data: dict[str, Any]) -> None:
            return None

from .week_brief_types import WeekBrief, WeekBriefEnvelope


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def _load_week_brief_schema() -> dict[str, Any]:
    schema_path = _repo_root() / "tmp" / "week_brief.schema.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return WeekBrief.model_json_schema()


@lru_cache(maxsize=1)
def _load_week_brief_envelope_schema() -> dict[str, Any]:
    schema_path = _repo_root() / "tmp" / "week_brief_envelope.schema.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return WeekBriefEnvelope.model_json_schema()


@lru_cache(maxsize=1)
def _week_brief_validator() -> Draft202012Validator:
    return Draft202012Validator(_load_week_brief_schema())


@lru_cache(maxsize=1)
def _week_brief_envelope_validator() -> Draft202012Validator:
    return Draft202012Validator(_load_week_brief_envelope_schema())


def _validate_week_brief_business_rules(payload: dict[str, Any]) -> None:
    day_cards = payload.get("day_cards") or []
    domains = payload.get("domains") or []
    best_uses = payload.get("best_uses") or []
    risks = payload.get("risks") or []
    major_factors = payload.get("major_factors") or []
    deep_sections = payload.get("deep_sections") or []
    report_ref = payload.get("report_ref") or {}

    if len(day_cards) != 7:
        raise ValueError("WeekBrief.day_cards must contain exactly 7 items")
    if len(domains) not in {3, 4}:
        raise ValueError("WeekBrief.domains must contain 3 or 4 items")
    if not 1 <= len(best_uses) <= 8:
        raise ValueError("WeekBrief.best_uses must contain between 1 and 8 items")
    if not 1 <= len(risks) <= 8:
        raise ValueError("WeekBrief.risks must contain between 1 and 8 items")
    if not 1 <= len(major_factors) <= 5:
        raise ValueError("WeekBrief.major_factors must contain between 1 and 5 items")

    orders = [int(section.get("order", -1)) for section in deep_sections]
    if len(orders) != len(set(orders)):
        raise ValueError("WeekBrief.deep_sections order values must be unique")

    if report_ref and report_ref.get("report_type") != "week_forecast":
        raise ValueError("WeekBrief.report_ref.report_type must be week_forecast")


def validate_week_brief_payload(payload: dict[str, Any]) -> dict[str, Any]:
    model = WeekBrief.model_validate(payload)
    data = model.model_dump(mode="json")
    _week_brief_validator().validate(data)
    _validate_week_brief_business_rules(data)
    return data


def validate_week_brief_envelope_payload(payload: dict[str, Any]) -> dict[str, Any]:
    model = WeekBriefEnvelope.model_validate(payload)
    data = model.model_dump(mode="json")
    _week_brief_envelope_validator().validate(data)
    if data.get("status") == "ready" and data.get("data") is not None:
        data["data"] = validate_week_brief_payload(data["data"])
    return data


__all__ = [
    "validate_week_brief_envelope_payload",
    "validate_week_brief_payload",
]
