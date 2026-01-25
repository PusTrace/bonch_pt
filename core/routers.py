from core.start import start_router
from services.schedule.router import router as schedule_router
from services.user.router import router as user_router
from services.tasks.router import router as tasks_router

def register_routers(dp):
    dp.include_router(start_router) # Основной роутер
    #dp.include_router(deadlines_router) # Роутер для работы с дедлайнами(сроками)
    #dp.include_router(queue_router) # Роутер для работы с очередями
    dp.include_router(schedule_router) # Роутер для работы со статистикой
    dp.include_router(user_router) # Роутер для работы с пользователями
    dp.include_router(tasks_router)
    

