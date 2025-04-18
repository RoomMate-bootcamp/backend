from aiogram import Dispatcher

from bot.middlewares.auth import AuthMiddleware

def setup_middlewares(dp: Dispatcher):
    dp.update.middleware(AuthMiddleware())
