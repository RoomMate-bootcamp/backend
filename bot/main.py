import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

from bot.handlers import register_all_handlers
from bot.middlewares import setup_middlewares
from bot.config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
from bot.services.database import init_db
from bot.handlers.notifications import check_notifications
from src.core.database import postgres_helper
from sqlalchemy import select, text
from src.core.database import User


async def periodic_notification_check(bot: Bot):
    """Periodically check for new notifications for all users"""
    while True:
        try:
            logging.info("Running periodic notification check")

            async with postgres_helper.session_factory() as session:
                query = text(
                    "SELECT id FROM users WHERE user_metadata->>'telegram_id' IS NOT NULL"
                )
                result = await session.execute(query)
                users = result.fetchall()

                for user_row in users:
                    user_id = user_row[0]
                    await check_notifications(user_id, bot)

            await asyncio.sleep(60)
        except Exception as e:
            logging.error(f"Error in periodic notification check: {e}")
            await asyncio.sleep(60)


async def start_bot():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.CHAT)

    setup_middlewares(dp)

    register_all_handlers(dp)

    await init_db()

    asyncio.create_task(periodic_notification_check(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(start_bot())
