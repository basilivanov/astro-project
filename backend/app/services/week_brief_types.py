"""WeekBrief contract models mirrored from tmp/day_week_models.py for runtime use."""

from __future__ import annotations

from datetime import date, datetime
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


class FactorEntry(StrictModel):
    label: str = Field(..., min_length=2, max_length=80)
    explanation_human: str = Field(..., min_length=4, max_length=220)
    explanation_astro: str | None = Field(default=None, max_length=220)
    value: str | None = Field(default=None, max_length=64)


class ActionRiskItem(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    text: str = Field(..., min_length=8, max_length=220)
    factor_id: str | None = Field(default=None, max_length=64)
    impact: ImpactLevel | None = None
    timeframe: str | None = Field(default=None, max_length=64)
    why_text: str | None = Field(default=None, max_length=280)
    supporting_factors: list[FactorEntry] = Field(default_factory=list, max_length=4)


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
    reliability_support: list[str] = Field(default_factory=list, max_length=12)
    calibration: dict[str, object] | None = None


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


class WeekType(str, Enum):
    push = "push"
    balance = "balance"
    caution = "caution"
    deep_work = "deep_work"
    recovery = "recovery"
    transition = "transition"


class WeekStatus(str, Enum):
    ready = "ready"
    in_progress = "in_progress"
    error = "error"


class WeekSummary(StrictModel):
    headline: str = Field(..., min_length=8, max_length=160)
    subhead: str = Field(..., min_length=8, max_length=300)
    week_type: WeekType
    theme: str = Field(..., min_length=4, max_length=80)


class WeekDayMode(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class WeekDayCard(StrictModel):
    date: date
    weekday: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    mode: WeekDayMode
    score: int = Field(..., ge=0, le=100)
    headline: str = Field(..., min_length=4, max_length=100)
    lead: str | None = Field(default=None, max_length=180)
    practical: list[str] = Field(default_factory=list, max_length=3)
    supporting_factors: list[FactorEntry] = Field(default_factory=list, max_length=3)
    best_for: list[str] = Field(default_factory=list, max_length=4)
    avoid: list[str] = Field(default_factory=list, max_length=4)
    peak_window_label: str | None = Field(default=None, max_length=64)


class WeekDomainKey(str, Enum):
    work_money = "work_money"
    relationships = "relationships"
    energy = "energy"
    focus = "focus"


class WeekDomain(StrictModel):
    key: WeekDomainKey
    title: str = Field(..., min_length=2, max_length=48)
    status: LightStatus
    value: int = Field(..., ge=0, le=100)
    headline: str = Field(..., min_length=6, max_length=100)
    advice: str = Field(..., min_length=8, max_length=220)
    why_text: str | None = Field(default=None, max_length=280)
    supporting_factors: list[FactorEntry] = Field(default_factory=list, max_length=4)


class DeepSection(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    slug: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=2, max_length=80)
    summary: str | None = Field(default=None, max_length=240)
    body_markdown: str = Field(..., min_length=1)
    is_primary: bool = False
    order: int = Field(..., ge=0, le=100)


class ReportRef(StrictModel):
    report_id: str = Field(..., min_length=1, max_length=128)
    report_type: Literal["week_forecast"] = "week_forecast"
    source_status: str = Field(..., min_length=1, max_length=32)
    generated_at: datetime | None = None


class WeekBrief(StrictModel):
    version: Literal["week_brief_v1"] = "week_brief_v1"
    week_start: date
    week_end: date
    personalization_level: str = Field(..., min_length=1, max_length=64)
    fallback_mode: bool = False
    status: WeekStatus = WeekStatus.ready

    summary: WeekSummary
    day_cards: list[WeekDayCard] = Field(..., min_length=7, max_length=7)
    domains: list[WeekDomain] = Field(..., min_length=3, max_length=4)
    best_uses: list[ActionRiskItem] = Field(default_factory=list, max_length=8)
    risks: list[ActionRiskItem] = Field(default_factory=list, max_length=8)
    major_factors: list[PersonalizedFactor] = Field(default_factory=list, max_length=5)
    deep_sections: list[DeepSection] = Field(default_factory=list, max_length=16)
    explainability: Explainability

    premium: PremiumState | None = None
    cta: CtaSet | None = None
    report_ref: ReportRef | None = None

    @model_validator(mode="after")
    def validate_week_range(self) -> "WeekBrief":
        if self.week_end < self.week_start:
            raise ValueError("week_end must be on or after week_start")
        return self

    @field_validator("day_cards")
    @classmethod
    def day_cards_are_unique(cls, value: list[WeekDayCard]) -> list[WeekDayCard]:
        dates = [item.date for item in value]
        if len(dates) != len(set(dates)):
            raise ValueError("day_cards dates must be unique")
        return value

    @field_validator("domains")
    @classmethod
    def unique_week_domain_keys(cls, value: list[WeekDomain]) -> list[WeekDomain]:
        keys = [item.key for item in value]
        if len(keys) != len(set(keys)):
            raise ValueError("domains keys must be unique")
        return value


class WeekBriefEnvelope(StrictModel):
    status: WeekStatus
    data: WeekBrief | None = None
    message: str | None = Field(default=None, max_length=240)
    retry_after_seconds: int | None = Field(default=None, ge=1, le=120)

    @model_validator(mode="after")
    def validate_envelope(self) -> "WeekBriefEnvelope":
        if self.status == WeekStatus.ready and self.data is None:
            raise ValueError("data is required when status=ready")
        if self.status != WeekStatus.ready and self.data is not None:
            raise ValueError("data must be null unless status=ready")
        return self


__all__ = [
    "SignalSource",
    "WeekBrief",
    "WeekBriefEnvelope",
    "WeekDomainKey",
    "WeekStatus",
    "WeekType",
]
