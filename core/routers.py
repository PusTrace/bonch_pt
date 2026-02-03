from services.start import start_router
from services.schedule import router as schedule_router
from services.user import router as user_router
from services.tasks import router as tasks_router
from services.cancel import router as cancel_router

def register_routers(dp):
    dp.include_router(cancel_router) # Роутер для глобальной отмены действий
    dp.include_router(start_router) # Основной роутер
    dp.include_router(schedule_router) # Роутер для расписания
    dp.include_router(user_router) # Роутер для работы с пользователем
    dp.include_router(tasks_router) # Роутер для работы с задачами
    

