import asyncio
import os
from dotenv import load_dotenv
import signal

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.db import Database
from core.middlewares import DatabaseMiddleware, ErrorLoggingMiddleware, handle_async_exception
from core.routers import register_routers
from core.scheduler import init_scheduler
import logging
from core.logger import setup_logging, install_global_exception_handler

load_dotenv()

async def main():
    setup_logging(
        module_name="BONCH_BOT",
        log_file="logs/bot.log",
        level=logging.INFO
    )
    logging.getLogger("aiogram").propagate = True
    logging.getLogger("aiogram.event").propagate = True
    logging.getLogger("aiogram.dispatcher").propagate = True

    logging.getLogger("aiogram").setLevel(logging.ERROR)
    logging.getLogger("aiogram.event").setLevel(logging.ERROR)
    logging.getLogger("aiogram.dispatcher").setLevel(logging.ERROR)

    install_global_exception_handler("BONCH_BOT")

    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_async_exception)
    
    log = logging.getLogger("BONCH_BOT")

    log.info("🚀 Запуск бота...")

    log.info("1️⃣ Telegram")
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    log.info("2️⃣ База данных")
    db = Database()
    await db.connect()

    # middleware
    dp.message.middleware(DatabaseMiddleware(db))
    dp.callback_query.middleware(DatabaseMiddleware(db))
    dp.update.middleware(ErrorLoggingMiddleware())

    log.info("3️⃣ Роутеры")
    register_routers(dp)

    log.info(" 4️⃣ Планировщик")
    scheduler = AsyncIOScheduler()
    init_scheduler(scheduler, bot, db)
    scheduler.start()

    # log.info("Проверка живости")
    # await bot.send_message(1185330189, "✅ Бот запущен и работает!")
    
    # 🧹 Корректное завершение при SIGINT / SIGTERM
    async def shutdown():
        log.info("🧹 Закрываю соединения...")
        # scheduler.shutdown(wait=False)
        await db.close()  # закрываем пул
        await bot.session.close()
        log.info("🟢 Завершено корректно")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        
    log.info("5️⃣ Запуск основного цикла")
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
