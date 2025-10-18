from aiogram import Router, types, F

# Импортируем внутренние роутеры этого сервиса
#from .handlers.do_reminder import do_reminder_router
#from .handlers.bot_settings import bot_settings_router

# Создаём главный роутер для сервиса "deadlines"
router = Router(name="deadlines")

@router.callback_query(F.data == "statistic")
async def LoopBack(callback: types.CallbackQuery):
    await callback.answer("Этот модуль ёщё не доделан, statistics 📊")

    # Включаем подроутеры (подмодули)
    # router.include_router(do_reminder_router)
    # router.include_router(bot_settings_router)
