from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_roommate_keyboard(roommate_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎 Пропустить", callback_data=f"roommate_skip_{roommate_id}"),
                InlineKeyboardButton(text="👍 Нравится", callback_data=f"roommate_like_{roommate_id}")
            ],
            [
                InlineKeyboardButton(text="📊 Проверить совместимость", callback_data=f"compatibility_{roommate_id}")
            ]
        ]
    )
    return keyboard

def get_compatibility_keyboard(roommate_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎 Пропустить", callback_data=f"roommate_skip_{roommate_id}"),
                InlineKeyboardButton(text="👍 Нравится", callback_data=f"roommate_like_{roommate_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад к профилю", callback_data=f"back_to_profile_{roommate_id}")
            ]
        ]
    )
    return keyboard