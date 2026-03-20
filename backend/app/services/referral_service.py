# ############################################################################
# AI_HEADER: MODULE_REFERRAL_SERVICE
# ROLE: Handle referral logic (linking users, rewarding referrers).
# DEPENDENCIES: sqlalchemy, backend.app.models
# ############################################################################

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from ..models import User, Referral, Transaction
import structlog

logger = structlog.get_logger()

# Config
PARTNER_COMMISSION_PERCENT = 0.20

def process_partner_reward(payer_id: uuid.UUID, amount: float, db: Session) -> None:
    """
    # PURPOSE: Calculate and credit commission to the partner who referred the payer.
    # CONTEXT: Called by billing webhook upon successful payment.
    """
    # 1. Find Referrer
    referral_link = db.query(Referral).filter(Referral.referee_id == payer_id).first()
    if not referral_link or not referral_link.referrer_id:
        return # Organic user or no tracking

    referrer = db.query(User).filter(User.id == referral_link.referrer_id).first()
    if not referrer or not referrer.is_partner:
        return # Referrer is not a partner (regular users get Days on signup, not Money on pay)

    # 2. Calculate Commission
    commission = float(amount) * PARTNER_COMMISSION_PERCENT
    if commission <= 0:
        return

    # 3. Credit Balance
    referrer.balance += type(referrer.balance)(commission)
    
    # 4. Log Transaction
    trx = Transaction(
        user_id=referrer.id,
        amount=commission,
        currency="RUB",
        type="referral_bonus",
        status="success",
        provider_id=f"ref_commision_{payer_id}_{datetime.now().timestamp()}"
    )
    db.add(trx)
    db.commit()
    
    logger.info("referral.partner_reward", partner_id=str(referrer.id), amount=commission)
    
    # Notify partner via bot
    if referrer.telegram_id:
        import asyncio
        from .notification import send_bot_notification
        msg = f"💸 <b>Бонус!</b>\nВаш реферал совершил покупку.\nНачислено: {commission:.0f}₽"
        asyncio.create_task(send_bot_notification(referrer.telegram_id, msg))

def process_referral(referrer_id: uuid.UUID, new_user_id: uuid.UUID, db: Session) -> bool:
    """
    # PURPOSE: Process a new referral connection.
    # INPUT: referrer_id, new_user_id, db session.
    # OUTPUT: Boolean (True if processed, False if ignored/invalid).
    # LOGIC:
    # 1. Validate users exist.
    # 2. Check if referral already exists (idempotency).
    # 3. Create Referral record.
    # 4. Reward New User (15 days).
    # 5. Reward Referrer (15 days) IF not partner. Partner gets nothing now (CPA model later).
    """
    
    # 1. Fetch Users
    referrer = db.query(User).filter(User.id == referrer_id).first()
    new_user = db.query(User).filter(User.id == new_user_id).first()
    
    if not referrer or not new_user:
        return False
        
    if referrer.id == new_user.id:
        return False # Self-referral protection

    # 2. Check Exists
    existing = db.query(Referral).filter(Referral.referee_id == new_user.id).first()
    if existing:
        return False # Already referred
        
    # 3. Create Record
    referral = Referral(
        referrer_id=referrer.id,
        referee_id=new_user.id,
        status="pending", 
        reward_type="days"
    )
    db.add(referral)
    
    now = datetime.now(timezone.utc)
    
    # 4. Reward New User (Always +14 days from NOW)
    # Standard MVP Trial = 14 days.
    new_user.subscription_active_until = now + timedelta(days=14)
    
    # 5. Reward Referrer
    if referrer.is_partner:
        # Partners get money/percent later (RevShare)
        referral.reward_type = "money"
        referral.status = "active"
    else:
        # Regular user gets +14 days immediately
        referral.reward_type = "days"
        referral.status = "rewarded" 
        
        current_sub = referrer.subscription_active_until
        # Ensure timezone awareness for comparison
        if current_sub and current_sub.tzinfo is None:
             current_sub = current_sub.replace(tzinfo=timezone.utc)

        if current_sub and current_sub > now:
            referrer.subscription_active_until = current_sub + timedelta(days=14)
        else:
            referrer.subscription_active_until = now + timedelta(days=14)
            
    db.commit()
    return True

def resolve_referrer(code: str, db: Session) -> User | None:
    """
    # PURPOSE: Find referrer user by code (supports 'ref_123' and 'u_CODE').
    """
    if not code:
        return None
        
    # 1. Exact match (e.g. "u_ABC123" or just code if stored so)
    user = db.query(User).filter(User.referral_code == code).first()
    if user:
        return user
        
    # 2. Try stripping prefixes
    
    # Handle "ref_" prefix (common in start params)
    clean_code = code
    if code.startswith("ref_"):
        clean_code = code[4:] # Remove "ref_"
        
        # Try to find by code without "ref_"
        user = db.query(User).filter(User.referral_code == clean_code).first()
        if user:
            return user
            
    # Handle "u_" prefix stripping if DB stores without "u_" (just in case)
    # If input is "u_ABC" and DB has "ABC"
    if clean_code.startswith("u_"):
        stripped = clean_code[2:]
        user = db.query(User).filter(User.referral_code == stripped).first()
        if user:
            return user

    # 3. Legacy: ref_ID (Telegram ID)
    # Only if we stripped "ref_" and failed to find by code string
    if code.startswith("ref_"):
        try:
            tg_id_str = code.replace("ref_", "")
            if tg_id_str.isdigit():
                tg_id = int(tg_id_str)
                user = db.query(User).filter(User.telegram_id == tg_id).first()
                if user:
                    return user
        except ValueError:
            pass
            
    return None
