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

@admin_router.message(F.text.casefold() == 'удалить запись 🔒'.casefold())
async def delete_entry(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Удаление записи отменено.", reply_markup=kb.main)
        return

    await state.set_state(ReminderStates.waiting_for_name_delete)
    await message.answer("Введите имя для кого хотите удалить запись 🔒", reply_markup=clear)

@admin_router.message(ReminderStates.waiting_for_name_delete)
async def confirm_deletion(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Удаление записи отменено.", reply_markup=kb.main)
        return

    name_to_delete = message.text.strip()

    # Проверяем существование записи с таким именем
    user_id = str(message.chat.id)
    record_found = False

    if user_id in reminders:
        for reminder in reminders[user_id]["reminders"]:
            if reminder["name"].lower() == name_to_delete.lower():
                reminders[user_id]["reminders"].remove(reminder)
                record_found = True
                break

        # Удаляем пользователя из базы, если у него больше нет записей
        if not reminders[user_id]["reminders"]:
            del reminders[user_id]

    if record_found:
        save_reminders(reminders)  # Сохраняем изменения в базе данных
        await message.answer(f"Запись для {name_to_delete} успешно удалена!", reply_markup=kb.main)
    else:
        await message.answer("Пользователь с таким именем не найден в базе данных.", reply_markup=kb.main)

    await state.clear()