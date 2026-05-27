# ############################################################################
# AI_HEADER: MODULE_REPORT_WORKFLOW_LOGGING
# ROLE: Canonical GRACE logging helpers for report workflow runtime.
# DEPENDENCIES: backend/app/models.py, backend/app/logging_utils.py
# GRACE_ANCHORS: [WORKFLOW_LOGGING]
# ############################################################################

# START_MODULE_CONTRACT: M-REPORT-WORKFLOW-LOGGING
# purpose: Emit report workflow logs with module, function, contract, block, and trace identifiers.
# inputs:
#   - Report entities, explicit report ids, correlation ids, and structured event fields
# outputs:
#   - structlog events plus GRACE log evidence records
# trace_obligations:
#   - Every emitted workflow log carries module, contract, block, fn, report_id, and correlation metadata when available
# invariants:
#   - Event names and payload fields remain compatible with existing workflow/admin evidence
# non_goals:
#   - Does not mutate report lifecycle state or decide generation outcomes
# END_MODULE_CONTRACT: M-REPORT-WORKFLOW-LOGGING

# START_MODULE_MAP: M-REPORT-WORKFLOW-LOGGING
# entrypoints:
#   - _workflow_log -> WORKFLOW_GRACE_EVENT
#   - _workflow_trace_context -> WORKFLOW_TRACE_CONTEXT
#   - _admin_report_log_context -> ADMIN_REPORT_LOG_CONTEXT
# END_MODULE_MAP: M-REPORT-WORKFLOW-LOGGING

from __future__ import annotations

from typing import Optional

import structlog

from ..logging_utils import get_correlation_ids, log_grace_event
from ..models import Report

logger = structlog.get_logger()
MODULE_ID = "M-REPORT-WORKFLOW"

# START_BLOCK: WORKFLOW_GRACE_EVENT
def _admin_report_log_context(report: Report | None, **fields: object) -> dict[str, object]:
    context: dict[str, object] = {}
    if report is not None:
        context["report_id"] = str(report.id)
        context["report_type"] = report.report_type
        context["report_status"] = report.status
        context["client_id"] = str(report.client_id)
    context.update({key: value for key, value in fields.items() if value is not None})
    return context

def _workflow_trace_context(
    *,
    correlation_id: Optional[str] = None,
    report: Optional[Report] = None,
    report_id: Optional[object] = None,
) -> dict[str, Optional[str]]:
    """Return normalized workflow trace identifiers for report lifecycle logs."""
    trace_context = get_correlation_ids()
    resolved_report_id = str(report.id) if report is not None else (str(report_id) if report_id is not None else None)
    return {
        "correlation_id": correlation_id or trace_context.get("correlation_id"),
        "trace_id": trace_context.get("trace_id"),
        "correlation_source": trace_context.get("correlation_source"),
        "report_id": resolved_report_id,
    }

def _build_workflow_logger(
    *,
    contract: str,
    block: str,
    correlation_id: Optional[str] = None,
    report_id: Optional[str] = None,
    **fields,
):
    """Create a bound workflow logger with canonical GRACE trace fields."""
    return logger.bind(
        module=MODULE_ID,
        contract=contract,
        block=block,
        correlation_id=correlation_id,
        report_id=report_id,
        **fields,
    )

def _workflow_log(
    level: str,
    event: str,
    *,
    fn: str,
    contract: str,
    block: str,
    correlation_id: Optional[str] = None,
    report: Optional[Report] = None,
    report_id: Optional[object] = None,
    **fields,
) -> None:
    """Emit canonical workflow logs aligned with access and entitlement modules."""
    trace_context = _workflow_trace_context(
        correlation_id=correlation_id,
        report=report,
        report_id=report_id,
    )
    payload = {
        **(
            {
                key: value
                for key, value in _admin_report_log_context(report).items()
                if key != "report_id"
            }
            if report is not None
            else {}
        ),
        **{key: value for key, value in fields.items() if value is not None},
    }
    bound_logger = _build_workflow_logger(
        contract=contract,
        block=block,
        correlation_id=trace_context["correlation_id"],
        report_id=trace_context["report_id"],
        fn=fn,
    )
    getattr(bound_logger, level)(event, **payload)
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        contract=contract,
        block=block,
        correlation_id=trace_context["correlation_id"],
        report_id=trace_context["report_id"],
        trace_id=trace_context["trace_id"],
        correlation_source=trace_context["correlation_source"],
        **payload,
    )
# END_BLOCK: WORKFLOW_GRACE_EVENT
