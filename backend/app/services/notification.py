from __future__ import annotations

# START_MODULE_CONTRACT: M-NOTIFICATION-SERVICE
# module_id: M-NOTIFICATION-SERVICE
# purpose: Deliver report/admin/subscription notifications through the internal bot API with strict GRACE tracing.
# inputs:
#   - telegram_id/user-facing routing identifiers for bot delivery
#   - notification payloads for report ready/failure, subscription status, and admin replay flows
#   - optional correlation identifiers and notification/job identifiers for trace continuity
# outputs:
#   - boolean delivery/enqueue outcomes for caller-controlled workflows
#   - canonical GRACE logs/events for module, contract, and block execution
# trace_obligations:
#   - Every public entrypoint emits START_CONTRACT/END_CONTRACT and START_BLOCK/END_BLOCK events via log_grace_event
#   - Delivery attempts include module, contract, block, and correlation_id or notification_id in logs
#   - Report-ready/failure labels stay aligned with report_workflow/access_control terminology
# END_MODULE_CONTRACT: M-NOTIFICATION-SERVICE
# START_MODULE_MAP: M-NOTIFICATION-SERVICE
# role: Send notifications to users and admins via the Bot internal API.
# dependencies:
#   - httpx.AsyncClient for internal HTTP calls
#   - backend.app.logging_utils.log_grace_event/get_correlation_ids for canonical tracing
# external_effects:
#   - POSTs notification payloads to BOT_INTERNAL_URL/notify
# failure_modes:
#   - Missing telegram ids return False without network calls
#   - 4xx/5xx bot responses and network errors are logged and surfaced as False
#   - Unexpected runtime failures are logged and surfaced as False
# invariants:
#   - Public entrypoints never raise for delivery failures; they return False and emit canonical GRACE evidence
#   - Public labels remain synchronized with report workflow/admin replay vocabulary
# END_MODULE_MAP: M-NOTIFICATION-SERVICE

import os
from typing import Any, Mapping, Optional

import httpx
import structlog

from ..logging_utils import get_correlation_ids, log_grace_event

logger = structlog.get_logger()
MODULE_ID = "M-NOTIFICATION-SERVICE"
BOT_INTERNAL_URL = os.getenv("BOT_INTERNAL_URL", "http://bot:8001")


def get_notification_delivery_telemetry(
    *,
    delivered: bool,
    status_code: int | None = None,
    error: str | None = None,
    attempt: int | None = None,
) -> dict[str, Any]:
    """Build compact telemetry evidence for notification delivery outcomes."""
    if delivered:
        delivery_status = "delivered"
        non_fatal = False
    elif status_code in {403, 404}:
        delivery_status = "blocked_chat" if status_code == 403 else "chat_not_found"
        non_fatal = True
    elif status_code is not None and status_code >= 500:
        delivery_status = "server_error"
        non_fatal = False
    elif error:
        delivery_status = "network_error"
        non_fatal = False
    else:
        delivery_status = "failed"
        non_fatal = False

    telemetry: dict[str, Any] = {
        "delivery_status": delivery_status,
        "non_fatal": non_fatal,
    }
    if status_code is not None:
        telemetry["status_code"] = status_code
    if error:
        telemetry["error"] = error
    if attempt is not None:
        telemetry["attempt"] = attempt
    return telemetry


def _notification_trace_context(
    *,
    correlation_id: Optional[str] = None,
    notification_id: Optional[object] = None,
    telegram_id: Optional[object] = None,
) -> dict[str, Optional[str]]:
    trace_context = get_correlation_ids()
    return {
        "correlation_id": correlation_id or trace_context.get("correlation_id"),
        "trace_id": trace_context.get("trace_id"),
        "correlation_source": trace_context.get("correlation_source"),
        "notification_id": str(notification_id) if notification_id is not None else None,
        "telegram_id": str(telegram_id) if telegram_id is not None else None,
    }


def _notification_log(
    level: str,
    event: str,
    *,
    fn: str,
    contract: str,
    block: str,
    correlation_id: Optional[str] = None,
    notification_id: Optional[object] = None,
    telegram_id: Optional[object] = None,
    **fields: object,
) -> None:
    trace_context = _notification_trace_context(
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
    )
    payload = {key: value for key, value in fields.items() if value is not None}
    bound_logger = logger.bind(
        module=MODULE_ID,
        fn=fn,
        contract=contract,
        block=block,
        correlation_id=trace_context["correlation_id"],
        notification_id=trace_context["notification_id"],
        telegram_id=trace_context["telegram_id"],
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
        notification_id=trace_context["notification_id"],
        telegram_id=trace_context["telegram_id"],
        trace_id=trace_context["trace_id"],
        correlation_source=trace_context["correlation_source"],
        **payload,
    )


async def _post_notification(
    *,
    telegram_id: int,
    payload: Mapping[str, Any],
    correlation_id: Optional[str],
    notification_id: Optional[object],
    contract: str,
    label: str,
) -> bool:
    fn = "_post_notification"
    url = f"{BOT_INTERNAL_URL}/notify"

    _notification_log(
        "info",
        "START_BLOCK",
        fn=fn,
        contract=contract,
        block="POST_NOTIFY_REQUEST",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
        url=url,
    )
    try:
        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                try:
                    response = await client.post(url, json=dict(payload), timeout=5.0)
                    if response.status_code == 200:
                        _notification_log(
                            "info",
                            "END_BLOCK",
                            fn=fn,
                            contract=contract,
                            block="POST_NOTIFY_REQUEST",
                            correlation_id=correlation_id,
                            notification_id=notification_id,
                            telegram_id=telegram_id,
                            label=label,
                            outcome="delivered",
                            **get_notification_delivery_telemetry(delivered=True, status_code=response.status_code, attempt=attempt + 1),
                        )
                        return True
                    if response.status_code == 403:
                        _notification_log(
                            "warning",
                            "END_BLOCK",
                            fn=fn,
                            contract=contract,
                            block="POST_NOTIFY_REQUEST",
                            correlation_id=correlation_id,
                            notification_id=notification_id,
                            telegram_id=telegram_id,
                            label=label,
                            outcome="blocked",
                            **get_notification_delivery_telemetry(delivered=False, status_code=response.status_code),
                        )
                        return False
                    if response.status_code == 404:
                        _notification_log(
                            "warning",
                            "END_BLOCK",
                            fn=fn,
                            contract=contract,
                            block="POST_NOTIFY_REQUEST",
                            correlation_id=correlation_id,
                            notification_id=notification_id,
                            telegram_id=telegram_id,
                            label=label,
                            outcome="chat_not_found",
                            **get_notification_delivery_telemetry(delivered=False, status_code=response.status_code),
                        )
                        return False
                    if response.status_code >= 500:
                        _notification_log(
                            "error",
                            "BOT_DELIVERY_RETRY",
                            fn=fn,
                            contract=contract,
                            block="POST_NOTIFY_REQUEST",
                            correlation_id=correlation_id,
                            notification_id=notification_id,
                            telegram_id=telegram_id,
                            label=label,
                            outcome="server_error",
                            **get_notification_delivery_telemetry(delivered=False, status_code=response.status_code, attempt=attempt + 1),
                        )
                        continue
                    _notification_log(
                        "error",
                        "END_BLOCK",
                        fn=fn,
                        contract=contract,
                        block="POST_NOTIFY_REQUEST",
                        correlation_id=correlation_id,
                        notification_id=notification_id,
                        telegram_id=telegram_id,
                        label=label,
                        outcome="failed",
                        response_body=response.text,
                        **get_notification_delivery_telemetry(delivered=False, status_code=response.status_code),
                    )
                    return False
                except httpx.RequestError as exc:
                    _notification_log(
                        "warning",
                        "BOT_DELIVERY_RETRY",
                        fn=fn,
                        contract=contract,
                        block="POST_NOTIFY_REQUEST",
                        correlation_id=correlation_id,
                        notification_id=notification_id,
                        telegram_id=telegram_id,
                        label=label,
                        outcome="network_error",
                        **get_notification_delivery_telemetry(delivered=False, error=str(exc), attempt=attempt + 1),
                    )
                    continue
        _notification_log(
            "error",
            "END_BLOCK",
            fn=fn,
            contract=contract,
            block="POST_NOTIFY_REQUEST",
            correlation_id=correlation_id,
            notification_id=notification_id,
            telegram_id=telegram_id,
            label=label,
            outcome="retry_exhausted",
            **get_notification_delivery_telemetry(delivered=False),
        )
        return False
    except Exception as exc:
        _notification_log(
            "error",
            "END_BLOCK",
            fn=fn,
            contract=contract,
            block="POST_NOTIFY_REQUEST",
            correlation_id=correlation_id,
            notification_id=notification_id,
            telegram_id=telegram_id,
            label=label,
            outcome="unexpected_error",
            **get_notification_delivery_telemetry(delivered=False, error=str(exc)),
        )
        return False


# START_CONTRACT: send_bot_notification
# purpose: Send a generic bot notification payload for caller-managed flows.
# inputs: telegram_id, text, optional image_url, optional correlation_id/notification_id.
# outputs: bool delivery status.
# errors: suppresses delivery errors into False while emitting GRACE trace evidence.
# END_CONTRACT: send_bot_notification
async def send_bot_notification(
    telegram_id: int,
    text: str,
    image_url: str | None = None,
    *,
    correlation_id: str | None = None,
    notification_id: object | None = None,
) -> bool:
    """Send a generic bot notification through the internal notification gateway."""
    contract = "send_bot_notification"
    fn = "send_bot_notification"
    _notification_log(
        "info",
        "START_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="generic_notification",
    )
    if not telegram_id:
        _notification_log(
            "warning",
            "END_CONTRACT",
            fn=fn,
            contract=contract,
            block="ENTRYPOINT",
            correlation_id=correlation_id,
            notification_id=notification_id,
            telegram_id=telegram_id,
            label="generic_notification",
            outcome="missing_telegram_id",
        )
        return False

    _notification_log(
        "info",
        "START_BLOCK",
        fn=fn,
        contract=contract,
        block="BUILD_PAYLOAD",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="generic_notification",
    )
    payload: dict[str, Any] = {"telegram_id": telegram_id, "text": text}
    if image_url:
        payload["image_url"] = image_url
    _notification_log(
        "info",
        "END_BLOCK",
        fn=fn,
        contract=contract,
        block="BUILD_PAYLOAD",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="generic_notification",
        has_image=bool(image_url),
    )

    ok = await _post_notification(
        telegram_id=telegram_id,
        payload=payload,
        correlation_id=correlation_id,
        notification_id=notification_id,
        contract=contract,
        label="generic_notification",
    )
    _notification_log(
        "info" if ok else "warning",
        "END_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="generic_notification",
        outcome="delivered" if ok else "not_delivered",
    )
    return ok


# START_CONTRACT: send_report_ready_notification
# purpose: Send the canonical report ready notification aligned with report workflow delivery flow.
# inputs: telegram_id, message, optional image_url, optional correlation_id/notification_id.
# outputs: bool delivery status.
# errors: suppresses delivery errors into False while preserving report ready trace evidence.
# END_CONTRACT: send_report_ready_notification
async def send_report_ready_notification(
    telegram_id: int,
    message: str,
    image_url: str | None = None,
    *,
    correlation_id: str | None = None,
    notification_id: object | None = None,
) -> bool:
    """Send a report ready notification using report workflow wording."""
    contract = "send_report_ready_notification"
    fn = "send_report_ready_notification"
    _notification_log(
        "info",
        "START_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_ready",
    )
    _notification_log(
        "info",
        "START_BLOCK",
        fn=fn,
        contract=contract,
        block="DELEGATE_DELIVERY",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_ready",
    )
    ok = await send_bot_notification(
        telegram_id,
        message,
        image_url=image_url,
        correlation_id=correlation_id,
        notification_id=notification_id,
    )
    _notification_log(
        "info" if ok else "warning",
        "END_BLOCK",
        fn=fn,
        contract=contract,
        block="DELEGATE_DELIVERY",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_ready",
        outcome="delivered" if ok else "not_delivered",
    )
    _notification_log(
        "info" if ok else "warning",
        "END_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_ready",
        outcome="delivered" if ok else "not_delivered",
    )
    return ok


# START_CONTRACT: send_failure_notification
# purpose: Send the canonical report failure notification aligned with report workflow fallback/failure flows.
# inputs: telegram_id, message, optional correlation_id/notification_id.
# outputs: bool delivery status.
# errors: suppresses delivery errors into False while preserving report failure trace evidence.
# END_CONTRACT: send_failure_notification
async def send_failure_notification(
    telegram_id: int,
    message: str,
    *,
    correlation_id: str | None = None,
    notification_id: object | None = None,
) -> bool:
    """Send a report failure notification with workflow-aligned labeling."""
    contract = "send_failure_notification"
    fn = "send_failure_notification"
    _notification_log(
        "info",
        "START_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_failure",
    )
    _notification_log(
        "info",
        "START_BLOCK",
        fn=fn,
        contract=contract,
        block="DELEGATE_DELIVERY",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_failure",
    )
    ok = await send_bot_notification(
        telegram_id,
        message,
        correlation_id=correlation_id,
        notification_id=notification_id,
    )
    _notification_log(
        "info" if ok else "warning",
        "END_BLOCK",
        fn=fn,
        contract=contract,
        block="DELEGATE_DELIVERY",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_failure",
        outcome="delivered" if ok else "not_delivered",
    )
    _notification_log(
        "info" if ok else "warning",
        "END_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="report_failure",
        outcome="delivered" if ok else "not_delivered",
    )
    return ok


# START_CONTRACT: send_subscription_status
# purpose: Send a subscription status notification aligned with access control entitlement wording.
# inputs: telegram_id, message, optional correlation_id/notification_id.
# outputs: bool delivery status.
# errors: suppresses delivery errors into False while preserving entitlement trace evidence.
# END_CONTRACT: send_subscription_status
async def send_subscription_status(
    telegram_id: int,
    message: str,
    *,
    correlation_id: str | None = None,
    notification_id: object | None = None,
) -> bool:
    """Send a subscription status update consistent with access control labels."""
    contract = "send_subscription_status"
    fn = "send_subscription_status"
    _notification_log(
        "info",
        "START_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="subscription_status",
    )
    _notification_log(
        "info",
        "START_BLOCK",
        fn=fn,
        contract=contract,
        block="DELEGATE_DELIVERY",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="subscription_status",
    )
    ok = await send_bot_notification(
        telegram_id,
        message,
        correlation_id=correlation_id,
        notification_id=notification_id,
    )
    _notification_log(
        "info" if ok else "warning",
        "END_BLOCK",
        fn=fn,
        contract=contract,
        block="DELEGATE_DELIVERY",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="subscription_status",
        outcome="delivered" if ok else "not_delivered",
    )
    _notification_log(
        "info" if ok else "warning",
        "END_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label="subscription_status",
        outcome="delivered" if ok else "not_delivered",
    )
    return ok


# START_CONTRACT: enqueue_notification_job
# purpose: Record enqueue intent for notification jobs before delegating to delivery flows.
# inputs: telegram_id, message, label, optional image_url/correlation_id/notification_id.
# outputs: bool enqueue-and-delivery status.
# errors: suppresses delivery errors into False while preserving queue trace evidence.
# END_CONTRACT: enqueue_notification_job
async def enqueue_notification_job(
    telegram_id: int,
    message: str,
    *,
    label: str = "notification_job",
    image_url: str | None = None,
    correlation_id: str | None = None,
    notification_id: object | None = None,
) -> bool:
    """Enqueue a notification job and immediately delegate to bot delivery in-process."""
    contract = "enqueue_notification_job"
    fn = "enqueue_notification_job"
    _notification_log(
        "info",
        "START_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
    )
    _notification_log(
        "info",
        "START_BLOCK",
        fn=fn,
        contract=contract,
        block="QUEUE_NOTIFICATION_JOB",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
    )
    _notification_log(
        "info",
        "END_BLOCK",
        fn=fn,
        contract=contract,
        block="QUEUE_NOTIFICATION_JOB",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
        outcome="queued",
    )
    ok = await send_bot_notification(
        telegram_id,
        message,
        image_url=image_url,
        correlation_id=correlation_id,
        notification_id=notification_id,
    )
    _notification_log(
        "info" if ok else "warning",
        "END_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
        outcome="delivered" if ok else "not_delivered",
    )
    return ok


# START_CONTRACT: replay_admin_log
# purpose: Replay admin notification log entries through the canonical notification delivery flow.
# inputs: admin_log payload with telegram_id/text/image_url plus optional correlation_id/notification_id.
# outputs: bool replay delivery status.
# errors: suppresses malformed payloads and delivery errors into False while emitting replay evidence.
# END_CONTRACT: replay_admin_log
async def replay_admin_log(
    admin_log: Mapping[str, Any],
    *,
    correlation_id: str | None = None,
    notification_id: object | None = None,
) -> bool:
    """Replay an admin notification log entry using admin replay terminology."""
    contract = "replay_admin_log"
    fn = "replay_admin_log"
    telegram_id = admin_log.get("telegram_id")
    text = admin_log.get("text") or admin_log.get("message")
    image_url = admin_log.get("image_url")
    label = str(admin_log.get("label") or "admin_log_replay")
    _notification_log(
        "info",
        "START_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
    )
    if not telegram_id or not text:
        _notification_log(
            "warning",
            "END_CONTRACT",
            fn=fn,
            contract=contract,
            block="ENTRYPOINT",
            correlation_id=correlation_id,
            notification_id=notification_id,
            telegram_id=telegram_id,
            label=label,
            outcome="invalid_admin_log_payload",
        )
        return False

    _notification_log(
        "info",
        "START_BLOCK",
        fn=fn,
        contract=contract,
        block="REPLAY_ADMIN_LOG",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
    )
    ok = await send_bot_notification(
        int(telegram_id),
        str(text),
        image_url=str(image_url) if image_url else None,
        correlation_id=correlation_id,
        notification_id=notification_id,
    )
    _notification_log(
        "info" if ok else "warning",
        "END_BLOCK",
        fn=fn,
        contract=contract,
        block="REPLAY_ADMIN_LOG",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
        outcome="delivered" if ok else "not_delivered",
    )
    _notification_log(
        "info" if ok else "warning",
        "END_CONTRACT",
        fn=fn,
        contract=contract,
        block="ENTRYPOINT",
        correlation_id=correlation_id,
        notification_id=notification_id,
        telegram_id=telegram_id,
        label=label,
        outcome="delivered" if ok else "not_delivered",
    )
    return ok
