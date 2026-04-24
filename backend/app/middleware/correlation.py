"""Correlation middleware for FastAPI requests."""

# ############################################################################
# AI_HEADER: MODULE_CORRELATION_MIDDLEWARE
# ROLE: Bind request correlation identifiers into FastAPI request and structlog context.
# DEPENDENCIES: fastapi, starlette, backend.app.logging_utils.
# GRACE_ANCHORS: [CORRELATION_HEADER_CONSTANTS, CORRELATION_HEADER_SANITIZATION, CORRELATION_HEADER_EXTRACTION, CORRELATION_REQUEST_CONTEXT]
# ############################################################################

# START_MODULE_CONTRACT: M-TRACE-LOGGING
# purpose: Normalize incoming correlation headers and bind canonical request trace context for FastAPI flows.
# owns:
#   - backend/app/middleware/correlation.py
# inputs:
#   - Incoming FastAPI Request headers carrying correlation/request identifiers
#   - Existing ambient correlation context inherited from caller/runtime
# outputs:
#   - request.state.correlation_context snapshots for downstream API handlers
#   - Response headers carrying canonical correlation_id and trace_id
#   - Diagnostic structured logs for sanitized invalid headers
# dependencies:
#   - FastAPI/Starlette request-response middleware dispatch
#   - backend.app.logging_utils resolve_correlation_context and set_correlation_ids helpers
#   - structlog logger for invalid inbound header diagnostics
# trace_obligations:
#   - Request correlation binding preserves correlation_id, trace_id, correlation_source, and request_id semantics
#   - Header sanitization warnings remain attributable by stable middleware block names
#   - Middleware cleanup restores prior context after request completion
# side_effects:
#   - Writes correlation data into request.state and structlog contextvars
#   - Emits warning logs for invalid inbound headers on a rate-limited basis
# invariants:
#   - Invalid inbound ids are ignored and replaced with generated canonical ids
#   - trace_id is freshly generated for each middleware dispatch
#   - Response headers mirror the context assigned to the request
# failure_policy:
#   - Invalid inbound headers degrade to generated canonical ids plus rate-limited warning logs
#   - Downstream request exceptions still trigger correlation context restoration before propagation
#   - Middleware does not mutate correlation payload semantics outside request.state and response headers
# non_goals:
#   - Replacing FastAPI middleware architecture
#   - Redesigning correlation header names or transport behavior
# END_MODULE_CONTRACT: M-TRACE-LOGGING

# START_MODULE_MAP: M-TRACE-LOGGING
# public_entrypoints:
#   - get_request_correlation -> request.state correlation snapshot for route handlers
#   - CorrelationIdMiddleware.dispatch -> FastAPI request correlation bind/restore orchestration
# internal_entrypoints:
#   - _is_allowed_id -> inbound header validation helper
#   - _log_invalid_header -> rate-limited invalid header diagnostics
#   - _extract_correlation_header -> inbound header resolution and source attribution
#   - CorrelationIdMiddleware.__init__ -> middleware wiring passthrough
#   - CorrelationIdMiddleware.__call__ -> BaseHTTPMiddleware compatibility shim
# semantic_blocks:
#   - CORRELATION_HEADER_CONSTANTS: inbound/outbound correlation header names
#   - CORRELATION_HEADER_SANITIZATION: validation and rate-limited diagnostics for inbound ids
#   - CORRELATION_HEADER_EXTRACTION: inbound header resolution and source attribution
#   - CORRELATION_REQUEST_CONTEXT: request.state access and middleware dispatch binding
# owned_tests:
#   - tests/test_logging_utils_grace.py
# adjacent_modules:
#   - backend/app/logging_utils.py
#   - backend/app/main.py
# END_MODULE_MAP: M-TRACE-LOGGING

from __future__ import annotations

import time
import uuid
from typing import Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from ..logging_utils import (
    resolve_correlation_context,
    set_correlation_ids,
)

# START_BLOCK: CORRELATION_HEADER_CONSTANTS
CORRELATION_HEADER = "x-correlation-id"
TRACE_HEADER = "x-trace-id"
REQUEST_ID_FALLBACK_HEADER = "x-request-id"

logger = structlog.get_logger(__name__)
_INVALID_HEADER_LOG_INTERVAL = 60.0
_next_invalid_log_ts = 0.0
# END_BLOCK: CORRELATION_HEADER_CONSTANTS


# START_BLOCK: CORRELATION_HEADER_SANITIZATION
# START_CONTRACT: FN-IS-ALLOWED-CORRELATION-ID
def _is_allowed_id(value: Optional[str]) -> bool:
    if not value:
        return False
    value = value.strip()
    if not value:
        return False
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return value.isalnum() and len(value) <= 64
# END_CONTRACT: FN-IS-ALLOWED-CORRELATION-ID


# START_CONTRACT: FN-LOG-INVALID-CORRELATION-HEADER
def _log_invalid_header(header_value: str, header_name: str) -> None:
    global _next_invalid_log_ts
    now = time.monotonic()
    if now < _next_invalid_log_ts:
        return
    _next_invalid_log_ts = now + _INVALID_HEADER_LOG_INTERVAL
    logger.warning(
        "diagnostic.correlation_middleware",
        action="sanitize_header",
        header_name=header_name,
        header_sample=header_value[:64],
        header_length=len(header_value),
    )
# END_CONTRACT: FN-LOG-INVALID-CORRELATION-HEADER
# END_BLOCK: CORRELATION_HEADER_SANITIZATION


# START_BLOCK: CORRELATION_HEADER_EXTRACTION
# START_CONTRACT: FN-EXTRACT-CORRELATION-HEADER
def _extract_correlation_header(request: Request) -> tuple[Optional[str], str]:
    correlation_header = request.headers.get(CORRELATION_HEADER)
    fallback_header = request.headers.get(REQUEST_ID_FALLBACK_HEADER)
    header_value = correlation_header or fallback_header
    if _is_allowed_id(header_value):
        source = "header" if correlation_header else "request_id"
        return header_value.strip(), source
    if header_value:
        _log_invalid_header(header_value, CORRELATION_HEADER if correlation_header else REQUEST_ID_FALLBACK_HEADER)
    return None, "generated"
# END_CONTRACT: FN-EXTRACT-CORRELATION-HEADER
# END_BLOCK: CORRELATION_HEADER_EXTRACTION


# START_BLOCK: CORRELATION_REQUEST_CONTEXT
# START_CONTRACT: FN-GET-REQUEST-CORRELATION
def get_request_correlation(request: Request) -> dict[str, Optional[str]]:
    return getattr(request.state, "correlation_context", resolve_correlation_context())
# END_CONTRACT: FN-GET-REQUEST-CORRELATION


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    # START_CONTRACT: FN-CORRELATION-MIDDLEWARE-INIT
    def __init__(self, app: ASGIApp) -> None:  # pragma: no cover - initial wiring
        super().__init__(app)
    # END_CONTRACT: FN-CORRELATION-MIDDLEWARE-INIT

    # START_CONTRACT: FN-CORRELATION-MIDDLEWARE-DISPATCH
    async def dispatch(self, request: Request, call_next):
        existing_context = resolve_correlation_context()
        correlation_id, source = _extract_correlation_header(request)
        trace_id = str(uuid.uuid4())
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        context = set_correlation_ids(
            correlation_id=correlation_id,
            trace_id=trace_id,
            correlation_source=source,
        )
        request.state.correlation_context = context
        response: Response
        try:
            response = await call_next(request)
        finally:
            set_correlation_ids(
                correlation_id=existing_context.get("correlation_id"),
                trace_id=existing_context.get("trace_id"),
                correlation_source=existing_context.get("correlation_source"),
            )

        response.headers[CORRELATION_HEADER] = context.get("correlation_id") or ""
        response.headers[TRACE_HEADER] = context.get("trace_id") or ""
        return response
    # END_CONTRACT: FN-CORRELATION-MIDDLEWARE-DISPATCH

    # START_CONTRACT: FN-CORRELATION-MIDDLEWARE-ASGI-CALL
    async def __call__(self, scope: Scope, receive: Receive, send: Send):  # pragma: no cover - BaseHTTPMiddleware handles
        return await super().__call__(scope, receive, send)
    # END_CONTRACT: FN-CORRELATION-MIDDLEWARE-ASGI-CALL
# END_BLOCK: CORRELATION_REQUEST_CONTEXT
