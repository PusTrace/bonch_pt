from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.db import Database
import core.keyboards as main_kb
import services.statistics.keyboards as kb
from core.utils import format_teacher_schedule, format_own_schedule

router = Router(name="statistics")

@router.callback_query(F.data == "statistic_main")
async def statistics_main(callback: types.CallbackQuery, db: Database):
        user = await db.get_user_info(callback.message.chat.id)
        if user:
            schedule = await db.get_today_schedule(user[4])

            await callback.message.edit_text(
                text=format_teacher_schedule(schedule, "Расписание на сегодня"),
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


    await callback.message.edit_text(
        format_teacher_schedule(schedule, f"Расписание преподавателя: {teacher}"),
        reply_markup=kb.main
    )
    await callback.answer()


@router.callback_query(F.data == "statistic_week")
async def teacher_schedule(callback: types.CallbackQuery, db: Database):
    user = await db.get_user_info(callback.message.chat.id)
    
    schedule = await db.get_week_schedule(user[4])

    if not schedule:
        await callback.message.edit_text("❌ Нет расписания для этой группы.", reply_markup=kb.main)
        return

    await callback.message.edit_text(
        format_own_schedule(schedule, f"Расписание на неделю для группы: {user[4]}"),
        reply_markup=kb.main
    )
    await callback.answer()
    
    
@router.callback_query(F.data == "statistic_progress")
async def statistic_progress(callback: types.CallbackQuery):
    await callback.message.edit_text("Здесь будет прогресс бар.", reply_markup=kb.main)
    await callback.answer()
    
@router.callback_query(F.data == "statistic_add_task")
async def statistic_add_task(callback: types.CallbackQuery, db: Database):
    user = await db.get_user_info(callback.message.chat.id)
    
    await callback.message.edit_text("Здесь можно добавить лабу/задание.", reply_markup=kb.main)
    await callback.answer()

@router.callback_query(F.data == "main")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=main_kb.main)