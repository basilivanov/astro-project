"""Helper functions for catalog and billing structured logging."""

from __future__ import annotations

from typing import Any, Optional

from .logging_utils import checkout_session_log_fields, log_catalog_event, hash_identifier, get_correlation_ids


def _log_event(event: str, *, correlation_id: Optional[str] = None, trace_id: Optional[str] = None, correlation_source: Optional[str] = None, **fields: Any) -> None:
    context = get_correlation_ids()
    log_catalog_event(
        event,
        correlation_id=correlation_id or context.get("correlation_id"),
        trace_id=trace_id or context.get("trace_id"),
        correlation_source=correlation_source or context.get("correlation_source"),
        **fields,
    )


def _with_surface(surface: str, **fields: Any) -> dict[str, Any]:
    if "surface" not in fields:
        fields["surface"] = surface
    return fields


def _apply_session_fields(payload: dict[str, Any], checkout_session: Any | None = None) -> dict[str, Any]:
    if checkout_session is not None:
        payload.update(checkout_session_log_fields(checkout_session))
    return payload


def log_catalog_surface_error(
    *,
    surface: str,
    user: Any | None = None,
    report: Any | None = None,
    checkout_session: Any | None = None,
    error: Optional[str] = None,
    status_code: Optional[int] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(
        _with_surface(surface, error=error, status_code=status_code, **fields),
        checkout_session,
    )
    _log_event(
        "catalog.error",
        user=user,
        report=report,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_history_start(
    user: Any,
    *,
    limit: int,
    offset: int,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> None:
    _log_event(
        "catalog.history_start",
        user=user,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **_with_surface("history", limit=limit, offset=offset),
    )


def log_history_success(
    user: Any,
    *,
    count: int,
    has_more: bool,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> None:
    _log_event(
        "catalog.history_success",
        user=user,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **_with_surface("history", count=count, has_more=has_more),
    )


def log_history_error(
    user: Any,
    *,
    error: str,
    status_code: Optional[int] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> None:
    _log_event(
        "catalog.error",
        user=user,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **_with_surface("history", error=error, status_code=status_code),
    )


def log_report_detail_start(
    user: Any,
    *,
    report_id: str,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> None:
    _log_event(
        "catalog.history_start",
        user=user,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **_with_surface("report_detail", report_id=report_id),
    )


def log_report_detail_success(
    user: Any,
    *,
    report: Any,
    chunk_count: int,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> None:
    _log_event(
        "catalog.history_success",
        user=user,
        report=report,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **_with_surface("report_detail", chunk_count=chunk_count),
    )


def log_report_detail_error(
    user: Any,
    *,
    report_id: str,
    error: str,
    status_code: Optional[int] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> None:
    _log_event(
        "catalog.error",
        user=user,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **_with_surface("report_detail", report_id=report_id, error=error, status_code=status_code),
    )


def log_checkout_start(
    *,
    surface: str = "checkout",
    user: Any | None = None,
    report_type: Optional[str] = None,
    product_code: Optional[str] = None,
    amount: Optional[float] = None,
    checkout_session: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(
        _with_surface(surface, product_code=product_code, amount=amount, **fields),
        checkout_session,
    )
    _log_event(
        "catalog.checkout_start",
        user=user,
        report_type=report_type,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_checkout_decision(
    *,
    surface: str = "checkout",
    user: Any | None = None,
    report_type: Optional[str] = None,
    decision: Any | None = None,
    checkout_session: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, **fields), checkout_session)
    _log_event(
        "catalog.checkout_decision",
        user=user,
        report_type=report_type,
        decision=decision,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_checkout_denied(
    *,
    surface: str = "checkout",
    user: Any | None = None,
    report_type: Optional[str] = None,
    decision: Any | None = None,
    reason: Optional[str] = None,
    checkout_session: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, reason=reason, **fields), checkout_session)
    _log_event(
        "catalog.checkout_denied",
        user=user,
        report_type=report_type,
        decision=decision,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_checkout_success(
    *,
    surface: str = "checkout",
    user: Any | None = None,
    report: Any | None = None,
    decision: Any | None = None,
    checkout_session: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, **fields), checkout_session)
    _log_event(
        "catalog.checkout_success",
        user=user,
        report=report,
        decision=decision,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_checkout_error(
    *,
    surface: str = "checkout",
    user: Any | None = None,
    report: Any | None = None,
    report_type: Optional[str] = None,
    decision: Any | None = None,
    checkout_session: Any | None = None,
    error: Optional[str] = None,
    status_code: Optional[int] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(
        _with_surface(surface, report_type=report_type, error=error, status_code=status_code, **fields),
        checkout_session,
    )
    _log_event(
        "catalog.error",
        user=user,
        report=report,
        decision=decision,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_checkout_payment_created(
    checkout_session: Any | None,
    *,
    surface: str = "billing",
    user: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, **fields), checkout_session)
    _log_event(
        "catalog.checkout_payment_created",
        user=user,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_checkout_status(
    checkout_session: Any | None,
    *,
    surface: str = "billing",
    user: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, **fields), checkout_session)
    _log_event(
        "catalog.checkout_status",
        user=user,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_checkout_resume_ready(
    checkout_session: Any | None,
    *,
    surface: str = "billing",
    user: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, **fields), checkout_session)
    _log_event(
        "catalog.checkout_resume_ready",
        user=user,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_bridge_resume_start(
    checkout_session: Any | None,
    *,
    surface: str = "billing",
    user: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, **fields), checkout_session)
    _log_event(
        "catalog.bridge_resume_start",
        user=user,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_bridge_resume_success(
    checkout_session: Any | None,
    *,
    surface: str = "billing",
    user: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    payload = _apply_session_fields(_with_surface(surface, **fields), checkout_session)
    _log_event(
        "catalog.bridge_resume_success",
        user=user,
        checkout_session=checkout_session,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **payload,
    )


def log_resume_token_denied(
    *,
    user: Any | None = None,
    resume_token: str,
    reason: str,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> None:
    log_checkout_denied(
        surface="billing",
        user=user,
        reason=reason,
        requested_resume_token=hash_identifier(resume_token),
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
    )
