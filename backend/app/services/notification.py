# ############################################################################
# AI_HEADER: MODULE_NOTIFICATION_SERVICE
# ROLE: Send notifications to users via Bot Internal API.
# DEPENDENCIES: httpx
# GRACE_ANCHORS: [SEND_NOTIFICATION]
# ############################################################################

import httpx
import os
import structlog

logger = structlog.get_logger()

BOT_INTERNAL_URL = os.getenv("BOT_INTERNAL_URL", "http://bot:8001")

# #START_BLOCK_SEND_NOTIFICATION
async def send_bot_notification(telegram_id: int, text: str):
    """
    # PURPOSE: Send text to user via Bot service.
    # INPUT: telegram_id, text.
    # OUTPUT: True if success.
    # CONTEXT: Uses internal HTTP API of the bot container.
    """
    if not telegram_id:
        return False
        
    url = f"{BOT_INTERNAL_URL}/notify"
    payload = {
        "telegram_id": telegram_id,
        "text": text
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=5.0)
            if resp.status_code != 200:
                logger.error("notify.failed", status=resp.status_code, body=resp.text)
                return False
            return True
    except Exception as e:
        logger.error("notify.error", error=str(e))
        return False
# #END_BLOCK_SEND_NOTIFICATION
