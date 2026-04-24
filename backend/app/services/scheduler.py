"""Background scheduler jobs for operational automation."""

# ############################################################################
# AI_HEADER: MODULE_SCHEDULER
# ROLE: Simple in-memory background scheduler for periodic tasks.
# DEPENDENCIES: sqlalchemy, backend/app/models, backend/app/services/notification.
# GRACE_ANCHORS: [SCHEDULER_CONSTANTS, SCHEDULER_BIRTHDAY_JOB, SCHEDULER_SUBSCRIPTION_JOB, SCHEDULER_STARTUP]
############################################################################

# START_MODULE_CONTRACT: M-OPS-AUTOMATION
# purpose: Run bounded scheduler entrypoints for birthday prompts and subscription expiry checks.
# owns:
#   - backend/app/services/scheduler.py
# inputs:
#   - database session factory for active users and subscriptions
#   - current UTC time for daily job windows
#   - Telegram notification delivery helper
# outputs:
#   - scheduled notification side effects
#   - subscription status updates for expired active subscriptions
#   - scheduler.* structured log markers with stable module/function/block attribution
# dependencies:
#   - backend.app.db.SessionLocal for database sessions
#   - backend.app.models.User and backend.app.models.Subscription for job queries
#   - backend.app.services.notification.send_bot_notification for outbound messages
# side_effects:
#   - creates asyncio background tasks at API startup
#   - reads and mutates billing subscription rows
#   - sends Telegram bot notifications
# invariants:
#   - job cadence remains a 24-hour loop
#   - birthday target remains today + 3 days using UTC date matching
#   - subscription expiry cutoff remains now - 1 day for active subscriptions
# failure_policy:
#   - log and continue on job iteration failures without stopping the infinite scheduler loops
# non_goals:
#   - changing billing, user, or notification business semantics
#   - introducing a new scheduler runtime or persistence layer
# END_MODULE_CONTRACT: M-OPS-AUTOMATION

# START_MODULE_MAP: M-OPS-AUTOMATION
# public_entrypoints:
#   - start_scheduler -> FastAPI startup background task registration
# job_entrypoints:
#   - check_birthdays_daily -> daily birthday notification loop
#   - check_expired_subscriptions -> daily expired subscription loop
# internal_helpers:
#   - _log_scheduler_event -> emit stable scheduler.* structured logs with module/function/block attribution
# semantic_blocks:
#   - SCHEDULER_CONSTANTS: stable module id, sleep interval, and log marker helper
#   - SCHEDULER_BIRTHDAY_JOB: birthday query and notification job
#   - SCHEDULER_SUBSCRIPTION_JOB: subscription expiry mutation and notification job
#   - SCHEDULER_STARTUP: scheduler task creation entrypoint
# owned_tests:
#   - tests/test_billing_scheduler.py
# adjacent_modules:
#   - backend/app/main.py
#   - backend/app/services/billing.py
#   - backend/app/services/notification.py
# END_MODULE_MAP: M-OPS-AUTOMATION

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from ..db import SessionLocal
from ..logging_utils import log_grace_event
from ..models import User
from .notification import send_bot_notification

logger = structlog.get_logger()

# START_BLOCK: SCHEDULER_CONSTANTS
MODULE_ID = "M-OPS-AUTOMATION"
DAILY_JOB_SLEEP_SECONDS = 24 * 3600


# START_CONTRACT: FN-LOG-SCHEDULER-EVENT
# purpose: Emit stable structured logs for scheduler entrypoints without mutating business flow.
# inputs:
#   - structlog level, event name, function id, semantic block id, and optional fields
# outputs:
#   - scheduler.* log event with GRACE module/function/block metadata
# side_effects:
#   - writes to configured structlog sinks
def _log_scheduler_event(level: str, event: str, *, fn: str, block: str, **fields: Any) -> None:
    log_grace_event(
        level,
        event,
        module=MODULE_ID,
        fn=fn,
        block=block,
        **{key: value for key, value in fields.items() if value is not None},
    )
# END_CONTRACT: FN-LOG-SCHEDULER-EVENT
# END_BLOCK: SCHEDULER_CONSTANTS


# START_BLOCK: SCHEDULER_BIRTHDAY_JOB
# START_CONTRACT: FN-CHECK-BIRTHDAYS-DAILY
# purpose: Run the daily birthday reminder scheduler loop.
# inputs:
#   - current UTC date and DB-backed user records
# outputs:
#   - birthday reminder notifications for users matching today + 3 days
# side_effects:
#   - opens DB sessions, sends Telegram notifications, writes scheduler logs
# invariants:
#   - loop cadence stays daily
#   - birthday lookup stays anchored to month-day matching against today + 3 days
# errors:
#   - logs iteration failures and resumes after the sleep interval
async def check_birthdays_daily():
    while True:
        try:
            _log_scheduler_event(
                "info",
                "scheduler.birthday_check.start",
                fn="check_birthdays_daily",
                block="SCHEDULER_BIRTHDAY_JOB",
            )
            db = SessionLocal()
            try:
                # Calculate target date (today + 3 days)
                target_date = datetime.now(timezone.utc) + timedelta(days=3)
                target_md = target_date.strftime("%m-%d")  # birth_date is YYYY-MM-DD
                
                # We need to filter by month and day. birth_date is String(32).
                # In SQLite/Postgres this might differ. 
                # Let's do it simply: load users or use LIKE.
                # Since birth_date is "YYYY-MM-DD", we want "____-MM-DD".
                pattern = f"____-{target_md}"
                
                users = db.query(User).filter(User.birth_date.like(pattern)).all()
                
                for user in users:
                    if user.telegram_id:
                        msg = (
                            f"🎈 {user.full_name}, скоро твой День Рождения! ✨\n\n"
                            "Звезды готовят новый цикл. Самое время заказать «Соляр» — "
                            "персональный прогноз на твой личный год, чтобы прожить его максимально ярко. 🚀"
                        )
                        await send_bot_notification(user.telegram_id, msg)
                        _log_scheduler_event(
                            "info",
                            "scheduler.birthday_notify",
                            fn="check_birthdays_daily",
                            block="SCHEDULER_BIRTHDAY_JOB",
                            user_id=str(user.id),
                            telegram_id=user.telegram_id,
                        )
                
            finally:
                db.close()
                
        except Exception as e:
            _log_scheduler_event(
                "error",
                "scheduler.birthday_check.error",
                fn="check_birthdays_daily",
                block="SCHEDULER_BIRTHDAY_JOB",
                error=str(e),
            )
            
        # Wait until tomorrow (or check every 24h)
        # For precision, we could calculate seconds until 10:00 AM.
        await asyncio.sleep(DAILY_JOB_SLEEP_SECONDS)
# END_CONTRACT: FN-CHECK-BIRTHDAYS-DAILY
# END_BLOCK: SCHEDULER_BIRTHDAY_JOB


# START_BLOCK: SCHEDULER_SUBSCRIPTION_JOB
# START_CONTRACT: FN-CHECK-EXPIRED-SUBSCRIPTIONS
# purpose: Run the daily expired-subscription scheduler loop.
# inputs:
#   - current UTC time and active subscription/user rows
# outputs:
#   - inactive subscription statuses and expiry notifications for overdue users
# side_effects:
#   - opens DB sessions, mutates subscription rows, commits changes, sends Telegram notifications, writes scheduler logs
# invariants:
#   - active subscriptions become inactive only when user access expired before now - 1 day
#   - loop cadence stays daily
# errors:
#   - logs iteration failures and resumes after the sleep interval
async def check_expired_subscriptions():
    while True:
        try:
            _log_scheduler_event(
                "info",
                "scheduler.sub_check.start",
                fn="check_expired_subscriptions",
                block="SCHEDULER_SUBSCRIPTION_JOB",
            )
            db = SessionLocal()
            try:
                from ..models import Subscription
                now = datetime.now(timezone.utc)
                
                # Find active subs where next_billing_at < now (grace period?)
                # Actually, entitlements depend on User.subscription_active_until.
                # But Subscription model tracks the billing status.
                
                # Logic:
                # 1. Find Users where subscription_active_until < now - 1 day (grace)
                #    AND Subscription.status == 'active'
                
                expired_cutoff = now - timedelta(days=1)
                
                subs = (
                    db.query(Subscription)
                    .join(User)
                    .filter(Subscription.status == "active")
                    .filter(User.subscription_active_until < expired_cutoff)
                    .all()
                )
                
                for sub in subs:
                    sub.status = "inactive"
                    user = sub.user
                    _log_scheduler_event(
                        "info",
                        "scheduler.sub_expired",
                        fn="check_expired_subscriptions",
                        block="SCHEDULER_SUBSCRIPTION_JOB",
                        user_id=str(user.id),
                    )
                    
                    if user.telegram_id:
                        msg = (
                            "⚠️ <b>Подписка истекла</b>\n\n"
                            "Твой доступ к Premium прогнозам приостановлен. "
                            "Продли подписку, чтобы оставаться в потоке! ✨"
                        )
                        await send_bot_notification(user.telegram_id, msg)
                        
                db.commit()
                
            finally:
                db.close()
        except Exception as e:
            _log_scheduler_event(
                "error",
                "scheduler.sub_check.error",
                fn="check_expired_subscriptions",
                block="SCHEDULER_SUBSCRIPTION_JOB",
                error=str(e),
            )
            
        await asyncio.sleep(DAILY_JOB_SLEEP_SECONDS)  # Daily
# END_CONTRACT: FN-CHECK-EXPIRED-SUBSCRIPTIONS
# END_BLOCK: SCHEDULER_SUBSCRIPTION_JOB


# START_BLOCK: SCHEDULER_STARTUP
# START_CONTRACT: FN-START-SCHEDULER
# purpose: Register scheduler background tasks during FastAPI startup.
# inputs:
#   - running asyncio event loop at application startup
# outputs:
#   - detached tasks for birthday and subscription scheduler loops
# side_effects:
#   - schedules long-lived asyncio tasks and writes startup log event
async def start_scheduler():
    _log_scheduler_event(
        "info",
        "scheduler.start",
        fn="start_scheduler",
        block="SCHEDULER_STARTUP",
    )
    asyncio.create_task(check_birthdays_daily())
    asyncio.create_task(check_expired_subscriptions())
# END_CONTRACT: FN-START-SCHEDULER
# END_BLOCK: SCHEDULER_STARTUP
