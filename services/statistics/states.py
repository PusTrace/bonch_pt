from aiogram.fsm.state import StatesGroup, State

class ReminderStates(StatesGroup):
    waiting_for_teacher = State()
