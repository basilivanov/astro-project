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
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from functools import wraps

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
from app.stt import transcribe_audio

# Setup simple logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = structlog.get_logger()

# --- IMPORTS FROM BACKEND ---
try:
    from backend.app.models import AgentTask, User, Referral, Base
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
BOT_MEDIA_DIR = os.getenv("BOT_MEDIA_DIR", "/app/data")
BOT_ADMIN_IDS = {
    int(item.strip())
    for item in os.getenv("BOT_ADMIN_IDS", "").split(",")
    if item.strip().isdigit()
}

if not BOT_TOKEN:
    logger.critical("bot.token_missing")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Async DB Setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
# #END_BLOCK_BOT_SETUP


def is_admin_user(telegram_id: int) -> bool:
    if not BOT_ADMIN_IDS:
        return True
    return telegram_id in BOT_ADMIN_IDS


def normalize_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def summarize_text(text: str, max_len: int = 220) -> str:
    compact = normalize_text(text)
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 3]}..."


async def notify_admins(message: str) -> None:
    if not BOT_ADMIN_IDS:
        return
    for admin_id in BOT_ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message)
        except Exception:
            logger.warning("bot.admin_notify_failed", admin_id=admin_id)


async def handle_handler_error(event: types.Message | types.CallbackQuery, exc: Exception, handler: str) -> None:
    user = getattr(event, "from_user", None)
    user_id = user.id if user else None
    username = user.username if user else None
    logger.error("bot.handler_error", handler=handler, user_id=user_id, error=str(exc))

    alert = "💫 Звезды перестраиваются. Попробуйте через минуту."
    try:
        if isinstance(event, types.CallbackQuery):
            await event.answer(alert, show_alert=True)
            if user_id:
                await bot.send_message(user_id, alert)
        else:
            await event.answer(alert)
    except Exception:
        logger.warning("bot.user_notify_failed", handler=handler, user_id=user_id)

    admin_text = (
        "⚠️ Ошибка бота\n"
        f"Хэндлер: {handler}\n"
        f"Пользователь: {user_id or '—'} @{username or '—'}\n"
        f"Ошибка: {str(exc)[:500]}"
    )
    await notify_admins(admin_text)


def guard(handler_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            try:
                return await func(event, *args, **kwargs)
            except Exception as exc:
                await handle_handler_error(event, exc, handler_name)
                return None
        return wrapper
    return decorator


async def download_voice(message: types.Message) -> Path:
    file = await bot.get_file(message.voice.file_id)
    local_dir = Path(BOT_MEDIA_DIR)
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / f"voice_{message.message_id}.ogg"
    await bot.download_file(file.file_path, destination=local_path)
    return local_path


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
    
    # 4. Reward New User (+14 days from NOW)
    # Note: User was created with 14 days trial initially in get_or_create_user
    # So we ensure it's set correctly.
    new_user_obj.subscription_active_until = now + timedelta(days=14)
    
    # 5. Reward Referrer
    if referrer.is_partner:
        # Partners get money/percent later (CPA). Nothing now.
        referral.status = "pending"
    else:
        # Regular user gets +14 days
        referral.status = "rewarded"
        
        current_sub = referrer.subscription_active_until
        # Ensure timezone awareness
        if current_sub and current_sub.tzinfo is None:
             current_sub = current_sub.replace(tzinfo=timezone.utc)

        if current_sub and current_sub > now:
            referrer.subscription_active_until = current_sub + timedelta(days=14)
        else:
            referrer.subscription_active_until = now + timedelta(days=14)
            
        # Notify referrer
        try:
            await bot.send_message(
                referrer.telegram_id, 
                f"🎉 <b>У вас новый реферал!</b>\n"
                f"{new_user_obj.full_name} присоединился.\n"
                f"Вам начислено +14 дней доступа! 🎁"
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
        
        # Default trial: 14 days (MVP Standard)
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)
        
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
            clean_arg = referral_arg
            
            # Strip "ref_" prefix if present
            if clean_arg.startswith("ref_"):
                clean_arg = clean_arg[4:]
            
            # 1. Try code format (u_XXXXXX)
            if clean_arg.startswith("u_"):
                ref_res = await session.execute(select(User).where(User.referral_code == clean_arg))
                referrer = ref_res.scalars().first()
                if referrer:
                    referrer_id_to_find = referrer.telegram_id
            
            # 2. Try legacy ID format (if it looks like an int)
            elif clean_arg.isdigit():
                try:
                    referrer_id_to_find = int(clean_arg)
                except ValueError:
                    pass

            if referrer_id_to_find:
                await process_async_referral(session, referrer_id_to_find, new_user)

        await session.commit()
        return new_user
# #END_BLOCK_BOT_DB_LOGIC


# #START_BLOCK_BOT_TASKS
async def create_agent_task(
    telegram_id: int,
    source: str,
    transcript: str,
    voice_file_id: str | None = None,
):
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_res.scalars().first()
        summary = summarize_text(transcript)
        task = AgentTask(
            user_id=user.id if user else None,
            telegram_id=telegram_id,
            source=source,
            status="pending_confirmation",
            transcript=transcript,
            summary=summary,
            voice_file_id=voice_file_id,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def find_task_needing_clarification(telegram_id: int):
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(AgentTask)
            .where(
                AgentTask.telegram_id == telegram_id,
                AgentTask.status == "needs_clarification",
            )
            .order_by(AgentTask.created_at.desc())
            .limit(1)
        )
        return res.scalars().first()


async def update_task_status(
    task_id: uuid.UUID,
    *,
    status: str | None = None,
    clarification: str | None = None,
):
    async with AsyncSessionLocal() as session:
        task = await session.get(AgentTask, task_id)
        if not task:
            return None
        if status:
            task.status = status
            if status == "approved" and not task.approved_at:
                task.approved_at = datetime.now(timezone.utc)
            if status in {"completed", "failed"} and not task.completed_at:
                task.completed_at = datetime.now(timezone.utc)
        if clarification is not None:
            task.clarification = clarification
        await session.commit()
        await session.refresh(task)
        return task
# #END_BLOCK_BOT_TASKS


# #START_BLOCK_BOT_HANDLERS
@dp.message(CommandStart())
@guard("command_start")
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


@dp.message(F.voice)
@guard("voice_task")
async def voice_task_handler(message: types.Message):
    if not is_admin_user(message.from_user.id):
        await message.answer("Доступ ограничен.")
        return

    await message.answer("Принял голос. Распознаю...")
    local_path = None
    try:
        local_path = await download_voice(message)
        transcript = await asyncio.to_thread(transcribe_audio, str(local_path))
    except Exception as exc:
        logger.error("bot.voice.stt_failed", error=str(exc))
        await notify_admins(f"⚠️ Ошибка STT\nПользователь: {message.from_user.id}\nОшибка: {str(exc)[:500]}")
        await message.answer("Не смог распознать голос. Попробуй еще раз.")
        return
    finally:
        if local_path:
            try:
                local_path.unlink()
            except OSError:
                pass

    transcript = normalize_text(transcript)
    if not transcript:
        await message.answer("Текст не распознан. Попробуй еще раз.")
        return

    task = await create_agent_task(
        telegram_id=message.from_user.id,
        source="voice",
        transcript=transcript,
        voice_file_id=message.voice.file_id,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтверждаю",
                    callback_data=f"task_confirm:{task.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✍️ Уточнить",
                    callback_data=f"task_clarify:{task.id}",
                )
            ],
        ]
    )
    await message.answer(
        f"<b>Распознал задачу:</b>\n{task.summary}\n\nПодтвердить?",
        reply_markup=kb,
    )


@dp.message(F.text)
@guard("text_task")
async def text_task_handler(message: types.Message):
    if message.text.startswith("/"):
        return
    if not is_admin_user(message.from_user.id):
        await message.answer("Доступ ограничен.")
        return

    pending = await find_task_needing_clarification(message.from_user.id)
    if pending:
        updated = await update_task_status(
            pending.id,
            status="approved",
            clarification=normalize_text(message.text),
        )
        if updated:
            await message.answer("Принял уточнение. Задача подтверждена.")
        return

    transcript = normalize_text(message.text)
    if not transcript:
        await message.answer("Не вижу текста задачи.")
        return

    task = await create_agent_task(
        telegram_id=message.from_user.id,
        source="text",
        transcript=transcript,
        voice_file_id=None,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтверждаю",
                    callback_data=f"task_confirm:{task.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✍️ Уточнить",
                    callback_data=f"task_clarify:{task.id}",
                )
            ],
        ]
    )
    await message.answer(
        f"<b>Зафиксировал задачу:</b>\n{task.summary}\n\nПодтвердить?",
        reply_markup=kb,
    )


@dp.callback_query(F.data.startswith("task_confirm:"))
@guard("task_confirm")
async def task_confirm_handler(callback: types.CallbackQuery):
    task_id_raw = callback.data.split(":", 1)[-1]
    try:
        task_id = uuid.UUID(task_id_raw)
    except ValueError:
        await callback.answer("Некорректный id", show_alert=True)
        return

    task = await update_task_status(task_id, status="approved")
    await callback.answer()
    if not task:
        await bot.send_message(callback.from_user.id, "Задача не найдена.")
        return

    await bot.send_message(
        callback.from_user.id,
        "Задача подтверждена. Запускаю выполнение.",
    )


@dp.callback_query(F.data.startswith("task_clarify:"))
@guard("task_clarify")
async def task_clarify_handler(callback: types.CallbackQuery):
    task_id_raw = callback.data.split(":", 1)[-1]
    try:
        task_id = uuid.UUID(task_id_raw)
    except ValueError:
        await callback.answer("Некорректный id", show_alert=True)
        return

    task = await update_task_status(task_id, status="needs_clarification")
    await callback.answer()
    if not task:
        await bot.send_message(callback.from_user.id, "Задача не найдена.")
        return

    await bot.send_message(
        callback.from_user.id,
        "Что уточнить? Напиши детали следующим сообщением.",
    )
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
