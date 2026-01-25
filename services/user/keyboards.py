from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сменить группу")],
        [KeyboardButton(text="Сменить бригаду")],
        [KeyboardButton(text="Удалить мои данные")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)