# ############################################################################
# AI_HEADER: MODULE_BOT_MAIN
# ROLE: Telegram Bot Entry Point (Aiogram 3.x).
# DEPENDENCIES: aiogram, sqlalchemy, backend.app.models.
# GRACE_ANCHORS: [BOT_SETUP, BOT_HANDLERS, BOT_DB_LOGIC, BOT_STARTUP]
# ############################################################################

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import structlog
from app.api import start_bot_server

# Setup simple logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = structlog.get_logger()

# --- IMPORTS FROM BACKEND ---
try:
    from backend.app.models import User, Referral, Base
    from backend.app.services.code_gen import generate_referral_code
    # Note: backend.app.db is NOT imported to avoid Sync Engine creation side-effects.
    DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql+psycopg2", "postgresql+asyncpg")
except ImportError:
    logger.error("backend_import_failed", msg="Could not import backend.app.models")
    sys.exit(1)
except Exception as e:
    logger.error("backend_import_error", error=str(e))
    sys.exit(1)


# #START_BLOCK_BOT_SETUP
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://app.astrograce.ru")

if not BOT_TOKEN:
    logger.critical("bot.token_missing")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Async DB Setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
# #END_BLOCK_BOT_SETUP


# #START_BLOCK_BOT_DB_LOGIC
async def process_async_referral(session: AsyncSession, referrer_id: int, new_user_obj: User):
    """
    # PURPOSE: Async implementation of referral logic.
    # LOGIC:
    # 1. Validate referrer exists.
    # 2. Check if already referred.
    # 3. Create Referral record.
    # 4. Reward New User (Always +15 days).
    # 5. Reward Referrer (Only if NOT partner).
    """
    # 1. Find Referrer
    res = await session.execute(select(User).where(User.telegram_id == referrer_id))
    referrer = res.scalars().first()
    
    if not referrer:
        return # Invalid code
        
    if referrer.id == new_user_obj.id:
        return # Self-referral
        
    # 2. Check Existing
    existing_res = await session.execute(select(Referral).where(Referral.referee_id == new_user_obj.id))
    if existing_res.scalars().first():
        return # Already referred

    # 3. Create Record
    referral = Referral(
        referrer_id=referrer.id,
        referee_id=new_user_obj.id,
        status="pending",
        reward_type="days"
    )
    session.add(referral)
    
    now = datetime.now(timezone.utc)
    
    # 4. Reward New User (+15 days from NOW)
    # Note: User was created with 3 days trial initially in get_or_create_user?
    # Or we update it here.
    new_user_obj.subscription_active_until = now + timedelta(days=15)
    
    # 5. Reward Referrer
    if referrer.is_partner:
        # Partners get money/percent later (CPA). Nothing now.
        referral.status = "pending"
    else:
        # Regular user gets +15 days
        referral.status = "rewarded"
        
        current_sub = referrer.subscription_active_until
        # Ensure timezone awareness
        if current_sub and current_sub.tzinfo is None:
             current_sub = current_sub.replace(tzinfo=timezone.utc)

        if current_sub and current_sub > now:
            referrer.subscription_active_until = current_sub + timedelta(days=15)
        else:
            referrer.subscription_active_until = now + timedelta(days=15)
            
        # Notify referrer
        try:
            await bot.send_message(
                referrer.telegram_id, 
                f"🎉 <b>У вас новый реферал!</b>\n"
                f"{new_user_obj.full_name} присоединился.\n"
                f"Вам начислено +15 дней доступа! 🎁"
            )
        except Exception:
            pass 

async def get_or_create_user(telegram_id: int, username: str, full_name: str, referral_arg: str = None):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if user:
            # Update info
            if user.username != username or user.full_name != full_name:
                user.username = username
                user.full_name = full_name
                await session.commit()
            
            # Ensure ref code exists (migration for old users)
            if not user.referral_code:
                user.referral_code = generate_referral_code()
                await session.commit()
                
            return user

        # Create New User
        logger.info("bot.user_create", telegram_id=telegram_id)
        
        # Default trial: 3 days (will be upgraded to 15 if ref valid)
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=3)
        
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            subscription_active_until=trial_end,
            birth_time_known=True,
            balance=0,
            referral_code=generate_referral_code()
        )
        session.add(new_user)
        await session.flush()
        
        # Handle Referral
        if referral_arg:
            referrer_id_to_find = None
            
            # New format: u_12345
            if referral_arg.startswith("u_"):
                ref_res = await session.execute(select(User).where(User.referral_code == referral_arg))
                referrer = ref_res.scalars().first()
                if referrer:
                    referrer_id_to_find = referrer.telegram_id
            
            # Legacy format: ref_12345
            elif referral_arg.startswith("ref_"):
                try:
                    referrer_id_to_find = int(referral_arg.replace("ref_", ""))
                except ValueError:
                    pass

            if referrer_id_to_find:
                await process_async_referral(session, referrer_id_to_find, new_user)

        await session.commit()
        return new_user
# #END_BLOCK_BOT_DB_LOGIC


# #START_BLOCK_BOT_HANDLERS
@dp.message(CommandStart())
async def command_start_handler(message: types.Message, command: CommandObject):
    """
    # PURPOSE: Handle /start command.
    """
    args = command.args
    user_full_name = message.from_user.full_name
    username = message.from_user.username
    tg_id = message.from_user.id
    
    await get_or_create_user(tg_id, username, user_full_name, args)
    
    text = (
        f"Привет, {user_full_name}! ✨\n\n"
        "Я <b>AstroGrace</b> — твой персональный проводник по звездам.\n"
        "Я помогу найти ответы, спланировать год и понять себя.\n\n"
        "👇 <b>Нажми кнопку ниже, чтобы открыть приложение</b>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Открыть Космос", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await message.answer(text, reply_markup=kb)
# #END_BLOCK_BOT_HANDLERS


# #START_BLOCK_BOT_STARTUP
async def main():
    logger.info("bot.starting")
    
    # Start Internal API
    asyncio.create_task(start_bot_server(bot))
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
# #END_BLOCK_BOT_STARTUP