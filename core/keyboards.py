from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Статистика 📊", callback_data="statistic_main")],
        [InlineKeyboardButton(text="Мои данные", callback_data="user_menu")],
        [InlineKeyboardButton(text="ещё", callback_data="other")]
    ]
)

service_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        #[InlineKeyboardButton(text="Дедлайны ⏰", callback_data="deadlines")],
        #[InlineKeyboardButton(text="Очередь 📋", callback_data="queue_main")],
        [InlineKeyboardButton(text="Стать разработчиком", callback_data="became_developer")],
        [InlineKeyboardButton(text="Сообщить о баге", callback_data="report_issue")],
        [InlineKeyboardButton(text="Вернуться к сервисам", callback_data="main")]
    ]
)
