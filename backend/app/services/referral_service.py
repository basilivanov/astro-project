# ############################################################################
# AI_HEADER: MODULE_REFERRAL_SERVICE
# ROLE: Handle referral logic (linking users, rewarding referrers).
# DEPENDENCIES: sqlalchemy, backend.app.models
# ############################################################################

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from ..models import User, Referral

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
        # Partners get money/percent later, not days now.
        # We leave status as 'pending' to be processed by a future CPA batch job.
        referral.status = "pending"
    else:
        # Regular user gets +14 days immediately
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
