from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_

from bot.keyboards.matches_kb import get_matches_keyboard, get_match_actions_keyboard
from src.core.database import User, postgres_helper, Match

router = Router()


async def show_matches(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await message.answer("Пожалуйста, используйте /start для начала работы с ботом.")
        return

    async with postgres_helper.session_factory() as session:
        query = select(Match).where(
            or_(
                Match.user1_id == user_id,
                Match.user2_id == user_id
            )
        )
        result = await session.execute(query)
        matches = result.scalars().all()

        matches_data = []
        for match in matches:
            other_id = match.user2_id if match.user1_id == user_id else match.user1_id
            other_user = await session.get(User, other_id)

            if other_user:
                matches_data.append({
                    "id": match.id,
                    "timestamp": match.timestamp,
                    "roommate": {
                        "id": other_user.id,
                        "name": other_user.name,
                        "username": other_user.username
                    }
                })

    if not matches_data:
        await message.answer("У вас пока нет совпадений. Используйте /search, чтобы найти потенциальных соседей.")
        return

    await message.answer("🔄 Ваши совпадения:", reply_markup=get_matches_keyboard(matches_data))


async def show_match_details(callback: types.CallbackQuery, state: FSMContext):
    match_id = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    async with postgres_helper.session_factory() as session:
        match = await session.get(Match, match_id)

        if not match:
            await callback.message.answer("Совпадение не найдено.")
            await callback.answer()
            return

        other_id = match.user2_id if match.user1_id == user_id else match.user1_id
        roommate = await session.get(User, other_id)

        if not roommate:
            await callback.message.answer("Пользователь не найден.")
            await callback.answer()
            return

        profile_text = (
            f"👥 *Ваше совпадение*\n\n"
            f"*Имя:* {roommate.name or 'Не указано'}\n"
            f"*Возраст:* {roommate.age or 'Не указано'}\n"
            f"*Пол:* {roommate.gender or 'Не указано'}\n"
            f"*Профессия:* {roommate.occupation or 'Не указано'}\n"
            f"*Уровень чистоплотности:* {roommate.cleanliness_level or 'Не указано'}/5\n"
            f"*Режим сна:* {roommate.sleep_habits or 'Не указано'}\n"
            f"*Бюджет на аренду:* {roommate.rent_budget or 'Не указано'} ₽\n"
            f"*Район поиска:* {roommate.location or 'Не указано'}\n"
            f"*О себе:*\n{roommate.bio or 'Не указано'}\n\n"
            f"*Интересы:*\n{', '.join(roommate.interests or ['Не указано'])}"
        )

        await callback.message.answer(profile_text, reply_markup=get_match_actions_keyboard(match_id))

    await callback.answer()


async def delete_match(callback: types.CallbackQuery, state: FSMContext):
    match_id = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    async with postgres_helper.session_factory() as session:
        match = await session.get(Match, match_id)

        if not match:
            await callback.message.answer("Совпадение не найдено.")
            await callback.answer()
            return

        if match.user1_id != user_id and match.user2_id != user_id:
            await callback.message.answer("У вас нет прав для удаления этого совпадения.")
            await callback.answer()
            return

        await session.delete(match)
        await session.commit()

        await callback.message.answer("✅ Совпадение удалено.")
        await show_matches(callback.message, state)

    await callback.answer()


def register_matches_handlers(dp):
    dp.include_router(router)

    router.message.register(show_matches, Command("matches"))
    router.callback_query.register(show_match_details, F.data.startswith("match_"))
    router.callback_query.register(delete_match, F.data.startswith("delete_match_"))
    router.callback_query.register(back_to_matches_callback, F.data == "back_to_matches")


async def back_to_matches_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_matches(callback.message, state)
