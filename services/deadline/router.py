from aiogram import Router

# Импортируем внутренние роутеры этого сервиса
from .handlers.do_reminder import do_reminder_router
from .handlers.bot_settings import bot_settings_router

# Создаём главный роутер для сервиса "deadlines"
router = Router(name="deadlines")

# Включаем подроутеры (подмодули)
router.include_router(do_reminder_router)
router.include_router(bot_settings_router)
