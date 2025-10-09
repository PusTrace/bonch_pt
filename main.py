import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.db import Database
from core.routers import register_routers
from core.scheduler import init_scheduler

load_dotenv()

async def main():
    print("🚀 Запуск бота...")

    # 1️⃣ Telegram
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # 2️⃣ База данных
    db = Database()
    await db.connect()
    dp["db"] = db  # чтобы в хендлерах можно было писать db = message.bot.get("db")

    # 3️⃣ Роутеры
    register_routers(dp)

    # 4️⃣ Планировщик
    scheduler = AsyncIOScheduler()
    init_scheduler(scheduler, bot, db)
    scheduler.start()

    # 5️⃣ Проверка живости
    await bot.send_message(1185330189, "✅ Бот запущен и работает!")

    # 6️⃣ Запуск основного цикла
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
