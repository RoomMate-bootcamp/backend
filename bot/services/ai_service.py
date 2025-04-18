import json
from typing import Dict, Any, Optional

from yandex_cloud_ml_sdk import YCloudML

from bot.config import YANDEX_FOLDER_ID, YANDEX_API_KEY

sdk = YCloudML(
    folder_id=YANDEX_FOLDER_ID,
    auth=YANDEX_API_KEY
)
model = sdk.models.completions('yandexgpt-lite')
model.configure(
    temperature=0.5,
    max_tokens=2000,
)


async def get_ai_response(query: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
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
