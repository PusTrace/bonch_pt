# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Задачи"), KeyboardButton(text="Расписание 📊")],
        [KeyboardButton(text="Мои данные")],
        [KeyboardButton(text="Ещё")]
    ],
    resize_keyboard=True
)

service_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Стать разработчиком")],
        [KeyboardButton(text="Сообщить о баге")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


schedule = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Показать расписание на неделю")],
        [KeyboardButton(text="Показать расписание преподавателей")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)

user = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сменить группу")],
        [KeyboardButton(text="Сменить бригаду")],
        [KeyboardButton(text="Удалить мои данные")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)

tasks = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Показать задачи")],
        [KeyboardButton(text="Добавить задачу"), KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Обновить дедлайн"), KeyboardButton(text="Обновить описание")],
        [KeyboardButton(text="Обновить прогресс"), KeyboardButton(text="Удалить задачу")],
        [KeyboardButton(text="Автопланирование")],
        [KeyboardButton(text="◀️ Назад к главному")]
    ],
    resize_keyboard=True
)

# queue = InlineKeyboardMarkup(
#     inline_keyboard=[
#         [InlineKeyboardButton(text="Показать очередь на дату", callback_data="queue_custom_date")],
#         [InlineKeyboardButton(text="Абревиатуры предметов", callback_data="abbreviations"), InlineKeyboardButton(text="Занять очередь(GUI)", callback_data="take_queue")],
#         [InlineKeyboardButton(text="Вернуться к сервисам", callback_data="main")]
#     ]
# )