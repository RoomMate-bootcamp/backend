from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_matches_keyboard(matches) -> InlineKeyboardMarkup:
    keyboard = []

    for match in matches:
        roommate = match.get("roommate", {})
        name = roommate.get("name", "Неизвестно")
        keyboard.append([
            InlineKeyboardButton(text=f"👤 {name}", callback_data=f"match_{match.get('id')}")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_match_actions_keyboard(match_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Связаться", callback_data=f"contact_{match_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Удалить совпадение", callback_data=f"delete_match_{match_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад к совпадениям", callback_data="back_to_matches")
            ]
        ]
    )
    return keyboard


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Мой профиль", callback_data="show_profile")
            ],
            [
                InlineKeyboardButton(text="🔍 Поиск соседей", callback_data="start_search")
            ],
            [
                InlineKeyboardButton(text="🔄 Мои совпадения", callback_data="show_matches")
            ],
            [
                InlineKeyboardButton(text="🤖 ИИ-помощник", callback_data="start_ai_chat")
            ]
        ]
    )
    return keyboard