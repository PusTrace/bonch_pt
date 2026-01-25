# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить задачу"), KeyboardButton(text="Показать задачи")],
        [KeyboardButton(text="Обновить дедлайн"), KeyboardButton(text="Обновить описание")],
        [KeyboardButton(text="Обновить прогресс"), KeyboardButton(text="Удалить задачу")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)