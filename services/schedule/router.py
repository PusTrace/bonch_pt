from aiogram import Router

from .handlers.schedule import router as schedule_router


# Создаём главный роутер для сервиса "schedule"
router = Router(name="schedule")
# Включаем подроутеры (подмодули)
router.include_router(schedule_router)
