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
async def send_bot_notification(telegram_id: int, text: str, image_url: str = None):
    """
    # PURPOSE: Send text (and optionally image) to user via Bot service.
    # INPUT: telegram_id, text, image_url.
    # OUTPUT: True if success.
    # CONTEXT: Uses internal HTTP API of the bot container.
    """
    if not telegram_id:
        logger.warning("notify.missing_telegram_id")
        return False
        
    url = f"{BOT_INTERNAL_URL}/notify"
    payload = {
        "telegram_id": telegram_id,
        "text": text
    }
    if image_url:
        payload["image_url"] = image_url
    
    try:
        async with httpx.AsyncClient() as client:
            # Simple retry logic for connection errors
            for attempt in range(3):
                try:
                    resp = await client.post(url, json=payload, timeout=5.0)
                    if resp.status_code == 200:
                        return True
                    elif resp.status_code == 403: # User blocked bot
                        logger.warning("notify.blocked", telegram_id=telegram_id)
                        return False # Do not retry
                    elif resp.status_code == 404:
                        logger.warning("notify.chat_not_found", telegram_id=telegram_id)
                        return False
                    elif resp.status_code >= 500:
                        logger.error("notify.server_error", status=resp.status_code)
                        continue # Retry
                    else:
                        logger.error("notify.failed", status=resp.status_code, body=resp.text)
                        return False
                except httpx.RequestError as exc:
                    logger.warning("notify.network_error", error=str(exc), attempt=attempt)
                    continue
            return False
    except Exception as e:
        logger.error("notify.error", error=str(e))
        return False
# #END_BLOCK_SEND_NOTIFICATION
