from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Статистика 📊", callback_data="statistic")],
        [InlineKeyboardButton(text="Дедлайны ⏰", callback_data="deadlines"), InlineKeyboardButton(text="Очередь 📋", callback_data="queue_main")],
        [InlineKeyboardButton(text="Другие сервисы(написать свой)", callback_data="other")]
    ]
)

service_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Стать разработчиком", callback_data="became_developer")],
        [InlineKeyboardButton(text="Сообщить о баге", callback_data="report_issue")]
    ]
)
