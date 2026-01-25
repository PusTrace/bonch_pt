# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Показать расписание на неделю")],
        [KeyboardButton(text="Показать расписание преподавателей")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)