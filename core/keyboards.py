from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Статистика 📊", callback_data="statistic")],
        [InlineKeyboardButton(text="Дедлайны ⏰", callback_data="deadlines"), InlineKeyboardButton(text="Очередь 📋", callback_data="queue_main")],
        [InlineKeyboardButton(text="Другие сервисы(написать свой)", callback_data="other")]
    ]
)
