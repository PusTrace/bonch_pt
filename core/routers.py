from core.start import start_router
from services.deadline.router import router as deadlines_router
from services.queue.router import router as queue_router
from services.statistics.router import router as statistics_router
from services.user.router import router as user_router

def register_routers(dp):
    dp.include_router(start_router) # Основной роутер
    #dp.include_router(deadlines_router) # Роутер для работы с дедлайнами(сроками)
    #dp.include_router(queue_router) # Роутер для работы с очередями
    dp.include_router(statistics_router) # Роутер для работы со статистикой
    dp.include_router(user_router) # Роутер для работы с пользователями
    

