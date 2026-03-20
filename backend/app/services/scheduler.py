# ############################################################################
# AI_HEADER: MODULE_SCHEDULER
# ROLE: Simple in-memory background scheduler for periodic tasks.
# DEPENDENCIES: sqlalchemy, backend/app/models, backend/app/services/notification.
# GRACE_ANCHORS: [BIRTHDAY_TRIGGER]
############################################################################

import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, extract
from sqlalchemy.orm import Session
import structlog

from ..db import SessionLocal
from ..models import User
from .notification import send_bot_notification

logger = structlog.get_logger()

# #START_BLOCK_BIRTHDAY_TRIGGER
async def check_birthdays_daily():
    """
    # PURPOSE: Daily check for users with birthdays in 3 days.
    # LOGIC:
    # 1. Loop forever with 24h sleep.
    # 2. Query users whose birth_date (MM-DD) matches today + 3 days.
    # 3. Send notification offering "Solar Return" report.
    """
    while True:
        try:
            logger.info("scheduler.birthday_check.start")
            db = SessionLocal()
            try:
                # Calculate target date (today + 3 days)
                target_date = datetime.now(timezone.utc) + timedelta(days=3)
                target_md = target_date.strftime("%m-%d") # birth_date is YYYY-MM-DD
                
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
                        logger.info("scheduler.birthday_notify", user_id=str(user.id), telegram_id=user.telegram_id)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error("scheduler.birthday_check.error", error=str(e))
            
        # Wait until tomorrow (or check every 24h)
        # For precision, we could calculate seconds until 10:00 AM.
        await asyncio.sleep(24 * 3600)

# #END_BLOCK_BIRTHDAY_TRIGGER

# #START_BLOCK_SUBSCRIPTION_CHECK
async def check_expired_subscriptions():
    """
    # PURPOSE: Check for expired subscriptions daily.
    """
    while True:
        try:
            logger.info("scheduler.sub_check.start")
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
                    logger.info("scheduler.sub_expired", user_id=str(user.id))
                    
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
            logger.error("scheduler.sub_check.error", error=str(e))
            
        await asyncio.sleep(24 * 3600) # Daily
# #END_BLOCK_SUBSCRIPTION_CHECK

async def start_scheduler():
    """
    # PURPOSE: Entry point for background tasks.
    # CONTEXT: Called on FastAPI startup.
    """
    logger.info("scheduler.start")
    asyncio.create_task(check_birthdays_daily())
    asyncio.create_task(check_expired_subscriptions())
