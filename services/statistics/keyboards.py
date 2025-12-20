from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Показать расписание на неделю", callback_data="statistic_week"),InlineKeyboardButton(text="Показать расписание преподавателей", callback_data="statistic_teachers")],
        [InlineKeyboardButton(text="Задачи", callback_data="tasks"),InlineKeyboardButton(text="Назад", callback_data="main")]
    ]
)

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

tasks = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить задачу"), KeyboardButton(text="Показать задачи")],
        [KeyboardButton(text="Обновить дедлайн"), KeyboardButton(text="Обновить описание")],
        [KeyboardButton(text="Обновить прогресс")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)