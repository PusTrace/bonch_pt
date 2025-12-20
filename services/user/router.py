from aiogram import Router

from .handlers.user import router as tasks_router


# Создаём главный роутер для сервиса "user"
router = Router(name="user")
# Включаем подроутеры (подмодули)
router.include_router(tasks_router)
