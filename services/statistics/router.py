from aiogram import Router

from .handlers.schedule import router as schedule_router
from .handlers.tasks import router as tasks_router


# Создаём главный роутер для сервиса "statistics"
router = Router(name="statistics")
# Включаем подроутеры (подмодули)
router.include_router(schedule_router)
router.include_router(tasks_router)
