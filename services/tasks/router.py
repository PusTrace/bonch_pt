from aiogram import Router

from .handlers.tasks import router as tasks_router


# Создаём главный роутер для сервиса "tasks"
router = Router(name="tasks")
# Включаем подроутеры (подмодули)
router.include_router(tasks_router)
