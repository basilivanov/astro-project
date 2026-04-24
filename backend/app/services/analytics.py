"""Analytics event persistence for funnel and report telemetry."""

# ############################################################################
# AI_HEADER: MODULE_ANALYTICS
# ROLE: Store funnel analytics events.
# DEPENDENCIES: sqlalchemy, structlog.
# GRACE_ANCHORS: [ANALYTICS_EVENT_CATALOG, ANALYTICS_EVENT_PERSISTENCE]
# ############################################################################

# START_MODULE_CONTRACT: M-ANALYTICS-EVENTS
# purpose: Validate and persist bounded analytics events with stable GRACE attribution markers.
# owns:
#   - backend/app/services/analytics.py
# inputs:
#   - SQLAlchemy session for persistence
#   - allowed analytics event name and optional envelope metadata
# outputs:
#   - AnalyticsEvent row persisted to the database when validation succeeds
#   - analytics.* structured log markers for invalid and failed writes
# dependencies:
#   - backend.app.models.AnalyticsEvent for row construction
#   - structlog for diagnostics
# side_effects:
#   - inserts analytics event rows and commits the transaction
#   - rolls back the transaction when persistence fails
# invariants:
#   - allowed event-name contract remains the gate for writes
#   - metadata payload stays JSON-string serialized for non-string inputs
#   - analytics writes keep existing commit/rollback semantics
# non_goals:
#   - changing analytics schema or event business meaning
#   - introducing asynchronous persistence or new telemetry transport
# END_MODULE_CONTRACT: M-ANALYTICS-EVENTS

# START_MODULE_MAP: M-ANALYTICS-EVENTS
# public_entrypoints:
#   - log_analytics_event -> API gateway, billing, and report telemetry persistence
# semantic_blocks:
#   - ANALYTICS_EVENT_CATALOG: allowed event-name registry and module identifiers
#   - ANALYTICS_EVENT_PERSISTENCE: validation, serialization, row assembly, and commit/rollback flow
# owned_tests:
#   - tests/test_catalog_logging.py
# adjacent_modules:
#   - backend/app/main.py
#   - backend/app/services/billing.py
# END_MODULE_MAP: M-ANALYTICS-EVENTS

import json
import uuid
from typing import Any, Optional

import structlog
from sqlalchemy.orm import Session

from ..logging_utils import log_grace_event
from ..models import AnalyticsEvent

logger = structlog.get_logger()

# START_BLOCK: ANALYTICS_EVENT_CATALOG
MODULE_ID = "M-ANALYTICS-EVENTS"

ALLOWED_ANALYTICS_EVENTS = {
    "landing_view", "cta_click", "pricing_card_click", "sample_open", "faq_open",
    "signup_started", "signup_completed", "login_completed", "profile_started", 
    "profile_completed", "profile_error",
    "product_viewed", "checkout_started", "payment_started", "payment_succeeded", 
    "payment_failed",
    "report_generation_started", "report_generation_completed", "report_opened",
    "report_read_30s", "report_read_60s", "report_scroll_50", "report_scroll_80",
    "feedback_prompt_shown", "feedback_submitted", "refund_requested",
    "app_open", "profile_fill", "buy_click", "report_generated",
    "section_view", "block_view", "time_on_report"
}
# END_BLOCK: ANALYTICS_EVENT_CATALOG


# START_BLOCK: ANALYTICS_EVENT_PERSISTENCE
# START_CONTRACT: FN-LOG-ANALYTICS-EVENT
# purpose: Persist a bounded analytics event after validating its name and normalizing metadata serialization.
# inputs:
#   - db: SQLAlchemy session bound to the current request or job
#   - event_name: analytics event identifier constrained by ALLOWED_ANALYTICS_EVENTS
#   - optional analytics envelope fields for attribution, pricing, session, and device context
# outputs:
#   - True when the analytics row commits successfully
#   - False when validation rejects the event or persistence raises
# side_effects:
#   - inserts one AnalyticsEvent row and commits on success
#   - rolls back the transaction and emits analytics.event_failed on persistence errors
# invariants:
#   - invalid event names return False before any write attempt
#   - non-string metadata is JSON serialized with ensure_ascii=True
#   - persistence field mapping remains unchanged for downstream analytics consumers
# non_goals:
#   - changing allowed event semantics
#   - changing analytics storage schema or transaction policy
def log_analytics_event(
    db: Session,
    event_name: str,
    user_id: Optional[uuid.UUID] = None,
    telegram_id: Optional[int] = None,
    source: Optional[str] = None,
    metadata: Optional[Any] = None,
    session_id: Optional[str] = None,
    path: Optional[str] = None,
    product_type: Optional[str] = None,
    price: Optional[float] = None,
    currency: Optional[str] = None,
    duration_ms: Optional[int] = None,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    device: Optional[str] = None,
    os_name: Optional[str] = None, # os is keyword
    browser: Optional[str] = None,
) -> bool:
    """
    # PURPOSE: Persist a funnel analytics event.
    # INPUT: db session, event_name, optional user_id, telegram_id, source, metadata.
    # OUTPUT: True if stored, False if skipped/failed.
    """
    # START_BLOCK: ANALYTICS_EVENT_NAME_VALIDATION
    if event_name not in ALLOWED_ANALYTICS_EVENTS:
        log_grace_event(
            "warning",
            "analytics.event_invalid",
            module=MODULE_ID,
            fn="log_analytics_event",
            block="ANALYTICS_EVENT_PERSISTENCE",
            event_name=event_name,
        )
        return False
    # END_BLOCK: ANALYTICS_EVENT_NAME_VALIDATION

    # START_BLOCK: ANALYTICS_METADATA_SERIALIZATION
    metadata_value = None
    if metadata is not None:
        if isinstance(metadata, str):
            metadata_value = metadata
        else:
            metadata_value = json.dumps(metadata, ensure_ascii=True)
    # END_BLOCK: ANALYTICS_METADATA_SERIALIZATION

    # START_BLOCK: ANALYTICS_EVENT_ROW_ASSEMBLY
    event = AnalyticsEvent(
        user_id=user_id,
        telegram_id=telegram_id,
        event_name=event_name,
        source=source,
        event_metadata=metadata_value,
        session_id=session_id,
        path=path,
        product_type=product_type,
        price=price,
        currency=currency,
        duration_ms=duration_ms,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        device=device,
        os=os_name,
        browser=browser
    )
    # END_BLOCK: ANALYTICS_EVENT_ROW_ASSEMBLY

    # START_BLOCK: ANALYTICS_EVENT_COMMIT
    try:
        db.add(event)
        db.commit()
        log_grace_event(
            "info",
            "analytics.event_persisted",
            module=MODULE_ID,
            fn="log_analytics_event",
            block="ANALYTICS_EVENT_PERSISTENCE",
            event_name=event_name,
            user_id=str(user_id) if user_id is not None else None,
            telegram_id=telegram_id,
            source=source,
            path=path,
            product_type=product_type,
            has_metadata=metadata_value is not None,
        )
        return True
    except Exception as exc:
        db.rollback()
        log_grace_event(
            "warning",
            "analytics.event_failed",
            module=MODULE_ID,
            fn="log_analytics_event",
            block="ANALYTICS_EVENT_PERSISTENCE",
            event_name=event_name,
            error=str(exc),
        )
        return False
    # END_BLOCK: ANALYTICS_EVENT_COMMIT
# END_CONTRACT: FN-LOG-ANALYTICS-EVENT
# END_BLOCK: ANALYTICS_EVENT_PERSISTENCE
