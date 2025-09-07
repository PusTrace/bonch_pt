from datetime import datetime
import logging

from aiogram import types, Router, F
from aiogram.filters.command import CommandStart

import deadline_packages.keyboards as kb
from deadline_packages.utils import load_reminders

logging.basicConfig(level=logging.INFO)


reminders = load_reminders()

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.reply(
        "Привет! Я бот-напоминалка.\n",
        reply_markup=kb.main,
    )

@start_router.message(F.text == 'следующий дедлайн ➡️')
async def info(message: types.Message):
    now = datetime.now()
    user_id = str(message.chat.id)

    if user_id not in reminders or not reminders[user_id]["reminders"]:
        await message.answer("У вас нету напоминаний.")
        return

    # Ищем ближайший  дедлайн
    user_reminders = reminders[user_id]["reminders"]
    next_deadline = None

    for reminder in user_reminders:
        deadline = datetime.strptime(reminder["deadline"], "%d.%m")
        current_year_deadline = deadline.replace(year=now.year)

        # Обновляем ближайший  дедлайна
        if not next_deadline or current_year_deadline < next_deadline["date"]:
            next_deadline = {"name": reminder["name"], "date": current_year_deadline}

    # Если нашли ближайший  дедлайна
    if next_deadline:
        time_left = next_deadline["date"] - now
        days_left = time_left.days
        hours_left = time_left.seconds // 3600
        minutes_left = (time_left.seconds // 60) % 60

        await message.answer(
            f"Следующий дедлайн : {next_deadline['name']} через {days_left} дня, {hours_left} часов и {minutes_left} минут.")
    else:
        await message.answer("У вас нет предстоящих дней дедлайна.")


@start_router.message(F.text.casefold() == 'help'.casefold())
async def about_us(message: types.Message):
    await message.answer(
        "Github: https://github.com/PusTrace/bocnh_pt\n"
        "Чтобы стать частью проекта напишите в телеграмм аккаунт.\n"
        "Телеграм: https://t.me/PusTrace"
        , reply_markup=kb.main)