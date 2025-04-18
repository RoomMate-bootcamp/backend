from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.fsm.context import FSMContext


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        # Get FSM context from data
        fsm_context: FSMContext = data.get("state")

        if fsm_context:
            # Get user data from FSM storage
            user_data = await fsm_context.get_data()

            # Add token to data if available
            if "token" in user_data:
                data["token"] = user_data["token"]

        # Continue processing
        return await handler(event, data)