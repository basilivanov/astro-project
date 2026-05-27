# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-CHART
# purpose: Dispatch report payloads to chart engines and bridge adapters without changing chart semantics.
# inputs: report workflow payloads with birth/current/partner chart fields.
# outputs: serialized natal, horary, solar-return, or synastry chart dictionaries.
# trace_obligations: chart dispatch logs retain workflow module, contract, block, report_id, and report_type.
# invariants: astrology engine calls and adapter selection remain behavior-compatible with report_workflow facade.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-CHART

# START_MODULE_MAP: M-REPORT-WORKFLOW-CHART
# entrypoints:
#   - build_chart_data -> CHART_ENGINE_DISPATCH / HORARY_ADAPTER_BRIDGE / SOLAR_RETURN_BRIDGE / SYNASTRY_BRIDGE
#   - resolve_solar_return_location -> SOLAR_RETURN_LOCATION
#   - resolve_solar_return_target_year -> SOLAR_RETURN_YEAR
# END_MODULE_MAP: M-REPORT-WORKFLOW-CHART

from __future__ import annotations

import calendar
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException
import structlog

from stellium_engine import StelliumEngine

from .. import engine_utils
from ..engine_utils import normalize_datetime_input
from ..horary.adapters import detect_adapter
from ..horary.core import HoraryCore
from ..logging_utils import get_correlation_ids, log_grace_event

logger = structlog.get_logger()
MODULE_ID = "M-REPORT-WORKFLOW"

def _workflow_log(level: str, event: str, **fields: object) -> None:
    correlation = get_correlation_ids()
    payload = {
        "module": MODULE_ID,
        "component": "report_workflow",
        "contract": fields.pop("contract", "FN-REPORT-WORKFLOW"),
        "block": fields.pop("block", "REPORT_WORKFLOW"),
        **correlation,
        **fields,
    }
    log_grace_event(level, event, **payload)

# START_BLOCK: CHART_DISPATCH_HELPERS
def resolve_solar_return_location(payload: Any) -> Any:
    solar_location = getattr(payload, "solar_current_location", None)
    solar_lat = getattr(payload, "solar_current_lat", None)
    solar_lon = getattr(payload, "solar_current_lon", None)

    if solar_lat is not None and solar_lon is not None:
        return {
            "latitude": solar_lat,
            "longitude": solar_lon,
            "name": solar_location or getattr(payload, "birth_location", None) or "Solar Location",
            "timezone": getattr(payload, "solar_current_timezone", None),
        }

    return solar_location or getattr(payload, "birth_location", None) or "Greenwich"


def resolve_solar_return_target_year(payload: Any, now: Optional[datetime] = None) -> int:
    now_utc = now or datetime.now(timezone.utc)
    tz_str = getattr(payload, "solar_current_timezone", None) or getattr(payload, "birth_timezone", None)

    try:
        now_local = now_utc.astimezone(ZoneInfo(tz_str)) if tz_str else now_utc
    except Exception:
        now_local = now_utc

    birth_input = getattr(payload, "birth_date", None)
    if not birth_input:
        return now_local.year

    birth_local = normalize_datetime_input(
        birth_input,
        getattr(payload, "birth_timezone", None),
        assume_local=False,
    )

    try:
        birth_dt = datetime.fromisoformat(birth_local)
    except ValueError:
        return now_local.year

    last_day = calendar.monthrange(now_local.year, birth_dt.month)[1]
    birthday_this_year = datetime(
        now_local.year,
        birth_dt.month,
        min(birth_dt.day, last_day),
        birth_dt.hour,
        birth_dt.minute,
        birth_dt.second,
        tzinfo=now_local.tzinfo,
    )

    if now_local < birthday_this_year:
        return now_local.year - 1
    return now_local.year


def build_chart_data(payload: Any) -> dict:
    """
    # START_CONTRACT: FN-CREATE-REPORT-CHART-DATA
    # purpose: Build canonical chart payload for report generation and resume flows.
    # inputs: report workflow payload with report_type, birth data, and optional bridge fields.
    # returns: chart data dictionary used by context builders and sections.
    # side_effects: emits chart-engine and bridge-aligned workflow logs.
    # errors: propagates engine/adaptor failures to caller.
    # END_CONTRACT: FN-CREATE-REPORT-CHART-DATA
    """
    # START_BLOCK: CHART_ENGINE_DISPATCH
    _workflow_log(
        "info",
        "report.workflow.chart_build_start",
        fn="build_chart_data",
        contract="FN-CREATE-REPORT-CHART-DATA",
        block="CHART_ENGINE_DISPATCH",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
    )
    """
    # PURPOSE: Calculate chart data for report context.
    # INPUT: payload (ReportWorkflowRequest-like).
    # OUTPUT: Serialized chart dict.
    # CONTEXT: Used by report generation prompts.
    """

    engine = StelliumEngine()
    house_system = engine_utils.resolve_house_system(payload.house_system)

    # 1. Resolve Location (Prefer coordinates)
    is_horary = payload.report_type in ["horary", "horary_answer"]
    
    if is_horary and payload.solar_current_lat is not None and payload.solar_current_lon is not None:
        loc_input = {
            "latitude": payload.solar_current_lat,
            "longitude": payload.solar_current_lon,
            "name": payload.solar_current_location or "Current Location",
            "timezone": payload.solar_current_timezone
        }
        current_lat = payload.solar_current_lat
        tz_str = payload.solar_current_timezone
    else:
        loc_input = payload.birth_location
        tz_str = payload.birth_timezone
        current_lat = payload.birth_lat
        
        if payload.birth_lat is not None and payload.birth_lon is not None:
            loc_input = {
                "latitude": payload.birth_lat,
                "longitude": payload.birth_lon,
                "name": payload.birth_location or payload.client_name or "Unknown",
                "timezone": tz_str
            }
            current_lat = payload.birth_lat

    # Force Whole Sign for high latitudes to avoid SwissEph crash
    if current_lat is not None and abs(current_lat) >= 60.0:
        from stellium.engines.houses import WholeSignHouses
        house_system = WholeSignHouses()

    # 2. Resolve Time
    clean_date = ""
    if is_horary:
        # Horary: Use NOW. Try to find local timezone if coords available.
        now_utc = datetime.now(timezone.utc)
        
        target_tz = tz_str
        if not target_tz and payload.solar_current_lat and payload.solar_current_lon:
            try:
                from timezonefinder import TimezoneFinder
                tf = TimezoneFinder()
                target_tz = tf.timezone_at(lng=payload.solar_current_lon, lat=payload.solar_current_lat)
            except: pass
        
        # Format current time according to target TZ (or UTC if none)
        clean_date = normalize_datetime_input(now_utc.isoformat(), target_tz or "UTC")
    else:
        # Natal/Forecast: Use Birth Date
        clean_date = normalize_datetime_input(payload.birth_date, tz_str, assume_local=False)

    try:
        chart = engine.create_natal_chart(
            payload.client_name,
            clean_date,
            loc_input,
            house_system,
            birth_time_known=getattr(payload, "birth_time_known", True)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Chart error: {exc}"
        ) from exc

    stars = []
    if payload.include_fixed_stars:
        stars = engine.get_fixed_star_conjunctions(chart, orb=payload.fixed_star_orb)
        
    aspects = engine.find_natal_aspects(chart)
    patterns = engine.find_all_patterns(chart)
    
    extra_points = []
    try:
        selena_lon = engine.calculate_selena(chart.datetime.julian_day)
        extra_points.append({"name": "Selena", "longitude": selena_lon})
    except: pass
    
    try:
        pars_lon = engine.calculate_pars_fortuna(chart)
        extra_points.append({"name": "Part of Fortune", "longitude": pars_lon})
    except: pass

    chart_dict = engine_utils.serialize_chart(
        chart, 
        chart_type="natal", 
        fixed_stars=stars,
        aspects=aspects,
        patterns=patterns,
        extra_points=extra_points
    )
    
    if payload.report_type in ["horary", "horary_answer"]:
        q_text = getattr(payload, "question", "") or getattr(payload, "client_note", "") or ""
        adapter_id = detect_adapter(q_text)
        logger.info("horary.adapter.detect", adapter=adapter_id, question=q_text[:50])
        
        horary_core = HoraryCore(engine)
        chart_dict["horary"] = horary_core.analyze(chart, adapter_id)

    if payload.report_type == "solar_return":
        try:
            now = datetime.now(timezone.utc)
            target_year = resolve_solar_return_target_year(payload, now=now)
            sr_location = resolve_solar_return_location(payload)
            sr_chart = engine.calculate_solar_return_chart(chart, target_year, sr_location)
            chart_dict["solar_return"] = engine_utils.serialize_chart(sr_chart, "solar_return")
        except Exception as e:
            logger.error("solar_return.calc.error", error=str(e))

    if payload.report_type == "synastry":
        try:
            p_dt = normalize_datetime_input(
                payload.partner_birth_date,
                payload.partner_birth_timezone,
                assume_local=False,
            )
            p_loc = payload.partner_birth_location
            if payload.partner_birth_lat and payload.partner_birth_lon:
                p_loc = {
                    "latitude": payload.partner_birth_lat,
                    "longitude": payload.partner_birth_lon,
                    "name": payload.partner_birth_location or "Partner Loc"
                }
            
            p_chart = engine.create_natal_chart(payload.partner_name or "Partner", p_dt, p_loc or "Unknown")
            chart_dict["partner_chart"] = engine_utils.serialize_chart(p_chart, "natal")
            chart_dict["synastry"] = engine.calculate_synastry_data(chart, p_chart)
        except Exception as e:
            logger.error("synastry.calc.error", error=str(e))
        
    return chart_dict



def infer_gender(full_name: str) -> str:
    """Simple heuristic for Russian names."""
    name = full_name.strip().split()[0].lower() # Take first name
    if name.endswith(('а', 'я')): return "female"
    return "male"
# END_BLOCK: CHART_DISPATCH_HELPERS
