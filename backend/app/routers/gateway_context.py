# START_MODULE_CONTRACT: M-API-GATEWAY-CONTEXT
# purpose: Provide shared API gateway imports, logging, and helper contracts for extracted routers.
# owns:
#   - backend/app/routers/context.py
# invariants:
#   - preserve extracted main.py route behavior and dependency semantics
#   - keep auth and access-control dependencies unchanged
# non_goals:
#   - product behavior redesign
# END_MODULE_CONTRACT: M-API-GATEWAY-CONTEXT

# START_MODULE_MAP: M-API-GATEWAY-CONTEXT
# public_entrypoints:
#   - shared helper functions
# semantic_blocks:
#   - ROUTER_EXTRACTION: moved gateway code with stable route contracts
# END_MODULE_MAP: M-API-GATEWAY-CONTEXT

import asyncio
import copy
import json
import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Any

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response, Header, Query
from pydantic import ValidationError
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session
import structlog

from stellium_engine import StelliumEngine

from ..db import Base, SessionLocal, apply_runtime_migrations, engine, get_db
from ..diagnostics import run_diagnostics
from ..geonames import GeoNamesError, get_timezone, search_geonames
from ..llm.mode import resolve_llm_mode, build_llm_client
from ..llm.orchestrator import LLMContentValidationError
from ..models import (
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
from ..reporting.chart_renderer import build_natal_chart_svg
from ..services.report_workflow import (
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
from ..services.access_control import AccessConsumptionError, consume_report_access
from ..services.analytics import ALLOWED_ANALYTICS_EVENTS, log_analytics_event
from ..services.one_off_entitlements import (
    AccessGrantSource,
    EntitlementSource,
    allow_access,
    grant_report_entitlement,
    is_one_off_report_type,
    normalize_report_type,
)
from ..catalog_logging import (
    log_bridge_resume_start,
    log_bridge_resume_success,
    log_catalog_surface_error,
    log_checkout_decision,
    log_checkout_denied,
    log_checkout_error,
    log_checkout_start,
    log_checkout_success,
    log_history_error,
    log_history_start,
    log_history_success,
    log_report_detail_error,
    log_report_detail_start,
    log_report_detail_success,
)
from ..services.feed_service import build_daily_vibe_fallback, get_daily_vibe_llm
from ..services.day_brief import build_day_brief_telemetry, build_day_brief_payload
from ..logging_utils import get_correlation_ids, log_grace_event
from ..services.day_brief_types import DayBrief as DayBriefDTO
from ..services.week_brief_service import build_week_brief_envelope, build_week_brief_payload
from ..services.personalized_daily import (
    build_personalized_daily_facts,
    summarize_personalization_for_prompt,
)
from ..services.week_map import build_week_map
from ..auth import authenticate_telegram_user, get_current_user, get_current_user_from_query, get_admin_user
from ..reporting.static_content import SECTION_INTROS
from ..api_schemas import *
from ..api_helpers import (
    extract_birth_year,
    format_datetime,
    format_report_subtitle,
    format_report_title,
    get_moon_phase_emoji,
    get_phase_name,
    parse_birth_datetime,
    resolve_house_system,
    serialize_chart,
    transliterate_ru_to_en,
)

logger = structlog.get_logger()
API_GATEWAY_MODULE_ID = "M-API-GATEWAY"

# START_BLOCK: ROUTER_EXTRACTION
CONSENT_VERSIONS = {
    "terms": "offer_terms_ru_2026-04-01",
    "privacy": "privacy_policy_ru_2026-04-01",
    "data_processing": "data_processing_consent_ru_2026-04-01",
    "payments": "payments_refunds_ru_2026-04-01",
}


def build_consent_snapshot(*, flow: str, accepted: bool, explicit: bool = True, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "flow": flow,
        "accepted": bool(accepted),
        "explicit": bool(explicit),
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "versions": dict(CONSENT_VERSIONS),
    }
    if extra:
        snapshot.update({key: value for key, value in extra.items() if value is not None})
    return snapshot


def merge_user_consent_log(user: User, *, flow: str, accepted: bool, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    consent_log = dict(user.consent_log or {})
    history = list(consent_log.get("history") or [])
    snapshot = build_consent_snapshot(flow=flow, accepted=accepted, extra=extra)
    history.append(snapshot)
    consent_log.update({
        "current": snapshot,
        "history": history[-20:],
    })
    user.consent_log = consent_log
    return snapshot


def log_consent_event(db: Session, *, user: User, flow: str, accepted: bool, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    snapshot = merge_user_consent_log(user, flow=flow, accepted=accepted, extra=extra)
    try:
        log_analytics_event(
            db,
            "legal_consent_accept",
            user_id=user.id,
            telegram_id=user.telegram_id,
            source="webapp",
            metadata=snapshot,
        )
    except Exception as exc:
        logger.error("analytics.fail", error=str(exc), event="legal_consent_accept")
    return snapshot


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


# START_CONTRACT: FN-LOG-API-GATEWAY-EVENT
def _log_api_gateway_event(level: str, event: str, *, fn: str, block: str, **fields: Any) -> None:
    log_grace_event(
        level,
        event,
        module=API_GATEWAY_MODULE_ID,
        fn=fn,
        block=block,
        **fields,
    )

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

def _legacy_workflow_requires_structured_access(report_type: str) -> bool:
    from ..core.feature_flags import is_one_off_entitlements_runtime_enabled
    from ..services.one_off_entitlements import is_one_off_report_type

    return is_one_off_entitlements_runtime_enabled() and is_one_off_report_type(report_type)


def _resolve_legacy_workflow_access(user: User, report_type: str, db: Session):
    from ..services.access_control import check_user_access, resolve_report_access

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

    from ..services.access_control import AccessConsumptionError, consume_report_access

    try:
        consume_report_access(user, report, db, decision=access_decision)
    except AccessConsumptionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Access could not be consumed: {exc}",
        ) from exc

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
    day_brief: Optional[dict] = None,
    trace_id: Optional[str] = None,
    generation_mode: Optional[str] = None,
    birth_time_used: Optional[bool] = None,
    confidence_bucket: Optional[str] = None,
    factor_count: Optional[int] = None,
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
        "day_brief": day_brief,
        "trace_id": trace_id,
        "generation_mode": generation_mode,
        "birth_time_used": birth_time_used,
        "confidence_bucket": confidence_bucket,
        "factor_count": factor_count,
    }

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
# END_BLOCK: ROUTER_EXTRACTION

__all__ = [name for name in globals() if not name.startswith("__")]
