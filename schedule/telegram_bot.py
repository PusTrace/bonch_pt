import asyncio
import os
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv
from redis.asyncio import Redis

from formatters import (
    format_schedule_group,
    format_schedule_protection,
    format_schedule_teacher,
)
from repository import RedisDB

router = Router()


class ProfileStates(StatesGroup):
    waiting_group = State()


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Расписание группы"),
                KeyboardButton(text="👨‍🏫 Преподаватель"),
            ],
            [KeyboardButton(text="🛡 Защита"), KeyboardButton(text="⚙ Моя группа")],
        ],
        resize_keyboard=True,
    )


async def _log(db: RedisDB, message: Message, command: str, args: str = "") -> None:
    uid = message.from_user.id if message.from_user else None
    await db.log_command(uid, command, args)


@router.inline_query()
async def inline_schedule(query: InlineQuery, schedule: RedisDB):
    search = query.query.strip()
    if not search:
        await query.answer(
            results=[],
            cache_time=1,
            switch_pm_text="Введите часть имени преподавателя в чате",
            switch_pm_parameter="start",
        )
        return
    results = []
    try:
        teacher_lessons = await schedule.get_teacher_schedule(search)
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        teacher_lessons = [
            item
            for item in teacher_lessons
            if monday.isoformat() <= item.date <= sunday.isoformat()
        ]
        if teacher_lessons:
            results.append(
                InlineQueryResultArticle(
                    id="teacher_week",
                    title=f"👨‍🏫 {search}",
                    description="Расписание преподавателя на текущую неделю",
                    input_message_content=InputTextMessageContent(
                        message_text=format_schedule_teacher(
                            teacher_lessons,
                            f"Преподаватель: {search}",
                        ),
                        parse_mode=ParseMode.HTML,
                    ),
                )
            )
    except Exception as error:
        print(f"Ошибка inline-поиска: {error}")
    await query.answer(results=results, cache_time=1, is_personal=True)


@router.message(Command("start"))
async def cmd_start(message: Message, schedule: RedisDB):
    await _log(schedule, message, "start")
    await message.answer(
        "Привет! Используй кнопки ниже или команды.\n"
        "Можно задать свою группу в «⚙ Моя группа» — тогда в расписании группы/защите "
        "её можно не вводить повторно.",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("setgroup"))
async def cmd_setgroup(message: Message, command: CommandObject, schedule: RedisDB):
    await _log(schedule, message, "setgroup", command.args or "")
    if not command.args or not command.args.strip():
        await message.answer("Укажи группу: /setgroup ИКБ-31")
        return
    uid = message.from_user.id if message.from_user else None
    if uid is None:
        return
    await schedule.set_user_group(uid, command.args.strip())
    await message.answer(f"Группа сохранена: {command.args.strip()}", reply_markup=main_menu_kb())


@router.message(Command("group"))
async def cmd_group(message: Message, command: CommandObject, schedule: RedisDB):
    uid = message.from_user.id if message.from_user else None
    sect = (command.args or "").strip()
    if not sect and uid is not None:
        sect = (await schedule.get_user_group(uid)) or ""
    await _log(schedule, message, "group", sect)
    if not sect:
        await message.answer(
            "Укажи группу: /group ИКБ-31 или задай её в «⚙ Моя группа».",
            reply_markup=main_menu_kb(),
        )
        return
    try:
        lessons = await schedule.get_week_schedule(sect)
        text = format_schedule_group(lessons, f"Расписание группы {sect}")
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
    except Exception as error:
        print(f"Ошибка /group: {error}")
        await message.answer(
            "Не удалось получить расписание. Проверь название группы и Redis.",
            reply_markup=main_menu_kb(),
        )


@router.message(Command("teacher"))
async def cmd_teacher(message: Message, command: CommandObject, schedule: RedisDB):
    await _log(schedule, message, "teacher", command.args or "")
    if not command.args or not command.args.strip():
        await message.answer("Укажи преподавателя: /teacher Иванов")
        return
    teacher = command.args.strip()
    try:
        teacher_lessons = await schedule.get_teacher_schedule(teacher)
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        teacher_lessons = [
            item
            for item in teacher_lessons
            if monday.isoformat() <= item.date <= sunday.isoformat()
        ]
        text = format_schedule_teacher(teacher_lessons, f"Преподаватель: {teacher}")
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
    except Exception as error:
        print(f"Ошибка /teacher: {error}")
        await message.answer("Не удалось получить расписание преподавателя.", reply_markup=main_menu_kb())


@router.message(Command("protection"))
async def cmd_protection(message: Message, command: CommandObject, schedule: RedisDB):
    uid = message.from_user.id if message.from_user else None
    sect = (command.args or "").strip()
    if not sect and uid is not None:
        sect = (await schedule.get_user_group(uid)) or ""
    await _log(schedule, message, "protection", sect)
    if not sect:
        await message.answer(
            "Укажи группу: /protection ИКБ-31 или задай её в «⚙ Моя группа».",
            reply_markup=main_menu_kb(),
        )
        return
    try:
        lessons = await schedule.get_protection_lessons(group=sect, week_only=True)
        text = format_schedule_protection(lessons, f"Защита/обзор — {sect}", main_group=sect)
        if not text:
            await message.answer("Нет данных для отображения.", reply_markup=main_menu_kb())
            return
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
    except Exception as error:
        print(f"Ошибка /protection: {error}")
        await message.answer("Не удалось получить данные для формата защиты.", reply_markup=main_menu_kb())


@router.message(F.text == "⚙ Моя группа")
async def btn_my_group(message: Message, schedule: RedisDB, state: FSMContext):
    await _log(schedule, message, "btn_my_group")
    uid = message.from_user.id if message.from_user else None
    current = await schedule.get_user_group(uid) if uid is not None else None
    msg = "Пришли название группы (например ИКБ-31)."
    if current:
        msg = f"Текущая группа: <b>{current}</b>\n{msg}"
    await state.set_state(ProfileStates.waiting_group)
    await message.answer(msg, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())


@router.message(ProfileStates.waiting_group, F.text)
async def profile_set_group(message: Message, schedule: RedisDB, state: FSMContext):
    text = (message.text or "").strip()
    if text.startswith("/"):
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu_kb())
        return
    uid = message.from_user.id if message.from_user else None
    if uid is None:
        await state.clear()
        return
    await schedule.set_user_group(uid, text)
    await _log(schedule, message, "set_group_profile", text)
    await state.clear()
    await message.answer(f"Группа сохранена: {text}", reply_markup=main_menu_kb())


@router.message(F.text == "📅 Расписание группы")
async def btn_group(message: Message, schedule: RedisDB):
    uid = message.from_user.id if message.from_user else None
    sect = await schedule.get_user_group(uid) if uid is not None else None
    await _log(schedule, message, "btn_group", sect or "")
    if not sect:
        await message.answer(
            "Группа не задана. Нажми «⚙ Моя группа» или отправь /group ИКБ-31.",
            reply_markup=main_menu_kb(),
        )
        return
    try:
        lessons = await schedule.get_week_schedule(sect)
        text = format_schedule_group(lessons, f"Расписание группы {sect}")
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
    except Exception as error:
        print(f"Ошибка btn group: {error}")
        await message.answer("Не удалось получить расписание.", reply_markup=main_menu_kb())


@router.message(F.text == "👨‍🏫 Преподаватель")
async def btn_teacher(message: Message):
    await message.answer(
        "Отправь команду: /teacher Фамилия (или часть имени).\n"
        "Inline: в любом чате набери @имя_бота и часть фамилии преподавателя.",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "🛡 Защита")
async def btn_protection(message: Message, schedule: RedisDB):
    uid = message.from_user.id if message.from_user else None
    sect = await schedule.get_user_group(uid) if uid is not None else None
    await _log(schedule, message, "btn_protection", sect or "")
    if not sect:
        await message.answer(
            "Группа не задана. Нажми «⚙ Моя группа» или отправь /protection ИКБ-31.",
            reply_markup=main_menu_kb(),
        )
        return
    try:
        lessons = await schedule.get_protection_lessons(group=sect, week_only=True)
        text = format_schedule_protection(lessons, f"Защита/обзор — {sect}", main_group=sect)
        if not text:
            await message.answer("Нет данных для отображения.", reply_markup=main_menu_kb())
            return
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
    except Exception as error:
        print(f"Ошибка btn protection: {error}")
        await message.answer("Не удалось получить данные.", reply_markup=main_menu_kb())


async def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if not token:
        raise RuntimeError("Не задан BOT_TOKEN")
    redis = Redis.from_url(redis_url, decode_responses=True)
    proxy_url = (os.getenv("SOCKS_PROXY") or "").strip()
    if proxy_url:
        session = AiohttpSession(proxy=proxy_url)
    else:
        session = AiohttpSession()
    bot = Bot(token=token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    dp["schedule"] = RedisDB(redis)
    try:
        await redis.ping()
        print("Redis подключён. Inline-бот запущен.")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
