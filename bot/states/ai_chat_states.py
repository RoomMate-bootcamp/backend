from aiogram.fsm.state import State, StatesGroup

class AIChatState(StatesGroup):
    chatting = State()