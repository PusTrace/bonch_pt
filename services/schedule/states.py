from aiogram.fsm.state import StatesGroup, State

class ReminderStates(StatesGroup):
    waiting_for_teacher = State()
    waiting_for_task = State()
    waiting_for_subject = State()
