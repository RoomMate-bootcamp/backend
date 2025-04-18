from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot.handlers.profile import show_profile
from bot.handlers.search import start_search
from bot.handlers.matches import show_matches
from bot.handlers.ai_chat import start_ai_chat
from bot.keyboards.main_kb import get_main_menu_keyboard

router = Router()


async def show_main_menu(message: types.Message):
    await message.answer(
        "Главное меню. Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


async def return_to_menu_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Главное меню. Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


async def show_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_profile(callback.message, state)


async def start_search_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await start_search(callback.message, state)


async def show_matches_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_matches(callback.message, state)


async def start_ai_chat_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await start_ai_chat(callback.message, state)


def register_menu_handlers(dp):
    dp.include_router(router)

    router.callback_query.register(return_to_menu_callback, F.data == "return_to_menu")
    router.callback_query.register(show_profile_callback, F.data == "show_profile")
    router.callback_query.register(start_search_callback, F.data == "start_search")
    router.callback_query.register(show_matches_callback, F.data == "show_matches")
    router.callback_query.register(start_ai_chat_callback, F.data == "start_ai_chat")