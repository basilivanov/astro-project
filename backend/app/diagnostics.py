# ############################################################################
# AI_HEADER: MODULE_DIAGNOSTICS
# ROLE: Log-driven diagnostics for core pipeline steps.
# DEPENDENCIES: structlog, stellium_engine.py, backend/app/llm/orchestrator.py
# GRACE_ANCHORS: [DIAG_LOGGER, DIAG_RUNNER]
# ############################################################################

from typing import Any, Dict

import structlog

from stellium_engine import StelliumEngine

from .llm.orchestrator import LLMOrchestrator, SectionSpec, StubLLMClient

# #START_BLOCK_DIAG_LOGGER
logger = structlog.get_logger()
# #END_BLOCK_DIAG_LOGGER

# #START_BLOCK_DIAG_RUNNER
def run_diagnostics() -> Dict[str, Any]:
    """
    # PURPOSE: Run core scenarios and collect diagnostic logs.
    # INPUT: None.
    # OUTPUT: Result summary with success markers.
    # CONTEXT: Used by CLI/admin trigger for Log-Driven validation.
    """

    result: Dict[str, Any] = {"status": "ok", "steps": []}
    engine = StelliumEngine()

    try:
        natal = engine.create_natal_chart(
            "Diagnostic",
            "1990-01-15 12:00",
            "Sochi, Russia",
        )
        logger.info(
            "diagnostic.natal",
            block_id="DIAG_NATAL",
            client_id="diagnostic",
            report_id="diagnostic",
            positions=len(natal.positions),
        )
        result["steps"].append({"name": "natal", "ok": True})
    except Exception as exc:
        logger.error(
            "diagnostic.natal.error",
            block_id="DIAG_NATAL",
            client_id="diagnostic",
            report_id="diagnostic",
            error=str(exc),
        )
        return {"status": "failed", "steps": result["steps"]}

    try:
        transit = engine.create_transit_chart(
            "2026-06-15 12:00",
            "Sochi, Russia",
        )
        aspects = engine.find_transit_aspects(natal, transit, orb=1.5)
        logger.info(
            "diagnostic.transit",
            block_id="DIAG_TRANSIT",
            client_id="diagnostic",
            report_id="diagnostic",
            aspects=len(aspects),
        )
        result["steps"].append({"name": "transit", "ok": True})
        
        # Test Month Data
        month_data = engine.calculate_forecast_month_data(natal, "2026-03-01 12:00", "Sochi, Russia")
        logger.info(
            "diagnostic.month",
            block_id="DIAG_MONTH",
            client_id="diagnostic",
            ingresses=len(month_data.get("ingresses", [])),
        )
        result["steps"].append({"name": "month_data", "ok": True})
        
        # Test Synastry
        partner = engine.create_natal_chart("Partner", "1995-05-20 12:00", "Moscow")
        syn_data = engine.calculate_synastry_data(natal, partner)
        logger.info(
            "diagnostic.synastry",
            block_id="DIAG_SYNASTRY",
            client_id="diagnostic",
            score=syn_data.get("score"),
        )
        result["steps"].append({"name": "synastry", "ok": True})
        
    except Exception as exc:
        logger.error(
            "diagnostic.engine.error",
            block_id="DIAG_ENGINE",
            error=str(exc),
        )
        return {"status": "failed", "steps": result["steps"]}

    try:
        orchestrator = LLMOrchestrator(StubLLMClient(), validate_content=False)
        sections = [
            SectionSpec(
                section_id="core",
                title="Core Profile",
                prompt="Describe the core personality archetypes.",
            )
        ]
        generated = orchestrator.generate_sections(
            sections, context={"client_id": "diagnostic"}
        )
        logger.info(
            "diagnostic.llm",
            block_id="DIAG_LLM",
            client_id="diagnostic",
            report_id="diagnostic",
            sections=len(generated),
        )
        result["steps"].append({"name": "llm", "ok": True})
    except Exception as exc:
        logger.error(
            "diagnostic.llm.error",
            block_id="DIAG_LLM",
            client_id="diagnostic",
            report_id="diagnostic",
            error=str(exc),
        )
        return {"status": "failed", "steps": result["steps"]}

    try:
        markdown = assemble_markdown(
            "Diagnostic Report",
            [
                ReportSection(
                    section_id=generated[0].section_id,
                    title=generated[0].title,
                    content=generated[0].content,
                )
            ],
        )
        logger.info(
            "diagnostic.report",
            block_id="DIAG_REPORT",
            client_id="diagnostic",
            report_id="diagnostic",
            length=len(markdown),
        )
        result["steps"].append({"name": "report", "ok": True})
    except Exception as exc:
        logger.error(
            "diagnostic.report.error",
            block_id="DIAG_REPORT",
            client_id="diagnostic",
            report_id="diagnostic",
            error=str(exc),
        )
        return {"status": "failed", "steps": result["steps"]}

    return result
# #END_BLOCK_DIAG_RUNNER

if __name__ == "__main__":
    print(run_diagnostics())
