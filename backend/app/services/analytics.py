# ############################################################################
# AI_HEADER: MODULE_ANALYTICS
# ROLE: Store funnel analytics events.
# DEPENDENCIES: sqlalchemy, structlog.
# GRACE_ANCHORS: [ANALYTICS_EVENTS]
# ############################################################################

import json
import uuid
from typing import Any, Optional

import structlog
from sqlalchemy.orm import Session

from ..models import AnalyticsEvent

logger = structlog.get_logger()

# #START_BLOCK_ANALYTICS_EVENTS
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
    if event_name not in ALLOWED_ANALYTICS_EVENTS:
        logger.warning("analytics.event_invalid", event_name=event_name)
        return False

    metadata_value = None
    if metadata is not None:
        if isinstance(metadata, str):
            metadata_value = metadata
        else:
            metadata_value = json.dumps(metadata, ensure_ascii=True)

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
    try:
        db.add(event)
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        logger.warning("analytics.event_failed", event_name=event_name, error=str(exc))
        return False
# #END_BLOCK_ANALYTICS_EVENTS