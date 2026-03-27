"""Correlation middleware for FastAPI requests."""

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

CORRELATION_HEADER = "x-correlation-id"
TRACE_HEADER = "x-trace-id"
REQUEST_ID_FALLBACK_HEADER = "x-request-id"

logger = structlog.get_logger(__name__)
_INVALID_HEADER_LOG_INTERVAL = 60.0
_next_invalid_log_ts = 0.0


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


def get_request_correlation(request: Request) -> dict[str, Optional[str]]:
    return getattr(request.state, "correlation_context", resolve_correlation_context())


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:  # pragma: no cover - initial wiring
        super().__init__(app)

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

    async def __call__(self, scope: Scope, receive: Receive, send: Send):  # pragma: no cover - BaseHTTPMiddleware handles
        return await super().__call__(scope, receive, send)
