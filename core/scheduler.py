from datetime import datetime
from core.db import get_db

def init_scheduler(scheduler, bot):
    async def send_reminders():
        db = get_db()
        now = datetime.now().strftime("%d.%m")
        rows = db.execute("SELECT chat_id, text FROM deadlines WHERE date=?", (now,)).fetchall()
        for chat_id, text in rows:
            await bot.send_message(chat_id, f"🕒 Сегодня дедлайн: {text}")

    scheduler.add_job(send_reminders, "cron", hour=9, minute=0)
