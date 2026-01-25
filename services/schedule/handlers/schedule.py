# schedule.py
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from core.db import Database
import services.schedule.keyboards as kb
from core.utils import format_teacher_schedule, format_own_schedule

router = Router(name="schedule")

@router.message(F.text == "Расписание 📊")
async def schedule_main(message: types.Message, db: Database):
    user = await db.get_user_info(message.chat.id)
    if user:
        schedule = await db.get_today_schedule(user[4])
        await message.answer(
            text=format_own_schedule(schedule, "Расписание на сегодня"),
            reply_markup=kb.main
        )

@router.message(F.text == "Показать расписание преподавателей")
async def schedule_teachers(message: types.Message, db: Database, state: FSMContext):
    user = await db.get_user_info(message.chat.id)
    if not user:
        await message.answer("Ошибка доступа")
        return
    
    teachers_records = await db.get_distinct_teachers()
    buttons = [
        [KeyboardButton(text=rec['teacher'])]
        for rec in teachers_records
        if rec['teacher'] and rec['teacher'].strip()
    ]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    teachers_kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer("👨‍🏫 Выберите преподавателя:", reply_markup=teachers_kb)
    await state.set_state("waiting_for_teacher")

@router.message(StateFilter("waiting_for_teacher"))
async def teacher_schedule(message: types.Message, db: Database, state: FSMContext):
    teacher = message.text.strip()
    
    teachers_records = await db.get_distinct_teachers()
    valid_teachers = [rec['teacher'] for rec in teachers_records if rec['teacher'] and rec['teacher'].strip()]
    
    if teacher not in valid_teachers:
        await message.answer("Неверный преподаватель. Выберите из списка выше.")
        return
    
    await state.clear()
    schedule = await db.get_teacher_schedule(teacher)
    
    if not schedule:
        await message.answer("❌ Нет расписания для этого преподавателя.", reply_markup=kb.main)
        return
    
    await message.answer(
        format_teacher_schedule(schedule, f"Расписание преподавателя: {teacher}"),
        reply_markup=kb.main
    )

@router.message(F.text == "Показать расписание на неделю")
async def week_schedule(message: types.Message, db: Database):
    user = await db.get_user_info(message.chat.id)
    schedule = await db.get_week_schedule(user[4])
    
    if not schedule:
        await message.answer("❌ Нет расписания для этой группы.", reply_markup=kb.main)
        return
    
    await message.answer(
        format_own_schedule(schedule, f"Расписание на неделю для группы: {user[4]}"),
        reply_markup=kb.main
    )
