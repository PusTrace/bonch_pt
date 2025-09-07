import json
import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

import deadline_packages.keyboards as kb
from deadline_packages.keyboards import clear
from deadline_packages.states import ReminderStates
from deadline_packages.utils import load_reminders, save_reminders

logging.basicConfig(level=logging.INFO)


reminders = load_reminders()

admin_router = Router()
# TODO: сделать чтобы показывалось только мне, переделать вывод
# Вывести всю базу данных 📂
@admin_router.message(F.text.casefold() == 'Вывести всю базу данных 📂'.casefold())
async def settings_interval(message: types.Message):

    user_id = str(message.chat.id)
    if user_id not in reminders:
        reminders[user_id] = {"reminders": []}
        output_database = "у вас ещё нет базы данных"
    else:
        user_data = reminders.get(user_id, {})
        output_database = json.dumps(user_data, ensure_ascii=False, indent=4)

    await message.answer(output_database, reply_markup=kb.main)

