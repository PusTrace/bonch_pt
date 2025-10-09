from aiogram import types, Router
from aiogram.filters.command import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message):
    db = message.bot.get("db")
    user = await db.get_user(message.from_user.id)
    print(user)
    
    if user:
        # Пользователь уже зарегистрирован
        await message.answer("С возвращением! 👋", reply_markup=main)
    else:

        await message.answer("Привет! 👋 Похоже, ты здесь впервые.")

        await message.answer("Введите свою группу")

        await db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            message.from_user.group
        )

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Statistics 📊')],
    [KeyboardButton(text='Queue 📋'), KeyboardButton(text='Deadlines ⏰')]
],
    resize_keyboard=True,
    input_field_placeholder="Choose an option"
)