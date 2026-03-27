"""Strict DayBrief DTO models aligned with the Day/Week contract packet."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class LightStatus(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class ImpactLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class TimingPrecision(str, Enum):
    exact = "exact"
    approximate = "approximate"


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


class WindowMode(str, Enum):
    best = "best"
    caution = "caution"
    soft = "soft"


class DaySummary(StrictModel):
    headline: str = Field(..., min_length=8, max_length=140)
    subhead: str = Field(..., min_length=8, max_length=240)
    day_type: DayType
    tone: str | None = Field(default=None, max_length=64)


class DayContext(StrictModel):
    moon_sign: str | None = Field(default=None, max_length=32)
    moon_phase: str | None = Field(default=None, max_length=64)
    moon_emoji: str | None = Field(default=None, max_length=8)
    aspects_count: int | None = Field(default=None, ge=0, le=50)
    label: str | None = Field(default=None, max_length=120)


class DayScoreKey(str, Enum):
    energy = "energy"
    money = "money"
    love = "love"
    focus = "focus"


class DayScore(StrictModel):
    key: DayScoreKey
    title: str = Field(..., min_length=2, max_length=32)
    value: int = Field(..., ge=0, le=100)
    status: LightStatus
    advice: str = Field(..., min_length=6, max_length=220)


class DayWindow(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    label: str = Field(..., min_length=2, max_length=48)
    mode: WindowMode
    advice: str = Field(..., min_length=6, max_length=200)

    @staticmethod
    def _to_minutes(value: str) -> int:
        hh, mm = value.split(":")
        return int(hh) * 60 + int(mm)

    @model_validator(mode="after")
    def validate_range(self) -> "DayWindow":
        if self._to_minutes(self.end) <= self._to_minutes(self.start):
            raise ValueError("DayWindow.end must be later than DayWindow.start")
        return self


class ActionRiskItem(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    text: str = Field(..., min_length=8, max_length=220)
    factor_id: str | None = Field(default=None, max_length=64)
    impact: ImpactLevel | None = None
    timeframe: str | None = Field(default=None, max_length=64)


class PersonalizedFactor(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=4, max_length=80)
    impact: ImpactLevel
    category: str | None = Field(default=None, max_length=64)
    explanation_human: str = Field(..., min_length=10, max_length=260)
    explanation_astro: str | None = Field(default=None, max_length=260)
    source_models: list[SignalSource] = Field(default_factory=list, max_length=8)
    weight: float | None = Field(default=None, ge=0.0, le=1.0)


class Explainability(StrictModel):
    confidence: float = Field(..., ge=0.0, le=1.0)
    birth_time_used: bool
    factor_count: int = Field(..., ge=0, le=500)
    timing_precision: TimingPrecision | None = None
    top_signal_source: SignalSource | None = None
    explanation_depth: Literal["minimal", "standard", "full"] | None = None


class PremiumState(StrictModel):
    subscription_active: bool
    subscription_active_until: date | None = None
    days_left: int | None = Field(default=None, ge=0, le=3650)
    show_upgrade_cta: bool = False
    show_resume_banner: bool = False

    @model_validator(mode="after")
    def validate_consistency(self) -> "PremiumState":
        if self.subscription_active is False and self.days_left not in (None, 0):
            raise ValueError("days_left must be 0 or null when subscription_active is false")
        return self


class CtaLink(StrictModel):
    type: CtaType = CtaType.custom
    label: str = Field(..., min_length=2, max_length=40)
    href: str = Field(..., min_length=1, max_length=200)


class CtaSet(StrictModel):
    primary: CtaLink | None = None
    secondary: CtaLink | None = None


class LegacyTrafficLights(StrictModel):
    health: LightStatus | None = None
    money: LightStatus | None = None
    love: LightStatus | None = None


class LegacyFastHit(StrictModel):
    type: str | None = Field(default=None, max_length=48)
    summary: str | None = Field(default=None, max_length=240)
    transit: str | None = Field(default=None, max_length=64)
    natal: str | None = Field(default=None, max_length=64)


class LegacyDayFeedCompat(StrictModel):
    general_vibe: str | None = Field(default=None, max_length=400)
    moon_sign: str | None = Field(default=None, max_length=32)
    moon_phase: str | None = Field(default=None, max_length=64)
    moon_emoji: str | None = Field(default=None, max_length=8)
    aspects_count: int | None = Field(default=None, ge=0, le=50)
    traffic_lights: LegacyTrafficLights | None = None
    fast_hits: list[LegacyFastHit] = Field(default_factory=list)


class DayBrief(StrictModel):
    version: Literal["day_brief_v1"] = "day_brief_v1"
    date: date
    personalization_level: str = Field(..., min_length=1, max_length=64)
    fallback_mode: bool = False

    summary: DaySummary
    context: DayContext
    scores: list[DayScore] = Field(..., min_length=3, max_length=4)
    windows: list[DayWindow] = Field(default_factory=list, max_length=8)
    best_uses: list[ActionRiskItem] = Field(default_factory=list, max_length=6)
    risks: list[ActionRiskItem] = Field(default_factory=list, max_length=6)
    personalized_factors: list[PersonalizedFactor] = Field(default_factory=list, max_length=5)
    explainability: Explainability

    premium: PremiumState | None = None
    cta: CtaSet | None = None
    legacy: LegacyDayFeedCompat | None = None

    @field_validator("scores")
    @classmethod
    def unique_day_score_keys(cls, value: list[DayScore]) -> list[DayScore]:
        keys = [item.key for item in value]
        if len(keys) != len(set(keys)):
            raise ValueError("scores keys must be unique")
        return value
