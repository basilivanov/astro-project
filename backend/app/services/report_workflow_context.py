# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_EXTRACT
# ROLE: Extracted report workflow helper module.
# DEPENDENCIES: report_workflow.py compatibility facade
# GRACE_ANCHORS: [MODULE_CONTRACT, MODULE_MAP]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTEXT
# purpose: Assemble report and section contexts from payloads, chart facts, and forecast layers.
# inputs: report workflow payloads, serialized chart data, and section IDs.
# outputs: global report context and per-section trimmed context dictionaries.
# trace_obligations: context logs retain workflow module, contract, block, report_id, and report_type.
# invariants: context keys, fact trimming, forecast injection, and insight-pack dispatch remain unchanged.
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-CONTEXT

# START_MODULE_MAP: M-REPORT-WORKFLOW-CONTEXT
# entrypoints:
#   - build_section_context -> SECTION_CONTEXT_ASSEMBLY
#   - build_report_context -> FORECAST_WINDOW_RESOLUTION / CLIENT_PROFILE_NORMALIZATION / FACTS_CONTEXT_TRIM / FORECAST_SEMANTIC_LAYER
# END_MODULE_MAP: M-REPORT-WORKFLOW-CONTEXT

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict

import structlog

from stellium_engine import StelliumEngine

from .. import engine_utils
from ..engine_utils import normalize_datetime_input
from ..llm.orchestrator import NATAL_SECTION_IDS
from ..logging_utils import get_correlation_ids, log_grace_event
from ..reporting.markdown_helpers import format_house_context, get_chart_facts_json
from .report_workflow_chart import infer_gender
from .report_workflow_forecast import build_forecast_window, _build_forecast_prompt_context, _build_week_brief_seed_bundle
from .report_workflow_insight_core import (
    DEFAULT_NATAL_SECTION_CONTEXT_RULE,
    FACTS_FIRST_INSIGHT_PACK_SECTION_IDS,
    NATAL_SECTION_CONTEXT_RULES,
    _build_house_lookup,
    _build_position_lookup,
    _build_section_chart_pack,
    _collect_section_aspects,
    _collect_section_patterns,
    _unique_preserve_order,
)
from .report_workflow_insight_extended import _build_natal_section_insight_pack

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

# START_BLOCK: REPORT_CONTEXT_ASSEMBLY
def build_section_context(section_id: str, global_context: dict, chart_data: dict) -> dict:
    """
    # PURPOSE: Build a section-specific context pack to keep natal prompts compact.
    # INPUT: section_id, global_context, chart_data.
    # OUTPUT: Trimmed context dict for the current section.
    # CONTEXT: Used only for natal LLM sections; other report types keep the global context.
    """

    context = copy.deepcopy(global_context)
    client = context.get("client", {})
    report_type = client.get("report_type")
    if report_type in {"week_forecast", "month_forecast"}:
        return _build_forecast_prompt_context(context)
    if report_type != "natal_master":
        return context

    if section_id in {"input_frame", "technical_appendix"}:
        return context

    rule = NATAL_SECTION_CONTEXT_RULES.get(section_id)
    if rule is None and section_id not in NATAL_SECTION_IDS and section_id != "executive_summary":
        return context
    rule = copy.deepcopy(rule or DEFAULT_NATAL_SECTION_CONTEXT_RULE)

    facts = context.get("facts", {})
    position_names = _unique_preserve_order(rule.get("positions", []))
    house_numbers = _unique_preserve_order(rule.get("houses", []))
    aspect_points = _unique_preserve_order(rule.get("aspect_points", position_names))
    aspect_limit = int(rule.get("aspect_limit", 0) or 0)

    position_lookup = _build_position_lookup(facts, chart_data)
    house_lookup = _build_house_lookup(facts, chart_data)

    filtered_facts: Dict[str, Any] = {
        "v": facts.get("v", "facts_v1"),
        "tz": facts.get("tz", "UTC"),
        "pos": [copy.deepcopy(position_lookup[name]) for name in position_names if name in position_lookup],
        "houses": [copy.deepcopy(house_lookup[number]) for number in house_numbers if number in house_lookup],
        "aspects": _collect_section_aspects(chart_data, aspect_points, aspect_limit),
    }
    if rule.get("include_balance") and facts.get("balance") is not None:
        filtered_facts["balance"] = copy.deepcopy(facts.get("balance"))
    if facts.get("_truncated"):
        filtered_facts["_truncated"] = True

    trimmed_context: Dict[str, Any] = {
        "client": copy.deepcopy(client),
        "forecast_window": copy.deepcopy(context.get("forecast_window", {})),
        "facts": filtered_facts,
        "section_context": {
            "section_id": section_id,
            "focus": rule.get("focus"),
            "relevant_points": position_names,
            "relevant_houses": house_numbers,
        },
    }

    chart_pack = _build_section_chart_pack(rule, chart_data)
    if chart_pack:
        trimmed_context["chart"] = chart_pack

    if rule.get("include_patterns"):
        patterns = _collect_section_patterns(chart_data, position_names)
        if patterns:
            trimmed_context["section_context"]["patterns"] = patterns

    if rule.get("include_balance") and facts.get("balance") is not None:
        trimmed_context["section_context"]["balance"] = copy.deepcopy(facts.get("balance"))

    if section_id in {"balance_wheel_1_6", "balance_wheel_7_12"}:
        trimmed_context["section_context"]["house_context"] = format_house_context(chart_data)

    if section_id in FACTS_FIRST_INSIGHT_PACK_SECTION_IDS:
        insight_pack = _build_natal_section_insight_pack(
            section_id,
            filtered_facts,
            chart_data,
            position_lookup,
            house_lookup,
            client,
            context.get("forecast_window", {}),
        )
        if insight_pack:
            trimmed_context["section_context"]["insight_pack"] = insight_pack

    return trimmed_context


def build_report_context(payload: Any, chart_data: dict) -> dict:
    """
    # START_CONTRACT: FN-BUILD-REPORT-CONTEXT
    # purpose: Assemble canonical prompt/runtime context for report generation and resume flows.
    # inputs: report payload plus canonical chart_data dictionary.
    # returns: context dict for semantic blocks, llm orchestration, and fallback rendering.
    # side_effects: emits context assembly and forecast semantic-layer logs.
    # errors: suppresses forecast enrichment failures into logs while preserving base context output.
    # END_CONTRACT: FN-BUILD-REPORT-CONTEXT
    """
    
    # START_BLOCK: FORECAST_WINDOW_RESOLUTION
    # Determine forecast timezone (current location > birth location > UTC)
    forecast_tz = (
        payload.solar_current_timezone 
        or payload.birth_timezone 
        or "UTC"
    )
    
    forecast_window = build_forecast_window(payload.report_type, forecast_tz)
    _workflow_log(
        "info",
        "report.workflow.context_forecast_window",
        fn="build_report_context",
        contract="FN-BUILD-REPORT-CONTEXT",
        block="FORECAST_WINDOW_RESOLUTION",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
        forecast_timezone=forecast_tz,
    )
    # END_BLOCK: FORECAST_WINDOW_RESOLUTION

    # START_BLOCK: CLIENT_PROFILE_NORMALIZATION
    # Clean client name (remove text in parentheses)
    clean_name = payload.client_name
    clean_name = re.sub(r'\s*\(.*?\)', '', clean_name)
    clean_name = re.sub(r'\s*\[.*?\]', '', clean_name)
    clean_name = clean_name.strip()
    _workflow_log(
        "info",
        "report.workflow.context_client_name_cleaned",
        fn="build_report_context",
        contract="FN-BUILD-REPORT-CONTEXT",
        block="CLIENT_PROFILE_NORMALIZATION",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
        original=payload.client_name,
        cleaned=clean_name,
    )

    # Inferred gender
    gender = infer_gender(clean_name)
    
    # Base context
    display_birth_date = payload.birth_date
    if (
        payload.birth_date
        and payload.birth_timezone
        and payload.report_type not in ["horary", "horary_answer"]
    ):
        display_birth_date = normalize_datetime_input(
            payload.birth_date,
            payload.birth_timezone,
            assume_local=False,
        )

    display_partner_birth_date = payload.partner_birth_date
    if payload.partner_birth_date and payload.partner_birth_timezone:
        display_partner_birth_date = normalize_datetime_input(
            payload.partner_birth_date,
            payload.partner_birth_timezone,
            assume_local=False,
        )

    context = {
        "client": {
            "name": clean_name,
            "gender": "женский" if gender == "female" else "мужской",
            "note": payload.client_note,
            "question": getattr(payload, "question", None) or payload.client_note,
            "birth_date": display_birth_date,
            "birth_location": payload.birth_location,
            "birth_lat": payload.birth_lat,
            "birth_lon": payload.birth_lon,
            "birth_timezone": payload.birth_timezone,
            "birth_place_id": payload.birth_place_id,
            "birth_time_known": getattr(payload, "birth_time_known", True),
            "report_type": payload.report_type,
        },
        "partner": {
            "name": payload.partner_name,
            "birth_date": display_partner_birth_date,
            "birth_location": payload.partner_birth_location,
            "birth_lat": payload.partner_birth_lat,
            "birth_lon": payload.partner_birth_lon,
            "birth_timezone": payload.partner_birth_timezone,
            "birth_place_id": payload.partner_birth_place_id,
        },
        "solar": {
            "current_location": payload.solar_current_location,
            "current_lat": payload.solar_current_lat,
            "current_lon": payload.solar_current_lon,
            "current_timezone": payload.solar_current_timezone,
            "current_place_id": payload.solar_current_place_id,
            "next_location": payload.solar_next_location,
            "next_lat": payload.solar_next_lat,
            "next_lon": payload.solar_next_lon,
            "next_timezone": payload.solar_next_timezone,
            "next_place_id": payload.solar_next_place_id,
        },
        "forecast_window": forecast_window,
        "facts": get_chart_facts_json(chart_data)
    }

    # END_BLOCK: CLIENT_PROFILE_NORMALIZATION

    # START_BLOCK: FACTS_CONTEXT_TRIM
    # Optimization: context size control for free models
    # If facts JSON is too large, it can trigger 402 on OpenRouter free accounts
    facts_json = json.dumps(context["facts"])
    if len(facts_json) > 3000:
        _workflow_log(
            "info",
            "report.workflow.context_facts_truncated",
            fn="build_report_context",
            contract="FN-BUILD-REPORT-CONTEXT",
            block="FACTS_CONTEXT_TRIM",
            report_id=getattr(payload, "report_id", None),
            report_type=getattr(payload, "report_type", None),
            original_len=len(facts_json),
        )
        # Simple truncation of aspects if too many
        if len(context["facts"].get("aspects", [])) > 10:
            context["facts"]["aspects"] = context["facts"]["aspects"][:10]
            context["facts"]["_truncated"] = True

    # Optimization: for horary, we don't need the full 'chart' object anymore
    # because 'facts' contains all essentials.
    if payload.report_type not in ["horary", "horary_answer"]:
        context["chart"] = chart_data

    # END_BLOCK: FACTS_CONTEXT_TRIM

    # START_BLOCK: FORECAST_SEMANTIC_LAYER
    # Inject detailed forecast data
    if payload.report_type in ["year_forecast", "week_forecast", "month_forecast", "ten_year_forecast"]:
        try:
            engine = StelliumEngine()
            house_system = engine_utils.resolve_house_system(payload.house_system)
            
            clean_birth_date = payload.birth_date
            if "+" in clean_birth_date:
                clean_birth_date = clean_birth_date.split("+")[0]
            
            location_input = payload.birth_location
            if payload.birth_lat is not None and payload.birth_lon is not None:
                location_input = {
                    "latitude": payload.birth_lat,
                    "longitude": payload.birth_lon,
                    "name": payload.birth_location or payload.client_name,
                }
                
            natal_chart = engine.create_natal_chart(
                payload.client_name,
                clean_birth_date,
                location_input,
                house_system,
            )
            
            forecast_loc = payload.solar_current_location or payload.birth_location
            
            if payload.report_type == "year_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                    target_year = start_dt.year
                except:
                    target_year = datetime.now(timezone.utc).year
                    
                context["year_forecast_data"] = engine.calculate_forecast_year_data(
                    natal_chart,
                    target_year,
                    forecast_loc
                )
                
            elif payload.report_type == "week_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                except:
                    start_dt = datetime.now(timezone.utc)
                    
                context["week_forecast_data"] = engine.calculate_forecast_week_data(
                    natal_chart,
                    start_dt,
                    forecast_loc
                )
                try:
                    context["month_forecast_data"] = engine.calculate_forecast_month_data(
                        natal_chart,
                        start_dt,
                        forecast_loc
                    )
                except Exception as exc:
                    _workflow_log(
                        "warning",
                        "report.workflow.context_week_brief_layer_partial",
                        fn="build_report_context",
                        contract="FN-BUILD-REPORT-CONTEXT",
                        block="FORECAST_SEMANTIC_LAYER",
                        report_id=getattr(payload, "report_id", None),
                        report_type=getattr(payload, "report_type", None),
                        layer="month_forecast_data",
                        error=str(exc),
                    )
                try:
                    context["year_forecast_data"] = engine.calculate_forecast_year_data(
                        natal_chart,
                        start_dt.year,
                        forecast_loc
                    )
                except Exception as exc:
                    _workflow_log(
                        "warning",
                        "report.workflow.context_week_brief_layer_partial",
                        fn="build_report_context",
                        contract="FN-BUILD-REPORT-CONTEXT",
                        block="FORECAST_SEMANTIC_LAYER",
                        report_id=getattr(payload, "report_id", None),
                        report_type=getattr(payload, "report_type", None),
                        layer="year_forecast_data",
                        error=str(exc),
                    )
                context["week_brief_seed"] = _build_week_brief_seed_bundle(context)
                
            elif payload.report_type == "month_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                except:
                    start_dt = datetime.now(timezone.utc)
                    
                context["month_forecast_data"] = engine.calculate_forecast_month_data(
                    natal_chart,
                    start_dt,
                    forecast_loc
                )

            elif payload.report_type == "ten_year_forecast":
                try:
                    start_dt = datetime.fromisoformat(forecast_window["start"])
                    start_year = start_dt.year
                except:
                    start_year = datetime.now(timezone.utc).year
                    
                context["decade_forecast_data"] = engine.calculate_forecast_decade_data(
                    natal_chart,
                    start_year,
                    forecast_loc
                )

        except Exception as exc:
            _workflow_log(
                "error",
                "report.workflow.context_forecast_error",
                fn="build_report_context",
                contract="FN-BUILD-REPORT-CONTEXT",
                block="FORECAST_SEMANTIC_LAYER",
                report_id=getattr(payload, "report_id", None),
                report_type=getattr(payload, "report_type", None),
                error=str(exc),
            )

    _workflow_log(
        "info",
        "report.workflow.context_ready",
        fn="build_report_context",
        contract="FN-BUILD-REPORT-CONTEXT",
        block="FORECAST_SEMANTIC_LAYER",
        report_id=getattr(payload, "report_id", None),
        report_type=getattr(payload, "report_type", None),
        keys=sorted(context.keys()),
    )
    # END_BLOCK: FORECAST_SEMANTIC_LAYER
    return context
# END_BLOCK: REPORT_CONTEXT_ASSEMBLY
