import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.db import Database
from core.routers import register_routers
from core.scheduler import init_scheduler

load_dotenv()

# Основной запуск бота
async def main():
    await bot_health_check()


    # Настраиваем планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_send_reminders,  "cron", hour=9, minute=0)  # Проверяем каждый день в 9 утра
    scheduler.start()
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"error: {e}")
    finally:
        scheduler.shutdown()
        await bot.session.close()


# send messages
async def check_and_send_reminders(): # TODO: fix check and send reminders from .json to db
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for row in reminders:
        for reminder in chat_data["reminders"]:
            deadline = datetime.strptime(reminder[1], "%d.%m")
            current_year_deadline = deadline.replace(year=now.year)

            days_left = (current_year_deadline - now).days 
            if days_left in reminder["intervals"]:
                try:
                    message_thread_id = 22
                    await bot.send_message(
                        chat_id,
                        f"Напоминание: {reminder[0]} через {days_left} дней!",
                        message_thread_id=message_thread_id  # Указываем ID топика
                    )
                except Exception as e:
                    print(f"Ошибка отправки напоминания: {e}")




# для проверки работы бота
async def bot_health_check():
    chat_ids = [1185330189]
    try:
        for chat_id in chat_ids:
            await bot.send_message(
                chat_id,
                text="admin check health\n"
                     "/start\n"
            )
    except Exception as e:
        print(f"Ошибка отправки тестового сообщения: {e}")


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # init db
    await db = Database()

    # Роутеры
    register_routers(dp)

    # Планировщик
    scheduler = AsyncIOScheduler()
    init_scheduler(scheduler, bot)
    scheduler.start()

    # Запуск
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
