# bot/handlers/search.py
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_, not_, or_

from bot.keyboards.search_kb import get_roommate_keyboard, get_compatibility_keyboard
from src.core.database import User, postgres_helper, Like, Match
from src.core.database.alchemy_models.like import LikeStatus
from src.api_v1.like.crud import create_like
from src.core.utils.AIMatchingService import ai_matching_service

router = Router()


async def start_search(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await message.answer("Пожалуйста, используйте /start для начала работы с ботом.")
        return

    # Get potential roommates
    async with postgres_helper.session_factory() as session:
        # Get current user
        current_user = await session.get(User, user_id)

        # First, get all matches to exclude
        query = select(Match).where(
            or_(
                Match.user1_id == user_id,
                Match.user2_id == user_id
            )
        )
        result = await session.execute(query)
        matches = result.scalars().all()

        matched_ids = []
        for match in matches:
            if match.user1_id == user_id:
                matched_ids.append(match.user2_id)
            else:
                matched_ids.append(match.user1_id)

        # Get all likes already sent
        query = select(Like).where(
            Like.liker_id == user_id
        )
        result = await session.execute(query)
        likes_sent = result.scalars().all()

        liked_ids = [like.liked_id for like in likes_sent]

        # Get all users except current user and those already matched or liked
        exclude_ids = matched_ids + liked_ids + [user_id]
        query = select(User).where(
            and_(
                not_(User.id.in_(exclude_ids)),
                User.is_active == True
            )
        )
        result = await session.execute(query)
        roommates = result.scalars().all()

        roommates_data = []
        for roommate in roommates:
            roommates_data.append({
                "id": roommate.id,
                "name": roommate.name,
                "age": roommate.age,
                "gender": roommate.gender,
                "occupation": roommate.occupation,
                "bio": roommate.bio,
                "interests": roommate.interests or [],  # Ensure interests is a list
                "cleanliness_level": roommate.cleanliness_level,
                "sleep_habits": roommate.sleep_habits,
                "rent_budget": roommate.rent_budget,
                "location": roommate.location,
                "smoking_preference": roommate.smoking_preference,
                "pet_preference": roommate.pet_preference
            })

    if not roommates_data:
        await message.answer("🔍 На данный момент нет подходящих соседей. Попробуйте позже.")
        return

    await state.update_data(roommates=roommates_data, current_index=0)
    await show_roommate(message, state)


async def show_roommate(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    roommates = user_data.get("roommates", [])
    current_index = user_data.get("current_index", 0)

    if not roommates or current_index >= len(roommates):
        await message.answer("🔍 Вы просмотрели всех потенциальных соседей. Попробуйте позже.")
        return

    roommate = roommates[current_index]

    # Ensure interests is an iterable list
    interests = roommate.get('interests', [])
    if not interests or not isinstance(interests, (list, tuple)):
        interests = ['Не указано']

    # Check if other fields are None and provide default values
    name = roommate.get('name') or 'Не указано'
    age = roommate.get('age') or 'Не указано'
    gender = roommate.get('gender') or 'Не указано'
    occupation = roommate.get('occupation') or 'Не указано'
    cleanliness = roommate.get('cleanliness_level') or 'Не указано'
    sleep_habits = roommate.get('sleep_habits') or 'Не указано'
    rent_budget = roommate.get('rent_budget') or 'Не указано'
    location = roommate.get('location') or 'Не указано'
    smoking = roommate.get('smoking_preference') or 'Не указано'
    pets = roommate.get('pet_preference') or 'Не указано'
    bio = roommate.get('bio') or 'Не указано'

    profile_text = (
        f"👤 *Потенциальный сосед*\n\n"
        f"*Имя:* {name}\n"
        f"*Возраст:* {age}\n"
        f"*Пол:* {gender}\n"
        f"*Профессия:* {occupation}\n"
        f"*Уровень чистоплотности:* {cleanliness}/5\n"
        f"*Режим сна:* {sleep_habits}\n"
        f"*Бюджет на аренду:* {rent_budget} ₽\n"
        f"*Район поиска:* {location}\n"
        f"*Отношение к курению:* {smoking}\n"
        f"*Отношение к животным:* {pets}\n\n"
        f"*О себе:*\n{bio}\n\n"
        f"*Интересы:*\n{', '.join(interests)}"
    )

    await message.answer(profile_text, reply_markup=get_roommate_keyboard(roommate.get('id')))


async def check_compatibility(callback: types.CallbackQuery, state: FSMContext):
    roommate_id = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    async with postgres_helper.session_factory() as session:
        current_user = await session.get(User, user_id)
        roommate = await session.get(User, roommate_id)

        if not current_user or not roommate:
            await callback.message.answer("Не удалось получить данные пользователей.")
            await callback.answer()
            return

        # Use AI service to calculate compatibility
        score, explanation = ai_matching_service.calculate_compatibility_score(current_user, roommate)

        compatibility_text = (
            f"📊 *Результат анализа совместимости*\n\n"
            f"*Ваша совместимость с {roommate.name}:* {score:.1f}%\n\n"
            f"*Анализ:*\n{explanation}"
        )

        await callback.message.answer(compatibility_text, reply_markup=get_compatibility_keyboard(roommate_id))

    await callback.answer()


async def roommate_action(callback: types.CallbackQuery, state: FSMContext):
    action, roommate_id = callback.data.split("_")[1:]
    roommate_id = int(roommate_id)
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if action == "like":
        # Like roommate
        async with postgres_helper.session_factory() as session:
            like, is_match, notification = await create_like(
                session=session,
                liker_id=user_id,
                liked_id=roommate_id
            )

            if is_match:
                await callback.message.answer(
                    "✅ Совпадение! Вы можете начать общение с этим пользователем."
                )
            else:
                await callback.message.answer(
                    "👍 Вы проявили интерес к этому пользователю."
                )

    # Move to next roommate
    current_index = user_data.get("current_index", 0)
    await state.update_data(current_index=current_index + 1)
    await show_roommate(callback.message, state)
    await callback.answer()


async def back_to_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    roommate_id = int(callback.data.split("_")[3])
    await callback.answer()

    # Show roommate profile again
    user_data = await state.get_data()
    roommates = user_data.get("roommates", [])
    current_index = user_data.get("current_index", 0)

    if not roommates or current_index >= len(roommates):
        await callback.message.answer("Не удалось отобразить профиль. Попробуйте /search.")
        return

    roommate = roommates[current_index]

    # Ensure interests is an iterable list
    interests = roommate.get('interests', [])
    if not interests or not isinstance(interests, (list, tuple)):
        interests = ['Не указано']

    # Check if other fields are None and provide default values
    name = roommate.get('name') or 'Не указано'
    age = roommate.get('age') or 'Не указано'
    gender = roommate.get('gender') or 'Не указано'
    occupation = roommate.get('occupation') or 'Не указано'
    cleanliness = roommate.get('cleanliness_level') or 'Не указано'
    sleep_habits = roommate.get('sleep_habits') or 'Не указано'
    rent_budget = roommate.get('rent_budget') or 'Не указано'
    location = roommate.get('location') or 'Не указано'
    smoking = roommate.get('smoking_preference') or 'Не указано'
    pets = roommate.get('pet_preference') or 'Не указано'
    bio = roommate.get('bio') or 'Не указано'

    profile_text = (
        f"👤 *Потенциальный сосед*\n\n"
        f"*Имя:* {name}\n"
        f"*Возраст:* {age}\n"
        f"*Пол:* {gender}\n"
        f"*Профессия:* {occupation}\n"
        f"*Уровень чистоплотности:* {cleanliness}/5\n"
        f"*Режим сна:* {sleep_habits}\n"
        f"*Бюджет на аренду:* {rent_budget} ₽\n"
        f"*Район поиска:* {location}\n"
        f"*Отношение к курению:* {smoking}\n"
        f"*Отношение к животным:* {pets}\n\n"
        f"*О себе:*\n{bio}\n\n"
        f"*Интересы:*\n{', '.join(interests)}"
    )

    await callback.message.answer(profile_text, reply_markup=get_roommate_keyboard(roommate.get('id')))


def register_search_handlers(dp):
    dp.include_router(router)

    router.message.register(start_search, Command("search"))
    router.callback_query.register(roommate_action, F.data.startswith("roommate_"))
    router.callback_query.register(check_compatibility, F.data.startswith("compatibility_"))
    router.callback_query.register(back_to_profile_callback, F.data.startswith("back_to_profile_"))