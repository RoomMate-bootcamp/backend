from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    edit_name = State()
    edit_age = State()
    edit_gender = State()
    edit_occupation = State()
    edit_bio = State()
    edit_interests = State()
    edit_cleanliness = State()
    edit_sleep = State()
    edit_budget = State()
    edit_location = State()
    edit_smoking = State()
    edit_pets = State()

    edit_study_location = State()
    edit_study_program = State()
    edit_accommodation = State()
    edit_telegram_username = State()