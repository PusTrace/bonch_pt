from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_report = State()

class QueueStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_subject = State()
    waiting_for_brigade = State()
