# core/start.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import aiohttp
from core.db import Database
from core.states import RegistrationStates
import core.keyboards as kb
from core.utils import format_own_schedule

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, db: Database):
    user = await db.get_user_info(message.chat.id)
    if user:
        schedule = await db.get_today_schedule(user[4])
        await message.answer(format_own_schedule(schedule, "Расписание на сегодня"), reply_markup=kb.main)
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
    else:
        await db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            group
        )
    
    await state.clear()
    await message.answer(
        f"Отлично! Группа '{group}' сохранена ✅",
        reply_markup=kb.main
    )

@start_router.message(F.text == "Ещё")
async def other(message: types.Message):
    await message.answer("Дополнительные функции:", reply_markup=kb.service_keyboard)

@start_router.message(F.text == "Стать разработчиком")
async def became_developer(message: types.Message):
    await message.answer(
        "Чтобы стать разработчиком, выполните следующие шаги:\n"
        "1) Прочитайте README проекта: github.com/PusTrace/bonch_pt\n"
        "2) Напишите: t.me/PusTrace",
        reply_markup=kb.main
    )

@start_router.message(F.text == "Сообщить о баге")
async def report_issue_start(message: types.Message, state: FSMContext):
    cancel_kb = kb.cancel_keyboard()
    await message.answer("Опишите проблему:", reply_markup=cancel_kb)
    await state.set_state(RegistrationStates.waiting_for_report)

@start_router.message(F.text == "❌ Отмена", StateFilter(RegistrationStates.waiting_for_report))
async def cancel_report(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=kb.main)

@start_router.message(RegistrationStates.waiting_for_report)
async def report_issue_save(message: types.Message, state: FSMContext, db: Database):
    issue_description = message.text.strip()
    user_id = message.from_user.id
    
    await db.save_issue_report(user_id, issue_description)
    await state.clear()
    await message.answer("Спасибо за ваш отчет! Мы рассмотрим его в ближайшее время.", reply_markup=kb.main)

@start_router.message(F.text == "◀️ Назад к главному")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=kb.main)

@start_router.message(F.text == "getip")
async def get_ip(message: types.Message):
    user_id = message.from_user.id
    if user_id != 1185330189:
        print("Unauthorized access attempt to get IP:", user_id)
        return await message.answer("Access denied.")
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.ipify.org?format=json") as resp:
            ip_info = await resp.json()
            await message.answer(f"Your IP is: {ip_info.get('ip')}")