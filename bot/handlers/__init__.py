from aiogram import Dispatcher

from bot.handlers.start import register_start_handlers
from bot.handlers.profile import register_profile_handlers
from bot.handlers.search import register_search_handlers
from bot.handlers.matches import register_matches_handlers
from bot.handlers.ai_chat import register_ai_chat_handlers
from bot.handlers.menu import register_menu_handlers
from bot.handlers.notifications import register_notifications_handlers


def register_all_handlers(dp: Dispatcher):
    handlers = [
        register_start_handlers,
        register_profile_handlers,
        register_search_handlers,
        register_matches_handlers,
        register_ai_chat_handlers,
        register_menu_handlers,
        register_notifications_handlers,
    ]

    for handler in handlers:
        handler(dp)
