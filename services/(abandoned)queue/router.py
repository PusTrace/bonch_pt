from aiogram import Router

from .handlers.queue_router import router as queue_router


# Создаём главный роутер для сервиса "queue"
router = Router(name="queue")

# Включаем подроутеры (подмодули)
router.include_router(queue_router)

