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
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import List, Optional, Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response, Header, Query, Request
from pydantic import BaseModel, Field, ValidationError, validator
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
import structlog

from stellium_engine import StelliumEngine

from .db import Base, SessionLocal, apply_runtime_migrations, engine, get_db
from .diagnostics import run_diagnostics
from . import engine_utils
from .geonames import GeoNamesError, get_timezone, search_geonames
from .llm.mode import resolve_llm_mode, build_llm_client
from .llm.orchestrator import LLMContentValidationError
from .models import (
    AgentTask,
    AnalyticsEvent,
    Client,
    Report,
    ReportChunk,
    ReportRun,
    User,
    Subscription,
    ReportFeedback,
    Transaction,
)
from .reporting.chart_renderer import build_natal_chart_svg
from .services.report_workflow import (
    build_chart_data,
    build_section_context,
    build_report_context,
    build_section_fallback_content,
    build_section_template_content,
    build_section_validation_fallback_content,
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
from .services.access_control import AccessConsumptionError, consume_report_access
from .services.analytics import ALLOWED_ANALYTICS_EVENTS, log_analytics_event
from .services.one_off_entitlements import (
    AccessGrantSource,
    EntitlementSource,
    allow_access,
    grant_report_entitlement,
    is_one_off_report_type,
    normalize_report_type,
)

from .routers import billing
from .services.feed_service import (
    build_daily_vibe_fallback,
    get_daily_vibe_llm,
)
from .services.personalized_daily import (
    build_personalized_daily_facts,
    summarize_personalization_for_prompt,
)
from .services.scheduler import start_scheduler
from .auth import authenticate_telegram_user, get_current_user, get_current_user_from_query, get_admin_user
from .reporting.static_content import SECTION_INTROS

# #START_BLOCK_LOGGER
logger = structlog.get_logger()


def log_admin_report_event(event: str, *, admin: User | None = None, report: Report | None = None, **fields):
    payload = {key: value for key, value in fields.items() if value is not None}
    if admin is not None:
        payload["admin_user_id"] = str(admin.id)
    if report is not None:
        payload["report_id"] = str(report.id)
        payload["report_type"] = report.report_type
        payload["report_status"] = report.status
        payload["client_id"] = str(report.client_id)
    logger.info(event, **payload)
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

@app.get("/api/admin/feedback", response_model=List[dict])
def list_admin_feedback(
    limit: int = 20,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: List recent user feedback.
    """
    rows = (
        db.query(ReportFeedback)
        .order_by(ReportFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    res = []
    for r in rows:
        res.append({
            "id": str(r.id),
            "report_id": str(r.report_id),
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
            "report_type": r.report.report_type if r.report else "unknown",
            "client_name": r.report.client.full_name if r.report and r.report.client else "—"
        })
    return res



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

@app.get("/api/admin/audit", response_model=List[AdminAuditLogOut])
def list_admin_audit_logs(
    limit: int = 50,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    # PURPOSE: View audit logs for security and history.
    """
    from .models import AuditLog
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    
    if user_id:
        try:
            uid = uuid.UUID(user_id)
            query = query.filter(or_(AuditLog.target_user_id == uid, AuditLog.admin_id == uid))
        except ValueError:
            pass
            
    if action:
        query = query.filter(AuditLog.action == action)
        
    logs = query.limit(limit).all()
    
    res = []
    for l in logs:
        res.append({
            "id": str(l.id),
            "admin_id": str(l.admin_id) if l.admin_id else None,
            "target_user_id": str(l.target_user_id) if l.target_user_id else None,
            "action": l.action,
            "reason": l.reason,
            "details": l.details,
            "created_at": format_datetime(l.created_at),
            "admin_name": l.admin.full_name if l.admin else "System",
            "target_user_name": l.target_user.full_name if l.target_user else "—"
        })
    return res

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

@app.get("/api/admin/users/{user_id}", response_model=AdminUserDetailOut)

def get_admin_user_detail(

    user_id: str,

    db: Session = Depends(get_db),

    admin: User = Depends(get_admin_user)

):
    """
    # PURPOSE: Get full user profile for admin.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
        
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Reports
    reports = (
        db.query(Report)
        .filter(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Transactions
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Referrals
    from .models import Referral
    ref_count = db.query(func.count(Referral.id)).filter(Referral.referrer_id == user.id).scalar() or 0
    report_count = db.query(func.count(Report.id)).filter(Report.user_id == user.id).scalar() or 0

    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "username": user.username,
        "balance": float(user.balance),
        "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
        "created_at": user.created_at.isoformat(),
        "is_partner": user.is_partner,
        "referral_code": user.referral_code,
        "reports_count": report_count,
        "referrals_count": ref_count,
        "recent_reports": [
            {
                "id": str(r.id),
                "type": r.report_type,
                "status": r.status,
                "created_at": r.created_at.isoformat()
            } for r in reports
        ],
        "recent_transactions": [
            {
                "id": str(t.id),
                "amount": float(t.amount),
                "type": t.type,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            } for t in txs
        ]
    }

@app.post("/api/admin/users/{user_id}/subscription/add-days")
def admin_add_subscription_days(
    user_id: str, 
    payload: AdminUserUpdateDays,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Manually extend user subscription (Audit Logged).
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
    
    # Audit Log
    from .models import AuditLog
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=user.id,
        action="add_subscription_days",
        reason=payload.reason,
        details=json.dumps({"days": payload.days})
    )
    db.add(audit)
        
    db.commit()
    return {"status": "ok", "new_date": format_datetime(user.subscription_active_until)}

@app.post("/api/admin/users/{user_id}/balance/add")
def admin_add_balance(
    user_id: str,
    payload: AdminUserUpdateBalance,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Manually add credits/money (Audit Logged).
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
    
    # Audit Log
    from .models import AuditLog
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=user.id,
        action="add_balance",
        reason=payload.reason,
        details=json.dumps({"amount": payload.amount})
    )
    db.add(audit)

    db.commit()
    return {"status": "ok", "new_balance": float(user.balance)}

class AdminGrantRequest(BaseModel):
    type: str # 'credits', 'report'
    amount: Optional[int] = None
    report_type: Optional[str] = None
    reason: str = Field(..., min_length=3)

    @validator("report_type", pre=True)
    @classmethod
    def normalize_report_type_value(cls, value: Optional[str]) -> Optional[str]:
        return normalize_report_type(value)

@app.post("/api/admin/users/{user_id}/grant")
def admin_grant_item(
    user_id: str,
    payload: AdminGrantRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    # PURPOSE: Grant credits or specific report to user.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
        
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from .models import AuditLog
    details = {}

    if payload.type == "credits":
        if not payload.amount:
            raise HTTPException(status_code=400, detail="Amount required for credits")
        
        # Add transaction
        trx = Transaction(
            user_id=user.id,
            amount=payload.amount,
            currency="CRD",
            type="admin_grant",
            status="success",
            provider_id=f"grant_{admin.id}_{datetime.now().timestamp()}"
        )
        db.add(trx)
        details["amount"] = payload.amount
        details["currency"] = "CRD"

    elif payload.type == "report":
        if not payload.report_type:
            raise HTTPException(status_code=400, detail="Report type required")

        report_type = payload.report_type
        entitlement = None
        one_off_admin_grant = is_one_off_report_type(report_type)

        # Check profile
        if not user.birth_date or not user.birth_place:
            raise HTTPException(status_code=400, detail="User profile incomplete, cannot generate report.")

        # Create Report
        birth_dt_iso = user.birth_date
        if user.birth_time:
            birth_dt_iso = f"{user.birth_date}T{user.birth_time}:00"

        wf_payload = ReportWorkflowRequest(
            client_name=user.full_name or "User",
            client_note=f"Gift from admin {admin.telegram_id}",
            birth_date=birth_dt_iso,
            birth_location=user.birth_place,
            birth_lat=user.birth_lat,
            birth_lon=user.birth_lon,
            report_type=report_type,
            house_system="placidus",
            include_fixed_stars=True
        )
        
        # Upsert client (reuse logic?)
        # We can just use user_id directly if we link it. 
        # But Report model needs client_id. 
        # Upsert client from payload helper:
        client = upsert_client_from_payload(wf_payload, db, owner_user_id=user.id)
        db.flush()

        if one_off_admin_grant:
            entitlement = grant_report_entitlement(
                db,
                user_id=user.id,
                report_type=report_type,
                source=EntitlementSource.ADMIN_GRANT,
                notes=payload.reason,
            )

        report = Report(
            client_id=client.id,
            user_id=user.id,
            report_type=report_type,
            status="in_progress",
            paid=not one_off_admin_grant,
            is_test=user.is_test
        )
        report.input_payload = json.dumps(wf_payload.model_dump(), ensure_ascii=True)
        db.add(report)
        db.flush()

        if entitlement is not None:
            try:
                consume_report_access(
                    user,
                    report,
                    db,
                    decision=allow_access(
                        report_type,
                        AccessGrantSource.REPORT_ENTITLEMENT,
                        entitlement_id=str(entitlement.id),
                        remaining_unlocks=1,
                    ),
                )
            except AccessConsumptionError as exc:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=f"Admin grant could not be consumed: {exc}",
                ) from exc

        # Run generation
        section_specs = build_section_specs(wf_payload)
        initialize_report_chunks(report, section_specs, db, reset=True)
        
        background_tasks.add_task(
            run_report_generation, report.id, wf_payload.model_dump(), False
        )

        details["report_type"] = report_type
        details["report_id"] = str(report.id)
        if entitlement is not None:
            details["entitlement_id"] = str(entitlement.id)
            details["access_source"] = report.access_source
            details["grant_model"] = "entitlement_first"

    else:
        raise HTTPException(status_code=400, detail="Invalid grant type")

    # Audit
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=user.id,
        action=f"grant_{payload.type}",
        reason=payload.reason,
        details=json.dumps(details)
    )
    db.add(audit)
    db.commit()
    
    return {"status": "ok", "details": details}

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

@app.get("/api/admin/users", response_model=List[AdminUserOut])
def list_admin_users(
    limit: int = 50, 
    q: Optional[str] = None, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
    
    results = []
    for u in users:
        credits = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == u.id, 
            Transaction.currency == "CRD"
        ).scalar() or 0
        
        results.append({
            "id": str(u.id),
            "telegram_id": u.telegram_id,
            "full_name": u.full_name,
            "username": u.username,
            "balance": float(u.balance),
            "subscription_active_until": format_datetime(u.subscription_active_until),
            "created_at": format_datetime(u.created_at),
            "is_partner": u.is_partner,
            "referral_code": u.referral_code,
            "horary_credits": int(credits)
        })
    
    return results


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
    payload: Any, 
    db: Session,
    owner_user_id: Optional[uuid.UUID] = None
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
        if getattr(payload, "client_note", None) is not None:
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

    # Resolve User ID
    final_user_id = owner_user_id
    if not final_user_id and hasattr(payload, "user_id") and payload.user_id:
        try:
            final_user_id = uuid.UUID(payload.user_id)
        except ValueError:
            pass

    birth_dt = parse_birth_datetime(payload.birth_date, payload.birth_timezone)
    client = Client(
        full_name=payload.client_name,
        user_id=final_user_id,
        notes=getattr(payload, "client_note", None),
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
    return client
# #END_BLOCK_REPORT_WORKFLOW_UTILS

# #START_BLOCK_ENDPOINTS
from sqlalchemy import func, or_, text

@app.get("/health")
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """
    # PURPOSE: Check service availability and DB connection.
    # INPUT: None.
    # OUTPUT: {"status": "ok", "db": "connected"}.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error("health.db_fail", error=str(e))
        return {"status": "error", "db": str(e)}


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

        generated_sections, _ = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=reset_chunks,
            raise_on_error=False,
            run=run,
        )
        if report.status == "completed":
            finish_report_run(run, db, "completed")
            if report.report_type == "week_forecast":
                logger.info("week_generate_succeeded", user_id=str(report.user_id), report_id=str(report.id))
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
            if report.report_type == "week_forecast":
                logger.error("week_generate_failed", user_id=str(report.user_id), report_id=str(report.id), error=report.error_message)
            finish_report_run(run, db, "failed", error_message=report.error_message)
    except Exception as exc:
        if report:
            if report.report_type == "week_forecast":
                logger.error("week_generate_failed", user_id=str(report.user_id), report_id=str(report.id), error=str(exc))
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
        section_context = build_section_context(section_id, context, chart_data)
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
        fallback_models = []
        if llm_mode in {"openrouter", "cheap"}:
            model = resolve_llm_fallback_model()
            if model:
                fallback_models = [model]
        use_template = llm_mode in {"fallback", "local", "mock", "stub"}

        try:
            result = await generate_section_content(
                target_spec,
                section_context,
                chart_data,
                llm_client,
                fallback_models,
                retry_attempts,
                use_template
            )
            content = result.content
            usage = result.usage
            if usage and run:
                run.prompt_tokens = usage.get("prompt_tokens", 0)
                run.completion_tokens = usage.get("completion_tokens", 0)
                run.total_tokens = usage.get("total_tokens", 0)
                run.estimated_cost = Decimal(str(round(run.total_tokens * 0.0000001, 4)))
                db.commit()
        except Exception as exc:
            if should_fallback_on_llm_error(exc) or isinstance(exc, LLMContentValidationError):
                error_message = str(exc)
                if isinstance(exc, LLMContentValidationError):
                    content = inject_planet_emojis(
                        build_section_validation_fallback_content(target_spec, section_context)
                    )
                else:
                    content = inject_planet_emojis(
                        build_section_fallback_content(target_spec, section_context)
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

        # Markdown assembly removed (JSON-only pipeline)

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


def _legacy_workflow_requires_structured_access(report_type: str) -> bool:
    from .core.feature_flags import is_one_off_entitlements_runtime_enabled
    from .services.one_off_entitlements import is_one_off_report_type

    return is_one_off_entitlements_runtime_enabled() and is_one_off_report_type(report_type)


def _resolve_legacy_workflow_access(user: User, report_type: str, db: Session):
    from .services.access_control import check_user_access, resolve_report_access

    if _legacy_workflow_requires_structured_access(report_type):
        access_decision = resolve_report_access(user, report_type, db)
        if access_decision.allowed:
            return access_decision
    elif check_user_access(user, report_type, db):
        return None

    if report_type == "week_forecast":
        logger.warning("week_generate_failed", user_id=str(user.id), error="Access denied / No subscription")
    raise HTTPException(
        status_code=402,
        detail=(
            f"Generation of {report_type} is not available. "
            "Please check your entitlements or subscribe."
        ),
    )


def _consume_legacy_workflow_access_if_needed(
    user: User,
    report: Report,
    db: Session,
    *,
    access_decision,
) -> None:
    if access_decision is None:
        return

    from .services.access_control import AccessConsumptionError, consume_report_access

    try:
        consume_report_access(user, report, db, decision=access_decision)
    except AccessConsumptionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Access could not be consumed: {exc}",
        ) from exc


@app.post(
    "/api/workflows/report/async",
    response_model=ReportWorkflowStartResponse,
)
async def create_report_async(
    payload: ReportWorkflowRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Run an end-to-end report generation workflow asynchronously.
    # INPUT: ReportWorkflowRequest payload.
    # OUTPUT: ReportWorkflowStartResponse.
    # CONTEXT: Primary entry point for report generation with progress UI.
    """
    client = upsert_client_from_payload(payload, db)
    db.flush()

    access_decision = _resolve_legacy_workflow_access(user, payload.report_type, db)

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
    _consume_legacy_workflow_access_if_needed(
        user,
        report,
        db,
        access_decision=access_decision,
    )

    if payload.report_type == "week_forecast":
        logger.info("week_generate_started", user_id=str(user.id), report_id=str(report.id))

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


@app.post(
    "/api/workflows/report",
    response_model=ReportWorkflowResponse,
)
async def create_report(
    payload: ReportWorkflowRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Run an end-to-end report generation workflow synchronously.
    # INPUT: ReportWorkflowRequest payload.
    # OUTPUT: ReportWorkflowResponse with sections and chart.
    # CONTEXT: Legacy/Dev entry point for direct report generation.
    """
    client = upsert_client_from_payload(payload, db)
    db.flush()

    access_decision = _resolve_legacy_workflow_access(user, payload.report_type, db)

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
    _consume_legacy_workflow_access_if_needed(
        user,
        report,
        db,
        access_decision=access_decision,
    )

    if payload.report_type == "week_forecast":
        logger.info("week_generate_started", user_id=str(user.id), report_id=str(report.id))

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
        generated_sections, chart_data = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=True,
            raise_on_error=True,
            run=run,
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
        "sections": generated_sections,
        "chart": chart_data,
    }


@app.post(
    "/api/admin/reports/{report_id}/regenerate",
    response_model=ReportRegenerateResponse,
)
async def regenerate_report(
    report_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
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
        generated_sections, chart_data = await generate_report_sections(
            report,
            payload,
            db,
            llm_client=llm_client,
            llm_mode=llm_mode,
            reset_chunks=True,
            raise_on_error=True,
            run=run,
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
    admin: User = Depends(get_admin_user)
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
    report_id: str,
    section_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
        log_admin_report_event("admin.error", admin=admin, report=report, stage="section_missing", section_id=section_id)
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
        section_context = build_section_context(section_id, context, chart_data)
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
            fallback_models = []
            if llm_mode in {"openrouter", "cheap"}:
                model = resolve_llm_fallback_model()
                if model:
                    fallback_models = [model]
            use_template = llm_mode in {"fallback", "local", "mock", "stub"}

            result = await generate_section_content(
                target_spec,
                section_context,
                chart_data,
                llm_client,
                fallback_models,
                retry_attempts,
                use_template
            )
            content = result.content
            
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
            if should_fallback_on_llm_error(exc) or isinstance(exc, LLMContentValidationError):
                if isinstance(exc, LLMContentValidationError):
                    content = inject_planet_emojis(
                        build_section_validation_fallback_content(target_spec, section_context)
                    )
                else:
                    content = inject_planet_emojis(build_section_fallback_content(target_spec, section_context))
                generated_sections = [
                    SectionResultOut(
                        section_id=target_spec.section_id,
                        title=target_spec.title,
                        content=content,
                    )
                ]
                logger.warning(
                    "report.section.regen.fallback",
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
    admin: User = Depends(get_admin_user)
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
    log_admin_report_event("admin.section_regenerate", admin=admin, report=report, section_id=section_id, stage="queued", pending=sum(1 for chunk in report.chunks if chunk.status == "pending"), running=sum(1 for chunk in report.chunks if chunk.status == "in_progress"), error=sum(1 for chunk in report.chunks if chunk.status in {"failed", "error"}))
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


class AdminRegenerateRequest(BaseModel):
    reason: Optional[str] = None

@app.post("/api/admin/reports/{report_id}/regenerate_copy")
def regenerate_report_copy(
    report_id: str,
    payload: Optional[AdminRegenerateRequest] = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    # PURPOSE: Create a fresh copy of a report and regenerate it.
    """
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    old_report = db.query(Report).filter(Report.id == rid).first()
    if not old_report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Clone logic
    new_report = Report(
        client_id=old_report.client_id,
        user_id=old_report.user_id,
        report_type=old_report.report_type,
        status="in_progress",
        paid=old_report.paid,
        is_test=old_report.is_test,
        input_payload=old_report.input_payload # Copy payload
    )
    db.add(new_report)
    db.commit()
    
    # Audit
    from .models import AuditLog
    reason = payload.reason if payload else "Manual regeneration"
    audit = AuditLog(
        admin_id=admin.id,
        target_user_id=old_report.user_id,
        action="regenerate_copy",
        reason=reason,
        details=json.dumps({"original_id": str(old_report.id), "new_id": str(new_report.id)})
    )
    db.add(audit)
    db.commit()
    
    # Start generation
    if new_report.input_payload:
        try:
            payload_data = json.loads(new_report.input_payload)
            # Re-init chunks
            section_specs = build_section_specs(ReportWorkflowRequest.model_validate(payload_data))
            initialize_report_chunks(new_report, section_specs, db, reset=True)
            db.commit()
            
            background_tasks.add_task(
                run_report_generation, new_report.id, payload_data, False
            )
        except Exception as e:
            logger.error("regen.copy.failed", error=str(e))
            
    return {"status": "ok", "new_report_id": str(new_report.id)}

@app.get("/api/admin/stats", response_model=AdminStatsOut)
def get_admin_stats(
    days: int = 7,
    show_test: bool = False,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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

    feedback_stats = db.query(
        func.avg(ReportFeedback.rating),
        func.count(ReportFeedback.id)
    ).first()
    
    feedback_avg = float(feedback_stats[0]) if feedback_stats[0] else 0
    feedback_count = int(feedback_stats[1]) if feedback_stats[1] else 0

    # Entitlement Stats
    total_balance = db.query(func.sum(User.balance)).scalar() or 0
    active_subs = db.query(func.count(User.id)).filter(User.subscription_active_until > datetime.now(timezone.utc)).scalar() or 0
    horary_credits = db.query(func.sum(Transaction.amount)).filter(Transaction.currency == "CRD").scalar() or 0

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
        "feedback_avg": feedback_avg,
        "feedback_count": feedback_count,
        "entitlements": {
            "total_balance_rub": float(total_balance),
            "active_subscriptions": active_subs,
            "outstanding_credits": int(horary_credits)
        }
    }


@app.get("/api/admin/tasks", response_model=List[AdminTaskOut])
def get_admin_tasks(
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
    admin: User = Depends(get_admin_user)
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
        "user_id": str(client.user_id) if client.user_id else None,
        "full_name": client.full_name,
        "email": client.email,
        "notes": client.notes,
        "birth_datetime": format_datetime(client.birth_datetime),
        "birth_time_known": client.birth_time_known,
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
def create_admin_client(
    payload: AdminClientCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
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
        user_id=uuid.UUID(payload.user_id) if payload.user_id else None,
        notes=payload.client_note,
        birth_datetime=birth_dt,
        birth_time_known=payload.birth_time_known,
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
    client.birth_time_known = payload.birth_time_known
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
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
    admin: User = Depends(get_admin_user)
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
    log_admin_report_event("admin.queue", admin=admin, stage="list", queue_size=len(rows), status_filter=status, show_test=show_test)

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
    admin: User = Depends(get_admin_user)
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
        log_admin_report_event("admin.error", admin=admin, stage="detail_missing", target_report_id=report_id)
        raise HTTPException(status_code=404, detail="Report not found.")
    log_admin_report_event("admin.entry", admin=admin, report=report, stage="detail", include_content=include_content, chunk_count=len(report.chunks), run_count=len(report.runs))

    chunks_sorted = sorted(report.chunks, key=lambda item: item.order_index)
    payload_data = safe_load_report_payload_data(report)
    section_specs = load_section_specs_for_report(report, payload_data)
    title_map = {spec.section_id: spec.title for spec in section_specs}
    chunks_payload = []
    for chunk in chunks_sorted:
        content_html = None
        # Legacy markdown_to_html removed
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
                "prompt_tokens": run.prompt_tokens,
                "completion_tokens": run.completion_tokens,
                "total_tokens": run.total_tokens,
                "estimated_cost": float(run.estimated_cost),
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
            log_admin_report_event("admin.error", admin=admin, report=report, stage="chart_svg_failed")

    return {
        "report": report_payload,
        "chunks": chunks_payload,
        "runs": runs_payload,
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
    admin: User = Depends(get_admin_user)
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
        log_admin_report_event("admin.error", admin=admin, stage="section_report_missing", target_report_id=report_id, section_id=section_id)
        raise HTTPException(status_code=404, detail="Report not found.")

    chunk = next((item for item in report.chunks if item.section == section_id), None)
    if not chunk:
        log_admin_report_event("admin.error", admin=admin, report=report, stage="section_missing", section_id=section_id)
        raise HTTPException(status_code=404, detail="Section not found.")
    log_admin_report_event("admin.entry", admin=admin, report=report, stage="section_detail", section_id=section_id, include_content=include_content, section_status=chunk.status)

    payload_data = safe_load_report_payload_data(report)
    section_specs = load_section_specs_for_report(report, payload_data)
    title_map = {spec.section_id: spec.title for spec in section_specs}

    content_html = None
    # Legacy markdown_to_html removed

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

@app.get("/api/users/me", response_model=UserProfileOut)
def get_my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: Get current user profile for Telegram WebApp.
    """
    if not user.referral_code:
        from .services.code_gen import generate_referral_code
        user.referral_code = generate_referral_code()
        db.add(user)
        db.commit()
        db.refresh(user)

    now = datetime.now(timezone.utc)
    days_left = 0
    if user.subscription_active_until:
        sub_end = user.subscription_active_until
        if sub_end.tzinfo is None: sub_end = sub_end.replace(tzinfo=timezone.utc)
        delta = sub_end - now
        days_left = max(0, delta.days)

    from .models import Referral, Transaction, Report
    from .services.access_control import build_report_access_snapshot, check_user_access
    from .core.feature_flags import get_feature_flag_snapshot
    from .services.one_off_entitlements import build_report_unlock_snapshot
    
    referrals_count = db.query(Referral).filter(Referral.referrer_id == user.id).count()
    
    # Horary Stats
    horary_balance = int(
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user.id)
        .filter(Transaction.currency == "CRD")
        .scalar() or 0
    )
    
    from .services.access_control import get_local_week_start_utc
    monday_utc = get_local_week_start_utc(user)
    
    quota_used = (
        db.query(func.count(Report.id))
        .filter(Report.user_id == user.id)
        .filter(Report.report_type.in_(["horary", "horary_answer", "horary_full"]))
        .filter(Report.created_at >= monday_utc)
        .scalar()
    ) or 0

    log_analytics_event(db, "app_open", user_id=user.id, telegram_id=user.telegram_id, source="webapp")

    return {
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "is_partner": user.is_partner,
        "is_test": user.is_test,
        "balance": float(user.balance),
        "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
        "days_left": days_left,
        "birth_time_known": user.birth_time_known,
        "birth_date": user.birth_date,
        "birth_place": user.birth_place,
        "birth_timezone": user.birth_timezone,
        "current_location": user.current_location,
        "current_lat": user.current_lat,
        "current_lon": user.current_lon,
        "current_timezone": user.current_timezone,
        "sun_sign": user.sun_sign,
        "referral_code": user.referral_code,
        "referrals_count": referrals_count,
        "horary_balance": horary_balance,
        "weekly_quota_used": quota_used,
        "report_unlocks": build_report_unlock_snapshot(db, user_id=user.id),
        "report_access": build_report_access_snapshot(user, db),
        "feature_flags": get_feature_flag_snapshot(),
        "can_access_premium": check_user_access(user, "natal_master", db),
        "can_ask_horary": check_user_access(user, "horary", db)
    }

@app.get("/api/billing/packs")
def list_payment_packs():
    """
    # PURPOSE: Provide list of available horary packs for frontend.
    """
    from .core.config_business import HORARY_PACKS
    return HORARY_PACKS

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

@app.post("/api/reports/{report_id}/feedback", response_model=AnalyticsEventOut)
async def submit_report_feedback(
    report_id: uuid.UUID,
    payload: FeedbackIn,
    db: Session = Depends(get_db),
    x_telegram_auth: Optional[str] = Header(None, alias="X-Telegram-Auth"),
):
    """
    # PURPOSE: Submit user feedback for a report or section.
    # INPUT: report_id, rating, comment.
    # OUTPUT: ok status.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    user_id = None
    # If auth provided, use it
    if x_telegram_auth:
        try:
            from .auth import verify_telegram_auth
            user_data = verify_telegram_auth(x_telegram_auth)
            tg_id = int(user_data["id"])
            user = db.query(User).filter(User.telegram_id == tg_id).first()
            if user:
                user_id = user.id
        except:
            pass
    
    # Fallback to telegram_id in payload if no auth
    if not user_id and payload.telegram_id:
        user = db.query(User).filter(User.telegram_id == payload.telegram_id).first()
        if user:
            user_id = user.id

    feedback = ReportFeedback(
        report_id=report_id,
        user_id=user_id,
        section_id=payload.section_id,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(feedback)
    db.commit()
    
    return {"ok": True}

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

def get_sun_sign(birth_date_str: str) -> str:
    """Determine Sun sign from YYYY-MM-DD string."""
    try:
        dt = datetime.fromisoformat(birth_date_str)
        month, day = dt.month, dt.day
        if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "Aries"
        if (month == 4 and day >= 20) or (month == 5 and day <= 20): return "Taurus"
        if (month == 5 and day >= 21) or (month == 6 and day <= 20): return "Gemini"
        if (month == 6 and day >= 21) or (month == 7 and day <= 22): return "Cancer"
        if (month == 7 and day >= 23) or (month == 8 and day <= 22): return "Leo"
        if (month == 8 and day >= 23) or (month == 9 and day <= 22): return "Virgo"
        if (month == 9 and day >= 23) or (month == 10 and day <= 22): return "Libra"
        if (month == 10 and day >= 23) or (month == 11 and day <= 21): return "Scorpio"
        if (month == 11 and day >= 22) or (month == 12 and day <= 21): return "Sagittarius"
        if (month == 12 and day >= 22) or (month == 1 and day <= 19): return "Capricorn"
        if (month == 1 and day >= 20) or (month == 2 and day <= 18): return "Aquarius"
        return "Pisces"
    except:
        return "Unknown"

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
        if payload.birth_date is not None: 
            user.birth_date = payload.birth_date
            user.sun_sign = get_sun_sign(payload.birth_date)
        if payload.birth_time is not None: user.birth_time = payload.birth_time
        if payload.birth_time_known is not None: user.birth_time_known = payload.birth_time_known
        if payload.birth_place is not None: user.birth_place = payload.birth_place
        if payload.birth_lat is not None: user.birth_lat = payload.birth_lat
        if payload.birth_lon is not None: user.birth_lon = payload.birth_lon
        if payload.birth_timezone is not None: user.birth_timezone = payload.birth_timezone
        if payload.current_location is not None: user.current_location = payload.current_location
        if payload.current_lat is not None: user.current_lat = payload.current_lat
        if payload.current_lon is not None: user.current_lon = payload.current_lon
        if payload.current_timezone is not None: user.current_timezone = payload.current_timezone
        if payload.is_test is not None: user.is_test = payload.is_test

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
            "is_test": user.is_test,
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

@app.get("/api/reports/my", response_model=List[UserReportOut])
def get_my_reports(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    # PURPOSE: List reports belonging to the current user (last 30 days).
    # INPUT: Auth Dependency.
    # OUTPUT: List of user reports.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    reports = (
        db.query(Report)
        .filter(Report.user_id == user.id)
        .filter(Report.created_at >= cutoff)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "report_type": r.report_type,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "client_name": r.client.full_name if r.client else "Unknown",
            "access_source": r.access_source,
        }
        for r in reports
    ]

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

    # Get Chunks
    chunks_out = []
    
    # Sort chunks by order_index
    sorted_chunks = sorted(report.chunks, key=lambda c: c.order_index)
    
    for chunk in sorted_chunks:
        if chunk.section != "input_frame": # Optionally exclude technical chunks
             chunks_out.append({
                 "section": chunk.section,
                 "content": chunk.content,
                 "status": chunk.status,
                 "order_index": chunk.order_index
             })

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
            "client_name": report.client.full_name if report.client else "Unknown",
            "access_source": report.access_source,
        },
        "chart_svg": chart_svg,
        "chunks": chunks_out
    }



@app.post("/api/reports/{report_id}/regenerate", response_model=ReportWorkflowStartResponse)
def user_regenerate_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Allow user to retry generation of a failed report.
    # INPUT: report_id.
    # OUTPUT: ReportWorkflowStartResponse.
    """
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    report = db.query(Report).filter(Report.id == rid, Report.user_id == user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed reports can be regenerated by user")
        
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

# #START_BLOCK_FEED_ENDPOINT
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

    class Config:
        arbitrary_types_allowed = True

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


def _build_feed_payload(
    now: datetime,
    moon_sign: str,
    moon_phase: str,
    moon_emoji: str,
    general_vibe: str,
    aspects_count: int,
    traffic_lights: Optional[dict] = None,
    moon: Optional[dict] = None,
    fast_hits: Optional[list] = None,
    personalization_level: Optional[str] = None,
    meta: Optional[dict] = None,
) -> dict:
    return {
        "date": now.strftime("%d.%m.%Y"),
        "moon_sign": moon_sign,
        "moon_phase": moon_phase,
        "moon_emoji": moon_emoji,
        "aspects_count": aspects_count,
        "general_vibe": general_vibe,
        "traffic_lights": traffic_lights or {
            "health": "yellow",
            "money": "yellow",
            "love": "yellow",
        },
        "moon": moon or {"sign": moon_sign, "phase": moon_phase, "emoji": moon_emoji},
        "fast_hits": fast_hits or [],
        "personalization_level": personalization_level,
        "meta": meta,
    }

@app.get("/api/feed/today", response_model=FeedOut)
async def get_daily_feed(
    request: Request,
    debug: bool = Query(False),
    x_telegram_auth: Optional[str] = Header(None, alias="X-Telegram-Auth"),
    x_feed_debug: Optional[str] = Header(None, alias="X-Feed-Debug"),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Get daily astrological feed (Moon, Vibe) with real LLM advice.
    # INPUT: Optional Telegram auth header for personalized context.
    # OUTPUT: FeedOut object.
    """
    now = datetime.now(timezone.utc)
    user = None
    auth_mode = "none"
    logger.info(
        "feed.entry",
        stage="request_start",
        path=str(request.url.path),
        debug=bool(debug),
        has_auth_header=bool(x_telegram_auth),
    )
    if x_telegram_auth:
        try:
            user = authenticate_telegram_user(x_telegram_auth, db)
            auth_mode = "telegram"
        except HTTPException as exc:
            auth_mode = "fallback_anonymous"
            logger.info(
                "feed.debug",
                stage="auth_fallback",
                path=str(request.url.path),
                auth_mode=auth_mode,
                reason="telegram_auth_invalid",
                detail=exc.detail,
            )

    debug_enabled = debug or str(x_feed_debug or "").lower() in {"1", "true", "yes", "on"}

    fallback_sign = "Луна"
    fallback_phase = "Текущий день"
    fallback_vibe = build_daily_vibe_fallback(fallback_sign, fallback_phase, "Нет мажорных аспектов")

    try:
        facts = build_personalized_daily_facts(now, user=user)
        prompt_context = summarize_personalization_for_prompt(facts)
        logger.info(
            "feed.debug",
            stage="llm_prompt_path",
            path=str(request.url.path),
            auth_mode=auth_mode,
            personalization_level=prompt_context.get("level"),
            cache_scope=prompt_context.get("cache_scope"),
            prompt_path=prompt_context.get("prompt_contract"),
        )
        vibe = await get_daily_vibe_llm(
            facts["moon_sign"],
            facts["moon_phase"],
            facts["aspect_summary"],
            personalization_context=prompt_context,
            cache_scope=prompt_context.get("cache_scope"),
        )

        logger.info(
            "feed.debug",
            stage="request_success",
            auth_mode=auth_mode,
            personalization_level=facts.get("personalization_level"),
            cache_scope=facts.get("cache_scope"),
            debug=debug_enabled,
            path=str(request.url.path),
            fallback_mode=bool((facts.get("meta") or {}).get("fallback_mode")),
        )
        return _build_feed_payload(
            now,
            moon_sign=facts["moon_sign"],
            moon_phase=facts["moon_phase"],
            moon_emoji=facts["moon_emoji"],
            general_vibe=vibe,
            aspects_count=int(facts.get("aspects_count", 0) or 0),
            traffic_lights=facts.get("traffic_lights"),
            moon={"sign": facts.get("moon_sign"), "phase": facts.get("moon_phase"), "emoji": facts.get("moon_emoji")},
            fast_hits=facts.get("fast_hits") or [],
            personalization_level=facts.get("personalization_level"),
            meta=(facts.get("meta") if debug_enabled and bool(x_telegram_auth) else None),
        )
    except Exception as exc:
        logger.error(
            "feed.error",
            stage="fallback_path",
            error=str(exc),
            auth_mode=auth_mode,
            debug=debug_enabled,
            path=str(request.url.path),
            fallback_reason="endpoint_error",
        )
        return _build_feed_payload(
            now,
            moon_sign=fallback_sign,
            moon_phase=fallback_phase,
            moon_emoji="🌙",
            general_vibe=fallback_vibe,
            aspects_count=0,
            traffic_lights={
                "health": "yellow",
                "money": "yellow",
                "love": "yellow",
            },
            moon={"sign": fallback_sign, "phase": fallback_phase, "emoji": "🌙"},
            fast_hits=[],
            personalization_level="anonymous",
            meta=({"fallback": True, "reason": "endpoint_error"} if debug_enabled and bool(x_telegram_auth) else None),
        )
# #END_BLOCK_FEED_ENDPOINT


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


def _validate_b2c_report_inputs(payload: B2CReportCreateRequest) -> None:
    if payload.report_type != "synastry":
        return

    missing_fields = []
    if not (payload.partner_birth_date or "").strip():
        missing_fields.append("partner_birth_date")
    if not (payload.partner_birth_location or "").strip():
        missing_fields.append("partner_birth_location")

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=(
                "Synastry requires partner birth date/time and partner birth location "
                f"({', '.join(missing_fields)})."
            ),
        )


@app.post("/api/reports/create", response_model=ReportWorkflowStartResponse)
def create_b2c_report(
    payload: B2CReportCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: B2C Endpoint to create a report (consumes quota/credits).
    # INPUT: report_type, question.
    # OUTPUT: Report metadata.
    """
    from .services.access_control import (
        AccessConsumptionError,
        consume_report_access,
        resolve_report_access,
    )
    
    _validate_b2c_report_inputs(payload)

    # 1. Resolve access before creating the report row.
    access_decision = resolve_report_access(user, payload.report_type, db)
    if not access_decision.allowed:
        raise HTTPException(
            status_code=402,
            detail="Access unavailable. Please check your subscription or payment status."
        )

    # 2. Build Payload from User Profile
    if not user.birth_date or not user.birth_place:
        raise HTTPException(
            status_code=400, 
            detail="Profile incomplete. Please set birth data in Profile."
        )

    # Parse User Birth Date
    # user.birth_date is "YYYY-MM-DD", user.birth_time is "HH:MM"
    birth_dt_iso = user.birth_date
    if user.birth_time:
        birth_dt_iso = f"{user.birth_date}T{user.birth_time}:00"
    
    # Prepare Workflow Request
    # We create a new Client record for this report to ensure data isolation/snapshotting
    # or reuse if we had logic for that. For now, create new to be safe.
    
    solar_current_location = payload.solar_current_location
    solar_current_lat = payload.solar_current_lat
    solar_current_lon = payload.solar_current_lon
    solar_current_timezone = payload.solar_current_timezone
    solar_current_place_id = payload.solar_current_place_id

    if not solar_current_location:
        solar_current_location = user.current_location or user.birth_place
        solar_current_lat = user.current_lat or user.birth_lat
        solar_current_lon = user.current_lon or user.birth_lon
        solar_current_timezone = user.current_timezone or user.birth_timezone

    wf_payload = ReportWorkflowRequest(
        client_name=user.full_name or "User",
        client_note=f"Telegram ID: {user.telegram_id}",
        question=payload.question,
        birth_date=birth_dt_iso,
        birth_location=user.birth_place,
        birth_lat=user.birth_lat,
        birth_lon=user.birth_lon,
        birth_timezone=user.birth_timezone,
        partner_name=payload.partner_name,
        partner_birth_date=payload.partner_birth_date,
        partner_birth_location=payload.partner_birth_location,
        partner_birth_lat=payload.partner_birth_lat,
        partner_birth_lon=payload.partner_birth_lon,
        partner_birth_timezone=payload.partner_birth_timezone,
        partner_birth_place_id=payload.partner_birth_place_id,
        solar_current_location=solar_current_location,
        solar_current_lat=solar_current_lat,
        solar_current_lon=solar_current_lon,
        solar_current_timezone=solar_current_timezone,
        solar_current_place_id=solar_current_place_id,
        report_type=payload.report_type,
        birth_time_known=user.birth_time_known if user.birth_time_known is not None else True,
        llm_mode=payload.llm_mode,
        house_system="placidus", # Default
        include_fixed_stars=True
    )
    
    # 3. Create Client & Report
    client = upsert_client_from_payload(wf_payload, db, owner_user_id=user.id)
    db.flush()
    
    report = Report(
        client_id=client.id,
        user_id=user.id,
        report_type=payload.report_type,
        status="in_progress",
        paid=False, # Marked as paid only if direct money transaction? Or generic "authorized"?
                    # Let's keep False, as it wasn't a direct "purchase" of this specific report object,
                    # but a consumption of rights.
        is_test=user.is_test
    )
    report.input_payload = json.dumps(wf_payload.model_dump(), ensure_ascii=True)
    db.add(report)
    db.flush()

    try:
        consume_report_access(user, report, db, decision=access_decision)
    except AccessConsumptionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Access could not be consumed: {exc}",
        ) from exc
    
    # 4. Initialize & Run
    section_specs = build_section_specs(wf_payload)
    initialize_report_chunks(report, section_specs, db, reset=True)
    db.commit()
    
    background_tasks.add_task(
        run_report_generation, report.id, wf_payload.model_dump(), False
    )
    
    if payload.report_type == "week_forecast":
        logger.info("week_generate_started", user_id=str(user.id), report_id=str(report.id))

    # 5. Notify if Horary
    if payload.report_type.startswith("horary"):
        # Log analytics
        log_analytics_event(
            db,
            "horary_asked",
            user_id=user.id,
            telegram_id=user.telegram_id,
            source="webapp",
            metadata={"question_len": len(payload.question or "")}
        )

    return {
        "report_id": str(report.id),
        "client_id": str(client.id),
        "status": report.status
    }

# #END_BLOCK_USER_ENDPOINTS
# #END_BLOCK_ENDPOINTS
