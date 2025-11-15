from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Показать расписание преподавателей", callback_data="statistic_teachers")],
        [InlineKeyboardButton(text="Вернуться к сервисам", callback_data="main")]
    ]
)
