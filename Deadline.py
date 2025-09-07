import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from deadline_packages.handlers.start import start_router
from deadline_packages.handlers.do_reminder import do_reminder_router
from deadline_packages.handlers.bot_settings import bot_settings_router
from deadline_packages.handlers.admin import admin_router

from deadline_packages.utils import load_reminders

# Объект бота

load_dotenv()
api_token = os.getenv("BOT_TOKEN")
bot = Bot(token=api_token)

storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

reminders = load_reminders()

# Основной запуск бота
async def main():
    await bot_health_check()
    dp.include_router(start_router)
    dp.include_router(do_reminder_router)
    dp.include_router(bot_settings_router)
    dp.include_router(admin_router)

    # Настраиваем планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_send_reminders,  "cron", hour=14, minute=42)  # Проверяем каждый день в 9 утра
    scheduler.start()
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"error: {e}")
    finally:
        scheduler.shutdown()
        await bot.session.close()


# send messages
async def check_and_send_reminders():
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  # Обнуляем время
    for chat_id, chat_data in reminders.items():  # user_id - это ID группы
        for reminder in chat_data["reminders"]:
            deadline = datetime.strptime(reminder["deadline"], "%d.%m")
            current_year_deadline = deadline.replace(year=now.year)

            days_left = (current_year_deadline - now).days  # Теперь дни считаются правильно
            if days_left in reminder["intervals"]:
                try:
                    # Получаем topic_id, если он указан
                    message_thread_id = 22
                    await bot.send_message(
                        chat_id,
                        f"Напоминание: {reminder['name']} через {days_left} дней!",
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


if __name__ == "__main__":
    asyncio.run(main())
