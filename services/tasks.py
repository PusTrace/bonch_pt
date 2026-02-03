from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from core.db import Database
import core.keyboards as kb
import re, logging
from datetime import datetime

MAX_LEN = 1000
router = Router(name="tasks")

log = logging.getLogger("tasks")
# === УТИЛИТЫ ===

def create_subject_abbreviation(subject: str) -> str:
    """Создаёт аббревиатуру предмета из первых букв слов"""
    words = subject.split()
    return ''.join(word[0].upper() for word in words if word)



def create_navigation_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup | None:
    """Создаёт клавиатуру навигации по страницам"""
    if total_pages <= 1:
        return None
    
    buttons = []
    if current_page > 0:
        buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data="prev_task_page"))
    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="▶️ Далее", callback_data="next_task_page"))
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None


async def get_tasks_keyboard(chat_id: int, db: Database) -> ReplyKeyboardMarkup | None:
    """Возвращает клавиатуру со списком задач пользователя с аббревиатурами предметов"""
    user_tasks = await db.get_user_tasks(chat_id)
    if not user_tasks:
        return None
    
    buttons = [
        [KeyboardButton(text=f"[{create_subject_abbreviation(task['subject'])}] {task['task_type']}")]
        for task in user_tasks
    ]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


async def get_subjects_keyboard(chat_id: int, db: Database) -> ReplyKeyboardMarkup | None:
    """Возвращает клавиатуру с предметами пользователя"""
    user_subjects = await db.get_user_subjects(chat_id)
    if not user_subjects:
        return None
    
    buttons = [
        [KeyboardButton(text=rec['subject'])] 
        for rec in user_subjects 
        if rec['subject'] and rec['subject'].strip()
    ]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def parse_task_selection(text: str) -> tuple[str, str] | None:
    """
    Парсит выбор задачи в формате '[ABBR] task_type' и возвращает (subject_abbr, task_type).
    Возвращает None если формат неверный.
    """
    import re
    match = re.match(r'\[([^\]]+)\]\s+(.+)', text.strip())
    if match:
        return match.group(1), match.group(2)
    return None


async def find_task_by_abbr_and_type(
    chat_id: int,
    db: Database,
    subject_abbr: str,
    task_type: str
) -> dict | None:
    """Находит задачу по аббревиатуре предмета и названию задачи"""
    user_tasks = await db.get_user_tasks(chat_id)
    for task in user_tasks:
        if (create_subject_abbreviation(task['subject']) == subject_abbr.upper() 
            and task['task_type'] == task_type):
            return task
    return None


def split_tasks_into_pages(tasks: list) -> list[str]:
    """Разбивает список задач на страницы с учётом MAX_LEN"""
    pages = []
    current = ""
    
    for task in tasks:
        brigade_text = "Бригада" if task['is_brigade'] else "Одиночное"
        deadline = task['deadline'].strftime('%d.%m.%Y') if task['deadline'] else None
        task_text = (
            f"📌 {task['task_type']}\n"
            f"Предмет: {task['subject']}\n"
            f"Тип: {brigade_text}\n"
        )
        if task['descriptions']:
            task_text += f"Описание: {task['descriptions']}\n"
        if deadline:
            task_text += f"Дедлайн: {deadline}\n"
        if task['progress']:
            task_text += f"Прогресс: {task['progress']}%\n"
        task_text += f"\n"
        
        if len(current) + len(task_text) > MAX_LEN:
            pages.append(current)
            current = ""
        current += task_text
    
    if current:
        pages.append(current)
    
    return pages


async def navigate_page(callback: CallbackQuery, state: FSMContext, direction: int):
    """Общая логика навигации по страницам (direction: -1 или 1)"""
    data = await state.get_data()
    pages = data.get("task_pages", [])
    current_index = data.get("page_index", 0)
    new_index = current_index + direction
    
    if new_index < 0:
        await callback.answer("Это первая страница.", show_alert=True)
        return
    if new_index >= len(pages):
        await callback.answer("Больше страниц нет.", show_alert=True)
        return
    
    await state.update_data(page_index=new_index)
    keyboard = create_navigation_keyboard(new_index, len(pages))
    
    await callback.message.edit_text(pages[new_index], reply_markup=keyboard)
    await callback.answer()


# === ПРОСМОТР ЗАДАЧ ===

@router.message(F.text == "Показать задачи")
async def tasks_progress(message: types.Message, db: Database, state: FSMContext):
    tasks = await db.get_user_tasks(message.chat.id)
    if not tasks:
        await message.answer("у вас нет задач", reply_markup=kb.tasks)
        return
    
    pages = split_tasks_into_pages(tasks)
    await state.update_data(task_pages=pages, page_index=0)
    
    keyboard = create_navigation_keyboard(0, len(pages))
    await message.answer(pages[0], reply_markup=keyboard)


@router.callback_query(F.data == "next_task_page")
async def next_task_page(callback: CallbackQuery, state: FSMContext):
    await navigate_page(callback, state, 1)


@router.callback_query(F.data == "prev_task_page")
async def prev_task_page(callback: CallbackQuery, state: FSMContext):
    await navigate_page(callback, state, -1)

@router.message(F.text.in_({"Задачи", "Статистика"}) )
async def tasks_progress(message: types.Message, db: Database, state: FSMContext):
    tasks = await db.get_tasks_statistics(message.chat.id)
    if not tasks:
        await message.answer("У вас нет задач", reply_markup=kb.tasks)
        return

    lines = []
    for row in tasks:
        subject = row["subject"]
        done = row["done_count"]
        not_done = row["not_done_count"]
        lines.append(f"📌 {subject}\n✅ Выполнено: {done}\n❌ Не выполнено: {not_done}")

    text = "\n\n".join(lines)
    await message.answer(text, reply_markup=kb.tasks)


# === ДОБАВЛЕНИЕ ЗАДАЧИ ===

@router.message(F.text == "Добавить задачу")
async def add_task(message: types.Message, db: Database, state: FSMContext):
    subjects_kb = await get_subjects_keyboard(message.chat.id, db)
    if not subjects_kb:
        await message.answer("У вас нет предметов в расписании.", reply_markup=kb.tasks)
        return
    
    await message.answer("Выберите предмет:", reply_markup=subjects_kb)
    await state.set_state("waiting_for_subject")


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
    await message.answer(f"Предмет: {subject}\n\nВыберите тип задачи:", reply_markup=mode_kb)


@router.message(StateFilter("waiting_for_task_mode"))
async def task_mode_selected(message: types.Message, state: FSMContext):
    mode = message.text.strip()
    if mode not in ["Одиночное", "Бригада"]:
        await message.answer("Выберите из предложенных вариантов.")
        return
    
    await state.update_data(is_brigade=(mode == "Бригада"))
    await state.set_state("waiting_for_task_type")
    
    data = await state.get_data()
    await message.answer(
        f"Предмет: {data['subject']}\nТип: {mode}\n\n"
        "Введите название задания (например: ЛР №1, Курсовая):",
        reply_markup=kb.cancel_keyboard()
    )


@router.message(StateFilter("waiting_for_task_type"))
async def task_type_entered(message: types.Message, db: Database, state: FSMContext):
    task_type = message.text.strip()
    data = await state.get_data()
    
    await db.add_user_task(
        message.chat.id,
        data['subject'],
        task_type,
        data['is_brigade']
    )
    await state.clear()
    
    mode_text = "Бригада" if data['is_brigade'] else "Одиночное"
    await message.answer(
        f"✅ Задание добавлено:\n\n"
        f"Предмет: {data['subject']}\n"
        f"Тип: {mode_text}\n"
        f"Название: {task_type}",
        reply_markup=kb.tasks
    )


# === ОБНОВЛЕНИЕ ЗАДАЧ (общая логика) ===

async def start_task_update(
    message: types.Message,
    db: Database,
    state: FSMContext,
    next_state: str,
    prompt: str
):
    """Универсальная функция для начала процесса обновления задачи"""
    tasks_kb = await get_tasks_keyboard(message.chat.id, db)
    if not tasks_kb:
        await message.answer("У вас нет задач.", reply_markup=kb.tasks)
        return
    
    await message.answer(prompt, reply_markup=tasks_kb)
    await state.set_state(next_state)


async def select_task_for_update(
    message: types.Message,
    db: Database,
    state: FSMContext,
    next_state: str,
    next_prompt: str
):
    """Универсальная функция для выбора задачи и перехода к следующему шагу"""
    parsed = parse_task_selection(message.text)
    if not parsed:
        await message.answer("Неверный формат. Выберите задачу из списка выше.")
        return
    
    subject_abbr, task_type = parsed
    task = await find_task_by_abbr_and_type(message.chat.id, db, subject_abbr, task_type)
    
    if not task:
        await message.answer("Задача не найдена. Выберите из списка выше.")
        return
    
    await state.update_data(
        task_type=task['task_type'],
        subject=task['subject']
    )
    await state.set_state(next_state)
    await message.answer(
        f"Задача: [{subject_abbr}] {task_type}\n\n{next_prompt}",
        reply_markup=kb.cancel_keyboard()
    )


# === ОБНОВЛЕНИЕ ДЕДЛАЙНА ===

@router.message(F.text == "Обновить дедлайн")
async def update_deadline_start(message: types.Message, db: Database, state: FSMContext):
    await start_task_update(
        message, db, state,
        "waiting_for_deadline_task",
        "Выберите задачу для обновления дедлайна:"
    )


@router.message(StateFilter("waiting_for_deadline_task"))
async def deadline_task_selected(message: types.Message, db: Database, state: FSMContext):
    await select_task_for_update(
        message, db, state,
        "waiting_for_deadline_date",
        "Введите дедлайн в формате ДД.ММ.ГГГГ (например: 25.12.2025):"
    )


@router.message(StateFilter("waiting_for_deadline_date"))
async def deadline_date_entered(message: types.Message, db: Database, state: FSMContext):
    date_text = message.text.strip()
    data = await state.get_data()
    
    try:
        deadline = datetime.strptime(date_text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 25.12.2025)")
        return
    
    await db.update_task_deadline(
        message.chat.id, 
        data['task_type'], 
        deadline,
        data['subject']
    )
    await state.clear()
    
    abbr = create_subject_abbreviation(data['subject'])
    await message.answer(
        f"✅ Дедлайн обновлён:\n\n"
        f"Задача: [{abbr}] {data['task_type']}\n"
        f"Дедлайн: {deadline.strftime('%d.%m.%Y')}",
        reply_markup=kb.tasks
    )


# === ОБНОВЛЕНИЕ ОПИСАНИЯ ===

@router.message(F.text == "Обновить описание")
async def update_description_start(message: types.Message, db: Database, state: FSMContext):
    await start_task_update(
        message, db, state,
        "waiting_for_description_task",
        "Выберите задачу для обновления описания:"
    )


@router.message(StateFilter("waiting_for_description_task"))
async def description_task_selected(message: types.Message, db: Database, state: FSMContext):
    await select_task_for_update(
        message, db, state,
        "waiting_for_description_text",
        "Введите новое описание:"
    )


@router.message(StateFilter("waiting_for_description_text"))
async def description_text_entered(message: types.Message, db: Database, state: FSMContext):
    description = message.text.strip()
    data = await state.get_data()
    
    await db.update_task_description(
        message.chat.id, 
        data['task_type'], 
        description,
        data['subject']
    )
    await state.clear()
    
    abbr = create_subject_abbreviation(data['subject'])
    await message.answer(
        f"✅ Описание обновлено:\n\n"
        f"Задача: [{abbr}] {data['task_type']}\n"
        f"Описание: {description}",
        reply_markup=kb.tasks
    )


# === ОБНОВЛЕНИЕ ПРОГРЕССА ===

@router.message(F.text == "Обновить прогресс")
async def update_progress_start(message: types.Message, db: Database, state: FSMContext):
    await start_task_update(
        message, db, state,
        "waiting_for_progress_task",
        "Выберите задачу для обновления процента:"
    )


@router.message(StateFilter("waiting_for_progress_task"))
async def progress_task_selected(message: types.Message, db: Database, state: FSMContext):
    await select_task_for_update(
        message, db, state,
        "waiting_for_progress_text",
        "Введите процент выполнения (0-100):"
    )


@router.message(StateFilter("waiting_for_progress_text"))
async def progress_text_entered(message: types.Message, db: Database, state: FSMContext):
    progress = message.text.strip()
    data = await state.get_data()
    
    try:
        progress_int = int(progress)
        if not 0 <= progress_int <= 100:
            raise ValueError
    except ValueError:
        await message.answer("Введите число от 0 до 100")
        return
    
    await db.update_task_progress(
        message.chat.id, 
        data['task_type'], 
        progress_int,
        data['subject']
    )
    await state.clear()
    
    abbr = create_subject_abbreviation(data['subject'])
    await message.answer(
        f"✅ Прогресс обновлен:\n\n"
        f"Задача: [{abbr}] {data['task_type']}\n"
        f"Прогресс: {progress_int}%",
        reply_markup=kb.tasks
    )


# === УДАЛЕНИЕ ЗАДАЧИ ===

@router.message(F.text == "Удалить задачу")
async def delete_task_start(message: types.Message, db: Database, state: FSMContext):
    await start_task_update(
        message, db, state,
        "waiting_for_delete_task",
        "Выберите задачу для удаления:"
    )


@router.message(StateFilter("waiting_for_delete_task"))
async def delete_task_confirm(message: types.Message, db: Database, state: FSMContext):
    parsed = parse_task_selection(message.text)
    if not parsed:
        await message.answer("Неверный формат. Выберите задачу из списка выше.")
        return
    
    subject_abbr, task_type = parsed
    task = await find_task_by_abbr_and_type(message.chat.id, db, subject_abbr, task_type)
    
    if not task:
        await message.answer("Задача не найдена. Выберите из списка выше.")
        return
    
    await db.delete_user_task(message.chat.id, task_type, task['subject'])
    await state.clear()
    
    await message.answer(
        f"✅ Задача удалена:\n\n[{subject_abbr}] {task_type}",
        reply_markup=kb.tasks
    )


# === МАССОВОЕ СОЗДАНИЕ ЗАДАЧ ===

@router.message(Command("create_task_pack"))
async def create_task_pack(message: types.Message, db: Database):
    text = message.text.replace("/create_task_pack", "").strip()
    parts = text.split(maxsplit=2)
    
    if len(parts) != 3:
        await message.answer("Формат: /create_task_pack лаба[1,9] True|False предмет")
        return
    
    title_part, is_brigade_raw, subject = parts
    
    match = re.match(r"(.+)\[(\d+)[,-](\d+)\]", title_part)
    if not match:
        await message.answer("Ошибка формата. Пример: лаба[1,9] или лаба[1-9]")
        return
    
    base_title = match.group(1)
    start = int(match.group(2))
    end = int(match.group(3))
    
    if is_brigade_raw not in ("True", "False"):
        await message.answer("Второй аргумент должен быть True или False")
        return
    
    is_brigade = is_brigade_raw.lower() == "true"
    tasks = [
        (message.chat.id, f"{base_title} {i}", subject, is_brigade)
        for i in range(start, end + 1)
    ]
    
    await db.create_task_pack(tasks)
    await message.answer(f"✅ Создано задач: {len(tasks)}")
    
# === автопланирование ===
    
@router.message(F.text == "Автопланирование")
async def turn_auto_schedule(message: types.Message):
    """Запрос подтверждения для автопланирования"""
    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, запустить", callback_data="auto_schedule_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="auto_schedule_cancel")
            ]
        ]
    )
    
    await message.answer(
        "⚠️ <b>Автопланирование</b>\n\n"
        "Эта функция полностью распределит все ваши задачи по парам. Включая расписание бригады\n\n"
        "Вы уверены?",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "auto_schedule_confirm")
async def auto_schedule_confirmed(callback: CallbackQuery, db: Database):
    """Запуск автопланирования после подтверждения"""
    await callback.message.edit_text("⏳ Запускаю автопланирование...")
    
    try:
        user = await db.get_user_info(callback.message.chat.id)
        schedule = await calc_auto_schedule(user, db)  # ДОБАВИЛ db
        
        if not schedule:
            await callback.message.edit_text(
                "❌ Не удалось создать расписание.\n"
                "Проверьте, что у вас есть задачи и расписание пар."
            )
            await callback.answer()
            return
        
        await db.update_tasks(schedule)
        
        await callback.message.edit_text(
            "✅ <b>Автопланирование завершено!</b>\n\n"
            f"📊 Распланировано задач: <b>{len(schedule)}</b>\n\n"
            "Проверьте расписание или таски в меню задач.",
            parse_mode="HTML"
        )
        await callback.answer("✅ Готово!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при автопланировании:\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "auto_schedule_cancel")
async def auto_schedule_cancelled(callback: CallbackQuery):
    """Отмена автопланирования"""
    await callback.message.edit_text("❌ Автопланирование отменено.")
    await callback.answer()

async def calc_auto_schedule(user: dict, db: Database) -> list:
    """
    1 пара (lesson) = 1 задача
    В БД пишем только date, но внутри считаем по lesson.id
    """

    chat_id = user[1]
    sect = user[4]

    all_tasks = await db.get_user_tasks(chat_id)
    schedule = await db.get_schedule(sect)

    if not all_tasks:
        log.info(f"У пользователя {chat_id} нет задач")
        return []

    if not schedule:
        log.info(f"Для секции {sect} нет будущих пар")
        return []

    # subject -> [lesson, lesson, ...]
    schedule_by_subject = {}
    for lesson in schedule:
        subject = lesson["subject"]
        schedule_by_subject.setdefault(subject, []).append(lesson)

    # сортируем по дате и номеру пары
    for subject in schedule_by_subject:
        schedule_by_subject[subject].sort(key=lambda x: (x["date"], x["pair"]))

    log.info(f"Всего задач: {len(all_tasks)}, предметов с парами: {len(schedule_by_subject)}")

    # занятые СЛОТЫ (пары), а не дни
    occupied_lessons = set()  # lesson.id

    # если задача уже имеет дедлайн — считаем, что она заняла одну пару
    # (привязываем к первой подходящей паре этого предмета)
    for task in all_tasks:
        if task["deadline"]:
            subj = task["subject"]
            if subj in schedule_by_subject and schedule_by_subject[subj]:
                lesson = schedule_by_subject[subj].pop(0)
                occupied_lessons.add(lesson["id"])
                log.info(f"🔒 Занята пара {lesson['date']} {lesson['pair']}")

    updates = []

    for task in all_tasks:
        task_subject = task["subject"]
        task_type = task["task_type"]
        task_chat_id = task["chat_id"]
        is_brigade = task["is_brigade"]
        current_deadline = task["deadline"]

        if task_subject not in schedule_by_subject:
            log.info(f"⚠️ Нет пар для '{task_subject}' (задача: {task_type})")
            continue

        deadline = None

        for lesson in schedule_by_subject[task_subject]:
            if lesson["id"] not in occupied_lessons:
                occupied_lessons.add(lesson["id"])
                deadline = lesson["date"]   # В БД пишем ТОЛЬКО ДАТУ
                break

        if deadline is None:
            log.info(f"❌ Все пары заняты для '{task_subject}' (задача: {task_type})")
            continue

        updates.append({
            "chat_id": task_chat_id,
            "task_type": task_type,
            "subject": task_subject,
            "deadline": deadline,  # только date
        })

        brigade_marker = "🔧" if is_brigade else "👤"
        status = "📅" if current_deadline else "🆕"
        log.info(f"{status}{brigade_marker} {task_subject} | {task_type} → {deadline}")

    log.info(f"Готово к обновлению: {len(updates)}/{len(all_tasks)} задач")
    return updates
