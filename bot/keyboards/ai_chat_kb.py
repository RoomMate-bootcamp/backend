from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_ai_chat_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Завершить диалог с ИИ", callback_data="exit_ai_chat"
                )
            ]
        ]
    )
    return keyboard
