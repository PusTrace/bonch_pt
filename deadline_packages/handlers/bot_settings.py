import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

import deadline_packages.keyboards as kb
from deadline_packages.keyboards import clear
from deadline_packages.states import ReminderStates
from deadline_packages.utils import load_reminders, save_reminders

logging.basicConfig(level=logging.INFO)


reminders = load_reminders()

bot_settings_router = Router()


@bot_settings_router.message(F.text.casefold() == 'настройки ⚙️'.casefold())
async def settings(message: types.Message):
    await message.answer("настройки ⚙️", reply_markup=kb.settings)

@bot_settings_router.message(F.text.casefold() == 'изменить интервал 🗓'.casefold()) # TODO: fix change interval from .json to db
async def settings_interval(message: types.Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Установка интервала отменено.", reply_markup=kb.main)
        return
    await state.set_state(ReminderStates.waiting_for_name_settings)
    await message.answer("Введите имя для кого хотите изменить интервал 🗓", reply_markup=clear)

@bot_settings_router.message(ReminderStates.waiting_for_name_settings)
async def enter_name(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Изменение интервала отменено.", reply_markup=kb.main)
        return

    name_to_check = message.text.strip()  # Имя, которое ввел пользователь

    # Проверяем, существует ли человек с таким именем в базе данных
    user_exists = False
    for user_id, user_info in reminders.items():
        for reminder in user_info["reminders"]:
            if reminder["name"].lower() == name_to_check.lower():  # Сравниваем имена без учета регистра
                user_exists = True
                break
        if user_exists:
            break

    if not user_exists:
        # Если такого имени нет в базе
        await message.answer("Пользователь с таким именем не существует в базе данных.", reply_markup=kb.main)
        return

    # Сохраняем имя пользователя в состоянии для дальнейшего использования
    await state.update_data(name=name_to_check)

    # Переходим к следующему шагу (ввод интервалов)
    await state.set_state(ReminderStates.waiting_for_interval_settings)
    await message.answer("Введите интервалы через запятую.\n"
                         "Пример: 1, 7, 30\n"
                         "Это изменит интервал так, что оповещения придут за 1, 7, 30 дней")

@bot_settings_router.message(ReminderStates.waiting_for_interval_settings)
async def enter_interval(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Изменение интервала отменено.", reply_markup=kb.main)
        return

    try:
        user_interval_str = str(message.text)
        user_interval = [int(item.strip()) for item in user_interval_str.split(",")]
        user_data = await state.get_data()

        # Сохраняем напоминание
        user_id = str(message.chat.id)
        if user_id not in reminders:
            reminders[user_id] = {"reminders": []}

        # Ищем существующее напоминание для данного пользователя
        for reminder in reminders[user_id]["reminders"]:
            if reminder["name"] == user_data["name"]:
                # Обновляем интервалы
                reminder["intervals"] = user_interval  # Просто присваиваем новый список интервалов
                break

        # Сохраняем изменения в базе данных
        save_reminders(reminders)

        # Завершаем процесс и возвращаем главную клавиатуру
        await state.clear()
        await message.answer(
            f"Интервал для {user_data['name']} на {user_interval_str} успешно изменён!",
            reply_markup=kb.main
        )
    except ValueError:
        await message.answer("Ошибка: введите интервал в формате: 1, 7, 30")
        
@bot_settings_router.message(F.text.casefold() == 'отмена❌'.casefold())
async def cancel_anywhere(message: types.Message, state: FSMContext):
    if await state.get_state():
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=kb.main)
    else:
        await message.answer("Вы не находитесь в процессе настройки ⚙️.", reply_markup=kb.main)
        
# TODO: add delete message from db
@bot_settings_router.message(F.text.casefold() == 'удалить запись 🔒'.casefold())
async def delete_entry(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Удаление записи отменено.", reply_markup=kb.main)
        return

    await state.set_state(ReminderStates.waiting_for_name_delete)
    await message.answer("Введите имя для кого хотите удалить запись 🔒", reply_markup=clear)

@bot_settings_router.message(ReminderStates.waiting_for_name_delete)
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