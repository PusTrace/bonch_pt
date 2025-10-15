def init_scheduler(scheduler, bot, db):
    async def send_reminders():
        deadlines = await db.get_deadlines()
        # Отправка уведомлений если дедлайн на сегодня или на интервалы TODO
        for chat_id, text in deadlines:
            await bot.send_message(chat_id, f"🕒 Сегодня дедлайн: {text}")

    scheduler.add_job(send_reminders, "cron", hour=9, minute=0)
