from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from core.db import Database
from core.states import RegistrationStates

start_router = Router()

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Статистика 📊')],
        [KeyboardButton(text='Очередь 📋'), KeyboardButton(text='Сроки ⏰')]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию"
)

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    db: Database = message.bot['db']  # достаём базу из контекста

    user = await db.get_user(message.from_user.id)

    if user:
        await message.answer("С возвращением! 👋", reply_markup=main)
    else:
        await message.answer("Привет! 👋 Похоже, ты здесь впервые.\n\nВведите вашу группу (например: ИКБ-31):")
        await state.set_state(RegistrationStates.waiting_for_group)


@start_router.message(RegistrationStates.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext):
    db: Database = message.bot['db']
    group = message.text.strip()

    await db.add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        group
    )

    await state.clear()
    await message.answer(f"Отлично! Группа '{group}' сохранена ✅", reply_markup=main)
