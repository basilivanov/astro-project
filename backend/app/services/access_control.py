# ############################################################################
# AI_HEADER: MODULE_ACCESS_CONTROL
# ROLE: Centralized logic for user entitlements and paywalls.
# DEPENDENCIES: models (User, Report, Transaction).
# ############################################################################

# START_MODULE_CONTRACT: M-ACCESS-CONTROL
# purpose: Enforce canonical runtime access decisions for subscriptions, credits, and one-off entitlements.
# inputs:
#   - User entity context
#   - Report type / product identifiers from API and billing flows
#   - SQLAlchemy session for read/write access mutations
# outputs:
#   - AccessDecision snapshots used by API/runtime guards
#   - Report row mutations for access source, entitlement linkage, and checkout bridge
# trace_obligations:
#   - Every public entrypoint emits contract/block-aware logs with module + contract + block
#   - Every runtime decision log carries correlation_id or access_request_id
#   - One-off bridge logs stay aligned with backend/app/services/one_off_entitlements.py contracts
# vm_ids:
#   - ADMIN-ENTITLEMENTS-FLOW
#   - FORECAST-LADDER-CATALOG-FLIP
# dependencies:
#   - backend/app/services/one_off_entitlements.py
#   - backend/app/services/billing.py
#   - backend/app/main.py
# side_effects:
#   - Consumes entitlements, deducts credits, ties checkout sessions to reports
# invariants:
#   - Canonical report types drive access policy
#   - Report entitlement grants remain bridgeable to checkout/admin issuance flows
# failure_policy:
#   - Raises AccessConsumptionError for invalid runtime-consumption transitions
#   - Propagates DB exceptions to caller-managed transactions
# END_MODULE_CONTRACT: M-ACCESS-CONTROL

# START_MODULE_MAP: M-ACCESS-CONTROL
# purpose: Map public runtime-access entrypoints to semantic blocks and adjacent GRACE slices.
# entrypoints:
#   - verify_runtime_access -> ACCESS_BYPASS / ACCESS_FREE / ACCESS_HORARY / ACCESS_ONE_OFF / ACCESS_SUBSCRIPTION_FALLBACK
#   - resolve_report_access -> ENTRYPOINT_ALIAS_RESOLUTION
#   - align_catalog_product -> CATALOG_ALIGNMENT (sync with one_off_entitlements FN-RESOLVE-CATALOG-PRODUCT)
#   - ensure_entitlement_bridge -> ENTITLEMENT_BRIDGE_GUARD (sync with one_off_entitlements FN-GRANT-ONE-OFF-ENTITLEMENT, LINK_CHECKOUT_SESSION)
#   - record_access_grant -> ACCESS_GRANT_RECORD
#   - build_report_access_snapshot -> SNAPSHOT_BUILD_LOOP
#   - consume_report_access -> CONSUME_DECISION_RESOLUTION / CONSUME_CREDITS / CONSUME_ENTITLEMENT_RESOLVE
# trace_obligations:
#   - Log contract boundaries and semantic block transitions without changing structlog payload shape
#   - Include module, contract, block, and correlation_id or access_request_id in bind/info/warning events
# vm_ids:
#   - ADMIN-ENTITLEMENTS-FLOW
#   - FORECAST-LADDER-CATALOG-FLIP
# owned_tests:
#   - tests/test_one_off_runtime_smoke.py
#   - tests/test_admin_grant_one_off_alignment.py
# adjacent_modules:
#   - backend/app/services/one_off_entitlements.py
#   - backend/app/services/billing.py
#   - backend/app/main.py
# END_MODULE_MAP: M-ACCESS-CONTROL

from datetime import datetime, timezone, timedelta
import os
from typing import Any, Optional, Sequence
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..core.feature_flags import (
    allow_legacy_premium_subscription_access,
    is_one_off_entitlements_runtime_enabled,
)
from ..models import BillingCheckoutSession, Report, Transaction, User
from .one_off_entitlements import (
    AccessDecision,
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
from ..logging_utils import get_correlation_ids, log_grace_event

logger = structlog.get_logger()
MODULE_ID = "M-ACCESS-CONTROL"


def _resolve_access_request_id(*, access_request_id: Optional[str] = None, report_id: Optional[Any] = None, user_id: Optional[Any] = None, report_type: Optional[str] = None) -> str:
    """
    # START_CONTRACT: FN-RESOLVE-ACCESS-REQUEST-ID
    # purpose: Derive stable access_request_id when caller does not supply one.
    # inputs: optional explicit access_request_id, report_id, user_id, report_type
    # returns: non-empty access request identifier string
    # side_effects: none
    # END_CONTRACT: FN-RESOLVE-ACCESS-REQUEST-ID
    """
    if access_request_id:
        return str(access_request_id)
    identity_parts = [str(part) for part in (user_id, report_id, report_type) if part is not None]
    return ":".join(identity_parts) if identity_parts else "access-request:unknown"


def _build_access_logger(
    *,
    contract: str,
    block: str,
    correlation_id: Optional[str] = None,
    access_request_id: Optional[str] = None,
    **fields,
):
    """
    # START_CONTRACT: FN-BUILD-ACCESS-LOGGER
    # purpose: Create structlog/logger context with canonical GRACE access fields.
    # inputs: contract, block, correlation_id/access_request_id, extra fields
    # returns: bound structlog logger
    # side_effects: none
    # END_CONTRACT: FN-BUILD-ACCESS-LOGGER
    """
    return logger.bind(
        module=MODULE_ID,
        contract=contract,
        block=block,
        correlation_id=correlation_id,
        access_request_id=access_request_id,
        **fields,
    )


def _access_log(
    level: str,
    event: str,
    *,
    fn: str,
    contract: str,
    block: str,
    correlation_id: Optional[str] = None,
    access_request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields,
) -> None:
    bound_logger = _build_access_logger(
        contract=contract,
        block=block,
        correlation_id=correlation_id,
        access_request_id=access_request_id,
        fn=fn,
    )
    getattr(bound_logger, level)(event, **fields)
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        contract=contract,
        block=block,
        correlation_id=correlation_id,
        access_request_id=access_request_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        **fields,
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


def verify_runtime_access(user: User, report_type: str, db: Session) -> AccessDecision:
    # START_CONTRACT: FN-VERIFY-RUNTIME-ACCESS
    # purpose: Resolve runtime access policy for subscription, credits, and one-off entitlements.
    # inputs:
    #   - User domain entity
    #   - Requested report_type (string, possibly alias)
    #   - SQLAlchemy Session for entitlement/subscription state
    # returns: AccessDecision with allowance, grant source, remaining unlocks, entitlement linkage
    # side_effects: none (pure read), emits access_control logs per block branch
    # errors: none (falls back to deny access)
    # END_CONTRACT: FN-VERIFY-RUNTIME-ACCESS
    contract = "FN-VERIFY-RUNTIME-ACCESS"
    canonical_report_type = normalize_report_type(report_type) or report_type

    trace_context = get_correlation_ids()
    correlation_id = trace_context.get("correlation_id")
    access_request_id = _resolve_access_request_id(
        user_id=user.id,
        report_type=canonical_report_type,
    )
    # START_BLOCK: CONTRACT_BOUNDARY
    _access_log(
        "info",
        "access_control.contract.start",
        fn="verify_runtime_access",
        contract=contract,
        block="CONTRACT_BOUNDARY",
        correlation_id=correlation_id,
        access_request_id=access_request_id,
        report_type=canonical_report_type,
        user_id=str(user.id),
        stage="start",
    )
    # END_BLOCK: CONTRACT_BOUNDARY

    # START_BLOCK: ACCESS_BYPASS
    if _has_bypass_access(user) or _has_qa_unlock(user):
        decision = allow_access(canonical_report_type, AccessGrantSource.BYPASS)
        _access_log(
            "info",
            "access_control.bypass_allow",
            fn="verify_runtime_access",
            contract=contract,
            block="ACCESS_BYPASS",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            result="ok",
            granted_via=decision.granted_via.value,
            report_type=canonical_report_type,
        )
        _access_log(
            "info",
            "access_control.contract.end",
            fn="verify_runtime_access",
            contract=contract,
            block="CONTRACT_BOUNDARY",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            report_type=canonical_report_type,
            user_id=str(user.id),
            decision="allow",
            stage="end",
        )
        return decision
    # END_BLOCK: ACCESS_BYPASS

    # START_BLOCK: ACCESS_FREE
    if canonical_report_type in FREE_REPORT_TYPES:
        decision = allow_access(canonical_report_type, AccessGrantSource.FREE)
        _access_log(
            "info",
            "access_control.free_allow",
            fn="verify_runtime_access",
            contract=contract,
            block="ACCESS_FREE",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            result="ok",
            report_type=canonical_report_type,
        )
        _access_log("info", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="allow", stage="end")
        return decision
    # END_BLOCK: ACCESS_FREE

    has_active_sub = _has_active_subscription(user)

    # START_BLOCK: ACCESS_HORARY
    if canonical_report_type in HORARY_REPORT_TYPES:
        if has_active_sub:
            quota_used = _get_horary_quota_used(user, db)
            if quota_used < 1:
                decision = allow_access(
                    canonical_report_type,
                    AccessGrantSource.SUBSCRIPTION,
                    remaining_unlocks=max(0, 1 - quota_used),
                )
                _access_log(
                    "info",
                    "access_control.horary_allow_subscription",
                    fn="verify_runtime_access",
                    contract=contract,
                    block="ACCESS_HORARY",
                    correlation_id=correlation_id,
                    access_request_id=access_request_id,
                    result="ok",
                    report_type=canonical_report_type,
                    remaining_unlocks=decision.remaining_unlocks,
                )
                _access_log("info", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="allow", stage="end")
                return decision

        credits = _get_horary_credit_balance(user, db)
        if credits >= 1:
            decision = allow_access(
                canonical_report_type,
                AccessGrantSource.CREDITS,
                remaining_unlocks=credits,
            )
            _access_log(
                "info",
                "access_control.horary_allow_credits",
                fn="verify_runtime_access",
                contract=contract,
                block="ACCESS_HORARY",
                correlation_id=correlation_id,
                access_request_id=access_request_id,
                result="ok",
                report_type=canonical_report_type,
                remaining_unlocks=credits,
            )
            _access_log("info", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="allow", stage="end")
            return decision

        _access_log(
            "info",
            "access_control.horary_deny",
            fn="verify_runtime_access",
            contract=contract,
            block="ACCESS_HORARY",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            result="fail",
            report_type=canonical_report_type,
            reason="credits_required",
        )
        decision = deny_access(canonical_report_type)
        _access_log("warning", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="deny", stage="end")
        return decision
    # END_BLOCK: ACCESS_HORARY

    # START_BLOCK: ACCESS_ONE_OFF
    if is_one_off_entitlements_runtime_enabled() and is_one_off_report_type(canonical_report_type):
        if allow_legacy_premium_subscription_access() and has_active_sub:
            decision = allow_access(
                canonical_report_type,
                AccessGrantSource.SUBSCRIPTION,
                legacy_subscription_applied=True,
            )
            _access_log(
                "info",
                "access_control.one_off_legacy_subscription",
                fn="verify_runtime_access",
                contract=contract,
                block="ACCESS_ONE_OFF",
                correlation_id=correlation_id,
                access_request_id=access_request_id,
                result="ok",
                report_type=canonical_report_type,
            )
            _access_log("info", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="allow", stage="end")
            return decision

        active_entitlement = get_active_report_entitlement(
            db,
            user_id=user.id,
            report_type=canonical_report_type,
        )
        if active_entitlement is not None:
            remaining_unlocks = count_active_report_entitlements(
                db,
                user_id=user.id,
                report_type=canonical_report_type,
            )
            decision = allow_access(
                canonical_report_type,
                AccessGrantSource.REPORT_ENTITLEMENT,
                entitlement_id=str(active_entitlement.id),
                remaining_unlocks=remaining_unlocks,
            )
            _access_log(
                "info",
                "access_control.one_off_allow_entitlement",
                fn="verify_runtime_access",
                contract=contract,
                block="ACCESS_ONE_OFF",
                correlation_id=correlation_id,
                access_request_id=access_request_id,
                result="ok",
                report_type=canonical_report_type,
                entitlement_id=str(active_entitlement.id),
                remaining_unlocks=remaining_unlocks,
            )
            _access_log("info", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="allow", stage="end")
            return decision
        _access_log(
            "info",
            "access_control.one_off_deny",
            fn="verify_runtime_access",
            contract=contract,
            block="ACCESS_ONE_OFF",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            result="fail",
            report_type=canonical_report_type,
            reason="entitlement_missing",
        )
        decision = deny_access(canonical_report_type)
        _access_log("warning", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="deny", stage="end")
        return decision
    # END_BLOCK: ACCESS_ONE_OFF

    # START_BLOCK: ACCESS_SUBSCRIPTION_FALLBACK
    if has_active_sub:
        decision = allow_access(canonical_report_type, AccessGrantSource.SUBSCRIPTION)
        _access_log(
            "info",
            "access_control.subscription_allow",
            fn="verify_runtime_access",
            contract=contract,
            block="ACCESS_SUBSCRIPTION_FALLBACK",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            result="ok",
            report_type=canonical_report_type,
        )
        _access_log("info", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="allow", stage="end")
        return decision

    _access_log(
        "info",
        "access_control.subscription_deny",
        fn="verify_runtime_access",
        contract=contract,
        block="ACCESS_SUBSCRIPTION_FALLBACK",
        correlation_id=correlation_id,
        access_request_id=access_request_id,
        result="fail",
        report_type=canonical_report_type,
        reason="subscription_expired",
    )
    decision = deny_access(canonical_report_type)
    _access_log("warning", "access_control.contract.end", fn="verify_runtime_access", contract=contract, block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_type=canonical_report_type, user_id=str(user.id), decision="deny", stage="end")
    return decision
    # END_BLOCK: ACCESS_SUBSCRIPTION_FALLBACK


def resolve_report_access(user: User, report_type: str, db: Session):
    """
    # PURPOSE: Resolve report access with a structured decision for the phase-2 one-off runtime.
    # CONTEXT: Additive API; legacy bool helpers remain for current subscription frontend paths.
    """
    # START_CONTRACT: FN-RESOLVE-REPORT-ACCESS
    # purpose: Public legacy alias that forwards runtime access resolution with contract-visible logging.
    # inputs: user, report_type, db session
    # returns: AccessDecision
    # side_effects: emits alias entrypoint logs only
    # END_CONTRACT: FN-RESOLVE-REPORT-ACCESS
    # START_BLOCK: ENTRYPOINT_ALIAS_RESOLUTION
    trace_context = get_correlation_ids()
    correlation_id = trace_context.get("correlation_id")
    access_request_id = _resolve_access_request_id(user_id=user.id, report_type=report_type)
    _access_log("info", "access_control.contract.start", fn="resolve_report_access", contract="FN-RESOLVE-REPORT-ACCESS", block="ENTRYPOINT_ALIAS_RESOLUTION", correlation_id=correlation_id, access_request_id=access_request_id, report_type=report_type, user_id=str(user.id), stage="start")
    decision = verify_runtime_access(user, report_type, db)
    _access_log("info", "access_control.contract.end", fn="resolve_report_access", contract="FN-RESOLVE-REPORT-ACCESS", block="ENTRYPOINT_ALIAS_RESOLUTION", correlation_id=correlation_id, access_request_id=access_request_id, report_type=report_type, user_id=str(user.id), decision="allow" if decision.allowed else "deny", stage="end")
    return decision
    # END_BLOCK: ENTRYPOINT_ALIAS_RESOLUTION


def serialize_access_decision(decision) -> dict[str, object]:
    return {
        "allowed": decision.allowed,
        "granted_via": decision.granted_via.value if decision.granted_via is not None else None,
        "remaining_unlocks": int(decision.remaining_unlocks or 0),
        "reason_code": decision.reason_code,
        "legacy_subscription_applied": decision.legacy_subscription_applied,
        "entitlement_id": decision.entitlement_id,
    }


def align_catalog_product(product_code: str) -> Optional[str]:
    # START_CONTRACT: FN-ALIGN-CATALOG-PRODUCT
    # purpose: Normalize incoming product code to canonical catalog key.
    # inputs:
    #   - Raw product_code from billing/admin flows
    # returns: Canonical product code string or None if unsupported
    # side_effects: none
    # errors: none
    # sync_with:
    #   - backend/app/services/one_off_entitlements.py FN-RESOLVE-CATALOG-PRODUCT
    #   - backend/app/services/one_off_entitlements.py catalog alias normalization rules
    # END_CONTRACT: FN-ALIGN-CATALOG-PRODUCT
    # START_BLOCK: CATALOG_ALIGNMENT
    trace_context = get_correlation_ids()
    correlation_id = trace_context.get("correlation_id")
    access_request_id = _resolve_access_request_id(report_type=product_code)
    _access_log("info", "access_control.contract.start", fn="align_catalog_product", contract="FN-ALIGN-CATALOG-PRODUCT", block="CATALOG_ALIGNMENT", correlation_id=correlation_id, access_request_id=access_request_id, product_code=product_code, stage="start")
    canonical = normalize_report_type(product_code)
    aligned_product = canonical if canonical in ONE_OFF_REPORT_TYPES else None
    _access_log("info" if aligned_product else "warning", "access_control.contract.end", fn="align_catalog_product", contract="FN-ALIGN-CATALOG-PRODUCT", block="CATALOG_ALIGNMENT", correlation_id=correlation_id, access_request_id=access_request_id, product_code=product_code, canonical_product=aligned_product, decision="aligned" if aligned_product else "unsupported", stage="end")
    return aligned_product
    # END_BLOCK: CATALOG_ALIGNMENT


def ensure_entitlement_bridge(access_decision: AccessDecision) -> None:
    # START_CONTRACT: FN-ENSURE-ENTITLEMENT-BRIDGE
    # purpose: Guard that a valid entitlement exists when runtime decision says REPORT_ENTITLEMENT.
    # inputs:
    #   - AccessDecision produced by verify_runtime_access
    # returns: None
    # side_effects: raises AccessConsumptionError if invariant breaks
    # errors: AccessConsumptionError("entitlement_missing") when invariant violated
    # sync_with:
    #   - backend/app/services/one_off_entitlements.py FN-GRANT-ONE-OFF-ENTITLEMENT
    #   - backend/app/services/one_off_entitlements.py LINK_CHECKOUT_SESSION
    # END_CONTRACT: FN-ENSURE-ENTITLEMENT-BRIDGE
    # START_BLOCK: ENTITLEMENT_BRIDGE_GUARD
    trace_context = get_correlation_ids()
    correlation_id = trace_context.get("correlation_id")
    access_request_id = _resolve_access_request_id(
        access_request_id=access_decision.entitlement_id,
        report_type=access_decision.report_type,
    )
    _access_log("info", "access_control.contract.start", fn="ensure_entitlement_bridge", contract="FN-ENSURE-ENTITLEMENT-BRIDGE", block="ENTITLEMENT_BRIDGE_GUARD", correlation_id=correlation_id, access_request_id=access_request_id, report_type=access_decision.report_type, granted_via=access_decision.granted_via.value if access_decision.granted_via else None, entitlement_id=access_decision.entitlement_id, stage="start")
    if access_decision.granted_via != AccessGrantSource.REPORT_ENTITLEMENT:
        _access_log("info", "access_control.contract.end", fn="ensure_entitlement_bridge", contract="FN-ENSURE-ENTITLEMENT-BRIDGE", block="ENTITLEMENT_BRIDGE_GUARD", correlation_id=correlation_id, access_request_id=access_request_id, report_type=access_decision.report_type, decision="skip", stage="end")
        return
    if not access_decision.entitlement_id:
        _access_log("warning", "access_control.entitlement_bridge_missing", fn="ensure_entitlement_bridge", contract="FN-ENSURE-ENTITLEMENT-BRIDGE", block="ENTITLEMENT_BRIDGE_GUARD", correlation_id=correlation_id, access_request_id=access_request_id, report_type=access_decision.report_type, decision="error", stage="end")
        raise AccessConsumptionError("entitlement_missing")
    _access_log("info", "access_control.contract.end", fn="ensure_entitlement_bridge", contract="FN-ENSURE-ENTITLEMENT-BRIDGE", block="ENTITLEMENT_BRIDGE_GUARD", correlation_id=correlation_id, access_request_id=access_request_id, report_type=access_decision.report_type, entitlement_id=access_decision.entitlement_id, decision="ok", stage="end")
    # END_BLOCK: ENTITLEMENT_BRIDGE_GUARD


def record_access_grant(report: Report, access_decision: AccessDecision) -> None:
    # START_CONTRACT: FN-RECORD-ACCESS-GRANT
    # purpose: Persist access metadata onto the Report row for downstream telemetry.
    # inputs:
    #   - Report ORM entity with resolved access decision
    # returns: None
    # side_effects: Mutates report.access_source
    # errors: none
    # END_CONTRACT: FN-RECORD-ACCESS-GRANT
    # START_BLOCK: ACCESS_GRANT_RECORD
    trace_context = get_correlation_ids()
    correlation_id = trace_context.get("correlation_id")
    access_request_id = _resolve_access_request_id(
        access_request_id=access_decision.entitlement_id,
        report_id=report.id,
        report_type=report.report_type,
        user_id=report.user_id,
    )
    _access_log("info", "access_control.contract.start", fn="record_access_grant", contract="FN-RECORD-ACCESS-GRANT", block="ACCESS_GRANT_RECORD", correlation_id=correlation_id, access_request_id=access_request_id, report_id=str(report.id), report_type=report.report_type, granted_via=access_decision.granted_via.value if access_decision.granted_via else None, stage="start")
    report.access_source = access_decision.granted_via.value if access_decision.granted_via else None
    _access_log("info", "access_control.contract.end", fn="record_access_grant", contract="FN-RECORD-ACCESS-GRANT", block="ACCESS_GRANT_RECORD", correlation_id=correlation_id, access_request_id=access_request_id, report_id=str(report.id), report_type=report.report_type, access_source=report.access_source, stage="end")
    # END_BLOCK: ACCESS_GRANT_RECORD


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
    # START_CONTRACT: FN-BUILD-REPORT-ACCESS-SNAPSHOT
    # purpose: Build serialized runtime access snapshot for requested canonical one-off report types.
    # inputs: user, db session, optional report_types sequence
    # returns: mapping of canonical report type to serialized AccessDecision
    # side_effects: emits block-aware snapshot logs
    # END_CONTRACT: FN-BUILD-REPORT-ACCESS-SNAPSHOT
    trace_context = get_correlation_ids()
    correlation_id = trace_context.get("correlation_id")
    access_request_id = _resolve_access_request_id(user_id=user.id, report_type="snapshot")
    # START_BLOCK: SNAPSHOT_BUILD_LOOP
    _access_log("info", "access_control.contract.start", fn="build_report_access_snapshot", contract="FN-BUILD-REPORT-ACCESS-SNAPSHOT", block="SNAPSHOT_BUILD_LOOP", correlation_id=correlation_id, access_request_id=access_request_id, user_id=str(user.id), stage="start")
    snapshot: dict[str, dict[str, object]] = {}
    for report_type in report_types or ONE_OFF_REPORT_TYPES:
        canonical_report_type = normalize_report_type(report_type) or report_type
        snapshot[canonical_report_type] = serialize_access_decision(
            verify_runtime_access(user, canonical_report_type, db)
        )
    _access_log("info", "access_control.contract.end", fn="build_report_access_snapshot", contract="FN-BUILD-REPORT-ACCESS-SNAPSHOT", block="SNAPSHOT_BUILD_LOOP", correlation_id=correlation_id, access_request_id=access_request_id, user_id=str(user.id), snapshot_size=len(snapshot), stage="end")
    return snapshot
    # END_BLOCK: SNAPSHOT_BUILD_LOOP


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
    # START_CONTRACT: FN-CONSUME-REPORT-ACCESS
    # purpose: Apply state changes after a verify_runtime_access decision once Report row exists.
    # inputs:
    #   - User entity, Report entity, SQLAlchemy Session, optional AccessDecision
    # returns: AccessDecision used for consumption
    # side_effects:
    #   - Deducts credits or consumes entitlements
    #   - Mutates Report fields (access_source, paid, entitlement_id, checkout_session_id)
    # errors:
    #   - AccessConsumptionError on missing/invalid entitlements or denied decisions
    # END_CONTRACT: FN-CONSUME-REPORT-ACCESS
    trace_context = get_correlation_ids()
    correlation_id = trace_context.get("correlation_id")
    access_request_id = _resolve_access_request_id(report_id=report.id, user_id=user.id, report_type=report.report_type)
    # START_BLOCK: CONTRACT_BOUNDARY
    _access_log("info", "access_control.contract.start", fn="consume_report_access", contract="FN-CONSUME-REPORT-ACCESS", block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_id=str(report.id), user_id=str(user.id), report_type=report.report_type, stage="start")
    # END_BLOCK: CONTRACT_BOUNDARY
    # START_BLOCK: CONSUME_DECISION_RESOLUTION
    access_decision = decision or verify_runtime_access(user, report.report_type, db)
    if not access_decision.allowed or access_decision.granted_via is None:
        _access_log("warning", "access_control.consume_denied", fn="consume_report_access", contract="FN-CONSUME-REPORT-ACCESS", block="CONSUME_DECISION_RESOLUTION", correlation_id=correlation_id, access_request_id=access_request_id, report_id=str(report.id), user_id=str(user.id), report_type=report.report_type, stage="end", decision="deny")
        raise AccessConsumptionError("access_denied")

    record_access_grant(report, access_decision)
    _access_log(
        "info",
        "access_control.consume_resolved",
        fn="consume_report_access",
        contract="FN-CONSUME-REPORT-ACCESS",
        block="CONSUME_DECISION_RESOLUTION",
        correlation_id=correlation_id,
        access_request_id=access_request_id,
        report_id=str(report.id),
        user_id=str(user.id),
        granted_via=access_decision.granted_via.value,
    )
    # END_BLOCK: CONSUME_DECISION_RESOLUTION

    if access_decision.granted_via == AccessGrantSource.CREDITS:
        # START_BLOCK: CONSUME_CREDITS
        trx = Transaction(
            user_id=user.id,
            amount=-1,
            currency="CRD",
            type="horary_spend",
            status="success",
            provider_id="internal",
        )
        db.add(trx)
        _access_log(
            "info",
            "access_control.consume_credits",
            fn="consume_report_access",
            contract="FN-CONSUME-REPORT-ACCESS",
            block="CONSUME_CREDITS",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            report_id=str(report.id),
            user_id=str(user.id),
            result="ok",
        )
        _access_log("info", "access_control.contract.end", fn="consume_report_access", contract="FN-CONSUME-REPORT-ACCESS", block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_id=str(report.id), user_id=str(user.id), report_type=report.report_type, decision="allow", stage="end")
        return access_decision
        # END_BLOCK: CONSUME_CREDITS

    if access_decision.granted_via != AccessGrantSource.REPORT_ENTITLEMENT:
        _access_log("info", "access_control.contract.end", fn="consume_report_access", contract="FN-CONSUME-REPORT-ACCESS", block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_id=str(report.id), user_id=str(user.id), report_type=report.report_type, decision="allow", stage="end")
        return access_decision

    ensure_entitlement_bridge(access_decision)

    # START_BLOCK: CONSUME_ENTITLEMENT_RESOLVE
    try:
        from uuid import UUID

        entitlement_id = UUID(access_decision.entitlement_id)
    except ValueError as exc:
        _access_log(
            "error",
            "access_control.consume_entitlement_invalid",
            fn="consume_report_access",
            contract="FN-CONSUME-REPORT-ACCESS",
            block="CONSUME_ENTITLEMENT_RESOLVE",
            correlation_id=correlation_id,
            access_request_id=access_request_id,
            report_id=str(report.id),
            entitlement_id=str(access_decision.entitlement_id),
            result="fail",
        )
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

    _access_log(
        "info",
        "access_control.consume_entitlement_complete",
        fn="consume_report_access",
        contract="FN-CONSUME-REPORT-ACCESS",
        block="CONSUME_ENTITLEMENT_RESOLVE",
        correlation_id=correlation_id,
        access_request_id=access_request_id,
        report_id=str(report.id),
        entitlement_id=str(entitlement.id),
        checkout_session_id=str(entitlement.checkout_session_id)
        if entitlement.checkout_session_id
        else None,
        result="ok",
    )
    _access_log("info", "access_control.contract.end", fn="consume_report_access", contract="FN-CONSUME-REPORT-ACCESS", block="CONTRACT_BOUNDARY", correlation_id=correlation_id, access_request_id=access_request_id, report_id=str(report.id), user_id=str(user.id), report_type=report.report_type, decision="allow", stage="end")
    return access_decision
