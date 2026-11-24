import asyncio
import html
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from dotenv import load_dotenv
from redis.asyncio import Redis

from schedule import Schedule

router = Router()


def format_schedule_item(item: dict) -> str:
    """Форматирует одну пару."""

    def safe(value):
        return html.escape(str(value)) if value else "-"

    try:
        formatted_date = datetime.strptime(item["date"], "%Y-%m-%d").strftime(
            "%d.%m.%Y"
        )
    except (ValueError, TypeError, KeyError):
        formatted_date = safe(item.get("date"))

    return (
        f"📅 <b>{formatted_date}</b>\n"
        f"🔢 Пара: {safe(item.get('pair'))}\n"
        f"📖 Предмет: {safe(item.get('subject'))}\n"
        f"🏫 Аудитория: {safe(item.get('auditorium'))}\n"
        f"👨‍🏫 Преподаватель: {safe(item.get('teacher'))}\n"
        f"📝 Тип: {safe(item.get('lesson_type'))}\n"
        f"👥 Группа: {safe(item.get('sect'))}"
    )


def format_schedule(schedule: list[dict], title: str) -> str:
    """Формирует сообщение с расписанием."""

    if not schedule:
        return f"<b>{html.escape(title)}</b>\n\nРасписание отсутствует."

    text = f"<b>{html.escape(title)}</b>\n\n"

    for item in schedule:
        block = format_schedule_item(item) + "\n\n"

        # Ограничение Telegram: 4096 символов.
        if len(text) + len(block) > 3900:
            text += "\n... Расписание слишком длинное."
            break

        text += block

    return text


@router.inline_query()
async def inline_schedule(
    query: InlineQuery,
    schedule: Schedule,
):
    search = query.query.strip()

    if not search:
        await query.answer(
            results=[],
            cache_time=1,
        )
        return

    results = []

    try:
        # Поиск группы на текущую неделю.
        group_schedule = await schedule.get_week_schedule(search)

        if group_schedule:
            results.append(
                InlineQueryResultArticle(
                    id="group_week",
                    title=f"📅 Расписание группы: {search}",
                    description="Расписание на текущую неделю",
                    input_message_content=InputTextMessageContent(
                        message_text=format_schedule(
                            group_schedule,
                            f"Расписание группы {search}",
                        ),
                        parse_mode=ParseMode.HTML,
                    ),
                )
            )

        # Поиск преподавателя на текущую неделю.
        teacher_schedule = await schedule.get_teacher_schedule(search)

        # get_teacher_schedule возвращает всё расписание,
        # поэтому фильтруем его по текущей неделе.
        from datetime import date, timedelta

        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        teacher_schedule = [
            item
            for item in teacher_schedule
            if monday.isoformat() <= item["date"] <= sunday.isoformat()
        ]

        if teacher_schedule:
            results.append(
                InlineQueryResultArticle(
                    id="teacher_week",
                    title=f"👨‍🏫 Расписание преподавателя: {search}",
                    description="Расписание на текущую неделю",
                    input_message_content=InputTextMessageContent(
                        message_text=format_schedule(
                            teacher_schedule,
                            f"Расписание преподавателя: {search}",
                        ),
                        parse_mode=ParseMode.HTML,
                    ),
                )
            )

    except Exception as error:
        print(f"Ошибка inline-поиска: {error}")

    await query.answer(
        results=results,
        cache_time=1,
        is_personal=True,
    )


async def main():
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    redis_url = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )

    if not token:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN")

    redis = Redis.from_url(
        redis_url,
        decode_responses=True,
    )
    session = AiohttpSession(
        proxy="socks5://127.0.0.1:2080",
    )

    bot = Bot(
        token=token,
        session=session,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dp = Dispatcher()
    dp.include_router(router)

    dp["schedule"] = Schedule(redis)

    try:
        await redis.ping()
        print("Redis подключён.")
        print("Inline-бот запущен.")

        await dp.start_polling(bot)

    finally:
        await bot.session.close()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
