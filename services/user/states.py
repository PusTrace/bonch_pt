from aiogram.fsm.state import StatesGroup, State

class ReminderStates(StatesGroup):
    waiting_for_sect = State()
    waiting_for_brigade = State()
