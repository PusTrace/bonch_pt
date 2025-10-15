from aiogram import Router, types, F

# Импортируем внутренние роутеры этого сервиса
#from .handlers.do_reminder import do_reminder_router
#from .handlers.bot_settings import bot_settings_router

# Создаём главный роутер для сервиса "deadlines"
router = Router(name="deadlines")

@router.message(F.text == 'Статистика 📊')
async def LoopBack(message: types.Message):
    await message.answer("LoopBack, Статистика 📊")

    # Включаем подроутеры (подмодули)
    # router.include_router(do_reminder_router)
    # router.include_router(bot_settings_router)
