# ############################################################################
# AI_HEADER: MODULE_API
# ROLE: FastAPI entrypoint for raw StelliumEngine data.
# DEPENDENCIES: fastapi, pydantic, stellium_engine.py
# GRACE_ANCHORS: [APP_INIT, API_SCHEMAS, SERIALIZATION, LOGGER, ENDPOINTS]
# ############################################################################

import asyncio
import copy
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response, Header
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
import structlog

from stellium_engine import StelliumEngine

from .db import Base, SessionLocal, apply_runtime_migrations, engine, get_db
from .diagnostics import run_diagnostics
from . import engine_utils
from .geonames import GeoNamesError, get_timezone, search_geonames
from .llm.mode import resolve_llm_mode, build_llm_client
from .models import (
    AgentTask,
    AnalyticsEvent,
    Client,
    Report,
    ReportChunk,
    ReportRun,
    User,
    Subscription,
)
from .reporting.pdf_reporter import (
    build_natal_chart_svg,
    build_report_html,
    html_to_pdf,
    markdown_to_html,
    convert_chunk_to_html,
)
from .services.report_workflow import (
    assemble_markdown_from_specs,
    build_chart_data,
    build_report_context,
    build_section_fallback_content,
    build_section_template_content,
    build_section_specs,
    finish_report_run,
    generate_report_sections,
    generate_section_content,
    generate_section_with_retries,
    inject_planet_emojis,
    initialize_report_chunks,
    load_section_specs_for_report,
    resolve_primary_model,
    resolve_llm_fallback_model,
    resolve_llm_retry_attempts,
    should_fallback_on_llm_error,
    start_report_run,
)
from .services.analytics import ALLOWED_ANALYTICS_EVENTS, log_analytics_event

from .routers import billing
from .services.feed_service import get_daily_vibe_llm
from .services.scheduler import start_scheduler
from .auth import get_current_user, get_current_user_from_query
from .reporting.static_content import SECTION_INTROS

# #START_BLOCK_LOGGER
logger = structlog.get_logger()
# #END_BLOCK_LOGGER

# #START_BLOCK_APP_INIT
app = FastAPI(title="AstroSaaS API", version="0.1.0")

app.include_router(billing.router)

@app.on_event("startup")
async def init_db():
    """
    # PURPOSE: Ensure core tables exist for the MVP workflow.
    # INPUT: None.
    # OUTPUT: None.
    # CONTEXT: Simplifies local/dev setup before migrations.
    """

    Base.metadata.create_all(bind=engine)
    apply_runtime_migrations()
    await start_scheduler()
# #END_BLOCK_APP_INIT



# #START_BLOCK_API_SCHEMAS
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
    planet: str
    orb: float
    star_lon: float


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
    house_system: Optional[str] = None
    include_fixed_stars: bool = True
    fixed_star_orb: float = 1.0
    sections: Optional[List[SectionInput]] = None
    llm_mode: Optional[str] = None
    is_test: bool = False


class ReportWorkflowResponse(BaseModel):
    """
    # PURPOSE: Return the workflow result with markdown and sections.
    # INPUT: report_id, client_id, markdown, sections, chart.
    # OUTPUT: Serializable workflow response.
    # CONTEXT: Returned by /api/workflows/report.
    """

    report_id: str
    client_id: str
    markdown: str
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
    # INPUT: report_id, markdown, sections.
    # OUTPUT: Serializable regeneration response.
    # CONTEXT: Returned by admin regeneration endpoints.
    """

    report_id: str
    status: str
    markdown: Optional[str]
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
    full_name: str
    birth_date: str
    birth_location: str
    notes: Optional[str] = None
    email: Optional[str] = None
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
    markdown: Optional[str]
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
    """
    # PURPOSE: Describe admin dashboard summary metrics.
    # INPUT: aggregate counts.
    # OUTPUT: Serializable dashboard stats.
    # CONTEXT: Returned by /api/admin/stats.
    """

    clients: int
    reports_total: int
    reports_in_progress: int
    reports_completed: int
    reports_failed: int
    reports_by_type: Optional[dict[str, int]] = None
    reports_daily: Optional[List[AdminDailyCountOut]] = None
    tasks_open: Optional[int] = None
    tasks_total: Optional[int] = None
    analytics_funnel: Optional[dict[str, int]] = None
    window_days: Optional[int] = None


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


@app.post("/api/support/tickets")
async def create_support_ticket(
    payload: SupportTicketRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Create a new support ticket and notify admins.
    """
    from .models import SupportTicket
    from .services.notification import send_bot_notification

    ticket = SupportTicket(
        user_id=user.id,
        topic=payload.topic,
        message=payload.message,
        status="open"
    )
    db.add(ticket)
    db.commit()

    # Notify Admins via Bot
    admin_ids = [int(i) for i in os.getenv("BOT_ADMIN_IDS", "").split(",") if i.strip()]
    for admin_id in admin_ids:
        msg = (
            f"🎫 <b>Новый тикет!</b>\n"
            f"От: {user.full_name} (@{user.username or '—'})\n"
            f"Тема: {payload.topic}\n\n"
            f"{payload.message}"
        )
        asyncio.create_task(send_bot_notification(admin_id, msg))

    return {"status": "ok", "ticket_id": str(ticket.id)}


class AdminUserUpdateDays(BaseModel):
    days: int

class AdminUserUpdateBalance(BaseModel):
    amount: float

@app.post("/api/admin/users/{user_id}/subscription/add-days")
def admin_add_subscription_days(
    user_id: str, 
    payload: AdminUserUpdateDays,
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Manually extend user subscription.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
        
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    now = datetime.now(timezone.utc)
    current_end = user.subscription_active_until
    if current_end and current_end.tzinfo is None:
        current_end = current_end.replace(tzinfo=timezone.utc)
        
    if current_end and current_end > now:
        user.subscription_active_until = current_end + timedelta(days=payload.days)
    else:
        user.subscription_active_until = now + timedelta(days=payload.days)
        
    db.commit()
    return {"status": "ok", "new_date": format_datetime(user.subscription_active_until)}

@app.post("/api/admin/users/{user_id}/balance/add")
def admin_add_balance(
    user_id: str,
    payload: AdminUserUpdateBalance,
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Manually add credits/money to user balance.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from decimal import Decimal
    user.balance += Decimal(payload.amount)
    db.commit()
    return {"status": "ok", "new_balance": float(user.balance)}

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

@app.get("/api/admin/users", response_model=List[AdminUserOut])
def list_admin_users(
    limit: int = 50, 
    q: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: List Telegram users for admin management.
    """
    query = db.query(User)
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search),
                User.username.ilike(search),
                User.referral_code.ilike(search)
            )
        )
    
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": str(u.id),
            "telegram_id": u.telegram_id,
            "full_name": u.full_name,
            "username": u.username,
            "balance": float(u.balance),
            "subscription_active_until": format_datetime(u.subscription_active_until),
            "created_at": format_datetime(u.created_at),
            "is_partner": u.is_partner,
            "referral_code": u.referral_code
        }
        for u in users
    ]


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
# #END_BLOCK_API_SCHEMAS

# #START_BLOCK_SERIALIZATION
def resolve_house_system(system_name: Optional[str]):
    """
    # PURPOSE: Convert a string into a house system object.
    # INPUT: system_name (str | None).
    # OUTPUT: House system instance or None for default behavior.
    # CONTEXT: Wrapper over engine_utils.
    """

    return engine_utils.resolve_house_system(system_name)


def serialize_chart(chart, chart_type: str, fixed_stars=None):
    """
    # PURPOSE: Convert a Chart object into a JSON-ready structure.
    # INPUT: chart (CalculatedChart), chart_type (str), fixed_stars (list|None).
    # OUTPUT: ChartResponse-compatible dict.
    # CONTEXT: Wrapper over engine_utils.
    """

    return engine_utils.serialize_chart(chart, chart_type, fixed_stars=fixed_stars)


def format_datetime(value: Optional[datetime]) -> Optional[str]:
    """
    # PURPOSE: Convert datetime values into ISO 8601 strings.
    # INPUT: datetime or None.
    # OUTPUT: ISO 8601 string or None.
    # CONTEXT: Used in admin API responses.
    """

    return value.isoformat() if value else None
# #END_BLOCK_SERIALIZATION


# #START_BLOCK_REPORT_WORKFLOW_UTILS
def transliterate_ru_to_en(value: str) -> str:
    """
    # PURPOSE: Transliterate Russian Cyrillic to Latin for PDF headers.
    # INPUT: raw string.
    # OUTPUT: Latin transliteration string.
    # CONTEXT: Used in PDF export metadata.
    """

    mapping = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
    result = []
    for char in value:
        lower = char.lower()
        if lower in mapping:
            mapped = mapping[lower]
            result.append(mapped.capitalize() if char.isupper() else mapped)
        else:
            result.append(char)
    return "".join(result)


def extract_birth_year(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    for part in value.split("-"):
        if len(part) == 4 and part.isdigit():
            return part
        break
    return value[:4] if len(value) >= 4 else None


def format_report_title(report_type: str) -> str:
    if report_type == "natal_master":
        return "Natal Master · Natal Chart"
    return report_type.replace("_", " ").title()


def format_report_subtitle(client_name: str) -> str:
    return client_name or "Natal Report"


def parse_birth_datetime(value: Optional[str], tz_str: Optional[str] = None) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo:
            return parsed
            
        if tz_str:
            try:
                return parsed.replace(tzinfo=ZoneInfo(tz_str))
            except Exception:
                pass
            
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def load_report_payload(report: Report) -> ReportWorkflowRequest:
    if report.input_payload:
        try:
            payload_data = json.loads(report.input_payload)
            return ReportWorkflowRequest.model_validate(payload_data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=400,
                detail="Stored report payload is invalid.",
            ) from exc

    client = report.client
    birth_date = format_datetime(client.birth_datetime)
    if not birth_date or not client.birth_location:
        raise HTTPException(
            status_code=400,
            detail="Missing birth data to regenerate this report.",
        )

    fallback_payload = {
        "client_id": str(client.id),
        "client_name": client.full_name,
        "client_note": client.notes,
        "birth_date": birth_date,
        "birth_location": client.birth_location,
        "birth_lat": client.birth_lat,
        "birth_lon": client.birth_lon,
        "birth_timezone": client.birth_timezone,
        "birth_place_id": client.birth_place_id,
        "report_type": report.report_type,
        "include_fixed_stars": True,
        "fixed_star_orb": 1.0,
    }
    return ReportWorkflowRequest.model_validate(fallback_payload)


def safe_load_report_payload_data(report: Report) -> Optional[dict]:
    if report.input_payload:
        try:
            return json.loads(report.input_payload)
        except json.JSONDecodeError as exc:
            logger.error(
                "report.payload.invalid",
                block_id="REPORT_PAYLOAD",
                report_id=str(report.id),
                error=str(exc),
            )
    return None


def get_report_or_404(report_id: str, db: Session) -> Report:
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report id.") from exc

    report = db.query(Report).filter(Report.id == report_uuid).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


def upsert_client_from_payload(
    payload: ReportWorkflowRequest, db: Session
) -> Client:
    if payload.client_id:
        try:
            client_uuid = uuid.UUID(payload.client_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid client id.") from exc

        client = db.query(Client).filter(Client.id == client_uuid).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        # Update fields if provided
        if payload.client_name:
            client.full_name = payload.client_name
        if payload.client_note is not None:
            client.notes = payload.client_note
        
        if payload.birth_date:
            client.birth_datetime = parse_birth_datetime(payload.birth_date, payload.birth_timezone)
        if payload.birth_location:
            client.birth_location = payload.birth_location
        if payload.birth_lat is not None:
            client.birth_lat = payload.birth_lat
        if payload.birth_lon is not None:
            client.birth_lon = payload.birth_lon
        if payload.birth_timezone:
            client.birth_timezone = payload.birth_timezone
        if payload.birth_place_id:
            client.birth_place_id = payload.birth_place_id
        
        if payload.is_test:
            client.is_test = True
            
        db.add(client)
        
        # Backfill payload from client data (crucial for report context)
        if not payload.client_name: 
            payload.client_name = client.full_name
        if not payload.birth_date and client.birth_datetime: 
            payload.birth_date = client.birth_datetime.isoformat()
        if not payload.birth_location: 
            payload.birth_location = client.birth_location
        if payload.birth_lat is None: 
            payload.birth_lat = client.birth_lat
        if payload.birth_lon is None: 
            payload.birth_lon = client.birth_lon
        if not payload.birth_timezone: 
            payload.birth_timezone = client.birth_timezone
            
        return client

    # New Client Mode
    if not payload.client_name or not payload.birth_date or not payload.birth_location:
        raise HTTPException(status_code=400, detail="Missing required client fields (name, date, location).")

    birth_dt = parse_birth_datetime(payload.birth_date, payload.birth_timezone)
    client = Client(
        full_name=payload.client_name,
        notes=payload.client_note,
        birth_datetime=birth_dt,
        birth_location=payload.birth_location,
        birth_lat=payload.birth_lat,
        birth_lon=payload.birth_lon,
        birth_timezone=payload.birth_timezone,
        birth_place_id=payload.birth_place_id,
        is_test=payload.is_test,
    )
    db.add(client)
    return client
# #END_BLOCK_REPORT_WORKFLOW_UTILS

# #START_BLOCK_ENDPOINTS
@app.get("/health")
def health_check():
    """
    # PURPOSE: Check service availability.
    # INPUT: None.
    # OUTPUT: {"status": "ok"}.
    # CONTEXT: Simple liveness check for orchestration/monitoring.
    """

    return {"status": "ok"}


@app.post("/api/engine/natal", response_model=ChartResponse)
def create_natal_chart(payload: NatalRequest):
    """
    # PURPOSE: Return raw natal chart data.
    # INPUT: NatalRequest (name, birth_date, birth_location, house_system).
    # OUTPUT: ChartResponse with positions and houses.
    # CONTEXT: Primary data source for the LLM orchestrator.
    """

    engine = StelliumEngine()
    house_system = resolve_house_system(payload.house_system)
    chart = engine.create_natal_chart(
        payload.name, payload.birth_date, payload.birth_location, house_system
    )

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(
            chart, orb=payload.fixed_star_orb
        )

    return serialize_chart(chart, chart_type="natal", fixed_stars=stars)


@app.post("/api/engine/transit", response_model=ChartResponse)
def create_transit_chart(payload: TransitRequest):
    """
    # PURPOSE: Return raw transit chart data.
    # INPUT: TransitRequest (date, location, house_system).
    # OUTPUT: ChartResponse with positions and houses.
    # CONTEXT: Used for forecasts and current cycles.
    """

    engine = StelliumEngine()
    house_system = resolve_house_system(payload.house_system)
    chart = engine.create_transit_chart(payload.date, payload.location, house_system)

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(
            chart, orb=payload.fixed_star_orb
        )

    return serialize_chart(chart, chart_type="transit", fixed_stars=stars)


async def run_report_generation(
    report_id: uuid.UUID, payload_data: dict, reset_chunks: bool = False
) -> None:
    """
    # PURPOSE: Generate report sections and markdown in the background.
    # INPUT: report_id (UUID), payload_data (dict).
    # OUTPUT: None.
    # CONTEXT: Background task for /api/workflows/report/async.
    """

    db = SessionLocal()
    report: Optional[Report] = None
    run: Optional[ReportRun] = None
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        logger.info(
            "report.async.start",
            block_id="REPORT_ASYNC",
            report_id=str(report.id),
            client_id=str(report.client_id),
        )

        run = start_report_run(report, db)
        payload = ReportWorkflowRequest.model_validate(payload_data)
        llm_mode = resolve_llm_mode(payload)
        llm_client = None
        if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)

        generated_sections, _, _ = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=reset_chunks,
            raise_on_error=False,
        )
        if report.status == "completed":
            finish_report_run(run, db, "completed")
            log_analytics_event(
                db,
                "report_generated",
                user_id=report.user_id,
                telegram_id=None,
                source="backend",
                metadata={
                    "report_id": str(report.id),
                    "report_type": report.report_type,
                    "client_id": str(report.client_id),
                },
            )

            logger.info(
                "report.async.complete",
                block_id="REPORT_ASYNC",
                report_id=str(report.id),
                client_id=str(report.client_id),
                sections=len(generated_sections),
            )
        else:
            finish_report_run(run, db, "failed", error_message=report.error_message)
    except Exception as exc:
        if report:
            report.status = "failed"
            report.error_message = str(exc)
            report.error_at = datetime.now(timezone.utc)
            db.commit()
            finish_report_run(run, db, "failed", error_message=str(exc))
            logger.error(
                "report.async.error",
                block_id="REPORT_ASYNC",
                report_id=str(report.id),
                client_id=str(report.client_id),
                error=str(exc),
            )
    finally:
        db.close()


async def run_report_section_generation(
    report_id: uuid.UUID, section_id: str, payload_data: dict
) -> None:
    """
    # PURPOSE: Regenerate a single report section in the background.
    # INPUT: report_id (UUID), section_id (str), payload_data (dict).
    # OUTPUT: None.
    # CONTEXT: Background task for async section regeneration.
    """

    db = SessionLocal()
    report: Optional[Report] = None
    run: Optional[ReportRun] = None
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        logger.info(
            "report.section.async.start",
            block_id="REPORT_ASYNC_SECTION",
            report_id=str(report.id),
            section_id=section_id,
        )

        run = start_report_run(report, db)
        payload = ReportWorkflowRequest.model_validate(payload_data)
        llm_mode = resolve_llm_mode(payload)

        llm_client = None
        if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
            try:
                model_override = (
                    resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
                )
                llm_client = build_llm_client(llm_mode, model_override=model_override)
            except ValueError as exc:
                logger.warning("llm.init.error", error=str(exc))

        section_specs = build_section_specs(payload)
        target_spec = next(
            (spec for spec in section_specs if spec.section_id == section_id),
            None,
        )
        target_index = next(
            (idx for idx, spec in enumerate(section_specs) if spec.section_id == section_id),
            0,
        )
        if not target_spec:
            report.status = "failed"
            report.error_message = "Section not found."
            report.error_at = datetime.now(timezone.utc)
            db.commit()
            finish_report_run(run, db, "failed", error_message=report.error_message)
        chart_data = build_chart_data(payload)
        context = build_report_context(payload, chart_data)

        # Context Anonymization
        section_context = copy.deepcopy(context)
        if section_id != "input_frame":
            section_context["client"]["name"] = "Ты"
            section_context["client"]["note"] = ""

        chunk_map = initialize_report_chunks(report, section_specs, db, reset=False)
        report.status = "in_progress"
        report.error_message = None
        report.error_at = None

        target_chunk = chunk_map.get(section_id)
        if target_chunk:
            target_chunk.status = "in_progress"
            target_chunk.error_message = None
            target_chunk.error_at = None
        db.commit()

        error_message = None
        retry_attempts = resolve_llm_retry_attempts()
        fallback_model = ""
        if llm_mode in {"openrouter", "cheap"}:
            fallback_model = resolve_llm_fallback_model()
        use_template = llm_mode == "fallback"

        try:
            content = await generate_section_content(
                target_spec,
                section_context,
                chart_data,
                llm_client,
                fallback_model,
                retry_attempts,
                use_template
            )
        except Exception as exc:
            if should_fallback_on_llm_error(exc):
                error_message = str(exc)
                content = inject_planet_emojis(
                    build_section_fallback_content(target_spec)
                )
                logger.warning(
                    "report.section.fallback",
                    block_id="REPORT_SECTION",
                    report_id=str(report.id),
                    section_id=section_id,
                    error=str(exc),
                )
            else:
                if target_chunk:
                    target_chunk.status = "failed"
                    target_chunk.error_message = str(exc)
                    target_chunk.error_at = datetime.now(timezone.utc)
                report.status = "failed"
                report.error_message = str(exc)
                report.error_at = datetime.now(timezone.utc)
                db.commit()
                finish_report_run(run, db, "failed", error_message=str(exc))
                logger.error(
                    "report.section.error",
                    block_id="REPORT_SECTION",
                    report_id=str(report.id),
                    section_id=section_id,
                    error=str(exc),
                )
                return
        if target_chunk:
            target_chunk.content = content
            target_chunk.status = "completed"
            target_chunk.error_message = error_message
            target_chunk.error_at = (
                datetime.now(timezone.utc) if error_message else None
            )
        else:
            db.add(
                ReportChunk(
                    report_id=report.id,
                    section=section_id,
                    content=content,
                    status="completed",
                    order_index=target_index,
                    error_message=error_message,
                    error_at=datetime.now(timezone.utc) if error_message else None,
                )
            )
        db.commit()

        markdown_chunk = chunk_map.get("final_markdown")
        if markdown_chunk:
            markdown_chunk.status = "in_progress"
            db.commit()

        markdown = assemble_markdown_from_specs(
            report.report_type, section_specs, chunk_map
        )
        if markdown_chunk:
            markdown_chunk.content = markdown
            markdown_chunk.status = "completed"
            markdown_chunk.order_index = len(section_specs)
        else:
            db.add(
                ReportChunk(
                    report_id=report.id,
                    section="final_markdown",
                    content=markdown,
                    status="completed",
                    order_index=len(section_specs),
                )
            )

        report.status = "completed"
        db.commit()
        finish_report_run(run, db, "completed", error_message=error_message)
        logger.info(
            "report.section.async.complete",
            block_id="REPORT_ASYNC_SECTION",
            report_id=str(report.id),
            section_id=section_id,
        )
    except Exception as exc:
        if report:
            report.status = "failed"
            report.error_message = str(exc)
            report.error_at = datetime.now(timezone.utc)
            db.commit()
            finish_report_run(run, db, "failed", error_message=str(exc))
            logger.error(
                "report.section.async.error",
                block_id="REPORT_ASYNC_SECTION",
                report_id=str(report.id),
                section_id=section_id,
                error=str(exc),
            )
    finally:
        db.close()


    client = upsert_client_from_payload(payload, db)
    db.flush()

    # ENTITLEMENT CHECK
    from .services.access_control import check_user_access
    if not check_user_access(user, payload.report_type):
        raise HTTPException(
            status_code=402, 
            detail="Subscription expired. Please top up balance or extend subscription."
        )

    report = Report(
        client_id=client.id,
        user_id=user.id,
        report_type=payload.report_type,
        status="in_progress",
        paid=False,
        is_test=client.is_test,
    )
    report.input_payload = json.dumps(payload.model_dump(), ensure_ascii=True)
    db.add(report)
    db.flush()

    section_specs = build_section_specs(payload)
    initialize_report_chunks(report, section_specs, db, reset=True)
    db.commit()

    background_tasks.add_task(
        run_report_generation, report.id, payload.model_dump(), False
    )

    return {
        "report_id": str(report.id),
        "client_id": str(client.id),
        "status": report.status,
    }


    client = upsert_client_from_payload(payload, db)
    db.flush()

    # ENTITLEMENT CHECK
    from .services.access_control import check_user_access
    if not check_user_access(user, payload.report_type):
        raise HTTPException(
            status_code=402, 
            detail="Subscription expired. Please top up balance or extend subscription."
        )

    report = Report(
        client_id=client.id,
        user_id=user.id,
        report_type=payload.report_type,
        status="in_progress",
        paid=False,
        is_test=client.is_test,
    )
    report.input_payload = json.dumps(payload.model_dump(), ensure_ascii=True)
    db.add(report)
    db.flush()

    # LLM Setup
    llm_mode = resolve_llm_mode(payload)
    llm_client = None
    if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
        try:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)
        except ValueError as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = start_report_run(report, db)
    try:
        generated_sections, chart_data, markdown = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=True,
            raise_on_error=True,
        )
    except Exception as exc:
        report.status = "failed"
        report.error_message = str(exc)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        finish_report_run(run, db, "failed", error_message=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    finish_report_run(run, db, "completed")
    log_analytics_event(
        db,
        "report_generated",
        user_id=user.id,
        telegram_id=user.telegram_id,
        source="backend",
        metadata={
            "report_id": str(report.id),
            "report_type": report.report_type,
            "client_id": str(report.client_id),
        },
    )

    return {
        "report_id": str(report.id),
        "client_id": str(client.id),
        "markdown": markdown,
        "sections": generated_sections,
        "chart": chart_data,
    }


@app.post(
    "/api/admin/reports/{report_id}/regenerate",
    response_model=ReportRegenerateResponse,
)
async def regenerate_report(report_id: str, db: Session = Depends(get_db)):
    """
    # PURPOSE: Regenerate all report sections and markdown.
    # INPUT: report_id path param.
    # OUTPUT: ReportRegenerateResponse with fresh sections.
    # CONTEXT: Admin-only full regeneration.
    """

    report = get_report_or_404(report_id, db)
    payload = load_report_payload(report)

    llm_mode = resolve_llm_mode(payload)
    llm_client = None
    if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
        try:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = start_report_run(report, db)
    try:
        generated_sections, _, markdown = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=True,
            raise_on_error=True,
        )
    except Exception as exc:
        report.status = "failed"
        report.error_message = str(exc)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        finish_report_run(run, db, "failed", error_message=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    finish_report_run(run, db, "completed")

    return {
        "report_id": str(report.id),
        "status": report.status,
        "markdown": markdown,
        "sections": generated_sections,
    }


@app.post(
    "/api/admin/reports/{report_id}/regenerate/async",
    response_model=ReportWorkflowStartResponse,
)
def regenerate_report_async(
    report_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Regenerate all report sections asynchronously.
    # INPUT: report_id path param.
    # OUTPUT: ReportWorkflowStartResponse.
    # CONTEXT: Admin-only full regeneration with progress UI.
    """

    report = get_report_or_404(report_id, db)
    payload = load_report_payload(report)
    section_specs = build_section_specs(payload)

    report.status = "in_progress"
    report.error_message = None
    report.error_at = None

    initialize_report_chunks(report, section_specs, db, reset=True)
    db.commit()

    background_tasks.add_task(
        run_report_generation,
        report.id,
        payload.model_dump(),
        True,
    )

    return {
        "report_id": str(report.id),
        "client_id": str(report.client_id),
        "status": report.status,
    }


@app.post(
    "/api/admin/reports/{report_id}/sections/{section_id}/regenerate",
    response_model=ReportRegenerateResponse,
)
async def regenerate_report_section(
    report_id: str, section_id: str, db: Session = Depends(get_db)
):
    """
    # PURPOSE: Regenerate a single report section and refresh markdown.
    # INPUT: report_id, section_id path params.
    # OUTPUT: ReportRegenerateResponse with updated section.
    # CONTEXT: Admin-only section regeneration.
    """

    report = get_report_or_404(report_id, db)
    payload = load_report_payload(report)
    section_specs = build_section_specs(payload)
    target_spec = next(
        (spec for spec in section_specs if spec.section_id == section_id),
        None,
    )
    if not target_spec:
        raise HTTPException(status_code=404, detail="Section not found.")

    llm_mode = resolve_llm_mode(payload)
    llm_client = None
    if llm_mode in {"openrouter", "cheap", "cli", "gemini", "codex"}:
        try:
            model_override = (
                resolve_primary_model(payload.report_type) if llm_mode == "openrouter" else None
            )
            llm_client = build_llm_client(llm_mode, model_override=model_override)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = start_report_run(report, db)
    try:
        chart_data = build_chart_data(payload)
        context = build_report_context(payload, chart_data)

        # Context Anonymization
        section_context = copy.deepcopy(context)
        if section_id != "input_frame":
            section_context["client"]["name"] = "Ты"
            section_context["client"]["note"] = ""

        chunk_map = initialize_report_chunks(report, section_specs, db, reset=False)
        report.status = "in_progress"
        report.error_message = None
        report.error_at = None

        try:
            target_chunk = chunk_map.get(section_id)
            if target_chunk:
                target_chunk.status = "in_progress"
                target_chunk.error_message = None
                target_chunk.error_at = None
            db.commit()

            retry_attempts = resolve_llm_retry_attempts()
            fallback_model = ""
            if llm_mode in {"openrouter", "cheap"}:
                fallback_model = resolve_llm_fallback_model()
            use_template = llm_mode == "fallback"

            content = await generate_section_content(
                target_spec,
                section_context,
                chart_data,
                llm_client,
                fallback_model,
                retry_attempts,
                use_template
            )
            
            logger.info("regen.result", section_id=target_spec.section_id, content_len=len(content))

            if not content:
                content = "Content generation failed (empty result)."
                logger.error("regen.empty_content", section=target_spec.section_id)

            generated_sections = [
                SectionResultOut(
                    section_id=target_spec.section_id,
                    title=target_spec.title,
                    content=content,
                )
            ]
        except Exception as exc:
            if target_chunk:
                target_chunk.status = "failed"
                target_chunk.error_message = str(exc)
                target_chunk.error_at = datetime.now(timezone.utc)
            report.status = "failed"
            report.error_message = str(exc)
            report.error_at = datetime.now(timezone.utc)
            db.commit()
            finish_report_run(run, db, "failed", error_message=str(exc))
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        result = generated_sections[0]
        target_chunk = chunk_map.get(section_id)
        if target_chunk:
            target_chunk.content = result.content
            target_chunk.status = "completed"
            target_chunk.error_message = None
            target_chunk.error_at = None
        else:
            target_chunk = ReportChunk(
                report_id=report.id,
                section=section_id,
                content=result.content,
                status="completed",
            )
            db.add(target_chunk)
            chunk_map[section_id] = target_chunk
        db.commit()

        markdown = assemble_markdown_from_specs(
            report.report_type, section_specs, chunk_map
        )

        markdown_chunk = chunk_map.get("final_markdown")
        if markdown_chunk:
            markdown_chunk.status = "in_progress"
            db.commit()
            markdown_chunk.content = markdown
            markdown_chunk.status = "completed"
            markdown_chunk.order_index = len(section_specs)
        else:
            db.add(
                ReportChunk(
                    report_id=report.id,
                    section="final_markdown",
                    content=markdown,
                    status="completed",
                    order_index=len(section_specs),
                )
            )

        report.status = "completed"
        db.commit()
        finish_report_run(run, db, "completed")
    except HTTPException:
        raise
    except Exception as exc:
        report.status = "failed"
        report.error_message = str(exc)
        report.error_at = datetime.now(timezone.utc)
        db.commit()
        finish_report_run(run, db, "failed", error_message=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "report_id": str(report.id),
        "status": report.status,
        "markdown": markdown,
        "sections": generated_sections,
    }


@app.post(
    "/api/admin/reports/{report_id}/sections/{section_id}/regenerate/async",
    response_model=ReportWorkflowStartResponse,
)
def regenerate_report_section_async(
    report_id: str,
    section_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Regenerate a single report section asynchronously.
    # INPUT: report_id, section_id path params.
    # OUTPUT: ReportWorkflowStartResponse.
    # CONTEXT: Admin-only section regeneration with progress UI.
    """

    report = get_report_or_404(report_id, db)
    payload = load_report_payload(report)
    section_specs = build_section_specs(payload)
    target_spec = next(
        (spec for spec in section_specs if spec.section_id == section_id),
        None,
    )
    if not target_spec:
        raise HTTPException(status_code=404, detail="Section not found.")

    report.status = "in_progress"
    report.error_message = None
    report.error_at = None

    chunk_map = initialize_report_chunks(report, section_specs, db, reset=False)
    target_chunk = chunk_map.get(section_id)
    if target_chunk:
        target_chunk.status = "in_progress"
        target_chunk.error_message = None
        target_chunk.error_at = None

    db.commit()
    background_tasks.add_task(
        run_report_section_generation,
        report.id,
        section_id,
        payload.model_dump(),
    )

    return {
        "report_id": str(report.id),
        "client_id": str(report.client_id),
        "status": report.status,
    }


@app.get("/api/admin/stats", response_model=AdminStatsOut)
def get_admin_stats(
    days: int = 7,
    show_test: bool = False,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Return admin dashboard counters.
    # INPUT: days (window size).
    # OUTPUT: AdminStatsOut.
    # CONTEXT: Used by the admin UI dashboard.
    """

    window_days = max(1, min(days, 30))
    
    clients_query = db.query(func.count(Client.id))
    reports_query = db.query(Report)
    
    if not show_test:
        clients_query = clients_query.filter(Client.is_test == False)
        reports_query = reports_query.filter(Report.is_test == False)

    clients = clients_query.scalar() or 0
    reports_total = reports_query.count()
    
    reports_in_progress = (
        reports_query
        .filter(Report.status == "in_progress")
        .count()
    )
    reports_completed = (
        reports_query
        .filter(Report.status == "completed")
        .count()
    )
    reports_failed = (
        reports_query
        .filter(Report.status == "failed")
        .count()
    )

    report_type_rows = (
        reports_query
        .with_entities(Report.report_type, func.count(Report.id))
        .group_by(Report.report_type)
        .all()
    )
    reports_by_type = {row[0]: int(row[1]) for row in report_type_rows}

    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=window_days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    
    daily_rows = (
        reports_query
        .with_entities(func.date(Report.created_at).label("day"), func.count(Report.id))
        .filter(Report.created_at >= start_dt)
        .group_by("day")
        .order_by("day")
        .all()
    )
    daily_map = {str(row[0]): int(row[1]) for row in daily_rows}
    reports_daily = []
    for offset in range(window_days):
        day = start_date + timedelta(days=offset)
        day_key = day.isoformat()
        reports_daily.append(
            {
                "date": day_key,
                "count": daily_map.get(day_key, 0),
            }
        )

    tasks_total = db.query(func.count(AgentTask.id)).scalar() or 0
    tasks_open = (
        db.query(func.count(AgentTask.id))
        .filter(AgentTask.status.in_(["queued", "approved", "running"]))
        .scalar()
        or 0
    )

    analytics_rows = (
        db.query(AnalyticsEvent.event_name, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.created_at >= start_dt)
        .group_by(AnalyticsEvent.event_name)
        .all()
    )
    analytics_funnel = {name: 0 for name in ALLOWED_ANALYTICS_EVENTS}
    for name, count in analytics_rows:
        analytics_funnel[name] = int(count)

    return {
        "clients": clients,
        "reports_total": reports_total,
        "reports_in_progress": reports_in_progress,
        "reports_completed": reports_completed,
        "reports_failed": reports_failed,
        "reports_by_type": reports_by_type,
        "reports_daily": reports_daily,
        "tasks_open": tasks_open,
        "tasks_total": tasks_total,
        "analytics_funnel": analytics_funnel,
        "window_days": window_days,
    }


@app.get("/api/admin/tasks", response_model=List[AdminTaskOut])
def get_admin_tasks(
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Return recent operator tasks from the bot.
    # INPUT: limit, status.
    # OUTPUT: List of AdminTaskOut.
    # CONTEXT: Used by the admin dashboard.
    """

    query = db.query(AgentTask).order_by(AgentTask.created_at.desc())
    if status:
        query = query.filter(AgentTask.status == status)
    tasks = query.limit(limit).all()

    payload = []
    for task in tasks:
        payload.append(
            {
                "id": str(task.id),
                "user_id": str(task.user_id) if task.user_id else None,
                "telegram_id": task.telegram_id,
                "status": task.status,
                "source": task.source,
                "transcript": task.transcript,
                "summary": task.summary,
                "clarification": task.clarification,
                "voice_file_id": task.voice_file_id,
                "report_id": str(task.report_id) if task.report_id else None,
                "result_summary": task.result_summary,
                "error_message": task.error_message,
                "created_at": format_datetime(task.created_at),
                "updated_at": format_datetime(task.updated_at),
                "approved_at": format_datetime(task.approved_at),
                "completed_at": format_datetime(task.completed_at),
            }
        )
    return payload


@app.patch("/api/admin/tasks/{task_id}", response_model=AdminTaskOut)
def update_admin_task(
    task_id: str,
    payload: AdminTaskUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Update a task created via the bot.
    # INPUT: task_id, update payload.
    # OUTPUT: Updated task.
    # CONTEXT: Used by admin UI and automation.
    """

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid task id.") from exc

    task = db.query(AgentTask).filter(AgentTask.id == task_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if payload.status is not None:
        task.status = payload.status
        if payload.status == "approved" and not task.approved_at:
            task.approved_at = datetime.now(timezone.utc)
        if payload.status in {"completed", "failed"} and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
    if payload.summary is not None:
        task.summary = payload.summary
    if payload.clarification is not None:
        task.clarification = payload.clarification
    if payload.result_summary is not None:
        task.result_summary = payload.result_summary
    if payload.error_message is not None:
        task.error_message = payload.error_message
    if payload.report_id is not None:
        if payload.report_id:
            try:
                task.report_id = uuid.UUID(payload.report_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400, detail="Invalid report id."
                ) from exc
        else:
            task.report_id = None

    db.commit()
    db.refresh(task)

    return {
        "id": str(task.id),
        "user_id": str(task.user_id) if task.user_id else None,
        "telegram_id": task.telegram_id,
        "status": task.status,
        "source": task.source,
        "transcript": task.transcript,
        "summary": task.summary,
        "clarification": task.clarification,
        "voice_file_id": task.voice_file_id,
        "report_id": str(task.report_id) if task.report_id else None,
        "result_summary": task.result_summary,
        "error_message": task.error_message,
        "created_at": format_datetime(task.created_at),
        "updated_at": format_datetime(task.updated_at),
        "approved_at": format_datetime(task.approved_at),
        "completed_at": format_datetime(task.completed_at),
    }


def serialize_client(client: Client) -> dict:
    reports_sorted = sorted(
        client.reports, key=lambda item: item.created_at, reverse=True
    )
    last = reports_sorted[0] if reports_sorted else None
    last_payload = None
    if last:
        last_payload = {
            "id": str(last.id),
            "report_type": last.report_type,
            "status": last.status,
            "created_at": format_datetime(last.created_at),
        }

    return {
        "id": str(client.id),
        "full_name": client.full_name,
        "email": client.email,
        "notes": client.notes,
        "birth_datetime": format_datetime(client.birth_datetime),
        "birth_location": client.birth_location,
        "birth_lat": client.birth_lat,
        "birth_lon": client.birth_lon,
        "birth_timezone": client.birth_timezone,
        "birth_place_id": client.birth_place_id,
        "created_at": format_datetime(client.created_at),
        "report_count": len(client.reports),
        "last_report": last_payload,
    }


@app.get("/api/admin/clients", response_model=List[AdminClientOut])
def list_admin_clients(
    limit: int = 25,
    offset: int = 0,
    q: Optional[str] = None,
    show_test: bool = False,
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Return clients with report summaries.
    # INPUT: limit, offset, q.
    # OUTPUT: List[AdminClientOut].
    # CONTEXT: Used by the admin UI clients list.
    """

    query = db.query(Client)
    if not show_test:
        query = query.filter(Client.is_test == False)
        
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Client.full_name.ilike(search),
                Client.notes.ilike(search)
            )
        )

    rows = (
        query.order_by(Client.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [serialize_client(client) for client in rows]


@app.post("/api/admin/clients", response_model=AdminClientOut)
def create_admin_client(payload: AdminClientCreateRequest, db: Session = Depends(get_db)):
    """
    # PURPOSE: Create a client without generating a report.
    # INPUT: AdminClientCreateRequest payload.
    # OUTPUT: AdminClientOut.
    # CONTEXT: Admin-only manual client creation.
    """

    birth_dt = None
    try:
        birth_dt = parse_birth_datetime(payload.birth_date, payload.birth_timezone)
    except ValueError:
        birth_dt = None

    client = Client(
        full_name=payload.client_name,
        notes=payload.client_note,
        birth_datetime=birth_dt,
        birth_location=payload.birth_location,
        birth_lat=payload.birth_lat,
        birth_lon=payload.birth_lon,
        birth_timezone=payload.birth_timezone,
        birth_place_id=payload.birth_place_id,
        is_test=payload.is_test,
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return serialize_client(client)


@app.put("/api/admin/clients/{client_id}", response_model=AdminClientOut)
def update_admin_client(
    client_id: str,
    payload: AdminClientCreateRequest,
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Update existing client details.
    # INPUT: client_id, payload.
    # OUTPUT: Updated client.
    """
    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid client id.") from exc

    client = db.query(Client).filter(Client.id == client_uuid).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    birth_dt = None
    try:
        if payload.birth_date:
            birth_dt = parse_birth_datetime(payload.birth_date, payload.birth_timezone)
    except ValueError:
        pass

    client.full_name = payload.client_name
    client.notes = payload.client_note
    client.birth_datetime = birth_dt
    client.birth_location = payload.birth_location
    client.birth_lat = payload.birth_lat
    client.birth_lon = payload.birth_lon
    client.birth_timezone = payload.birth_timezone
    client.birth_place_id = payload.birth_place_id
    client.is_test = payload.is_test

    db.commit()
    db.refresh(client)
    return serialize_client(client)


@app.get("/api/admin/clients/{client_id}", response_model=AdminClientDetailOut)
def get_admin_client(
    client_id: str, 
    show_test: bool = False,
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Return client detail with related reports.
    # INPUT: client_id.
    # OUTPUT: AdminClientDetailOut.
    # CONTEXT: Used by the admin client detail page.
    """

    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid client id.") from exc

    client = (
        db.query(Client)
        .filter(Client.id == client_uuid)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    reports_query = (
        db.query(Report)
        .filter(Report.client_id == client.id)
    )
    
    if not show_test:
        reports_query = reports_query.filter(Report.is_test == False)
        
    reports = reports_query.order_by(Report.created_at.desc()).all()

    reports_payload = []
    for report in reports:
        reports_payload.append(
            {
                "id": str(report.id),
                "report_type": report.report_type,
                "status": report.status,
                "paid": report.paid,
                "error_message": report.error_message,
                "error_at": format_datetime(report.error_at),
                "created_at": format_datetime(report.created_at),
                "updated_at": format_datetime(report.updated_at),
                "client_id": str(report.client_id),
                "client_name": report.client.full_name if report.client else "",
                "chunk_count": len(report.chunks),
            }
        )

    return {
        "client": serialize_client(client),
        "reports": reports_payload,
    }


class AdminTicketOut(BaseModel):
    id: str
    user_id: str
    username: Optional[str]
    topic: str
    status: str
    message: str
    created_at: str

@app.get("/api/admin/tickets", response_model=List[AdminTicketOut])
def list_admin_tickets(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: List support tickets for admin.
    """
    from .models import SupportTicket
    query = db.query(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status:
        query = query.filter(SupportTicket.status == status)

    tickets = query.limit(limit).all()

    results = []
    for t in tickets:
        results.append({
            "id": str(t.id),
            "user_id": str(t.user_id),
            "username": t.user.username if t.user else None,
            "topic": t.topic,
            "status": t.status,
            "message": t.message,
            "created_at": format_datetime(t.created_at)
        })
    return results


class AdminBroadcastRequest(BaseModel):
    """
    # PURPOSE: Input payload for mass broadcasting messages.
    # INPUT: text, image_url (optional).
    """
    text: str = Field(..., min_length=1)
    image_url: Optional[str] = None


@app.post("/api/admin/broadcast")
async def admin_broadcast(
    payload: AdminBroadcastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Start a background task to broadcast a message to all users.
    """
    # We could also restrict this to admin users only if we had an admin check.
    # For now, it's an internal admin-only endpoint by convention.

    background_tasks.add_task(run_mass_broadcast, payload.text, payload.image_url)
    return {"status": "broadcast_started"}


async def run_mass_broadcast(text: str, image_url: Optional[str] = None):
    """
    # PURPOSE: Send messages to all Telegram users with batching.
    """
    from .services.notification import send_bot_notification
    db = SessionLocal()
    try:
        # Get all users with telegram_id
        users = db.query(User).filter(User.telegram_id.isnot(None)).all()
        logger.info("broadcast.start", total_users=len(users))

        batch_size = 20
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            tasks = []
            for user in batch:
                tasks.append(send_bot_notification(user.telegram_id, text, image_url))

            await asyncio.gather(*tasks)
            logger.info("broadcast.batch_sent", offset=i, size=len(batch))

            # Wait 1 second between batches to stay under TG limits (30/sec)
            await asyncio.sleep(1.0)

        logger.info("broadcast.complete")
    finally:
        db.close()


@app.get("/api/admin/reports", response_model=List[AdminReportOut])
def list_admin_reports(
    status: Optional[str] = None,
    show_test: bool = False,
    limit: int = 25,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Return reports with client names and chunk counts.
    # INPUT: status (optional), limit, offset.
    # OUTPUT: List[AdminReportOut].
    # CONTEXT: Used by the admin UI reports list.
    """

    query = db.query(Report).order_by(Report.created_at.desc())
    
    if not show_test:
        query = query.filter(Report.is_test == False)

    if status:
        query = query.filter(Report.status == status)
    rows = query.offset(offset).limit(limit).all()

    results = []
    for report in rows:
        results.append(
            {
                "id": str(report.id),
                "report_type": report.report_type,
                "status": report.status,
                "paid": report.paid,
                "error_message": report.error_message,
                "error_at": format_datetime(report.error_at),
                "created_at": format_datetime(report.created_at),
                "updated_at": format_datetime(report.updated_at),
                "client_id": str(report.client_id),
                "client_name": report.client.full_name if report.client else "",
                "chunk_count": len(report.chunks),
            }
        )

    return results


@app.get("/api/admin/reports/{report_id}", response_model=AdminReportDetailOut)
def get_admin_report(
    report_id: str,
    include_content: bool = True,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Return report detail with chunks and markdown.
    # INPUT: report_id.
    # OUTPUT: AdminReportDetailOut.
    # CONTEXT: Used by the admin report detail page.
    """

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report id.") from exc

    report = (
        db.query(Report)
        .filter(Report.id == report_uuid)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    chunks_sorted = sorted(report.chunks, key=lambda item: item.order_index)
    payload_data = safe_load_report_payload_data(report)
    section_specs = load_section_specs_for_report(report, payload_data)
    title_map = {spec.section_id: spec.title for spec in section_specs}
    chunks_payload = []
    markdown = None
    for chunk in chunks_sorted:
        if chunk.section == "final_markdown" and include_content:
            markdown = chunk.content or ""
        content_html = None
        if include_content and chunk.content:
            content_html = markdown_to_html(chunk.content)
        chunks_payload.append(
            {
                "id": str(chunk.id),
                "section": chunk.section,
                "title": title_map.get(chunk.section),
                "status": chunk.status,
                "error_message": chunk.error_message,
                "error_at": format_datetime(chunk.error_at),
                "order_index": chunk.order_index,
                "content": chunk.content if include_content else None,
                "content_html": content_html,
                "created_at": format_datetime(chunk.created_at),
            }
        )

    runs_sorted = sorted(
        report.runs, key=lambda item: item.created_at, reverse=True
    )
    runs_payload = []
    for run in runs_sorted:
        runs_payload.append(
            {
                "id": str(run.id),
                "status": run.status,
                "error_message": run.error_message,
                "started_at": format_datetime(run.started_at),
                "finished_at": format_datetime(run.finished_at),
                "created_at": format_datetime(run.created_at),
            }
        )

    report_payload = {
        "id": str(report.id),
        "report_type": report.report_type,
        "status": report.status,
        "paid": report.paid,
        "error_message": report.error_message,
        "error_at": format_datetime(report.error_at),
        "created_at": format_datetime(report.created_at),
        "updated_at": format_datetime(report.updated_at),
        "client_id": str(report.client_id),
        "client_name": report.client.full_name if report.client else "",
        "chunk_count": len(report.chunks),
    }

    chart_svg = None
    if include_content:
        try:
            payload_model = load_report_payload(report)
            chart_data = build_chart_data(payload_model)
            chart_svg = build_natal_chart_svg(chart_data)
            logger.info("admin.svg.generated", report_id=str(report.id), svg_len=len(chart_svg or ""))
        except Exception as e:
            logger.warning("admin.svg.gen_failed", report_id=str(report.id), error=str(e))

    return {
        "report": report_payload,
        "chunks": chunks_payload,
        "runs": runs_payload,
        "markdown": markdown if include_content else None,
        "chart_svg": chart_svg if include_content else None
    }


@app.get(
    "/api/admin/reports/{report_id}/sections/{section_id}",
    response_model=AdminReportChunkOut,
)
def get_admin_report_section(
    report_id: str,
    section_id: str,
    include_content: bool = True,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Return a single report chunk with optional content.
    # INPUT: report_id, section_id.
    # OUTPUT: AdminReportChunkOut.
    # CONTEXT: Used for lazy-loading section content in the admin UI.
    """

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report id.") from exc

    report = (
        db.query(Report)
        .filter(Report.id == report_uuid)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    chunk = next((item for item in report.chunks if item.section == section_id), None)
    if not chunk:
        raise HTTPException(status_code=404, detail="Section not found.")

    payload_data = safe_load_report_payload_data(report)
    section_specs = load_section_specs_for_report(report, payload_data)
    title_map = {spec.section_id: spec.title for spec in section_specs}

    content_html = None
    if include_content and chunk.content:
        content_html = markdown_to_html(chunk.content)

    return {
        "id": str(chunk.id),
        "section": chunk.section,
        "title": title_map.get(chunk.section),
        "status": chunk.status,
        "error_message": chunk.error_message,
        "error_at": format_datetime(chunk.error_at),
        "order_index": chunk.order_index,
        "content": chunk.content if include_content else None,
        "content_html": content_html,
        "created_at": format_datetime(chunk.created_at),
    }


@app.get("/api/admin/reports/{report_id}/markdown")
def get_admin_report_markdown(report_id: str, db: Session = Depends(get_db)):
    """
    # PURPOSE: Return report content as Markdown.
    # INPUT: report_id.
    # OUTPUT: Markdown text response.
    # CONTEXT: Used by admin UI for downloads.
    """

    report = get_report_or_404(report_id, db)
    markdown = None
    for chunk in report.chunks:
        if chunk.section == "final_markdown":
            markdown = chunk.content or ""
            break

    if markdown is None:
        payload_data = safe_load_report_payload_data(report)
        section_specs = load_section_specs_for_report(report, payload_data)
        chunk_map = {chunk.section: chunk for chunk in report.chunks}
        try:
            markdown = assemble_markdown_from_specs(
                report.report_type, section_specs, chunk_map
            )
        except Exception as exc:
            logger.error(
                "report.markdown.error",
                block_id="REPORT_MARKDOWN",
                report_id=str(report.id),
                error=str(exc),
            )
            markdown = f"# Report: {report.report_type}\n\n"

    filename = f"report-{report_id}.md"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=markdown or "",
        media_type="text/markdown; charset=utf-8",
        headers=headers,
    )


def _generate_pdf_response(report: Report) -> Response:
    """
    # PURPOSE: Internal helper to build PDF response from Report.
    # SHARED by: Admin and User PDF endpoints.
    """
    # 1. Assemble HTML Body
    payload_data = safe_load_report_payload_data(report)
    section_specs = load_section_specs_for_report(report, payload_data)
    chunk_map = {chunk.section: chunk for chunk in report.chunks}
    
    html_parts = []
    for spec in section_specs:
        chunk = chunk_map.get(spec.section_id)
        if chunk and chunk.content:
            # Convert JSON blocks or Markdown to HTML
            section_content_html = convert_chunk_to_html(chunk.content)
            
            # Wrap in section and add Title (mimic assemble_markdown behavior)
            html_parts.append(f"<div class='section' id='{spec.section_id}'>")
            html_parts.append(f"<h2>{spec.title}</h2>")
            html_parts.append(section_content_html)
            html_parts.append("</div>")
            
    body_html = "".join(html_parts)
    if not body_html:
        body_html = "<p>Отчет не содержит данных.</p>"

    # 2. Metadata for Cover
    payload_data = payload_data or {}
    client_name = payload_data.get("client_name") or (
        report.client.full_name if report.client else ""
    )
    birth_year = extract_birth_year(payload_data.get("birth_date"))
    translit_name = transliterate_ru_to_en(client_name) if client_name else ""
    title = format_report_title(report.report_type)
    subtitle = format_report_subtitle(client_name)

    meta_lines = []
    if translit_name:
        line = translit_name
        if birth_year:
            line = f"{line} · {birth_year}"
        meta_lines.append(line)
    elif client_name:
        meta_lines.append(client_name)
    
    meta_lines.append(format_datetime(datetime.now(timezone.utc)))

    # 3. Chart SVG
    chart_svg = None
    try:
        # Re-build chart data for SVG
        payload_model = load_report_payload(report)
        chart_data = build_chart_data(payload_model)
        chart_svg = build_natal_chart_svg(chart_data)
    except Exception as e:
        logger.warning("pdf.chart_svg.error", error=str(e))

    # 4. Build PDF
    html_content = build_report_html(
        title=title,
        subtitle=subtitle,
        meta_lines=meta_lines,
        chart_svg=chart_svg or "",
        body_html=body_html,
    )
    
    try:
        pdf_bytes = html_to_pdf(html_content)
    except Exception as e:
        logger.error("pdf.gen.error", error=str(e))
        raise HTTPException(status_code=500, detail="PDF generation failed")

    filename = f"report-{report.id}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


@app.get("/api/reports/{report_id}/pdf")
def get_user_report_pdf(
    report_id: str, 
    user: User = Depends(get_current_user_from_query),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Download PDF for the owner of the report.
    # AUTH: Query param (initData).
    """
    report = get_report_or_404(report_id, db)
    
    # Security Check: User must own the report
    if report.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this report")
        
    return _generate_pdf_response(report)


@app.get("/api/admin/reports/{report_id}/pdf")
def get_admin_report_pdf(report_id: str, db: Session = Depends(get_db)):
    """
    # PURPOSE: Return report content as PDF.
    # INPUT: report_id.
    # OUTPUT: PDF binary response.
    # CONTEXT: Used by admin UI for downloads.
    """

    report = get_report_or_404(report_id, db)
    return _generate_pdf_response(report)


@app.get("/api/geo/autocomplete", response_model=List[GeoSuggestionOut])
def geo_autocomplete(q: str, limit: int = 8):
    """
    # PURPOSE: Return GeoNames suggestions for location autocomplete.
    # INPUT: q (query), limit.
    # OUTPUT: List[GeoSuggestionOut].
    # CONTEXT: Used by the admin UI location picker.
    """

    try:
        return search_geonames(q, limit=limit)
    except GeoNamesError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/geo/timezone", response_model=GeoTimezoneOut)
def geo_timezone(lat: float, lon: float):
    """
    # PURPOSE: Return GeoNames timezone for coordinates.
    # INPUT: lat, lon.
    # OUTPUT: GeoTimezoneOut.
    # CONTEXT: Used by the admin UI location picker.
    """

    try:
        return get_timezone(lat, lon)
    except GeoNamesError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/diagnostics/run")
def run_diagnostics_endpoint():
    """
    # PURPOSE: Run diagnostics and return the result.
    # INPUT: None.
    # OUTPUT: Dict with status and steps.
    # CONTEXT: Admin trigger for Log-Driven verification.
    """

    return run_diagnostics()


# #START_BLOCK_USER_ENDPOINTS
class UserProfileOut(BaseModel):
    telegram_id: int
    full_name: Optional[str]
    is_partner: bool
    balance: float
    subscription_active_until: Optional[str]
    days_left: int
    birth_time_known: bool
    birth_date: Optional[str]
    birth_place: Optional[str]
    referral_code: Optional[str]
    referrals_count: int = 0

@app.get("/api/users/me", response_model=UserProfileOut)
def get_my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Get current user profile for Telegram WebApp.
    # INPUT: Auth Dependency.
    # OUTPUT: User profile JSON.
    """
    if not user.referral_code:
        import random, string
        chars = string.ascii_uppercase + string.digits
        user.referral_code = ''.join(random.choice(chars) for _ in range(6))
        db.add(user)
        db.commit()
        db.refresh(user)

    days_left = 0
    if user.subscription_active_until:
        if user.subscription_active_until.tzinfo:
            delta = user.subscription_active_until - datetime.now(timezone.utc)
        else:
             delta = user.subscription_active_until - datetime.utcnow()
        days_left = max(0, delta.days)

    from .models import Referral
    referrals_count = db.query(Referral).filter(Referral.referrer_id == user.id).count()

    log_analytics_event(
        db,
        "app_open",
        user_id=user.id,
        telegram_id=user.telegram_id,
        source="webapp",
        metadata={"endpoint": "/api/users/me"},
    )

    return {
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "is_partner": user.is_partner,
        "balance": float(user.balance),
        "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
        "days_left": days_left,
        "birth_time_known": user.birth_time_known,
        "birth_date": user.birth_date,
        "birth_place": user.birth_place,
        "referral_code": user.referral_code,
        "referrals_count": referrals_count
    }

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[str] = None # YYYY-MM-DD
    birth_time: Optional[str] = None # HH:MM
    birth_time_known: bool = True
    birth_place: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None

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

@app.post("/api/analytics/event", response_model=AnalyticsEventOut)
def capture_analytics_event(
    payload: AnalyticsEventIn,
    db: Session = Depends(get_db),
    x_telegram_id: Optional[int] = Header(None, alias="X-Telegram-ID"),
):
    """
    # PURPOSE: Capture a funnel analytics event from webapp or services.
    # INPUT: event payload.
    # OUTPUT: ok flag + optional error.
    """
    event_name = payload.event_name.strip()
    if event_name not in ALLOWED_ANALYTICS_EVENTS:
        return {"ok": False, "error": "invalid_event"}

    telegram_id = payload.telegram_id or x_telegram_id
    user_id = None
    if telegram_id:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user_id = user.id

    ok = log_analytics_event(
        db,
        event_name,
        user_id=user_id,
        telegram_id=telegram_id,
        source=payload.source or "webapp",
        metadata=payload.metadata,
        session_id=payload.session_id,
        path=payload.path,
        product_type=payload.product_type,
        price=payload.price,
        currency=payload.currency,
        duration_ms=payload.duration_ms,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        device=payload.device,
        os_name=payload.os,
        browser=payload.browser
    )
    return {"ok": ok}

@app.put("/api/users/me")
def update_my_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import sys
    print(f"DEBUG: Entered update_my_profile with {payload}", file=sys.stderr)
    try:
        was_complete = bool(user.full_name and user.birth_date and user.birth_place)
        # Update fields if provided
        if payload.full_name is not None: user.full_name = payload.full_name
        if payload.birth_date is not None: user.birth_date = payload.birth_date
        if payload.birth_time is not None: user.birth_time = payload.birth_time
        if payload.birth_time_known is not None: user.birth_time_known = payload.birth_time_known
        if payload.birth_place is not None: user.birth_place = payload.birth_place
        if payload.birth_lat is not None: user.birth_lat = payload.birth_lat
        if payload.birth_lon is not None: user.birth_lon = payload.birth_lon

        db.add(user)
        db.commit()
        db.refresh(user)

        is_complete = bool(user.full_name and user.birth_date and user.birth_place)
        if is_complete and not was_complete:
            try:
                log_analytics_event(
                    db,
                    "profile_fill",
                    user_id=user.id,
                    telegram_id=user.telegram_id,
                    source="webapp",
                    metadata={"endpoint": "/api/users/me"},
                )
            except Exception as e:
                logger.error("analytics.fail", error=str(e))

        days_left = 0
        if user.subscription_active_until:
            if user.subscription_active_until.tzinfo:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.utcnow()
            
            delta = user.subscription_active_until - now
            days_left = max(0, delta.days)

        return {
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "is_partner": user.is_partner,
            "balance": float(user.balance),
            "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
            "days_left": days_left,
            "birth_time_known": user.birth_time_known,
            "birth_date": user.birth_date,
            "birth_place": user.birth_place,
            "referral_code": user.referral_code,
            "referrals_count": 0
        }
    except Exception as e:
        import sys
        print(f"ERROR in update_my_profile: {e}", file=sys.stderr)
        with open("/tmp/backend_error.log", "w") as f:
            f.write(str(e))
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

class UserReportOut(BaseModel):
    id: str
    report_type: str
    status: str
    created_at: str
    client_name: str

class ReportDetailOut(BaseModel):
    report: UserReportOut
    markdown: Optional[str]
    chart_svg: Optional[str] = None

@app.get("/api/reports/{report_id}", response_model=ReportDetailOut)
def get_report_detail(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Get full report content for the owner.
    """
    try:
        r_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    report = db.query(Report).filter(Report.id == r_uuid, Report.user_id == user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Get Markdown
    markdown = None
    for chunk in report.chunks:
        if chunk.section == "final_markdown":
            markdown = chunk.content
            break

    # Generate SVG if applicable
    chart_svg = None
    # For MVP, generate for all types that have chart data
    try:
        payload = load_report_payload(report)
        chart_data = build_chart_data(payload)
        chart_svg = build_natal_chart_svg(chart_data)
    except Exception as e:
        logger.warning("svg.gen_failed", report_id=str(report.id), error=str(e))

    return {
        "report": {
            "id": str(report.id),
            "report_type": report.report_type,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "client_name": report.client.full_name if report.client else "Unknown"
        },
        "markdown": markdown,
        "chart_svg": chart_svg
    }

@app.get("/api/reports/my", response_model=List[UserReportOut])
def get_my_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: List reports belonging to the current user.
    # INPUT: Auth Dependency.
    # OUTPUT: List of user reports.
    """
    reports = db.query(Report).filter(Report.user_id == user.id).order_by(Report.created_at.desc()).all()
    return [
        {
            "id": str(r.id),
            "report_type": r.report_type,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "client_name": r.client.full_name if r.client else "Unknown"
        }
        for r in reports
    ]

# #START_BLOCK_FEED_ENDPOINT
class FeedOut(BaseModel):
    date: str
    moon_sign: str
    moon_phase: str
    moon_emoji: str
    aspects_count: int
    general_vibe: str
    traffic_lights: dict  # {health: "green", money: "yellow", love: "red"}

def get_moon_phase_emoji(phase_angle: float) -> str:
    # 0=New, 90=First Quarter, 180=Full, 270=Last Quarter
    if phase_angle < 45: return "🌑" # New
    if phase_angle < 90: return "🌒" # Waxing Crescent
    if phase_angle < 135: return "🌓" # First Quarter
    if phase_angle < 180: return "🌔" # Waxing Gibbous
    if phase_angle < 225: return "🌕" # Full
    if phase_angle < 270: return "🌖" # Waning Gibbous
    if phase_angle < 315: return "🌗" # Last Quarter
    return "🌘" # Waning Crescent

def get_phase_name(phase_angle: float) -> str:
    if phase_angle < 10: return "Новолуние"
    if phase_angle < 90: return "Растущая Луна"
    if phase_angle < 100: return "Первая четверть"
    if phase_angle < 170: return "Растущая Луна"
    if phase_angle < 190: return "Полнолуние"
    if phase_angle < 270: return "Убывающая Луна"
    if phase_angle < 280: return "Последняя четверть"
    return "Убывающая Луна"

@app.get("/api/feed/today", response_model=FeedOut)
async def get_daily_feed():
    """
    # PURPOSE: Get daily astrological feed (Moon, Vibe) with real LLM advice.
    # INPUT: None (uses current UTC time).
    # OUTPUT: FeedOut object.
    """
    now = datetime.utcnow()
    engine_inst = StelliumEngine()

    # Calculate simple transit for Moscow (default for MVP feed)
    house_system = engine_utils.resolve_house_system("placidus")
    chart = engine_inst.create_transit_chart(
        now.strftime("%Y-%m-%d %H:%M"),
        "Moscow",
        house_system,
    )

    moon = next((p for p in chart.positions if p.name == "Moon"), None)
    sun = next((p for p in chart.positions if p.name == "Sun"), None)

    if not moon or not sun:
        raise HTTPException(status_code=500, detail="Could not calculate chart")

    # Calculate Phase Angle
    angle = (moon.longitude - sun.longitude) % 360
    phase_name = get_phase_name(angle)

    # Calculate aspects
    aspects = engine_inst.find_natal_aspects(chart)
    aspect_summary = ", ".join([f"{a['p1']} {a['type']} {a['p2']}" for a in aspects[:5]]) or "Нет мажорных аспектов"

    # REAL LLM GENERATION (Cheap mode)
    vibe = await get_daily_vibe_llm(moon.sign, phase_name, aspect_summary)

    # Mock Traffic Lights based on aspects (Randomized for MVP demo based on day hash)
    day_seed = now.toordinal()
    import random
    random.seed(day_seed)

    lights = {
        "health": random.choice(["green", "yellow", "red"]),
        "money": random.choice(["green", "yellow", "red"]),
        "love": random.choice(["green", "yellow", "red"])
    }

    return {
        "date": now.strftime("%d.%m.%Y"),
        "moon_sign": moon.sign,
        "moon_phase": phase_name,
        "moon_emoji": get_moon_phase_emoji(angle),
        "aspects_count": len(chart.aspects),
        "general_vibe": vibe,
        "traffic_lights": lights
    }
# #END_BLOCK_FEED_ENDPOINT
# #END_BLOCK_USER_ENDPOINTS
# #END_BLOCK_ENDPOINTS
