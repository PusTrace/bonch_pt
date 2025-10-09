from datetime import datetime
import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

import deadline.keyboards as kb
from deadline.keyboards import clear
from deadline.states import ReminderStates
from deadline.utils import save_reminders

logging.basicConfig(level=logging.INFO)

do_reminder_router = Router(name="do_reminder")


@do_reminder_router.message(F.text == 'Установить напоминание 📆')
async def start_set_reminder(message: types.Message, state: FSMContext):
    user_id = str(message.chat.id)  # ID чата
    await state.set_state(ReminderStates.waiting_for_name)
    await state.update_data(user_id=user_id)  # Сохраняем ID в состоянии
    await message.answer("Введите сообщение которое хотите добавить", reply_markup=clear)

@do_reminder_router.message(ReminderStates.waiting_for_name)
async def enter_name(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Установка дедлайна отменена.", reply_markup=kb.main)
        return

    if not message.text.strip():  # Проверка на пустой ввод
        await message.answer("Имя не может быть пустым. Попробуйте снова.")
        return

    await state.update_data(name=message.text)
    user_data = await state.get_data()
    logging.info(f"Сохраненные данные после ввода имени: {user_data}")

    await state.set_state(ReminderStates.waiting_for_deadline)
    await message.answer("Введите дату дедлайна в формате ДД.ММ")

@do_reminder_router.message(ReminderStates.waiting_for_deadline)
async def enter_deadline(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Установка дедлайна отменена.", reply_markup=kb.main)
        return

    try:
        deadline = datetime.strptime(message.text, "%d.%m")
        deadline = deadline.replace(year=datetime.now().year)
        user_data = await state.get_data()

        # Сохраняем напоминание
        user_id = str(message.chat.id)

        print(user_id, user_data["name"], deadline, [0, 1, 2, 3, 7])

        reminders = (user_id, user_data['name'], deadline, [0, 1, 2, 3, 7])

        save_reminders(reminders)
        await state.clear()
        await message.answer(
            f"Напоминание {user_data['name']} на {deadline.strftime('%d.%m')} успешно установлено!",
            reply_markup=kb.main
        )
    except ValueError:
        await message.answer("Ошибка: введите дату в формате ДД.ММ")

