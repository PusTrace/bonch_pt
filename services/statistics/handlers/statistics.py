from email import message
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta


from core import db
from core.db import Database
from core.states import QueueStates
import core.keyboards as main_kb
import services.statistics.keyboards as kb
import core.keyboards as core_kb

router = Router(name="statistics")
ABBR = {
    "ASTRA": "Безопасность Astra-Linux",
    "ББЛС": "Безопасность беспроводных локальных сетей",
    "ЗОССУ": "Защита операционных систем сетевых устройств",
    "ЗПИД": "Защита программ и данных",
    "МИСКЗИ": "Методы и средства криптографической защиты информации",
    "ОМВКС": "Основы маршрутизации в компьютерных сетях",
    "ПАСЗИ": "Программно-аппаратные средства защиты информации",
    "ОИПОИБ": "Организационное и правовое обеспечение информационной безопасности"
}

@router.callback_query(F.data == "statistic_main")
async def statistics_main(callback: types.CallbackQuery, db: Database):
        user = await db.get_user_info(callback.message.chat.id)
        if user:
            schedule = await db.get_today_schedule(user[4])
            text_lines = ["📋 Расписание на сегодня:\n"]
            for date, pair, subject, auditorium, teacher, lesson_type in schedule:
                text_lines.append(f"{pair:>2}. {subject:<35} | {auditorium:>16} | {teacher:<20} | {lesson_type:<15}")

            await callback.message.edit_text(
                text="\n".join(text_lines),
                reply_markup=kb.main
            )

            await callback.answer()

@router.callback_query(F.data == "statistic_teachers")
async def statistics_teachers(callback: types.CallbackQuery, db: Database, state: FSMContext):
    user = await db.get_user_info(callback.message.chat.id)
    if not user:
        await callback.answer("Ошибка доступа", show_alert=True)
        return
    
    teachers_records = await db.get_distinct_teachers()
    buttons = [
        InlineKeyboardButton(
            text=rec['teacher'],
            callback_data=f"teacher_{rec['teacher']}"
        )
        for rec in teachers_records
        if rec['teacher'] and rec['teacher'].strip()
    ]



    await callback.message.edit_text(
        "👨‍🏫 Выберите преподавателя:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[button] for button in buttons])
    )

    await state.set_state("waiting_for_teacher")

@router.callback_query(F.data.startswith("teacher_"))
async def teacher_schedule(callback: types.CallbackQuery, db: Database, state: FSMContext):
    teacher = callback.data[len("teacher_"):]  # вырезаем имя
    await state.clear()

    schedule = await db.get_teacher_schedule(teacher)

    if not schedule:
        await callback.message.edit_text("❌ Нет расписания для этого преподавателя.", reply_markup=kb.main)
        return

    text_lines = [f"📋 Расписание преподавателя: {teacher} на 2 недели\n"]

    for date, pair, subject, auditorium, lesson_type, sect in schedule:
        text_lines.append(
            f"{date} | {pair:>2}. {subject:<35} | {auditorium:>10} | {lesson_type:<15} | {sect}"
        )

    await callback.message.edit_text(
        "\n".join(text_lines),
        reply_markup=kb.main
    )
    await callback.answer()


@router.callback_query(F.data == "main")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=main_kb.main)