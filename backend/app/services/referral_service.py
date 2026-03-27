# ############################################################################
# AI_HEADER: MODULE_REFERRAL_SERVICE
# ROLE: Handle referral logic (linking users, rewarding referrers).
# DEPENDENCIES: sqlalchemy, backend.app.models
# ############################################################################

# START_MODULE_CONTRACT: M-REFERRAL-FLOW
# purpose: Owns referral graph creation on signup and partner reward execution on payout.
# owns:
#   - backend/app/services/referral_service.py
# inputs:
#   - Auth/signup orchestrators providing referrer and referee IDs
#   - Billing webhook payloads providing payer IDs and payment amounts
# outputs:
#   - Referral edges, subscription extensions, partner transactions, structured logs
# dependencies:
#   - SQLAlchemy Session factory and models (User, Referral, Transaction)
#   - backend/app/services/notification.send_bot_notification
# side_effects:
#   - Mutates subscription windows and partner balances
#   - Emits referral.* structured logs with correlation identifiers
# invariants:
#   - Each referee can be linked to at most one referrer edge
#   - Partner commission percentage is applied only after validated payments
# failure_policy:
#   - Returns False for invalid referral attempts without raising
#   - Swallows notification errors after logging failure evidence
# non_goals:
#   - Does not manage referral campaign creation or catalog pricing
# END_MODULE_CONTRACT: M-REFERRAL-FLOW

# START_MODULE_MAP: M-REFERRAL-FLOW
# entrypoints:
#   - process_referral_signup
#   - process_partner_reward
#   - resolve_referrer
# queues:
#   - Billing webhook fan-in via /api/billing/webhook
# owned_tests:
#   - tests/test_referral_logic.py
#   - tests/test_referral_unit.py
#   - tests/test_referral_flow.py
# adjacent_modules:
#   - backend/app/auth.py (signup orchestration)
#   - backend/app/services/billing.py (webhook path)
#   - backend/app/services/notification.py (bot dispatch)
# END_MODULE_MAP: M-REFERRAL-FLOW

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from ..logging_utils import get_correlation_ids, log_grace_event
from ..models import Referral, Transaction, User

logger = structlog.get_logger()

MODULE_ID = "M-REFERRAL-FLOW"
REFERRAL_EXTENSION_DAYS = 14
PARTNER_COMMISSION_PERCENT = 0.20


def _generate_correlation_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _ensure_aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _referral_log(
    level: str,
    event: str,
    *,
    fn: str,
    block: str,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields,
) -> None:
    context = get_correlation_ids()
    cid = correlation_id or context["correlation_id"] or _generate_correlation_id("REF-TRACE")
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        block=block,
        correlation_id=cid,
        trace_id=trace_id or context["trace_id"],
        correlation_source=correlation_source or context["correlation_source"] or "referral_service",
        **fields,
    )


# START_CONTRACT: FN-GRANT-REFERRAL-REWARD
# purpose: Apply the correct reward semantics for the referee and referrer.
# inputs:
#   - referrer: User gaining potential bonus window or commission placeholder
#   - referee: User receiving guaranteed trial extension
#   - referral_record: Referral edge to update (status, reward_type)
#   - now: timezone-aware execution timestamp
#   - correlation_id: structured trace identifier propagated across logs
# returns: None
# side_effects:
#   - Mutates subscription_active_until for referee/referrer
#   - Updates referral_record metadata and emits referral.* logs
# invariants:
#   - Referee always receives exactly one +14 day extension per newly created referral edge
#   - Partner referrer remains pending money reward until validated payout flow credits balance
#   - Non-partner referrer receives one +14 day extension stacked from current active end or now
# errors:
#   - Does not raise; invariants are enforced via deterministic state transitions and logging
# END_CONTRACT: FN-GRANT-REFERRAL-REWARD
def grant_referral_reward(
    *,
    referrer: User,
    referee: User,
    referral_record: Referral,
    now: datetime,
    correlation_id: str,
) -> None:
    aware_now = _ensure_aware(now) or datetime.now(timezone.utc)

    # START_BLOCK: APPLY_REFEREE_REWARD
    referee.subscription_active_until = aware_now + timedelta(days=REFERRAL_EXTENSION_DAYS)
    _referral_log(
        "info",
        "referral.referee_reward_applied",
        fn="grant_referral_reward",
        block="APPLY_REFEREE_REWARD",
        correlation_id=correlation_id,
        result="ok",
        referee_id=str(referee.id),
        expires_at=referee.subscription_active_until.isoformat(),
    )
    # END_BLOCK: APPLY_REFEREE_REWARD

    # START_BLOCK: APPLY_REFERRER_REWARD
    if referrer.is_partner:
        referral_record.reward_type = "money"
        referral_record.status = "active"
        _referral_log(
            "info",
            "referral.partner_reward_pending",
            fn="grant_referral_reward",
            block="APPLY_REFERRER_REWARD",
            correlation_id=correlation_id,
            result="pending",
            referrer_id=str(referrer.id),
        )
        return

    referral_record.reward_type = "days"
    referral_record.status = "rewarded"

    current_sub = _ensure_aware(referrer.subscription_active_until)
    if current_sub and current_sub > aware_now:
        referrer.subscription_active_until = current_sub + timedelta(days=REFERRAL_EXTENSION_DAYS)
    else:
        referrer.subscription_active_until = aware_now + timedelta(days=REFERRAL_EXTENSION_DAYS)

    _referral_log(
        "info",
        "referral.referrer_reward_granted",
        fn="grant_referral_reward",
        block="APPLY_REFERRER_REWARD",
        correlation_id=correlation_id,
        result="ok",
        referrer_id=str(referrer.id),
        expires_at=referrer.subscription_active_until.isoformat(),
    )
    # END_BLOCK: APPLY_REFERRER_REWARD


# START_CONTRACT: FN-PROCESS-REFERRAL-SIGNUP
# purpose: Validate referral actors, create the referral edge, and apply immediate rewards.
# inputs:
#   - referrer_id: UUID of the inviting user
#   - new_user_id: UUID of the referee user
#   - db: SQLAlchemy session
# returns: bool indicating whether the referral was processed
# side_effects:
#   - Writes Referral rows, mutates subscriptions, emits referral logs
# invariants:
#   - Each referee can own at most one referral edge; duplicate signup calls are rejected idempotently
#   - Self-referral and missing-actor combinations never mutate DB state
#   - Successful path commits exactly one new referral edge before returning True
# errors:
#   - Returns False without raising for invalid combinations or duplicates
# END_CONTRACT: FN-PROCESS-REFERRAL-SIGNUP
def process_referral_signup(
    referrer_id: uuid.UUID,
    new_user_id: uuid.UUID,
    db: Session,
    *,
    correlation_id: Optional[str] = None,
) -> bool:
    correlation_id = correlation_id or _generate_correlation_id("REF-SIGNUP")
    fn_name = "process_referral_signup"

    # START_BLOCK: VALIDATE_ACTORS
    referrer = db.query(User).filter(User.id == referrer_id).first()
    referee = db.query(User).filter(User.id == new_user_id).first()
    if not referrer or not referee or referrer.id == referee.id:
        _referral_log(
            "warning",
            "referral.signup_rejected",
            fn=fn_name,
            block="VALIDATE_ACTORS",
            correlation_id=correlation_id,
            result="fail",
            reason="invalid_users",
            referrer_id=str(referrer_id),
            referee_id=str(new_user_id),
        )
        return False
    # END_BLOCK: VALIDATE_ACTORS

    # START_BLOCK: ENSURE_UNIQUENESS
    existing = db.query(Referral).filter(Referral.referee_id == referee.id).first()
    if existing:
        _referral_log(
            "info",
            "referral.signup_duplicate",
            fn=fn_name,
            block="ENSURE_UNIQUENESS",
            correlation_id=correlation_id,
            result="skip",
            referee_id=str(referee.id),
            existing_referrer_id=str(existing.referrer_id),
        )
        return False
    # END_BLOCK: ENSURE_UNIQUENESS

    # START_BLOCK: CREATE_REFERRAL_EDGE
    referral = Referral(
        referrer_id=referrer.id,
        referee_id=referee.id,
        status="pending",
        reward_type="days",
    )
    db.add(referral)
    _referral_log(
        "info",
        "referral.signup_edge_created",
        fn=fn_name,
        block="CREATE_REFERRAL_EDGE",
        correlation_id=correlation_id,
        result="ok",
        referrer_id=str(referrer.id),
        referee_id=str(referee.id),
    )
    # END_BLOCK: CREATE_REFERRAL_EDGE

    # START_BLOCK: APPLY_REWARDS
    now = datetime.now(timezone.utc)
    grant_referral_reward(
        referrer=referrer,
        referee=referee,
        referral_record=referral,
        now=now,
        correlation_id=correlation_id,
    )
    # END_BLOCK: APPLY_REWARDS

    db.commit()
    _referral_log(
        "info",
        "referral.signup_processed",
        fn=fn_name,
        block="COMMIT",
        correlation_id=correlation_id,
        result="ok",
        referrer_id=str(referrer.id),
        referee_id=str(referee.id),
    )
    return True


def process_referral(referrer_id: uuid.UUID, new_user_id: uuid.UUID, db: Session) -> bool:
    # START_CONTRACT: FN-PROCESS-REFERRAL
    # purpose: Preserve legacy referral entrypoint while delegating to canonical signup flow.
    # inputs:
    #   - referrer_id: UUID of inviting user
    #   - new_user_id: UUID of referred user
    #   - db: SQLAlchemy session
    # returns: bool mirroring process_referral_signup outcome
    # side_effects:
    #   - Delegates all mutations/logging to process_referral_signup
    # invariants:
    #   - Legacy callers observe the same idempotency and uniqueness guarantees as canonical flow
    # errors:
    #   - Propagates no new errors; returns False for invalid or duplicate attempts
    # END_CONTRACT: FN-PROCESS-REFERRAL
    """Backward-compatible alias for legacy callers."""
    return process_referral_signup(referrer_id, new_user_id, db)


# START_CONTRACT: FN-CREDIT-REFERRAL-BONUS
# purpose: Credit partner commission exactly once for a rewarded referral payment.
# inputs:
#   - payer_id: UUID of the paying referee
#   - amount: validated payment amount used for commission calculation
#   - db: SQLAlchemy session
#   - correlation_id: optional propagated correlation identifier
# returns: None
# side_effects:
#   - Mutates partner balance, writes Transaction row, updates referral status, emits referral.* logs
# invariants:
#   - Missing referral edge or non-partner referrer results in no-op with evidence log
#   - Already rewarded referral edge is treated as idempotent and never double-credits balance
#   - Non-positive commission inputs never create transactions
# errors:
#   - Returns silently for invalid/non-actionable states; DB failures propagate to caller transaction boundary
# END_CONTRACT: FN-CREDIT-REFERRAL-BONUS
def process_partner_reward(
    payer_id: uuid.UUID,
    amount: float,
    db: Session,
    *,
    correlation_id: Optional[str] = None,
) -> None:
    """Calculate and credit commission to the partner who referred the payer."""

    correlation_id = correlation_id or _generate_correlation_id("REF-REWARD")
    fn_name = "process_partner_reward"

    # START_BLOCK: LOAD_REFERRAL_EDGE
    referral_link = db.query(Referral).filter(Referral.referee_id == payer_id).first()
    if not referral_link or not referral_link.referrer_id:
        _referral_log(
            "info",
            "referral.partner_reward_skipped",
            fn=fn_name,
            block="LOAD_REFERRAL_EDGE",
            correlation_id=correlation_id,
            result="skip",
            reason="no_referral_edge",
            payer_id=str(payer_id),
        )
        return

    if referral_link.status == "rewarded":
        _referral_log(
            "info",
            "referral.partner_reward_skipped",
            fn=fn_name,
            block="LOAD_REFERRAL_EDGE",
            correlation_id=correlation_id,
            result="skip",
            reason="already_rewarded",
            payer_id=str(payer_id),
            referrer_id=str(referral_link.referrer_id),
        )
        return

    referrer = db.query(User).filter(User.id == referral_link.referrer_id).first()
    if not referrer or not referrer.is_partner:
        _referral_log(
            "info",
            "referral.partner_reward_skipped",
            fn=fn_name,
            block="LOAD_REFERRAL_EDGE",
            correlation_id=correlation_id,
            result="skip",
            reason="referrer_not_partner",
            referrer_id=str(referral_link.referrer_id),
        )
        return
    # END_BLOCK: LOAD_REFERRAL_EDGE

    # START_BLOCK: CALCULATE_COMMISSION
    commission = float(amount) * PARTNER_COMMISSION_PERCENT
    if commission <= 0:
        _referral_log(
            "info",
            "referral.partner_reward_skipped",
            fn=fn_name,
            block="CALCULATE_COMMISSION",
            correlation_id=correlation_id,
            result="skip",
            reason="non_positive_commission",
            amount=amount,
        )
        return
    # END_BLOCK: CALCULATE_COMMISSION

    # START_BLOCK: CREDIT_BALANCE
    referrer.balance += type(referrer.balance)(commission)

    trx = Transaction(
        user_id=referrer.id,
        amount=commission,
        currency="RUB",
        type="referral_bonus",
        status="success",
        provider_id=f"ref_commission_{payer_id}_{datetime.now(timezone.utc).timestamp()}",
    )
    db.add(trx)
    referral_link.status = "rewarded"
    db.commit()

    _referral_log(
        "info",
        "referral.partner_reward",
        fn=fn_name,
        block="CREDIT_BALANCE",
        correlation_id=correlation_id,
        result="ok",
        partner_id=str(referrer.id),
        referee_id=str(payer_id),
        commission=commission,
    )
    # END_BLOCK: CREDIT_BALANCE

    # START_BLOCK: NOTIFY_PARTNER
    notify_partner_reward(
        telegram_id=referrer.telegram_id,
        commission=commission,
        correlation_id=correlation_id,
    )
    # END_BLOCK: NOTIFY_PARTNER


# START_CONTRACT: FN-NOTIFY-PARTNER-REWARD
# purpose: Deliver asynchronous notification about partner commission credit.
# inputs:
#   - telegram_id: destination chat ID
#   - commission: numeric commission amount
#   - correlation_id: structured trace identifier
# returns: None
# side_effects:
#   - Calls send_bot_notification and logs referral.partner_reward_notification events
# invariants:
#   - Missing telegram destination never raises and is logged as skipped delivery
#   - Notification outcome never alters already-credited partner balance
# errors:
#   - Logs failure evidence; errors are swallowed to avoid webhook retries
# END_CONTRACT: FN-NOTIFY-PARTNER-REWARD
def notify_partner_reward(
    *, telegram_id: Optional[int], commission: float, correlation_id: str
) -> None:
    fn_name = "notify_partner_reward"

    # START_BLOCK: VALIDATE_DESTINATION
    if not telegram_id:
        _referral_log(
            "warning",
            "referral.partner_reward_notification",
            fn=fn_name,
            block="VALIDATE_DESTINATION",
            correlation_id=correlation_id,
            result="skip",
            reason="missing_telegram_id",
        )
        return
    # END_BLOCK: VALIDATE_DESTINATION

    from .notification import send_bot_notification

    # START_BLOCK: DISPATCH_NOTIFICATION
    message = (
        f"💸 <b>Бонус!</b>\nВаш реферал совершил покупку.\nНачислено: {commission:.0f}₽"
    )

    async def _dispatch():
        return await send_bot_notification(telegram_id, message)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        task = loop.create_task(_dispatch())

        def _finalize(task: asyncio.Task):
            try:
                success = task.result()
                level = "info" if success else "warning"
                result = "ok" if success else "fail"
                extra = {}
            except Exception as exc:  # pragma: no cover - callback exception path
                level = "error"
                result = "fail"
                extra = {"error": str(exc)}

            _referral_log(
                level,
                "referral.partner_reward_notification",
                fn=fn_name,
                block="DISPATCH_NOTIFICATION",
                correlation_id=correlation_id,
                result=result,
                telegram_id=telegram_id,
                commission=commission,
                **extra,
            )

        task.add_done_callback(_finalize)
        return

    try:
        success = asyncio.run(_dispatch())
        level = "info" if success else "warning"
        result = "ok" if success else "fail"
        _referral_log(
            level,
            "referral.partner_reward_notification",
            fn=fn_name,
            block="DISPATCH_NOTIFICATION",
            correlation_id=correlation_id,
            result=result,
            telegram_id=telegram_id,
            commission=commission,
        )
    except Exception as exc:
        _referral_log(
            "error",
            "referral.partner_reward_notification",
            fn=fn_name,
            block="DISPATCH_NOTIFICATION",
            correlation_id=correlation_id,
            result="fail",
            telegram_id=telegram_id,
            commission=commission,
            error=str(exc),
        )
    # END_BLOCK: DISPATCH_NOTIFICATION


# START_CONTRACT: FN-RESOLVE-REFERRER
# purpose: Resolve referrer from canonical and legacy referral-code representations.
# inputs:
#   - code: referral token from signup/link context
#   - db: SQLAlchemy session
# returns: User or None
# side_effects:
#   - Emits structured lookup logs only for terminal hit/miss states
# invariants:
#   - Exact referral code match has priority over normalized or telegram-id fallback
#   - Empty code never queries for legacy IDs after early return
# errors:
#   - Returns None for unknown/invalid codes without raising
# END_CONTRACT: FN-RESOLVE-REFERRER
def resolve_referrer(code: str, db: Session) -> User | None:
    """Find referrer user by referral code variations."""
    correlation_id = _generate_correlation_id("REF-RESOLVE")
    fn_name = "resolve_referrer"

    # START_BLOCK: VALIDATE_CODE
    if not code:
        _referral_log(
            "info",
            "referral.resolve_referrer",
            fn=fn_name,
            block="VALIDATE_CODE",
            correlation_id=correlation_id,
            result="skip",
            reason="empty_code",
        )
        return None
    # END_BLOCK: VALIDATE_CODE

    # START_BLOCK: LOOKUP_EXACT
    user = db.query(User).filter(User.referral_code == code).first()
    if user:
        _referral_log(
            "info",
            "referral.resolve_referrer",
            fn=fn_name,
            block="LOOKUP_EXACT",
            correlation_id=correlation_id,
            result="hit",
            lookup="exact",
            referrer_id=str(user.id),
        )
        return user
    # END_BLOCK: LOOKUP_EXACT

    # START_BLOCK: LOOKUP_NORMALIZED
    clean_code = code
    if code.startswith("ref_"):
        clean_code = code[4:]
        user = db.query(User).filter(User.referral_code == clean_code).first()
        if user:
            _referral_log(
                "info",
                "referral.resolve_referrer",
                fn=fn_name,
                block="LOOKUP_NORMALIZED",
                correlation_id=correlation_id,
                result="hit",
                lookup="strip_ref_prefix",
                referrer_id=str(user.id),
            )
            return user

    if clean_code.startswith("u_"):
        stripped = clean_code[2:]
        user = db.query(User).filter(User.referral_code == stripped).first()
        if user:
            _referral_log(
                "info",
                "referral.resolve_referrer",
                fn=fn_name,
                block="LOOKUP_NORMALIZED",
                correlation_id=correlation_id,
                result="hit",
                lookup="strip_u_prefix",
                referrer_id=str(user.id),
            )
            return user
    # END_BLOCK: LOOKUP_NORMALIZED

    # START_BLOCK: LOOKUP_LEGACY_TELEGRAM
    if code.startswith("ref_"):
        tg_id_str = code.replace("ref_", "")
        if tg_id_str.isdigit():
            tg_id = int(tg_id_str)
            user = db.query(User).filter(User.telegram_id == tg_id).first()
            if user:
                _referral_log(
                    "info",
                    "referral.resolve_referrer",
                    fn=fn_name,
                    block="LOOKUP_LEGACY_TELEGRAM",
                    correlation_id=correlation_id,
                    result="hit",
                    lookup="legacy_telegram_id",
                    referrer_id=str(user.id),
                )
                return user
    # END_BLOCK: LOOKUP_LEGACY_TELEGRAM

    # START_BLOCK: RETURN_MISS
    _referral_log(
        "info",
        "referral.resolve_referrer",
        fn=fn_name,
        block="RETURN_MISS",
        correlation_id=correlation_id,
        result="miss",
        lookup="all",
    )
    # END_BLOCK: RETURN_MISS

    return None
