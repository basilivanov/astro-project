# ############################################################################
# AI_HEADER: MODULE_ACCESS_CONTROL
# ROLE: Centralized logic for user entitlements and paywalls.
# DEPENDENCIES: models (User, Report, Transaction).
# ############################################################################

from datetime import datetime, timezone, timedelta
import os
from typing import Optional, Sequence
from zoneinfo import ZoneInfo
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..core.feature_flags import (
    allow_legacy_premium_subscription_access,
    is_one_off_entitlements_runtime_enabled,
)
from ..models import BillingCheckoutSession, Report, Transaction, User
from .one_off_entitlements import (
    AccessGrantSource,
    CheckoutSessionStatus,
    ONE_OFF_REPORT_TYPES,
    allow_access,
    consume_report_entitlement,
    count_active_report_entitlements,
    deny_access,
    get_active_report_entitlement,
    is_one_off_report_type,
    normalize_report_type,
)

HORARY_REPORT_TYPES = {"horary", "horary_answer", "horary_full"}
FREE_REPORT_TYPES = {"general_week", "general_month", "feed_daily"}


class AccessConsumptionError(RuntimeError):
    pass


def _has_bypass_access(user: User) -> bool:
    return user.is_partner or user.telegram_id in [123456789, 999]


def _has_qa_unlock(user: User) -> bool:
    if os.getenv("QA_UNLOCK_ALL_REPORTS") != "true" or not user.is_test:
        return False
    return os.getenv("ENVIRONMENT") in ["development", "staging"]


def _has_active_subscription(user: User) -> bool:
    if not user.subscription_active_until:
        return False

    sub_end = user.subscription_active_until
    if sub_end.tzinfo is None:
        sub_end = sub_end.replace(tzinfo=timezone.utc)
    return sub_end > datetime.now(timezone.utc)


def _get_horary_quota_used(user: User, db: Session) -> int:
    monday_utc = get_local_week_start_utc(user)
    quota_used = (
        db.query(func.count(Report.id))
        .filter(Report.user_id == user.id)
        .filter(Report.report_type.in_(list(HORARY_REPORT_TYPES)))
        .filter(Report.created_at >= monday_utc)
        .scalar()
    ) or 0
    return int(quota_used)


def _get_horary_credit_balance(user: User, db: Session) -> int:
    credits = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user.id)
        .filter(Transaction.currency == "CRD")
        .scalar()
    ) or 0
    return int(credits or 0)

def get_local_week_start_utc(user: User) -> datetime:
    """
    # PURPOSE: Calculate start of the week (Mon 00:00) in user's local time, converted to UTC.
    """
    tz_str = user.current_timezone or user.birth_timezone or "UTC"
    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        tz = timezone.utc
        
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(tz)
    # Go back to Monday
    monday_local = now_local - timedelta(days=now_local.weekday())
    # Reset to 00:00:00
    monday_start_local = monday_local.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Convert to UTC
    return monday_start_local.astimezone(timezone.utc)

def check_user_access(
    user: User,
    report_type: str = "natal_master",
    db: Optional[Session] = None,
) -> bool:
    """
    # PURPOSE: Determine if user is allowed to generate a report.
    # INPUT: user object, report_type, db session.
    # OUTPUT: True if allowed, False otherwise.
    """
    
    canonical_report_type = normalize_report_type(report_type) or report_type

    # 1. Partner / Admin / Specific IDs bypass
    if _has_bypass_access(user):
        return True

    # 1b. QA Unlock Bypass (Dev/Stage only for is_test=true users)
    if _has_qa_unlock(user):
        return True
    
    # 2. Free General Forecasts (by Sun sign)
    if canonical_report_type in FREE_REPORT_TYPES:
        return True

    # Check Active Sub/Trial
    has_active_sub = _has_active_subscription(user)

    # 3. Horary Logic (1 free/week for subscribers, then credits)
    if canonical_report_type in HORARY_REPORT_TYPES:
        if db is None:
            return False

        # a) Check Free Weekly Quota (Only for subscribers)
        if has_active_sub:
            quota_used = _get_horary_quota_used(user, db)
            if quota_used < 1:
                return True # Free quota available for subscriber
        
        # b) Check Credits (For everyone)
        return _get_horary_credit_balance(user, db) >= 1

    # 4. Personalized Reports (Natal, Synastry, Solar, Personalized Forecasts)
    # Require active subscription OR trial.
    return has_active_sub


def consume_access_if_needed(
    user: User,
    report_type: str,
    db: Optional[Session] = None,
) -> bool:
    """
    # PURPOSE: Deduct credits/quota if applicable.
    # INPUT: user, report_type, db.
    # OUTPUT: True if consumed or allowed (free), False if blocked.
    """
    # Partner/Test bypass
    if _has_bypass_access(user):
        return True

    # QA Unlock Bypass
    if _has_qa_unlock(user):
        return True

    canonical_report_type = normalize_report_type(report_type) or report_type

    if canonical_report_type not in HORARY_REPORT_TYPES:
        return check_user_access(user, canonical_report_type, db)

    if db is None:
        return False
        
    # Horary Consumption
    has_active_sub = _has_active_subscription(user)

    if has_active_sub:
        quota_used = _get_horary_quota_used(user, db)
        if quota_used < 1:
            return True # Uses free weekly quota
            
    # Deduct Credit
    credits = _get_horary_credit_balance(user, db)
    if credits >= 1:
        # Create deduction transaction
        trx = Transaction(
            user_id=user.id,
            amount=-1,
            currency="CRD",
            type="horary_spend",
            status="success",
            provider_id="internal"
        )
        db.add(trx)
        db.commit()
        return True
        
    return False


def resolve_report_access(user: User, report_type: str, db: Session):
    """
    # PURPOSE: Resolve report access with a structured decision for the phase-2 one-off runtime.
    # CONTEXT: Additive API; legacy bool helpers remain for current subscription frontend paths.
    """
    canonical_report_type = normalize_report_type(report_type) or report_type

    if _has_bypass_access(user) or _has_qa_unlock(user):
        return allow_access(canonical_report_type, AccessGrantSource.BYPASS)

    if canonical_report_type in FREE_REPORT_TYPES:
        return allow_access(canonical_report_type, AccessGrantSource.FREE)

    has_active_sub = _has_active_subscription(user)

    if canonical_report_type in HORARY_REPORT_TYPES:
        if has_active_sub:
            quota_used = _get_horary_quota_used(user, db)
            if quota_used < 1:
                return allow_access(
                    canonical_report_type,
                    AccessGrantSource.SUBSCRIPTION,
                    remaining_unlocks=max(0, 1 - quota_used),
                )

        credits = _get_horary_credit_balance(user, db)
        if credits >= 1:
            return allow_access(
                canonical_report_type,
                AccessGrantSource.CREDITS,
                remaining_unlocks=credits,
            )
        return deny_access(canonical_report_type)

    if is_one_off_entitlements_runtime_enabled() and is_one_off_report_type(canonical_report_type):
        if allow_legacy_premium_subscription_access() and has_active_sub:
            return allow_access(
                canonical_report_type,
                AccessGrantSource.SUBSCRIPTION,
                legacy_subscription_applied=True,
            )

        active_entitlement = get_active_report_entitlement(
            db,
            user_id=user.id,
            report_type=canonical_report_type,
        )
        if active_entitlement is not None:
            return allow_access(
                canonical_report_type,
                AccessGrantSource.REPORT_ENTITLEMENT,
                entitlement_id=str(active_entitlement.id),
                remaining_unlocks=count_active_report_entitlements(
                    db,
                    user_id=user.id,
                    report_type=canonical_report_type,
                ),
            )
        return deny_access(canonical_report_type)

    if has_active_sub:
        return allow_access(canonical_report_type, AccessGrantSource.SUBSCRIPTION)
    return deny_access(canonical_report_type)


def serialize_access_decision(decision) -> dict[str, object]:
    return {
        "allowed": decision.allowed,
        "granted_via": decision.granted_via.value if decision.granted_via is not None else None,
        "remaining_unlocks": int(decision.remaining_unlocks or 0),
        "reason_code": decision.reason_code,
        "legacy_subscription_applied": decision.legacy_subscription_applied,
    }


def build_report_access_snapshot(
    user: User,
    db: Session,
    *,
    report_types: Optional[Sequence[str]] = None,
) -> dict[str, dict[str, object]]:
    """
    # PURPOSE: Expose per-report runtime access truth for canonical one-off types.
    # CONTEXT: Additive `/api/users/me` contract; legacy bool flags stay in place.
    """
    snapshot: dict[str, dict[str, object]] = {}
    for report_type in report_types or ONE_OFF_REPORT_TYPES:
        canonical_report_type = normalize_report_type(report_type) or report_type
        snapshot[canonical_report_type] = serialize_access_decision(
            resolve_report_access(user, canonical_report_type, db)
        )
    return snapshot


def consume_report_access(
    user: User,
    report: Report,
    db: Session,
    *,
    decision=None,
):
    """
    # PURPOSE: Apply side effects for a pre-resolved access decision after a report row exists.
    # CONTEXT: Used by `/api/reports/create` to link one-off entitlements atomically to reports.
    """
    access_decision = decision or resolve_report_access(user, report.report_type, db)
    if not access_decision.allowed or access_decision.granted_via is None:
        raise AccessConsumptionError("access_denied")

    report.access_source = access_decision.granted_via.value

    if access_decision.granted_via == AccessGrantSource.CREDITS:
        trx = Transaction(
            user_id=user.id,
            amount=-1,
            currency="CRD",
            type="horary_spend",
            status="success",
            provider_id="internal",
        )
        db.add(trx)
        return access_decision

    if access_decision.granted_via != AccessGrantSource.REPORT_ENTITLEMENT:
        return access_decision

    if not access_decision.entitlement_id:
        raise AccessConsumptionError("entitlement_missing")

    try:
        from uuid import UUID

        entitlement_id = UUID(access_decision.entitlement_id)
    except ValueError as exc:
        raise AccessConsumptionError("entitlement_invalid") from exc

    entitlement = consume_report_entitlement(
        db,
        entitlement_id=entitlement_id,
        user_id=user.id,
        report_id=report.id,
    )
    if entitlement is None:
        raise AccessConsumptionError("entitlement_unavailable")

    report.entitlement_id = entitlement.id
    report.checkout_session_id = entitlement.checkout_session_id
    report.paid = True

    if entitlement.checkout_session_id:
        checkout_session = (
            db.query(BillingCheckoutSession)
            .filter(BillingCheckoutSession.id == entitlement.checkout_session_id)
            .first()
        )
        if checkout_session is not None:
            checkout_session.resumed_report_id = report.id
            if checkout_session.resumed_at is None:
                checkout_session.resumed_at = datetime.now(timezone.utc)
            if checkout_session.status == CheckoutSessionStatus.SUCCEEDED.value:
                checkout_session.status = CheckoutSessionStatus.RESUMED.value
            db.add(checkout_session)

    return access_decision
