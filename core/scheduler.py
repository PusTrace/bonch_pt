from datetime import date

def init_scheduler(scheduler, bot, db):
    async def send_reminders():
        today = date.today()
        deadlines = await db.get_deadlines()

        for chat_id, text, deadline in deadlines:
            days_left = (deadline - today).days

            if days_left == 3:
                await bot.send_message(chat_id, f"⏳ Через 3 дня дедлайн: {text}")
            elif days_left == 11:
                await bot.send_message(chat_id, f"⏳ Через 11 дня дедлайн: {text}")
            elif days_left == 2:
                await bot.send_message(chat_id, f"⏳ Через 2 дня дедлайн: {text}")
            elif days_left == 1:
                await bot.send_message(chat_id, f"⚠️ Завтра дедлайн: {text}")
            elif days_left == 0:
                await bot.send_message(chat_id, f"🚨 Сегодня дедлайн: {text}")

    # стандартный cron для ежедневного запуска
    scheduler.add_job(send_reminders, "cron", hour=9, minute=0)
