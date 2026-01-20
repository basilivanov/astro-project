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
    
    # 4. Reward New User (Always +15 days from NOW)
    # Task says: "Новичку всегда subscription_active_until = now + 15 days"
    new_user.subscription_active_until = now + timedelta(days=15)
    
    # 5. Reward Referrer
    if referrer.is_partner:
        # Partners get money/percent later, not days now.
        # We leave status as 'pending' to be processed by a future CPA batch job.
        referral.status = "pending"
    else:
        # Regular user gets +15 days immediately
        referral.status = "rewarded" 
        
        current_sub = referrer.subscription_active_until
        # Ensure timezone awareness for comparison
        if current_sub and current_sub.tzinfo is None:
             current_sub = current_sub.replace(tzinfo=timezone.utc)

        if current_sub and current_sub > now:
            referrer.subscription_active_until = current_sub + timedelta(days=15)
        else:
            referrer.subscription_active_until = now + timedelta(days=15)
            
    db.commit()
    return True
