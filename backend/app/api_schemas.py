# START_MODULE_CONTRACT: M-API-GATEWAY-SCHEMAS
# purpose: Own API gateway Pydantic DTOs extracted from backend.app.main without schema drift.
# owns:
#   - backend/app/api_schemas.py
# inputs:
#   - FastAPI request payloads and route response data assembled by backend.app.main
# outputs:
#   - validated request DTOs and serializable response DTOs with unchanged fields/defaults
# dependencies:
#   - pydantic for DTO validation
#   - backend.app.services.one_off_entitlements.normalize_report_type for existing report-type normalization
# invariants:
#   - DTO field names, defaults, validators, and nested response structure remain identical to pre-extraction main.py declarations
#   - backend.app.main re-exports these names for monkeypatch/import compatibility
# non_goals:
#   - moving endpoints or changing auth/billing/report behavior
# END_MODULE_CONTRACT: M-API-GATEWAY-SCHEMAS

# START_MODULE_MAP: M-API-GATEWAY-SCHEMAS
# public_entrypoints:
#   - Pydantic DTO classes imported and re-exported by backend.app.main
# semantic_blocks:
#   - API_SCHEMA_IMPORTS: schema dependencies only
#   - API_SCHEMA_DTOS: extracted request/response DTO contracts
# owned_tests:
#   - tests/test_api_contract_wave1.py
#   - tests/test_report_contract.py
# adjacent_modules:
#   - backend/app/main.py
# END_MODULE_MAP: M-API-GATEWAY-SCHEMAS

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field, validator

from .services.day_brief_types import DayBrief as DayBriefDTO
from .services.one_off_entitlements import normalize_report_type

# START_BLOCK: API_SCHEMA_DTOS
# START_CONTRACT: API-SCHEMA-DTO-COMPAT
class ChartLocationOut(BaseModel):
    """
    # PURPOSE: Describe chart location data for API responses.
    # INPUT: name, latitude, longitude, timezone.
    # OUTPUT: Serializable location object.
    # CONTEXT: Used in all chart responses.
    """

    name: str
    latitude: float
    longitude: float
    timezone: str

class PositionOut(BaseModel):
    """
    # PURPOSE: Describe a celestial position in a chart.
    # INPUT: name, longitude, latitude, sign, sign_degree, is_retrograde.
    # OUTPUT: Serializable position object.
    # CONTEXT: Included in the positions array.
    """

    name: str
    key: Optional[str] = None
    raw_name: Optional[str] = None
    longitude: float
    latitude: float
    sign: str
    sign_degree: float
    is_retrograde: bool

class HouseCuspOut(BaseModel):
    """
    # PURPOSE: Describe a house cusp.
    # INPUT: house, longitude, sign, sign_degree.
    # OUTPUT: Serializable cusp object.
    # CONTEXT: Returned together with house_system.
    """

    house: int
    longitude: float
    sign: str
    sign_degree: float

class FixedStarOut(BaseModel):
    """
    # PURPOSE: Describe a fixed-star conjunction.
    # INPUT: star, planet, orb, star_lon.
    # OUTPUT: Serializable conjunction object.
    # CONTEXT: Returned optionally for natal/transit charts.
    """

    star: str
    planet: Optional[str] = None
    name: Optional[str] = None
    point: Optional[str] = None
    raw_point: Optional[str] = None
    orb: Optional[float] = None
    star_lon: Optional[float] = None
    sign: Optional[str] = None

class DispositorLinkOut(BaseModel):
    """
    # PURPOSE: Describe a single dispositor link.
    # INPUT: planet, sign, dispositor.
    # OUTPUT: Serializable dispositor link object.
    # CONTEXT: Nested under ChartResponse.dispositor_summary.
    """

    planet: str
    sign: Optional[str] = None
    dispositor: str

class DispositorLoopOut(BaseModel):
    """
    # PURPOSE: Describe a final dispositor loop.
    # INPUT: type, planets.
    # OUTPUT: Serializable dispositor loop object.
    # CONTEXT: Nested under ChartResponse.dispositor_summary.
    """

    type: str
    planets: list[str] = Field(default_factory=list)

class DispositorSummaryOut(BaseModel):
    """
    # PURPOSE: Describe structured dispositor summary data.
    # INPUT: version, summary, links, loops.
    # OUTPUT: Serializable dispositor summary object.
    # CONTEXT: Returned alongside chart data for report consumers.
    """

    version: str
    summary: str = ""
    links: list[DispositorLinkOut] = Field(default_factory=list)
    loops: list[DispositorLoopOut] = Field(default_factory=list)

class NatalRequest(BaseModel):
    """
    # PURPOSE: Input payload for natal chart calculation.
    # INPUT: name, birth_date, birth_location, house_system.
    # OUTPUT: Validated request object.
    # CONTEXT: Used by /api/engine/natal.
    """

    name: str = Field(..., min_length=1)
    birth_date: str = Field(..., min_length=4)
    birth_location: str = Field(..., min_length=2)
    house_system: Optional[str] = None
    include_fixed_stars: bool = True
    fixed_star_orb: float = 1.0

class TransitRequest(BaseModel):
    """
    # PURPOSE: Input payload for transit chart calculation.
    # INPUT: date, location, house_system.
    # OUTPUT: Validated request object.
    # CONTEXT: Used by /api/engine/transit.
    """

    date: str = Field(..., min_length=4)
    location: str = Field(..., min_length=2)
    house_system: Optional[str] = None
    include_fixed_stars: bool = False
    fixed_star_orb: float = 1.0

class ChartResponse(BaseModel):
    """
    # PURPOSE: Unified response with chart data.
    # INPUT: chart_type, name, datetime_utc, location, positions, houses.
    # OUTPUT: Serializable chart object.
    # CONTEXT: Returned by /api/engine/* endpoints.
    """

    chart_type: str
    name: Optional[str]
    datetime_utc: str
    datetime_local: Optional[str]
    location: ChartLocationOut
    house_system: str
    houses: list[HouseCuspOut]
    positions: list[PositionOut]
    fixed_stars: list[FixedStarOut] = Field(default_factory=list)
    dispositor_summary: Optional[DispositorSummaryOut] = None

class SectionInput(BaseModel):
    """
    # PURPOSE: Define a report section to generate.
    # INPUT: section_id, title, prompt.
    # OUTPUT: Validated section input.
    # CONTEXT: Used by the report workflow endpoint.
    """

    section_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)

class SectionResultOut(BaseModel):
    """
    # PURPOSE: Describe a generated section result.
    # INPUT: section_id, title, content.
    # OUTPUT: Serializable section result.
    # CONTEXT: Returned by workflow response.
    """

    section_id: str
    title: str
    content: str

class ReportWorkflowRequest(BaseModel):
    """
    # PURPOSE: Run an end-to-end report generation workflow.
    # INPUT: client_name, birth_date, birth_location, report_type, sections.
    # OUTPUT: Validated workflow request.
    # CONTEXT: Used by /api/workflows/report.
    """

    client_id: Optional[str] = None
    client_name: Optional[str] = None
    client_note: Optional[str] = None
    question: Optional[str] = None
    birth_date: Optional[str] = None
    birth_location: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    birth_timezone: Optional[str] = None
    birth_place_id: Optional[str] = None
    partner_name: Optional[str] = None
    partner_birth_date: Optional[str] = None
    partner_birth_location: Optional[str] = None
    partner_birth_lat: Optional[float] = None
    partner_birth_lon: Optional[float] = None
    partner_birth_timezone: Optional[str] = None
    partner_birth_place_id: Optional[str] = None
    solar_current_location: Optional[str] = None
    solar_current_lat: Optional[float] = None
    solar_current_lon: Optional[float] = None
    solar_current_timezone: Optional[str] = None
    solar_current_place_id: Optional[str] = None
    solar_next_location: Optional[str] = None
    solar_next_lat: Optional[float] = None
    solar_next_lon: Optional[float] = None
    solar_next_timezone: Optional[str] = None
    solar_next_place_id: Optional[str] = None
    report_type: str = "natal_master"
    birth_time_known: bool = True
    house_system: Optional[str] = None
    include_fixed_stars: bool = True
    fixed_star_orb: float = 1.0
    sections: Optional[List[SectionInput]] = None
    llm_mode: Optional[str] = None
    is_test: bool = False

    @validator("report_type", pre=True)
    @classmethod
    def normalize_report_type_value(cls, value: Optional[str]) -> Optional[str]:
        return normalize_report_type(value)

class ReportWorkflowResponse(BaseModel):
    """
    # PURPOSE: Return the workflow result with sections and chart.
    # INPUT: report_id, client_id, sections, chart.
    # OUTPUT: Serializable workflow response.
    # CONTEXT: Returned by /api/workflows/report.
    """

    report_id: str
    client_id: str
    sections: List[SectionResultOut]
    chart: ChartResponse

class ReportWorkflowStartResponse(BaseModel):
    """
    # PURPOSE: Return the queued report metadata.
    # INPUT: report_id, client_id, status.
    # OUTPUT: Serializable start response.
    # CONTEXT: Returned by /api/workflows/report/async.
    """

    report_id: str
    client_id: str
    status: str

class ReportRegenerateResponse(BaseModel):
    """
    # PURPOSE: Return updated report content after regeneration.
    # INPUT: report_id, sections.
    # OUTPUT: Serializable regeneration response.
    # CONTEXT: Returned by admin regeneration endpoints.
    """

    report_id: str
    status: str
    sections: List[SectionResultOut]

class AdminClientReportOut(BaseModel):
    """
    # PURPOSE: Describe the latest report for a client.
    # INPUT: id, report_type, status, created_at.
    # OUTPUT: Serializable report summary.
    # CONTEXT: Used in admin client listings.
    """

    id: str
    report_type: str
    status: str
    created_at: str

class AdminClientOut(BaseModel):
    """
    # PURPOSE: Describe client details for admin listings.
    # INPUT: client metadata and report aggregates.
    # OUTPUT: Serializable client summary.
    # CONTEXT: Returned by /api/admin/clients.
    """

    id: str
    full_name: str
    email: Optional[str]
    notes: Optional[str]
    birth_datetime: Optional[str]
    birth_time_known: bool
    birth_location: Optional[str]
    birth_lat: Optional[float]
    birth_lon: Optional[float]
    birth_timezone: Optional[str]
    birth_place_id: Optional[str]
    created_at: str
    report_count: int
    last_report: Optional[AdminClientReportOut] = None

class AdminClientCreateRequest(BaseModel):
    """
    # PURPOSE: Payload for creating a new client via admin API.
    """
    client_name: str
    birth_date: str
    birth_time_known: bool = True
    birth_location: str
    client_note: Optional[str] = None
    email: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    birth_timezone: Optional[str] = None
    birth_place_id: Optional[str] = None
    user_id: Optional[str] = None
    is_test: bool = False

class AdminReportOut(BaseModel):
    """
    # PURPOSE: Describe report summary data for admin listings.
    # INPUT: report metadata, client data, chunk stats.
    # OUTPUT: Serializable report summary.
    # CONTEXT: Returned by /api/admin/reports.
    """

    id: str
    report_type: str
    status: str
    paid: bool
    error_message: Optional[str] = None
    error_at: Optional[str] = None
    created_at: str
    updated_at: str
    client_id: str
    client_name: str
    chunk_count: int

class AdminReportChunkOut(BaseModel):
    """
    # PURPOSE: Describe a single report chunk for admin review.
    # INPUT: chunk metadata and content.
    # OUTPUT: Serializable chunk summary.
    # CONTEXT: Returned by /api/admin/reports/{id}.
    """

    id: str
    section: str
    title: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    error_at: Optional[str] = None
    order_index: int
    content: Optional[str]
    content_html: Optional[str] = None
    created_at: str

class AdminReportRunOut(BaseModel):
    """
    # PURPOSE: Describe a single report run for admin review.
    # INPUT: run metadata and error info.
    # OUTPUT: Serializable run summary.
    # CONTEXT: Returned by /api/admin/reports/{id}.
    """

    id: str
    status: str
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    created_at: str

class AdminReportDetailOut(BaseModel):
    """
    # PURPOSE: Describe report details for admin review.
    # INPUT: report summary, chunks, markdown.
    # OUTPUT: Serializable report detail.
    # CONTEXT: Returned by /api/admin/reports/{id}.
    """

    report: AdminReportOut
    chunks: List[AdminReportChunkOut]
    runs: List[AdminReportRunOut]
    chart_svg: Optional[str] = None

class AdminDailyCountOut(BaseModel):
    """
    # PURPOSE: Describe daily aggregate counts.
    # INPUT: date and count.
    # OUTPUT: Serializable daily metric.
    # CONTEXT: Used in admin dashboard sparklines.
    """

    date: str
    count: int

class AdminStatsOut(BaseModel):
    clients: int
    reports_total: int
    reports_in_progress: int
    reports_completed: int
    reports_failed: int
    reports_by_type: dict
    reports_daily: list
    tasks_open: int
    tasks_total: int
    analytics_funnel: dict
    feedback_avg: float = 0
    feedback_count: int = 0
    entitlements: Optional[dict] = None

class AdminTaskOut(BaseModel):
    """
    # PURPOSE: Describe a task created via bot messages.
    # INPUT: task metadata and content.
    # OUTPUT: Serializable task summary.
    # CONTEXT: Returned by /api/admin/tasks.
    """

    id: str
    user_id: Optional[str] = None
    telegram_id: int
    status: str
    source: str
    transcript: Optional[str] = None
    summary: Optional[str] = None
    clarification: Optional[str] = None
    voice_file_id: Optional[str] = None
    report_id: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    approved_at: Optional[str] = None
    completed_at: Optional[str] = None

class AdminTaskUpdateRequest(BaseModel):
    """
    # PURPOSE: Input payload for updating task status/content.
    # INPUT: status, summary, clarification, result summary.
    """

    status: Optional[str] = None
    summary: Optional[str] = None
    clarification: Optional[str] = None
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    report_id: Optional[str] = None

class SupportTicketRequest(BaseModel):
    """
    # PURPOSE: Input payload for user support requests.
    """
    topic: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    consent_accepted: bool = Field(default=False)
    consent_flow: Optional[str] = None

class AdminAuditLogOut(BaseModel):
    id: str
    admin_id: Optional[str]
    target_user_id: Optional[str]
    action: str
    reason: Optional[str]
    details: Optional[str]
    created_at: str
    admin_name: Optional[str] = None
    target_user_name: Optional[str] = None

class AdminUserUpdateDays(BaseModel):
    days: int
    reason: str = Field(..., min_length=3)

class AdminUserUpdateBalance(BaseModel):
    amount: float
    reason: str = Field(..., min_length=3)

class AdminUserDetailOut(BaseModel):
    id: str
    telegram_id: int
    full_name: Optional[str]
    username: Optional[str]
    balance: float
    subscription_active_until: Optional[str]
    created_at: str
    is_partner: bool
    referral_code: Optional[str]
    # Stats
    reports_count: int
    referrals_count: int
    # Lists (simplified)
    recent_reports: List[dict]
    recent_transactions: List[dict]

class AdminGrantRequest(BaseModel):
    type: str # 'credits', 'report'
    amount: Optional[int] = None
    report_type: Optional[str] = None
    reason: str = Field(..., min_length=3)

    @validator("report_type", pre=True)
    @classmethod
    def normalize_report_type_value(cls, value: Optional[str]) -> Optional[str]:
        return normalize_report_type(value)

class AdminUserOut(BaseModel):
    id: str
    telegram_id: int
    full_name: Optional[str]
    username: Optional[str]
    balance: float
    subscription_active_until: Optional[str]
    created_at: str
    is_partner: bool
    referral_code: Optional[str]
    horary_credits: int = 0

class AdminClientDetailOut(BaseModel):
    """
    # PURPOSE: Describe client detail with reports.
    # INPUT: client summary and reports list.
    # OUTPUT: Serializable detail view.
    # CONTEXT: Returned by /api/admin/clients/{id}.
    """

    client: AdminClientOut
    reports: List[AdminReportOut]

class GeoSuggestionOut(BaseModel):
    """
    # PURPOSE: Describe a GeoNames autocomplete suggestion.
    # INPUT: geoname identifiers and location details.
    # OUTPUT: Serializable suggestion data.
    # CONTEXT: Returned by /api/geo/autocomplete.
    """

    id: str
    name: str
    admin1: Optional[str]
    country: Optional[str]
    lat: float
    lon: float
    label: str

class GeoTimezoneOut(BaseModel):
    """
    # PURPOSE: Describe GeoNames timezone response.
    # INPUT: timezone identifiers and offsets.
    # OUTPUT: Serializable timezone data.
    # CONTEXT: Returned by /api/geo/timezone.
    """

    timezone_id: Optional[str]
    gmt_offset: Optional[float]
    dst_offset: Optional[float]
    raw_offset: Optional[float]

class AdminRegenerateRequest(BaseModel):
    reason: Optional[str] = None

class AdminTicketOut(BaseModel):
    id: str
    user_id: str
    username: Optional[str]
    topic: str
    status: str
    message: str
    created_at: str

class AdminBroadcastRequest(BaseModel):
    """
    # PURPOSE: Input payload for mass broadcasting messages.
    # INPUT: text, image_url (optional).
    """
    text: str = Field(..., min_length=1)
    image_url: Optional[str] = None

class UserProfileOut(BaseModel):
    consent_log: dict[str, Any] = Field(default_factory=dict)
    class ReportAccessEntry(BaseModel):
        allowed: bool = False
        granted_via: Optional[str] = None
        remaining_unlocks: int = 0
        reason_code: str = "payment_required"
        legacy_subscription_applied: bool = False

    telegram_id: int
    full_name: Optional[str]
    is_partner: bool
    is_test: bool = False
    balance: float
    subscription_active_until: Optional[str]
    days_left: int
    birth_time_known: bool
    birth_date: Optional[str]
    birth_place: Optional[str]
    birth_timezone: Optional[str]
    current_location: Optional[str]
    current_lat: Optional[float]
    current_lon: Optional[float]
    current_timezone: Optional[str]
    sun_sign: Optional[str]
    referral_code: Optional[str]
    referrals_count: int = 0
    horary_balance: int = 0
    weekly_quota_used: int = 0
    report_unlocks: dict[str, int] = Field(default_factory=dict)
    report_access: dict[str, ReportAccessEntry] = Field(default_factory=dict)
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    # Access Flags
    can_access_premium: bool = False
    can_ask_horary: bool = False

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[str] = None # YYYY-MM-DD
    birth_time: Optional[str] = None # HH:MM
    birth_time_known: bool = True
    birth_place: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    birth_timezone: Optional[str] = None
    current_location: Optional[str] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    current_timezone: Optional[str] = None
    is_test: Optional[bool] = None
    consent_accepted: Optional[bool] = None
    consent_flow: Optional[str] = None

class AnalyticsEventIn(BaseModel):
    event_name: str = Field(..., min_length=1)
    telegram_id: Optional[int] = None
    source: Optional[str] = None
    metadata: Optional[dict] = None
    session_id: Optional[str] = None
    path: Optional[str] = None
    product_type: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    duration_ms: Optional[int] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    device: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None

class AnalyticsEventOut(BaseModel):
    ok: bool
    error: Optional[str] = None

class FeedbackIn(BaseModel):
    rating: int = Field(..., ge=1, le=10)
    comment: Optional[str] = None
    section_id: Optional[str] = None
    telegram_id: Optional[int] = None

class UserReportOut(BaseModel):
    id: str
    report_type: str
    status: str
    created_at: str
    client_name: str
    access_source: Optional[str] = None

class ChunkOut(BaseModel):
    section: str
    content: Optional[str]
    status: str
    order_index: int

class ReportDetailOut(BaseModel):
    report: UserReportOut
    chart_svg: Optional[str] = None
    chunks: List[ChunkOut] = []
    week_brief: Optional[dict[str, Any]] = None
    week_brief_envelope: Optional[dict[str, Any]] = None

class FeedOut(BaseModel):
    date: str
    moon_sign: str
    moon_phase: str
    moon_emoji: str
    aspects_count: int
    general_vibe: str
    traffic_lights: dict  # {health: "green", money: "yellow", love: "red"}
    moon: Optional[dict] = None
    fast_hits: list[dict] = Field(default_factory=list)
    personalization_level: Optional[str] = None
    meta: Optional[dict] = None
    day_brief: Optional[DayBriefDTO] = None
    trace_id: Optional[str] = None
    generation_mode: Optional[str] = None
    birth_time_used: Optional[bool] = None
    confidence_bucket: Optional[str] = None
    factor_count: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True

class WeekMapOut(BaseModel):
    theme: Optional[str] = None
    thesis: Optional[str] = None
    day_cards: list[dict[str, Any]] = Field(default_factory=list)
    domains: dict[str, int] = Field(default_factory=dict)
    major_factors: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    deep_sections: list[str] = Field(default_factory=list)
    explainability: dict[str, Any]
    timezone: Optional[str] = None
    location: Optional[str] = None
    week_start: Optional[str] = None

class B2CReportCreateRequest(BaseModel):
    report_type: str
    question: Optional[str] = None
    focus_area: Optional[str] = None
    llm_mode: Optional[str] = None
    partner_name: Optional[str] = None
    partner_birth_date: Optional[str] = None
    partner_birth_location: Optional[str] = None
    partner_birth_lat: Optional[float] = None
    partner_birth_lon: Optional[float] = None
    partner_birth_timezone: Optional[str] = None
    partner_birth_place_id: Optional[str] = None
    solar_current_location: Optional[str] = None
    solar_current_lat: Optional[float] = None
    solar_current_lon: Optional[float] = None
    solar_current_timezone: Optional[str] = None
    solar_current_place_id: Optional[str] = None

    @validator("report_type", pre=True)
    @classmethod
    def normalize_report_type_value(cls, value: Optional[str]) -> Optional[str]:
        return normalize_report_type(value)
# END_CONTRACT: API-SCHEMA-DTO-COMPAT
# END_BLOCK: API_SCHEMA_DTOS
