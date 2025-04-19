from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="show_profile")],
            [
                InlineKeyboardButton(
                    text="🔍 Поиск соседей", callback_data="start_search"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Мои совпадения", callback_data="show_matches"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 ИИ-помощник", callback_data="start_ai_chat"
                )
            ],
        ]
    )
    return keyboard
