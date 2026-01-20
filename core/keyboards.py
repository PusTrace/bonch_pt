# core/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Статистика 📊")],
        [KeyboardButton(text="Мои данные")],
        [KeyboardButton(text="Ещё")]
    ],
    resize_keyboard=True
)

service_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Стать разработчиком")],
        [KeyboardButton(text="Сообщить о баге")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )