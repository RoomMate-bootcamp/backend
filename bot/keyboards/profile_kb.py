from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def get_gender_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужской", callback_data="gender_male"),
                InlineKeyboardButton(text="Женский", callback_data="gender_female")
            ],
            [
                InlineKeyboardButton(text="Другой", callback_data="gender_other")
            ]
        ]
    )
    return keyboard


def get_interests_keyboard(selected_interests=[]) -> InlineKeyboardMarkup:
    interests = [
        "Спорт", "Музыка", "Кино", "Литература", "Технологии",
        "Путешествия", "Кулинария", "Игры", "Искусство", "Фотография"
    ]

    keyboard = []

    for i in range(0, len(interests), 2):
        row = []
        for j in range(2):
            if i + j < len(interests):
                interest = interests[i + j]
                prefix = "✅ " if interest in selected_interests else ""
                row.append(InlineKeyboardButton(
                    text=f"{prefix}{interest}",
                    callback_data=f"interest_{interest}"
                ))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="interests_done")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Имя", callback_data="edit_name"),
                InlineKeyboardButton(text="🔢 Возраст", callback_data="edit_age"),
                InlineKeyboardButton(text="👤 Пол", callback_data="edit_gender")
            ],
            [
                InlineKeyboardButton(text="💼 Профессия", callback_data="edit_occupation"),
                InlineKeyboardButton(text="🧹 Чистоплотность", callback_data="edit_cleanliness")
            ],
            [
                InlineKeyboardButton(text="😴 Режим сна", callback_data="edit_sleep"),
                InlineKeyboardButton(text="💰 Бюджет", callback_data="edit_budget")
            ],
            [
                InlineKeyboardButton(text="📍 Район", callback_data="edit_location"),
                InlineKeyboardButton(text="🚬 Курение", callback_data="edit_smoking")
            ],
            [
                InlineKeyboardButton(text="🐱 Животные", callback_data="edit_pets"),
                InlineKeyboardButton(text="👨‍👩‍👧‍👦 Интересы", callback_data="edit_interests")
            ],
            [
                InlineKeyboardButton(text="🏛️ ВУЗ/Город учебы", callback_data="edit_study_location"),
                InlineKeyboardButton(text="📚 Специальность", callback_data="edit_study_program")
            ],
            [
                InlineKeyboardButton(text="🏠 Предпочтения по жилью", callback_data="edit_accommodation"),
                InlineKeyboardButton(text="📱 Ник в Telegram", callback_data="edit_telegram_username")
            ],
            [
                InlineKeyboardButton(text="📝 О себе", callback_data="edit_bio")
            ],
            [
                InlineKeyboardButton(text="🔍 Поиск соседей", callback_data="start_search")
            ],
            [
                InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="return_to_menu")
            ]
        ]
    )
    return keyboard

def get_accommodation_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏢 Квартира", callback_data="accommodation_apartment"),
            ],
            [
                InlineKeyboardButton(text="🏨 Общежитие", callback_data="accommodation_dormitory"),
            ],
            [
                InlineKeyboardButton(text="🔄 Не имеет значения", callback_data="accommodation_no_preference"),
            ]
        ]
    )
    return keyboard