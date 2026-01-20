# ############################################################################
# AI_HEADER: MODULE_AUTH
# ROLE: Telegram WebApp authentication and data validation.
# DEPENDENCIES: fastapi, pydantic, sqlalchemy, hashlib, hmac.
# GRACE_ANCHORS: [AUTH_UTILS, AUTH_DEPENDENCY]
# ############################################################################

import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import structlog

from .db import get_db
from .models import User

logger = structlog.get_logger()

# #START_BLOCK_AUTH_UTILS
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def validate_init_data(init_data: str, bot_token: str) -> dict:
    """
    # PURPOSE: Validate Telegram WebApp initData string using HMAC-SHA256.
    # INPUT: init_data string (raw), bot_token.
    # OUTPUT: Decoded user data dict if valid. Raises ValueError if invalid.
    """
    if not bot_token:
        raise ValueError("Bot token is not set")

    try:
        parsed_data = dict(parse_qsl(init_data))
    except Exception:
        raise ValueError("Invalid initData format")

    if "hash" not in parsed_data:
        raise ValueError("Missing hash in initData")

    received_hash = parsed_data.pop("hash")
    
    # Sort keys alphabetically
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )

    # Calculate HMAC
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != received_hash:
        raise ValueError("Invalid hash signature")

    # Check expiration (e.g. 24 hours)
    auth_date = int(parsed_data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
         raise ValueError("Auth data expired")

    return parsed_data
# #END_BLOCK_AUTH_UTILS

# #START_BLOCK_AUTH_DEPENDENCY
async def get_current_user(
    x_telegram_auth: str = Header(..., alias="X-Telegram-Auth"),
    db: Session = Depends(get_db)
) -> User:
    """
    # PURPOSE: FastAPI dependency to authenticate user via initData.
    # INPUT: X-Telegram-Auth header (raw initData).
    # OUTPUT: ORM User object.
    # LOGIC:
    # 1. Validate hash.
    # 2. Extract user JSON.
    # 3. Upsert user in DB (sync fields).
    """
    if not x_telegram_auth:
        raise HTTPException(status_code=401, detail="Missing auth header")

    # DEV BYPASS (Optional, remove in strict prod if needed)
    # If header looks like a simple int, treat as ID for dev if enabled
    if os.getenv("ENVIRONMENT") == "development" and x_telegram_auth.isdigit():
        tg_id = int(x_telegram_auth)
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
             # Auto-create for dev convenience
             user = User(telegram_id=tg_id, full_name="Dev User")
             db.add(user)
             db.commit()
             db.refresh(user)
        return user

    try:
        data = validate_init_data(x_telegram_auth, BOT_TOKEN)
    except ValueError as e:
        logger.warning("auth.invalid", error=str(e))
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

    user_json = data.get("user")
    if not user_json:
        raise HTTPException(status_code=400, detail="Missing user data")

    try:
        tg_user = json.loads(user_json)
        tg_id = tg_user.get("id")
        username = tg_user.get("username")
        full_name = f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user JSON")

    # Upsert Logic
    user = db.query(User).filter(User.telegram_id == tg_id).first()
    if not user:
        user = User(
            telegram_id=tg_id,
            username=username,
            full_name=full_name,
            # Defaults
            birth_time_known=True 
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Sync profile updates if changed
        changed = False
        if user.username != username:
            user.username = username
            changed = True
        if user.full_name != full_name and full_name:
            user.full_name = full_name
            changed = True
        
        if changed:
            db.commit()
            db.refresh(user)
            
    return user
# #END_BLOCK_AUTH_DEPENDENCY
