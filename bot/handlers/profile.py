import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states.profile_states import ProfileStates
from bot.keyboards.profile_kb import get_profile_keyboard, get_gender_keyboard, get_interests_keyboard
from bot.keyboards.main_kb import get_main_menu_keyboard
from src.core.database import User, postgres_helper

router = Router()
logger = logging.getLogger(__name__)


async def show_profile(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await message.answer("Пожалуйста, используйте /start для начала работы с ботом.")
        return

    async with postgres_helper.session_factory() as session:
        user = await session.get(User, user_id)

        if not user:
            await message.answer("Произошла ошибка при загрузке профиля. Используйте /start для перезапуска бота.")
            return

        profile_text = (
            f"👤 *Ваш профиль*\n\n"
            f"*Имя:* {user.name or 'Не указано'}\n"
            f"*Возраст:* {user.age or 'Не указано'}\n"
            f"*Пол:* {user.gender or 'Не указано'}\n"
            f"*Профессия:* {user.occupation or 'Не указано'}\n"
            f"*Уровень чистоплотности:* {user.cleanliness_level or 'Не указано'}/5\n"
            f"*Режим сна:* {user.sleep_habits or 'Не указано'}\n"
            f"*Бюджет на аренду:* {user.rent_budget or 'Не указано'} ₽\n"
            f"*Район поиска:* {user.location or 'Не указано'}\n"
            f"*Отношение к курению:* {user.smoking_preference or 'Не указано'}\n"
            f"*Отношение к животным:* {user.pet_preference or 'Не указано'}\n\n"
            f"*О себе:*\n{user.bio or 'Не указано'}\n\n"
            f"*Интересы:*\n{', '.join(user.interests or ['Не указано'])}"
        )

        await message.answer(profile_text, reply_markup=get_profile_keyboard())


async def edit_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]

    field_prompts = {
        "name": "Введите ваше имя:",
        "age": "Введите ваш возраст (число):",
        "gender": "Выберите ваш пол:",
        "occupation": "Укажите вашу профессию:",
        "bio": "Расскажите о себе:",
        "interests": "Выберите ваши интересы:",
        "cleanliness": "Оцените уровень вашей чистоплотности от 1 до 5:",
        "sleep": "Опишите ваш режим сна (например, 'жаворонок', 'сова'):",
        "budget": "Укажите ваш бюджет на аренду (число в рублях):",
        "location": "Укажите предпочтительный район поиска:",
        "smoking": "Укажите ваше отношение к курению:",
        "pets": "Укажите ваше отношение к домашним животным:"
    }

    field_states = {
        "name": ProfileStates.edit_name,
        "age": ProfileStates.edit_age,
        "gender": ProfileStates.edit_gender,
        "occupation": ProfileStates.edit_occupation,
        "bio": ProfileStates.edit_bio,
        "interests": ProfileStates.edit_interests,
        "cleanliness": ProfileStates.edit_cleanliness,
        "sleep": ProfileStates.edit_sleep,
        "budget": ProfileStates.edit_budget,
        "location": ProfileStates.edit_location,
        "smoking": ProfileStates.edit_smoking,
        "pets": ProfileStates.edit_pets
    }

    await state.update_data(edit_field=field)

    if field == "gender":
        await callback.message.answer(field_prompts[field], reply_markup=get_gender_keyboard())
    elif field == "interests":
        # Get current user interests
        user_data = await state.get_data()
        user_id = user_data.get("user_id")

        async with postgres_helper.session_factory() as session:
            user = await session.get(User, user_id)
            current_interests = user.interests or []

        await callback.message.answer(field_prompts[field], reply_markup=get_interests_keyboard(current_interests))
        await state.update_data(selected_interests=current_interests)
    else:
        await callback.message.answer(field_prompts[field])

    await state.set_state(field_states[field])
    await callback.answer()


async def process_profile_edit(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await message.answer("Пожалуйста, используйте /start для начала работы с ботом.")
        return

    current_state = await state.get_state()
    value = message.text

    # Map states directly to DB fields
    field_mapping = {
        "ProfileStates:edit_name": "name",
        "ProfileStates:edit_age": "age",
        "ProfileStates:edit_gender": "gender",
        "ProfileStates:edit_occupation": "occupation",
        "ProfileStates:edit_bio": "bio",
        "ProfileStates:edit_cleanliness": "cleanliness_level",
        "ProfileStates:edit_sleep": "sleep_habits",
        "ProfileStates:edit_budget": "rent_budget",
        "ProfileStates:edit_location": "location",
        "ProfileStates:edit_smoking": "smoking_preference",
        "ProfileStates:edit_pets": "pet_preference"
    }

    # Get field directly from state
    api_field = field_mapping.get(current_state)

    if not api_field:
        logger.error(f"No field mapping for state: {current_state}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")
        return

    # Validate input for certain fields
    if api_field == "age" or api_field == "rent_budget":
        if not value.isdigit():
            await message.answer("Пожалуйста, введите число.")
            return
        value = int(value)

    if api_field == "cleanliness_level":
        if not value.isdigit() or int(value) < 1 or int(value) > 5:
            await message.answer("Пожалуйста, введите число от 1 до 5.")
            return
        value = int(value)

    # Update profile
    async with postgres_helper.session_factory() as session:
        user = await session.get(User, user_id)
        if not user:
            await message.answer("Пользователь не найден. Используйте /start для перезапуска бота.")
            return

        setattr(user, api_field, value)

        try:
            await session.commit()
            logger.info(f"Updated user {user.id} field {api_field} to {value}")

            # Check if this is part of the initial setup
            is_onboarding = user_data.get("edit_field") is None

            if is_onboarding:
                # Move to next profile setup step
                if api_field == "age":
                    await message.answer("Отлично! Теперь укажите ваш пол:", reply_markup=get_gender_keyboard())
                    await state.set_state(ProfileStates.edit_gender)
                    return
                elif api_field == "occupation":
                    await message.answer("Хорошо! Теперь расскажите немного о себе:")
                    await state.set_state(ProfileStates.edit_bio)
                    return
                elif api_field == "bio":
                    await message.answer("Отлично! Теперь оцените уровень вашей чистоплотности от 1 до 5:")
                    await state.set_state(ProfileStates.edit_cleanliness)
                    return
                elif api_field == "cleanliness_level":
                    await message.answer("Хорошо! Опишите ваш режим сна (например, 'жаворонок', 'сова'):")
                    await state.set_state(ProfileStates.edit_sleep)
                    return
                elif api_field == "sleep_habits":
                    await message.answer("Укажите ваш бюджет на аренду (число в рублях):")
                    await state.set_state(ProfileStates.edit_budget)
                    return
                elif api_field == "rent_budget":
                    await message.answer("Укажите предпочтительный район поиска:")
                    await state.set_state(ProfileStates.edit_location)
                    return
                elif api_field == "location":
                    await message.answer("Укажите ваше отношение к курению:")
                    await state.set_state(ProfileStates.edit_smoking)
                    return
                elif api_field == "smoking_preference":
                    await message.answer("Укажите ваше отношение к домашним животным:")
                    await state.set_state(ProfileStates.edit_pets)
                    return
                elif api_field == "pet_preference":
                    await message.answer(
                        "✅ Базовый профиль заполнен! Теперь вы можете искать соседей.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    await state.clear()
                    return

            # Regular profile editing
            await message.answer("✅ Информация обновлена!")
            await show_profile(message, state)
            await state.clear()

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            await message.answer("Произошла ошибка при обновлении профиля. Пожалуйста, попробуйте еще раз.")
            await session.rollback()


async def gender_callback(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]

    if gender == "male":
        gender_value = "Мужской"
    elif gender == "female":
        gender_value = "Женский"
    else:
        gender_value = "Другой"

    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    async with postgres_helper.session_factory() as session:
        user = await session.get(User, user_id)
        user.gender = gender_value
        await session.commit()

    # Check if this is part of the initial setup
    is_onboarding = user_data.get("edit_field") is None

    if is_onboarding:
        await callback.message.answer("Отлично! Теперь укажите вашу профессию:")
        await state.set_state(ProfileStates.edit_occupation)
    else:
        await callback.message.answer("✅ Пол успешно обновлен!")
        await show_profile(callback.message, state)
        await state.clear()

    await callback.answer()


async def process_interests_edit(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "interests_done":
        user_data = await state.get_data()
        user_id = user_data.get("user_id")
        interests = user_data.get("selected_interests", [])

        async with postgres_helper.session_factory() as session:
            user = await session.get(User, user_id)
            user.interests = interests
            await session.commit()

        await callback.message.answer("✅ Интересы обновлены!")
        await show_profile(callback.message, state)
        await state.clear()
    else:
        interest = callback.data.replace("interest_", "")
        user_data = await state.get_data()
        interests = user_data.get("selected_interests", [])

        if interest in interests:
            interests.remove(interest)
        else:
            interests.append(interest)

        await state.update_data(selected_interests=interests)

        selected_text = ", ".join(interests) if interests else "Нет выбранных интересов"
        await callback.message.edit_text(
            f"Выберите ваши интересы:\n\nВыбрано: {selected_text}",
            reply_markup=get_interests_keyboard(interests)
        )

    await callback.answer()


def register_profile_handlers(dp):
    dp.include_router(router)

    router.message.register(show_profile, Command("profile"))
    router.callback_query.register(edit_profile_callback, F.data.startswith("edit_"))
    router.callback_query.register(gender_callback, F.data.startswith("gender_"))
    router.callback_query.register(process_interests_edit, F.data.startswith("interest_"))

    # Register handlers for all profile states
    for state in ProfileStates:
        if state not in [ProfileStates.edit_interests, ProfileStates.edit_gender]:
            router.message.register(process_profile_edit, state)
