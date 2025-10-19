import asyncio
import os
from dotenv import load_dotenv
import signal

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.db import Database
from core.middlewares import DatabaseMiddleware
from core.routers import register_routers
from core.scheduler import init_scheduler

load_dotenv()

async def main():
    print("🚀 Запуск бота...")

    print("1️⃣ Telegram")
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    print("2️⃣ База данных")
    db = Database()
    await db.connect()

    # middleware
    dp.message.middleware(DatabaseMiddleware(db))
    dp.callback_query.middleware(DatabaseMiddleware(db))

    print("3️⃣ Роутеры")
    register_routers(dp)

    # print("4️⃣ Планировщик")
    # scheduler = AsyncIOScheduler()
    # init_scheduler(scheduler, bot, db)
    # scheduler.start()

    print("5️⃣ Проверка живости")
    await bot.send_message(1185330189, "✅ Бот запущен и работает!")
    
    # 🧹 Корректное завершение при SIGINT / SIGTERM
    async def shutdown():
        print("🧹 Закрываю соединения...")
        scheduler.shutdown(wait=False)
        await db.close()  # закрываем пул
        await bot.session.close()
        print("🟢 Завершено корректно")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        
    print("6️⃣ Запуск основного цикла")
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
