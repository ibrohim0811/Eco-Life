from aiogram.fsm.state import State, StatesGroup


class Register(StatesGroup):
    set_lang = State()
    first_name = State()
    last_name = State()
    phone = State()
    username = State()
    password = State()
    
    