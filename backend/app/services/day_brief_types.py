"""Strict DayBrief DTO models aligned with the Day/Week contract packet."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class StrictModel(BaseModel):
    class Config:
        extra = "forbid"
        allow_population_by_field_name = True
        use_enum_values = True
        anystr_strip_whitespace = True


class LightStatus(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"




class ImpactLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class SignalSource(str, Enum):
    transit_natal = "transit_natal"
    transit_transit = "transit_transit"
    progressions = "progressions"
    directions = "directions"
    solar = "solar"
    profections = "profections"
    lunar = "lunar"
    mixed = "mixed"

class CtaType(str, Enum):
    open_week = "open_week"
    open_today = "open_today"
    ask_question = "ask_question"
    open_premium = "open_premium"
    open_history = "open_history"
    open_report = "open_report"
    custom = "custom"


class DayType(str, Enum):
    push = "push"
    balance = "balance"
    caution = "caution"
    deep_focus = "deep_focus"
    recovery = "recovery"


class DayFieldStatus(str, Enum):
    complete = "complete"
    failed = "failed"
    missing = "missing"


class DayBriefStatus(str, Enum):
    complete = "complete"
    partial = "partial"
    failed = "failed"


class DayHero(StrictModel):
    title: str = Field(..., min_length=4, max_length=140)
    subtitle: str = Field(..., min_length=4, max_length=240)
    day_type: DayType
    tone: str | None = Field(default=None, max_length=64)


class DayScoreKey(str, Enum):
    energy = "energy"
    money = "money"
    love = "love"
    focus = "focus"


class DayDomain(StrictModel):
    key: DayScoreKey
    title: str = Field(..., min_length=2, max_length=32)
    score_status: DayFieldStatus
    score: int | None = Field(default=None, ge=0, le=100)
    status: LightStatus | None = None
    description_status: DayFieldStatus
    description: str | None = Field(default=None, max_length=320)
    why_status: DayFieldStatus
    why_astro_text: str | None = Field(default=None, max_length=420)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    text_reason_codes: list[str] = Field(default_factory=list)
    text_composition_mode: str | None = Field(default=None, max_length=32)


class PremiumState(StrictModel):
    subscription_active: bool
    subscription_active_until: str | None = Field(default=None, max_length=32)
    days_left: int = Field(default=0, ge=0)
    show_upgrade_cta: bool = False
    show_resume_banner: bool = False


class CtaLink(StrictModel):
    type: CtaType
    label: str = Field(..., min_length=2, max_length=80)
    href: str = Field(..., min_length=1, max_length=200)


class CtaSet(StrictModel):
    primary: CtaLink | None = None
    secondary: CtaLink | None = None


class DayBrief(StrictModel):
    version: Literal["day_brief_canon_v1"] = "day_brief_canon_v1"
    status: DayBriefStatus = DayBriefStatus.complete
    date: date
    personalization_level: str = Field(..., min_length=1, max_length=64)
    hero: DayHero
    domains: dict[DayScoreKey, DayDomain]
    premium: PremiumState | None = None
    cta: CtaSet | None = None

    @validator("domains")
    def require_all_domains(cls, value: dict[DayScoreKey, DayDomain]) -> dict[DayScoreKey, DayDomain]:
        required = {DayScoreKey.energy, DayScoreKey.money, DayScoreKey.love, DayScoreKey.focus}
        if set(value.keys()) != required:
            raise ValueError("domains must contain exactly energy, money, love, focus")
        return value
