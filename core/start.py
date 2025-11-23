from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import requests, aiohttp

from core.db import Database
from core.states import RegistrationStates
import core.keyboards as kb
start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, db: Database):
        user = await db.get_user_info(message.chat.id)
        if user:
            schedule = await db.get_today_schedule(user[4])
            text_lines = ["📋 Расписание на сегодня:\n"]
            for date, pair, subject, auditorium, teacher, lesson_type in schedule:
                text_lines.append(f"{pair:>2}. {subject:<35} | {auditorium:>16} | {teacher:<20} | {lesson_type:<15}")
            await message.answer("\n".join(text_lines), reply_markup=kb.main)
        else:
            await message.answer("Привет! 👋 Похоже, вы здесь впервые.\n\nВведите вашу группу (например: ИКБ-31):")
            await state.set_state(RegistrationStates.waiting_for_group)


@start_router.message(RegistrationStates.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext, db: Database):
    group = message.text.strip().upper()
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id != user_id:
        await db.add_user(
            message.chat.id,
            message.chat.username,
            message.chat.full_name,
            group
        )

        await state.clear()
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=f"Отлично! Группа '{group}' сохранена ✅",
            reply_markup=kb.main,
            message_thread_id=message.message_thread_id
        )
    else:
        await db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            group
        )

        await state.clear()
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=f"Отлично! Группа '{group}' сохранена ✅",
            reply_markup=kb.main,
            message_thread_id=message.message_thread_id
        )

@start_router.callback_query(F.data == 'other')
async def other(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=kb.service_keyboard)

@start_router.callback_query(F.data == 'became_developer')
async def became_developer(callback: types.CallbackQuery, db: Database):
    await callback.message.edit_text(
    "Чтобы стать разработчиком, выполните следующие шаги:\n"
    "1) Прочитайте README проекта: github.com/PusTrace/bonch_pt\n"
    "2) Напишите: t.me/PusTrace",
    reply_markup=kb.main
    )
    await callback.answer()

@start_router.callback_query(F.data == 'report_issue')
async def report_issue(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Напишите о проблеме:\n"
    )
    await state.set_state(RegistrationStates.waiting_for_report)
    
@start_router.message(RegistrationStates.waiting_for_report)
async def report_issue(message: types.Message, state: FSMContext, db: Database):
    issue_description = message.text.strip()
    user_id = message.from_user.id

    await db.save_issue_report(user_id, issue_description)

    await state.clear()
    await message.answer("Спасибо за ваш отчет! Мы рассмотрим его в ближайшее время.", reply_markup=kb.main)
    
@start_router.message(F.text == "getip")
async def get_ip(message: types.Message):
    user_id = message.from_user.id

    if user_id != 1185330189:
        print("Unauthorized access attempt to get IP:", user_id)
        return await message.answer("Access denied.")

    async with aiohttp.ClientSession() as session:
        async with session.get("https://ifconfig.me") as resp:
            ip = await resp.text()

    await message.answer(f"Your IP is: {ip.strip()}")