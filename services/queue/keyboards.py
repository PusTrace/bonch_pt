from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Очередь на сегодня", callback_data="queue_today"), InlineKeyboardButton(text="Очередь на завтра", callback_data="queue_tomorrow")],
        [InlineKeyboardButton(text="Как занять очередь?", callback_data="how_to_queue")]
    ]
)
