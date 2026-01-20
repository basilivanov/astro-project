# ############################################################################
# AI_HEADER: MODULE_API
# ROLE: FastAPI entrypoint for raw StelliumEngine data.
# DEPENDENCIES: fastapi, pydantic, stellium_engine.py
# GRACE_ANCHORS: [APP_INIT, API_SCHEMAS, SERIALIZATION, LOGGER, ENDPOINTS]
# ############################################################################

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response, Header
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session
import structlog

from stellium_engine import StelliumEngine

from .db import Base, SessionLocal, apply_runtime_migrations, engine, get_db
from .diagnostics import run_diagnostics
from . import engine_utils
from .geonames import GeoNamesError, get_timezone, search_geonames
from .llm.orchestrator import OpenRouterClient
from .models import Client, Report, ReportChunk, ReportRun, User, Subscription
from .reporting.pdf_reporter import (
    build_natal_chart_svg,
    build_report_html,
    html_to_pdf,
    markdown_to_html,
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

from .routers import billing
from .services.feed_service import get_daily_vibe_llm

# #START_BLOCK_LOGGER
logger = structlog.get_logger()
# #END_BLOCK_LOGGER
# ...
# #START_BLOCK_APP_INIT
app = FastAPI(title="AstroSaaS API", version="0.1.0")

app.include_router(billing.router)

@app.on_event("startup")
def init_db():
    """
    # PURPOSE: Ensure core tables exist for the MVP workflow.
    # INPUT: None.
    # OUTPUT: None.
    # CONTEXT: Simplifies local/dev setup before migrations.
    """

    Base.metadata.create_all(bind=engine)
    apply_runtime_migrations()
# #END_BLOCK_APP_INIT


def resolve_llm_mode(payload: "ReportWorkflowRequest") -> str:
    """
    # PURPOSE: Normalize the requested LLM mode.
    # INPUT: ReportWorkflowRequest payload.
    # OUTPUT: Normalized mode string.
    # CONTEXT: Used by sync/async report generation endpoints.
    """

    mode = (payload.llm_mode or "openrouter").strip().lower()
    if mode == "cheap":
        return "cheap"
    if mode not in {"openrouter", "fallback", "local", "mock", "stub"}:
        return "openrouter"
    return mode

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
    client_name: str = Field(..., min_length=1)
    client_note: Optional[str] = None
    birth_date: str = Field(..., min_length=4)
    birth_location: str = Field(..., min_length=2)
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


class AdminClientCreateRequest(BaseModel):
    """
    # PURPOSE: Input payload for client creation.
    # INPUT: client_name, birth data, optional notes.
    # OUTPUT: Validated request object.
    # CONTEXT: Used by /api/admin/clients POST.
    """

    client_name: str = Field(..., min_length=1)
    client_note: Optional[str] = None
    birth_date: str = Field(..., min_length=4)
    birth_location: str = Field(..., min_length=2)
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    birth_timezone: Optional[str] = None
    birth_place_id: Optional[str] = None


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


def parse_birth_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
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
    birth_dt = parse_birth_datetime(payload.birth_date)
    if payload.client_id:
        try:
            client_uuid = uuid.UUID(payload.client_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid client id.") from exc

        client = db.query(Client).filter(Client.id == client_uuid).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        client.full_name = payload.client_name
        client.notes = payload.client_note
        client.birth_datetime = birth_dt
        client.birth_location = payload.birth_location
        client.birth_lat = payload.birth_lat
        client.birth_lon = payload.birth_lon
        client.birth_timezone = payload.birth_timezone
        client.birth_place_id = payload.birth_place_id
        db.add(client)
        return client

    client = Client(
        full_name=payload.client_name,
        notes=payload.client_note,
        birth_datetime=birth_dt,
        birth_location=payload.birth_location,
        birth_lat=payload.birth_lat,
        birth_lon=payload.birth_lon,
        birth_timezone=payload.birth_timezone,
        birth_place_id=payload.birth_place_id,
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
        if llm_mode == "openrouter":
            llm_client = OpenRouterClient.from_env(
                model_override=resolve_primary_model(payload.report_type)
            )
        elif llm_mode == "cheap":
            llm_client = OpenRouterClient.from_env(mode="cheap")
            
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
            return

        chart_data = build_chart_data(payload)
        context = build_report_context(payload, chart_data)

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
        fallback_model = resolve_llm_fallback_model()
        try:
            if llm_mode == "fallback":
                content = inject_planet_emojis(
                    build_section_template_content(target_spec)
                )
            else:
                if llm_mode == "cheap":
                    llm_client = OpenRouterClient.from_env(mode="cheap")
                else:
                    llm_client = OpenRouterClient.from_env(
                        model_override=resolve_primary_model(payload.report_type)
                    )
                
                result = await asyncio.to_thread(
                    generate_section_with_retries,
                    target_spec,
                    context,
                    primary_client=llm_client,
                    fallback_model=fallback_model,
                    max_attempts=retry_attempts,
                )
                content = inject_planet_emojis(result.content)
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


@app.post("/api/workflows/report/async", response_model=ReportWorkflowStartResponse)
def run_report_workflow_async(
    payload: ReportWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    # PURPOSE: Queue report generation in the background.
    # INPUT: ReportWorkflowRequest payload.
    # OUTPUT: ReportWorkflowStartResponse with report metadata.
    # CONTEXT: Returns quickly to avoid UI lockups.
    """

    llm_mode = resolve_llm_mode(payload)
    if llm_mode in ("openrouter", "cheap"):
        try:
            OpenRouterClient.from_env(mode="cheap" if llm_mode == "cheap" else "smart")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    client = upsert_client_from_payload(payload, db)
    db.flush()

    report = Report(
        client_id=client.id,
        report_type=payload.report_type,
        status="in_progress",
        paid=False,
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


@app.post("/api/workflows/report", response_model=ReportWorkflowResponse)
async def run_report_workflow(
    payload: ReportWorkflowRequest, db: Session = Depends(get_db)
):
    """
    # PURPOSE: Run the full workflow: client -> raw chart -> LLM sections -> markdown.
    # INPUT: ReportWorkflowRequest payload.
    # OUTPUT: ReportWorkflowResponse with markdown and sections.
    # CONTEXT: End-to-end MVP path for report generation.
    """

    client = upsert_client_from_payload(payload, db)
    db.flush()

    report = Report(
        client_id=client.id,
        report_type=payload.report_type,
        status="in_progress",
        paid=False,
    )
    report.input_payload = json.dumps(payload.model_dump(), ensure_ascii=True)
    db.add(report)
    db.flush()

    # LLM Setup
    llm_mode = resolve_llm_mode(payload)
    llm_client = None
    if llm_mode in ("openrouter", "cheap"):
        try:
            llm_client = OpenRouterClient.from_env(
                mode="cheap" if llm_mode == "cheap" else "smart"
            )
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
    if llm_mode in ("openrouter", "cheap"):
        try:
            llm_client = OpenRouterClient.from_env(
                mode="cheap" if llm_mode == "cheap" else "smart"
            )
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
    if llm_mode in ("openrouter", "cheap"):
        try:
            model_override = None
            if llm_mode != "cheap":
                model_override = resolve_primary_model(payload.report_type)
            
            llm_client = OpenRouterClient.from_env(
                mode="cheap" if llm_mode == "cheap" else "smart",
                model_override=model_override
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = start_report_run(report, db)
    try:
        chart_data = build_chart_data(payload)
        context = build_report_context(payload, chart_data)

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

            if llm_mode == "fallback":
                generated_sections = [
                    SectionResultOut(
                        section_id=target_spec.section_id,
                        title=target_spec.title,
                        content=inject_planet_emojis(
                            build_section_template_content(target_spec)
                        ),
                    )
                ]
            else:
                retry_attempts = resolve_llm_retry_attempts()
                fallback_model = resolve_llm_fallback_model()
                result = await asyncio.to_thread(
                    generate_section_with_retries,
                    target_spec,
                    context,
                    primary_client=llm_client,
                    fallback_model=fallback_model,
                    max_attempts=retry_attempts,
                )
                generated_sections = [
                    SectionResultOut(
                        section_id=result.section_id,
                        title=result.title,
                        content=inject_planet_emojis(result.content),
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
def get_admin_stats(db: Session = Depends(get_db)):
    """
    # PURPOSE: Return admin dashboard counters.
    # INPUT: None.
    # OUTPUT: AdminStatsOut.
    # CONTEXT: Used by the admin UI dashboard.
    """

    clients = db.query(func.count(Client.id)).scalar() or 0
    reports_total = db.query(func.count(Report.id)).scalar() or 0
    reports_in_progress = (
        db.query(func.count(Report.id))
        .filter(Report.status == "in_progress")
        .scalar()
        or 0
    )
    reports_completed = (
        db.query(func.count(Report.id))
        .filter(Report.status == "completed")
        .scalar()
        or 0
    )
    reports_failed = (
        db.query(func.count(Report.id))
        .filter(Report.status == "failed")
        .scalar()
        or 0
    )

    return {
        "clients": clients,
        "reports_total": reports_total,
        "reports_in_progress": reports_in_progress,
        "reports_completed": reports_completed,
        "reports_failed": reports_failed,
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
    limit: int = 25, offset: int = 0, db: Session = Depends(get_db)
):
    """
    # PURPOSE: Return clients with report summaries.
    # INPUT: limit, offset.
    # OUTPUT: List[AdminClientOut].
    # CONTEXT: Used by the admin UI clients list.
    """

    rows = (
        db.query(Client)
        .order_by(Client.created_at.desc())
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
        parsed = datetime.fromisoformat(payload.birth_date)
        birth_dt = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
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
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return serialize_client(client)


@app.get("/api/admin/clients/{client_id}", response_model=AdminClientDetailOut)
def get_admin_client(client_id: str, db: Session = Depends(get_db)):
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

    reports = (
        db.query(Report)
        .filter(Report.client_id == client.id)
        .order_by(Report.created_at.desc())
        .all()
    )

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


@app.get("/api/admin/reports", response_model=List[AdminReportOut])
def list_admin_reports(
    status: Optional[str] = None,
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

    return {
        "report": report_payload,
        "chunks": chunks_payload,
        "runs": runs_payload,
        "markdown": markdown if include_content else None,
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


@app.get("/api/admin/reports/{report_id}/pdf")
def get_admin_report_pdf(report_id: str, db: Session = Depends(get_db)):
    """
    # PURPOSE: Return report content as PDF.
    # INPUT: report_id.
    # OUTPUT: PDF binary response.
    # CONTEXT: Used by admin UI for downloads.
    """

    report = get_report_or_404(report_id, db)
    markdown = None
    for chunk in report.chunks:
        if chunk.section == "final_markdown":
            markdown = chunk.content or ""
            break

    if not markdown:
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
                block_id="REPORT_PDF",
                report_id=str(report.id),
                error=str(exc),
            )
            markdown = f"# Report: {report.report_type}\n\n"

    payload_data = safe_load_report_payload_data(report) or {}
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
    if client_name and translit_name and translit_name != client_name:
        meta_lines.append(client_name)

    chart_svg = ""
    try:
        payload_model = ReportWorkflowRequest.model_validate(payload_data)
        chart_data = build_chart_data(payload_model)
        chart_svg = build_natal_chart_svg(chart_data)
    except Exception:
        chart_svg = ""

    body_html = markdown_to_html(markdown or "")
    html = build_report_html(
        title=title,
        subtitle=subtitle,
        meta_lines=meta_lines,
        chart_svg=chart_svg,
        body_html=body_html,
    )
    pdf_bytes = html_to_pdf(html)
    filename = f"report-{report_id}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


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

from .auth import get_current_user

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
        from .services.code_gen import generate_referral_code
        user.referral_code = generate_referral_code()
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
        "referral_code": user.referral_code
    }

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[str] = None # YYYY-MM-DD
    birth_time: Optional[str] = None # HH:MM
    birth_time_known: bool = True
    birth_place: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None

@app.put("/api/users/me", response_model=UserProfileOut)
def update_my_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update fields if provided
    if payload.full_name is not None: user.full_name = payload.full_name
    if payload.birth_date is not None: user.birth_date = payload.birth_date
    if payload.birth_time is not None: user.birth_time = payload.birth_time
    if payload.birth_time_known is not None: user.birth_time_known = payload.birth_time_known
    if payload.birth_place is not None: user.birth_place = payload.birth_place
    if payload.birth_lat is not None: user.birth_lat = payload.birth_lat
    if payload.birth_lon is not None: user.birth_lon = payload.birth_lon
    
    # Merge if detached (though usually it's attached if session matches)
    # Since we inject a new db session here, and get_current_user injects ANOTHER one...
    # Warning: Different sessions.
    # `get_current_user` has `db = Depends(get_db)`.
    # `update_my_profile` has `db = Depends(get_db)`.
    # FastAPI usually creates ONE session per request if the dependency is cached (default).
    # So `db` should be the SAME session object.
    
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

    return {
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "is_partner": user.is_partner,
        "balance": float(user.balance),
        "subscription_active_until": user.subscription_active_until.isoformat() if user.subscription_active_until else None,
        "days_left": days_left,
        "birth_time_known": user.birth_time_known,
        "birth_date": user.birth_date,
        "birth_place": user.birth_place
    }
    
    # Recalculate days left for response
    days_left = 0
    if user.subscription_active_until:
        if user.subscription_active_until.tzinfo:
            delta = user.subscription_active_until - datetime.now(timezone.utc)
        else:
             delta = user.subscription_active_until - datetime.utcnow()
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
        "birth_place": user.birth_place
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
    
    # REAL LLM GENERATION (Cheap mode)
    vibe = await get_daily_vibe_llm(moon.sign, phase_name, len(chart.aspects))
    
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
