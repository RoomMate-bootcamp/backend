import uuid
import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, text, or_
from sqlalchemy.exc import IntegrityError

from bot.handlers.notifications import check_notifications
from bot.states.profile_states import ProfileStates
from bot.keyboards.profile_kb import get_profile_keyboard
from src.api_v1.auth.crud import get_password_hash
from src.core.database import User, postgres_helper

router = Router()
logger = logging.getLogger(__name__)


async def start_command(message: types.Message, state: FSMContext):
    logger.info(f"Starting command for user {message.from_user.id}")

    async with postgres_helper.session_factory() as session:
        tg_id = str(message.from_user.id)

        username = f"tg_{message.from_user.id}"
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            query = text("SELECT * FROM users WHERE user_metadata->>'telegram_id' = :tg_id")
            result = await session.execute(query, {"tg_id": tg_id})
            user_row = result.fetchone()

            if user_row:
                user = await session.get(User, user_row[0])

        user_is_new = False
        if not user:
            user_is_new = True
            try:
                username = f"tg_{message.from_user.id}"
                email = f"{username}@telegram.user"
                password = str(uuid.uuid4())
                hashed_password = get_password_hash(password)

                new_user = User(
                    username=username,
                    email=email,
                    hashed_password=hashed_password,
                    name=message.from_user.first_name,
                    is_active=True,
                    user_metadata={"telegram_id": tg_id}
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                user = new_user

                logger.info(f"Created new user {username} for Telegram ID {tg_id}")

            except IntegrityError as e:
                await session.rollback()
                logger.warning(f"IntegrityError when creating user: {e}")

                query = select(User).where(
                    or_(
                        User.username == username,
                        User.email == f"{username}@telegram.user"
                    )
                )
                result = await session.execute(query)
                user = result.scalar_one_or_none()

                if not user:
                    import time
                    timestamp = int(time.time())
                    username = f"tg_{message.from_user.id}_{timestamp}"
                    email = f"{username}@telegram.user"
                    password = str(uuid.uuid4())
                    hashed_password = get_password_hash(password)

                    new_user = User(
                        username=username,
                        email=email,
                        hashed_password=hashed_password,
                        name=message.from_user.first_name,
                        is_active=True,
                        user_metadata={"telegram_id": tg_id}
                    )

                    session.add(new_user)
                    await session.commit()
                    await session.refresh(new_user)
                    user = new_user
                    user_is_new = True
                    logger.info(f"Created new user with timestamp {username} after handling IntegrityError")

        await state.update_data(user_id=user.id, is_onboarding=user_is_new)

        is_profile_incomplete = (
                user.age is None or
                user.gender is None or
                user.occupation is None or
                user.cleanliness_level is None or
                user.rent_budget is None
        )

        logger.info(f"User {user.id}: is_new={user_is_new}, profile_incomplete={is_profile_incomplete}")

        if user_is_new or is_profile_incomplete:
            await message.answer(
                f"👋 Привет, {user.name or message.from_user.first_name}!\n\n"
                "Давайте заполним ваш профиль, чтобы найти идеальных соседей для совместной аренды."
            )

            if user.age is None:
                await message.answer(
                    "Для начала, укажите ваш возраст (число):",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await state.set_state(ProfileStates.edit_age)
            elif user.gender is None:
                from bot.keyboards.profile_kb import get_gender_keyboard
                await message.answer(
                    "Укажите ваш пол:",
                    reply_markup=get_gender_keyboard()
                )
                await state.set_state(ProfileStates.edit_gender)
            elif user.occupation is None:
                await message.answer(
                    "Укажите вашу профессию:",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await state.set_state(ProfileStates.edit_occupation)
            elif user.cleanliness_level is None:
                await message.answer(
                    "Оцените уровень вашей чистоплотности от 1 до 5:",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await state.set_state(ProfileStates.edit_cleanliness)
            elif user.rent_budget is None:
                await message.answer(
                    "Укажите ваш бюджет на аренду (число в рублях):",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await state.set_state(ProfileStates.edit_budget)
            else:
                await message.answer(
                    "Продолжим заполнение профиля. Расскажите о себе:",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await state.set_state(ProfileStates.edit_bio)

        else:
            await message.answer(
                f"👋 С возвращением, {user.name or message.from_user.first_name}!"
            )

            from bot.keyboards.main_kb import get_main_menu_keyboard
            await message.answer(
                "Что вы хотите сделать?",
                reply_markup=get_main_menu_keyboard()
            )
    await check_notifications(user.id, message.bot)


def register_start_handlers(dp):
    dp.include_router(router)
    router.message.register(start_command, Command("start"))