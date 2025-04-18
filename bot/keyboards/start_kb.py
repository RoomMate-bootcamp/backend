from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔑 Авторизация", callback_data="auth_login"),
                InlineKeyboardButton(text="📝 Регистрация", callback_data="auth_register")
            ],
        ]
    )
    return keyboard

def get_auth_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔑 Авторизация", callback_data="auth_login"),
                InlineKeyboardButton(text="📝 Регистрация", callback_data="auth_register")
            ],
        ]
    )
    return keyboard