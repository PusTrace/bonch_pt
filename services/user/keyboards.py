from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мой профиль")],
        [KeyboardButton(text="Сменить группу"), KeyboardButton(text="Сменить бригаду")]
    ],
    resize_keyboard=True
)