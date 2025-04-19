from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    browsing = State()
    compatibility_check = State()
