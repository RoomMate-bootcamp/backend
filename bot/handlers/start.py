# bot/handlers/start.py
import uuid
import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, text, or_
from sqlalchemy.exc import IntegrityError

from bot.states.profile_states import ProfileStates
from bot.keyboards.profile_kb import get_profile_keyboard
from src.api_v1.auth.crud import get_password_hash
from src.core.database import User, postgres_helper

router = Router()
logger = logging.getLogger(__name__)


async def start_command(message: types.Message, state: FSMContext):
    # Get user from database or create one
    async with postgres_helper.session_factory() as session:
        # Check if user already exists based on telegram_id or username
        tg_id = str(message.from_user.id)
        potential_username = f"tg_{message.from_user.id}"

        # First try to find by username which is faster and more reliable
        query = select(User).where(User.username == potential_username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            # Then try to find by telegram_id in metadata using raw SQL for reliable JSON querying
            query = text("SELECT * FROM users WHERE user_metadata->>'telegram_id' = :tg_id")
            result = await session.execute(query, {"tg_id": tg_id})
            user_row = result.fetchone()

            if user_row:
                # Found user by telegram_id, get the full user object
                user = await session.get(User, user_row[0])

        if not user:
            try:
                # Generate username and random password
                username = potential_username
                email = f"{username}@telegram.user"
                password = str(uuid.uuid4())
                hashed_password = get_password_hash(password)

                # Create new user
                new_user = User(
                    username=username,
                    email=email,
                    hashed_password=hashed_password,
                    name=message.from_user.first_name,
                    is_active=True,
                    # Store telegram_id in user_metadata field
                    user_metadata={"telegram_id": tg_id}
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                user = new_user

                logger.info(f"Created new user {username} for Telegram ID {tg_id}")

            except IntegrityError as e:
                # User might have been created in a race condition, try to find them again
                await session.rollback()
                logger.warning(f"IntegrityError when creating user: {e}")

                # Try to find the user one more time
                query = select(User).where(
                    or_(
                        User.username == potential_username,
                        User.email == f"{potential_username}@telegram.user"
                    )
                )
                result = await session.execute(query)
                user = result.scalar_one_or_none()

                if not user:
                    # Still not found, generate a unique username with timestamp
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
                    logger.info(f"Created new user with timestamp {username} after handling IntegrityError")

        # Store user ID in state
        await state.update_data(user_id=user.id)

        # Check if user is a new user (profile not filled) or returning user
        is_new_user = not any([
            user.age, user.gender, user.occupation, user.bio,
            user.cleanliness_level, user.sleep_habits, user.rent_budget
        ])

        if is_new_user:
            await message.answer(
                f"👋 Привет, {user.name or message.from_user.first_name}!\n\n"
                "Давайте заполним ваш профиль, чтобы найти идеальных соседей для совместной аренды."
            )

            # Start profile setup
            await message.answer(
                "Для начала, укажите ваш возраст (число):",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await state.set_state(ProfileStates.edit_age)
        else:
            await message.answer(
                f"👋 С возвращением, {user.name or message.from_user.first_name}!"
            )

            # Show profile or main menu
            from bot.handlers.profile import show_profile
            await show_profile(message, state)


def register_start_handlers(dp):
    dp.include_router(router)
    router.message.register(start_command, Command("start"))