# core/start.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
import aiohttp
from core.db import Database
from core.states import RegistrationStates
import core.keyboards as kb
from core.utils import format_own_schedule
from services.user import change_group

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, db: Database):
    user = await db.get_user_info(message.chat.id)
    if user:
        schedule = await db.get_today_schedule(user[4])
        await message.answer(format_own_schedule(schedule, "Расписание на сегодня"), reply_markup=kb.main)
    else:
        await change_group(message, state, db)

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

@start_router.message(RegistrationStates.waiting_for_report)
async def report_issue_save(message: types.Message, state: FSMContext, db: Database):
    issue_description = message.text.strip()
    chat_id = message.chat.id
    
    await db.save_issue_report(chat_id, issue_description)
    await state.clear()
    await message.answer("Спасибо за ваш отчет! Мы рассмотрим его в ближайшее время.", reply_markup=kb.main)

@start_router.message(F.text == "◀️ Назад к главному")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=kb.main)

@start_router.message(F.text == "getip")
async def get_ip(message: types.Message):
    chat_id = message.chat.id
    if chat_id != 1185330189:
        print("Unauthorized access attempt to get IP:", chat_id)
        return await message.answer("Access denied.")
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.ipify.org?format=json") as resp:
            ip_info = await resp.json()
            await message.answer(f"Your IP is: {ip_info.get('ip')}")
            
@start_router.message(Command("docs"))
async def documents(message: types.Message):
    await message.answer(
        "**Политика конфиденциальности**\n\n"
        "Настоящая Политика конфиденциальности описывает, какие данные собирает и как использует Telegram-бот.\n\n"

        "**1. Какие данные собираются**\n\n"
        "Бот может собирать и хранить следующие данные пользователя:\n"
        "- `message.chat.id` (уникальный идентификатор чата)\n"
        "- `username` пользователя\n"
        "- `full_name` пользователя\n"
        "- информация о группе в университете\n"
        "- информация о бригаде в университете\n\n"

        "**2. Цели сбора данных**\n\n"
        "Собранные данные используются исключительно для работы функционала бота, включая:\n"
        "- идентификацию пользователя\n"
        "- привязку пользователя к его учебной группе и бригаде\n"
        "- корректную работу сервисных функций бота\n\n"

        "**3. Хранение данных**\n\n"
        "Данные хранятся в электронном виде и не передаются третьим лицам.\n\n"

        "**4. Передача данных третьим лицам**\n\n"
        "Бот не передаёт персональные данные пользователей третьим лицам, за исключением случаев, предусмотренных законодательством.\n\n"

        "**5. Защита данных**\n\n"
        "Разработчик принимает разумные меры для защиты данных от несанкционированного доступа, изменения или удаления.\n\n"

        "**6. Удаление данных**\n\n"
        "Пользователь может запросить удаление своих данных, прекратив использование бота, обратившись к разработчику или воспользовавшись функцией в боте.\n\n"

        "**7. Согласие пользователя**\n\n"
        "Используя данного бота, пользователь соглашается с настоящей Политикой конфиденциальности.",
        parse_mode="Markdown"
    )


