from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from src.core.database import User, postgres_helper
from src.core.utils.AIMatchingService import ai_matching_service
from bot.states.ai_chat_states import AIChatState
from yandex_cloud_ml_sdk import YCloudML
from bot.config import YANDEX_FOLDER_ID, YANDEX_API_KEY

router = Router()

# Initialize YandexGPT
sdk = YCloudML(
    folder_id=YANDEX_FOLDER_ID,
    auth=YANDEX_API_KEY
)
model = sdk.models.completions('yandexgpt-lite')
model.configure(
    temperature=0.5,
    max_tokens=2000,
)


async def start_ai_chat(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await message.answer("Пожалуйста, используйте /start для начала работы с ботом.")
        return

    await message.answer(
        "🤖 Привет! Я ИИ-помощник по бытовым вопросам. "
        "Могу помочь с организацией пространства, уборкой, готовкой, "
        "решением бытовых конфликтов и многим другим. Просто спросите меня о чем угодно!"
    )

    await state.set_state(AIChatState.chatting)


async def process_ai_query(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "AIChatState:chatting":
        return

    user_data = await state.get_data()
    user_id = user_data.get("user_id")

    if not user_id:
        await message.answer("Пожалуйста, используйте /start для начала работы с ботом.")
        return

    # Get user profile for context
    async with postgres_helper.session_factory() as session:
        user = await session.get(User, user_id)
        if not user:
            await message.answer("Ошибка при получении данных пользователя.")
            return

        # Create profile context
        user_profile = {
            "name": user.name,
            "age": user.age,
            "gender": user.gender,
            "cleanliness_level": user.cleanliness_level,
            "sleep_habits": user.sleep_habits,
            "smoking_preference": user.smoking_preference,
            "pet_preference": user.pet_preference,
            "interests": user.interests or []
        }

    query = message.text

    # Show typing indicator
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Get AI response
    response = await get_ai_response(query, user_profile)

    await message.answer(response)


async def get_ai_response(query: str, user_profile):
    system_prompt = """
    Ты - полезный ассистент по бытовым вопросам для соседей по квартире.
    Ты помогаешь с решением бытовых проблем, организацией пространства, уборкой, 
    готовкой, разрешением конфликтов между соседями по квартире и другими домашними вопросами.
    Всегда давай конкретные и практичные советы с учетом информации о пользователе.
    """

    user_context = ""
    if user_profile:
        user_context = f"""
        Вот информация о пользователе:
        - Имя: {user_profile.get('name', 'Неизвестно')}
        - Возраст: {user_profile.get('age', 'Неизвестно')}
        - Пол: {user_profile.get('gender', 'Неизвестно')}
        - Чистоплотность (1-5): {user_profile.get('cleanliness_level', 'Неизвестно')}
        - Режим сна: {user_profile.get('sleep_habits', 'Неизвестно')}
        - Отношение к курению: {user_profile.get('smoking_preference', 'Неизвестно')}
        - Отношение к животным: {user_profile.get('pet_preference', 'Неизвестно')}
        - Интересы: {', '.join(user_profile.get('interests', ['Неизвестно']))}

        Используй эту информацию, чтобы дать персонализированный совет.
        """

    user_prompt = f"{user_context}\n\nВопрос: {query}"

    messages = [
        {'role': 'system', 'text': system_prompt},
        {'role': 'user', 'text': user_prompt},
    ]

    try:
        operation = model.run_deferred(messages)
        result = operation.wait()
        return result.text
    except Exception as e:
        return f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}"


def register_ai_chat_handlers(dp):
    dp.include_router(router)

    router.message.register(start_ai_chat, Command("ai_chat"))
    router.message.register(process_ai_query, AIChatState.chatting)
