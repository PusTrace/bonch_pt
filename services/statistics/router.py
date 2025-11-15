from aiogram import Router

from .handlers.statistics import router as statistic_router


# Создаём главный роутер для сервиса "statistics"
router = Router(name="statistics")
# Включаем подроутеры (подмодули)
router.include_router(statistic_router)

