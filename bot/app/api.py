# ############################################################################
# AI_HEADER: MODULE_BOT_API
# ROLE: Internal API for Bot service to receive notifications from Backend.
# DEPENDENCIES: aiohttp, bot.app.main
# GRACE_ANCHORS: [BOT_SERVER_SETUP, NOTIFY_HANDLER]
# ############################################################################

from aiohttp import web
import logging

logger = logging.getLogger(__name__)

_bot_instance = None

# #START_BLOCK_NOTIFY_HANDLER
async def handle_notify(request):
    """
    # PURPOSE: Send a message to a user via Bot API.
    # INPUT: JSON {telegram_id, text, keyboard?}.
    # CONTEXT: Called by Backend when a report is ready.
    """
    global _bot_instance
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id")
        text = data.get("text")
        
        if not telegram_id or not text:
            return web.json_response({"error": "missing_fields"}, status=400)
            
        if _bot_instance:
            await _bot_instance.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
        else:
            logger.error("Bot instance not initialized")
            return web.json_response({"error": "bot_not_ready"}, status=500)
            
        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.error(f"Notify failed: {e}")
        return web.json_response({"error": str(e)}, status=500)
# #END_BLOCK_NOTIFY_HANDLER

# #START_BLOCK_BOT_SERVER_SETUP
async def start_bot_server(bot, host="0.0.0.0", port=8001):
    """
    # PURPOSE: Run a lightweight HTTP server alongside polling.
    # CONTEXT: Runs in the same asyncio loop as the bot.
    """
    global _bot_instance
    _bot_instance = bot
    
    app = web.Application()
    app.router.add_post("/notify", handle_notify)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Bot Internal API running on {host}:{port}")
# #END_BLOCK_BOT_SERVER_SETUP
