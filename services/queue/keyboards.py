from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Показать очередь на дату", callback_data="queue_custom_date")],
        [InlineKeyboardButton(text="Абревиатуры предметов", callback_data="abbreviations"), InlineKeyboardButton(text="Занять очередь(GUI)", callback_data="take_queue")],
        [InlineKeyboardButton(text="Вернуться к сервисам", callback_data="main")]
    ]
)
