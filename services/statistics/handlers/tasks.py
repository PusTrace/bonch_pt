from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from core.db import Database
import services.statistics.keyboards as kb

router = Router(name="statistics")

@router.callback_query(F.data == "tasks")
async def tasks_menu(callback: types.CallbackQuery):
    await callback.message.answer(
        text="📋 Меню задач:",
        reply_markup=kb.tasks
    )
    await callback.answer()

@router.message(F.text == "Показать задачи")
async def tasks_progress(message: types.Message, db: Database):
    tasks = await db.get_user_tasks(message.chat.id)
    if not tasks:
        return "У вас нет добавленных задач."
    result = "Ваши задачи:\n\n"
    for task in tasks:
        brigade_text = "Бригада" if task['is_brigade'] else "Одиночное"
        result += f"Предмет: {task['subject']}\nТип: {brigade_text}\nНазвание: {task['task_type']}\nОписание: {task['descriptions']}\nДедлайн: {task['deadline']}\n\n"
    await message.answer(result, reply_markup=kb.tasks)
@router.message(F.text == "Добавить задачу")
async def add_task(message: types.Message, db: Database, state: FSMContext):
    user_subjects = await db.get_user_subjects(message.chat.id)
    
    if not user_subjects:
        await message.answer("У вас нет предметов в расписании.", reply_markup=kb.tasks)
        return
    
    buttons = [[KeyboardButton(text=rec['subject'])] for rec in user_subjects if rec['subject'] and rec['subject'].strip()]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    subjects_kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer("Выберите предмет:", reply_markup=subjects_kb)
    await state.set_state("waiting_for_subject")

@router.message(F.text == "❌ Отмена", StateFilter("waiting_for_subject", "waiting_for_task_mode", "waiting_for_task_type"))
async def cancel_task(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=kb.tasks)

@router.message(StateFilter("waiting_for_subject"))
async def subject_selected(message: types.Message, db: Database, state: FSMContext):
    subject = message.text.strip()
    
    user_subjects = await db.get_user_subjects(message.chat.id)
    valid_subjects = [rec['subject'] for rec in user_subjects if rec['subject'] and rec['subject'].strip()]
    
    if subject not in valid_subjects:
        await message.answer("Неверный предмет. Выберите из списка выше.")
        return
    
    await state.update_data(subject=subject)
    await state.set_state("waiting_for_task_mode")
    
    mode_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Одиночное"), KeyboardButton(text="Бригада")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Предмет: {subject}\n\nВыберите тип задачи:",
        reply_markup=mode_kb
    )

@router.message(StateFilter("waiting_for_task_mode"))
async def task_mode_selected(message: types.Message, state: FSMContext):
    mode = message.text.strip()
    
    if mode not in ["Одиночное", "Бригада"]:
        await message.answer("Выберите из предложенных вариантов.")
        return
    
    await state.update_data(is_brigade=(mode == "Бригада"))
    await state.set_state("waiting_for_task_type")
    
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    
    data = await state.get_data()
    subject = data.get("subject")
    
    await message.answer(
        f"Предмет: {subject}\nТип: {mode}\n\nВведите название задания (например: ЛР №1, Курсовая):",
        reply_markup=cancel_kb
    )

@router.message(StateFilter("waiting_for_task_type"))
async def task_type_entered(message: types.Message, db: Database, state: FSMContext):
    task_type = message.text.strip()
    data = await state.get_data()
    subject = data.get("subject")
    is_brigade = data.get("is_brigade")
    
    await db.add_user_task(message.chat.id, subject, task_type, is_brigade)
    
    await state.clear()
    
    mode_text = "Бригада" if is_brigade else "Одиночное"
    await message.answer(
        f"✅ Задание добавлено:\n\nПредмет: {subject}\nТип: {mode_text}\nНазвание: {task_type}",
        reply_markup=kb.tasks
    )
    
    
@router.message(F.text == "Обновить дедлайн")
async def update_deadline_start(message: types.Message, db: Database, state: FSMContext):
    user_tasks = await db.get_user_tasks(message.chat.id)
    
    if not user_tasks:
        await message.answer("У вас нет задач.", reply_markup=kb.tasks)
        return
    
    buttons = [[KeyboardButton(text=task['task_type'])] for task in user_tasks]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    tasks_kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer("Выберите задачу для обновления дедлайна:", reply_markup=tasks_kb)
    await state.set_state("waiting_for_deadline_task")

@router.message(F.text == "❌ Отмена", StateFilter("waiting_for_deadline_task", "waiting_for_deadline_date"))
async def cancel_deadline(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=kb.tasks)

@router.message(StateFilter("waiting_for_deadline_task"))
async def deadline_task_selected(message: types.Message, db: Database, state: FSMContext):
    task_type = message.text.strip()
    
    user_tasks = await db.get_user_tasks(message.chat.id)
    valid_tasks = [task['task_type'] for task in user_tasks]
    
    if task_type not in valid_tasks:
        await message.answer("Неверная задача. Выберите из списка выше.")
        return
    
    await state.update_data(task_type=task_type)
    await state.set_state("waiting_for_deadline_date")
    
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Задача: {task_type}\n\nВведите дедлайн в формате ДД.ММ.ГГГГ (например: 25.12.2025):",
        reply_markup=cancel_kb
    )

@router.message(StateFilter("waiting_for_deadline_date"))
async def deadline_date_entered(message: types.Message, db: Database, state: FSMContext):
    from datetime import datetime
    
    date_text = message.text.strip()
    data = await state.get_data()
    task_type = data.get("task_type")
    
    # Парсим дату
    try:
        deadline = datetime.strptime(date_text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 25.12.2025)")
        return
    
    await db.update_task_deadline(message.chat.id, task_type, deadline)
    
    await state.clear()
    await message.answer(
        f"✅ Дедлайн обновлён:\n\nЗадача: {task_type}\nДедлайн: {deadline.strftime('%d.%m.%Y')}",
        reply_markup=kb.tasks
    )

@router.message(F.text == "Обновить описание")
async def update_description_start(message: types.Message, db: Database, state: FSMContext):
    user_tasks = await db.get_user_tasks(message.chat.id)
    
    if not user_tasks:
        await message.answer("У вас нет задач.", reply_markup=kb.tasks)
        return
    
    buttons = [[KeyboardButton(text=task['task_type'])] for task in user_tasks]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    tasks_kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer("Выберите задачу для обновления описания:", reply_markup=tasks_kb)
    await state.set_state("waiting_for_description_task")

@router.message(F.text == "❌ Отмена", StateFilter("waiting_for_description_task", "waiting_for_description_text"))
async def cancel_description(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=kb.tasks)

@router.message(StateFilter("waiting_for_description_task"))
async def description_task_selected(message: types.Message, db: Database, state: FSMContext):
    task_type = message.text.strip()
    
    user_tasks = await db.get_user_tasks(message.chat.id)
    valid_tasks = [task['task_type'] for task in user_tasks]
    
    if task_type not in valid_tasks:
        await message.answer("Неверная задача. Выберите из списка выше.")
        return
    
    await state.update_data(task_type=task_type)
    await state.set_state("waiting_for_description_text")
    
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Задача: {task_type}\n\nВведите новое описание:",
        reply_markup=cancel_kb
    )

@router.message(StateFilter("waiting_for_description_text"))
async def description_text_entered(message: types.Message, db: Database, state: FSMContext):
    description = message.text.strip()
    data = await state.get_data()
    task_type = data.get("task_type")
    
    await db.update_task_description(message.chat.id, task_type, description)
    
    await state.clear()
    await message.answer(
        f"✅ Описание обновлено:\n\nЗадача: {task_type}\nОписание: {description}",
        reply_markup=kb.tasks
    )
    
    
    
@router.message(F.text == "Обновить описание")
async def update_progress_start(message: types.Message, db: Database, state: FSMContext):
    user_tasks = await db.get_user_tasks(message.chat.id)
    
    if not user_tasks:
        await message.answer("У вас нет задач.", reply_markup=kb.tasks)
        return
    
    buttons = [[KeyboardButton(text=task['task_type'])] for task in user_tasks]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    tasks_kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer("Выберите задачу для обновления процента:", reply_markup=tasks_kb)
    await state.set_state("waiting_for_progress_task")

@router.message(F.text == "❌ Отмена", StateFilter("waiting_for_progress_task", "waiting_for_progress_text"))
async def cancel_description(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=kb.tasks)

@router.message(StateFilter("waiting_for_progress_task"))
async def progress_task_selected(message: types.Message, db: Database, state: FSMContext):
    task_type = message.text.strip()
    
    user_tasks = await db.get_user_tasks(message.chat.id)
    valid_tasks = [task['task_type'] for task in user_tasks]
    
    if task_type not in valid_tasks:
        await message.answer("Неверная задача. Выберите из списка выше.")
        return
    
    await state.update_data(task_type=task_type)
    await state.set_state("waiting_for_progress_text")
    
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Задача: {task_type}\n\nВведите новое значение прогресса:",
        reply_markup=cancel_kb
    )

@router.message(StateFilter("waiting_for_progress_text"))
async def progress_text_entered(message: types.Message, db: Database, state: FSMContext):
    progress = message.text.strip()
    data = await state.get_data()
    task_type = data.get("task_type")
    
    await db.update_task_progress(message.chat.id, task_type, progress)
    
    await state.clear()
    await message.answer(
        f"✅ Прогресс обновлен:\n\nЗадача: {task_type}\nПрогресс: {progress}",
        reply_markup=kb.tasks
    )