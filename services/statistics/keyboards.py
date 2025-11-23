from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Показать расписание преподавателей", callback_data="statistic_teachers")],
        [InlineKeyboardButton(text="Показать расписание на неделю", callback_data="statistic_week")],
        [InlineKeyboardButton(text="Добавить/обновить лабу/задание", callback_data="statistic_add_task"), InlineKeyboardButton(text="Показать прогресс бар", callback_data="statistic_progress")],
        [InlineKeyboardButton(text="Вернуться к сервисам", callback_data="main")]
    ]
)
