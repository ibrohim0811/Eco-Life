from aiogram.fsm.state import State, StatesGroup

class Payment(StatesGroup):
    version = State()
    payment_method = State()
    cheque = State()