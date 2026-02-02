from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta


from core.db import Database
from core.states import QueueStates
import core.keyboards as main_kb
import services.queue.keyboards as kb
import core.keyboards as core_kb

router = Router(name="queue")
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

@router.callback_query(F.data == "queue_main")
async def queue_main(callback: types.CallbackQuery, db: Database):
    
    thread_id = callback.message.message_thread_id
    date = datetime.now().date()
    
    queue = await db.get_queue(date)
    text_lines = ["📋 Очередь на сегодня:\n"]
    for record in queue:
        text_lines.append(f"{record['id']:>2} | Бригада {record['brigade_number']:>2} | {record['subject']:<35}")

    await callback.message.edit_text(
        text="\n".join(text_lines),
        reply_markup=kb.main
    )

    await callback.answer()

    

# 1️⃣ Пользователь нажимает кнопку "Выбрать дату"
@router.callback_query(F.data == "queue_custom_date")
async def choose_date(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите дату в формате ДД-ММ:")
    await state.set_state(QueueStates.waiting_for_date)

# 2️⃣ Пользователь присылает текстовое сообщение с датой
@router.message(QueueStates.waiting_for_date)
async def process_custom_date(message: types.Message, state: FSMContext, db: Database):
    date_str = message.text.strip()
    try:
        # используем текущий год, так как пользователь вводит только день и месяц
        date = datetime.strptime(f"{date_str}-{datetime.now().year}", "%d-%m-%Y").date()
    except ValueError:
        await message.answer("⚠️ Неверный формат даты. Используйте ДД-ММ")
        return

    queue = await db.get_queue(date)
    if not queue:
        await message.answer(f"Очередь на {date.strftime('%d-%m')} пуста.")
    else:
        text_lines = ["📋 Очередь:\n"]
        for record in queue:
            text_lines.append(f"{record['id']:>2} | Бригада {record['brigade_number']:>2} | {record['subject']:<35}")
        await message.answer("\n".join(text_lines), reply_markup=kb.main)

    await state.clear()  # сбрасываем состояние



# 1️⃣ Выбор предмета
@router.callback_query(F.data == "take_queue")
async def choose_subject(callback: types.CallbackQuery, state: FSMContext, db: Database):
    user_id = callback.from_user.id

    # проверяем, есть ли у пользователя сохранённая бригада
    user_brigade = await db.get_user_brigade(user_id)

    await state.update_data(user_brigade=user_brigade)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=name, callback_data=f"subject_{abbr}")] for abbr, name in ABBR.items()]
    )
    await callback.message.edit_text("Выберите предмет:", reply_markup=keyboard)
    await state.set_state(QueueStates.waiting_for_subject)


# 2️⃣ Выбор бригады
@router.callback_query(F.data.startswith("subject_"))
async def choose_brigade(callback: types.CallbackQuery, state: FSMContext, db: Database):
    subject_abbr = callback.data[len("subject_"):]
    await state.update_data(subject=subject_abbr)

    data = await state.get_data()
    user_brigade = data.get("user_brigade")

    # если бригада уже есть — пропускаем выбор
    if user_brigade:
        sect = "ИКБ-31"
        success = await db.take_a_place(sect, subject_abbr, user_brigade)
        if success:
            await callback.answer("✅ Место успешно занято!", show_alert=True)
        else:
            await callback.answer("⚠️ Не удалось занять место.", show_alert=True)
        return

    # иначе — показываем выбор бригады
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"Бригада {b}", callback_data=f"brigade_{b}")] for b in range(1, 16)]
    )
    await callback.message.edit_text(f"Выберите бригаду для {ABBR[subject_abbr]}:", reply_markup=keyboard)
    await state.set_state(QueueStates.waiting_for_brigade)


# 3️⃣ Занятие места
@router.callback_query(F.data.startswith("brigade_"))
async def take_place(callback: types.CallbackQuery, state: FSMContext, db: Database):
    brigade = int(callback.data[len("brigade_"):])
    data = await state.get_data()
    subject = data.get("subject")
    sect = "ИКБ-31"  # можно брать динамически, если нужно

    success = await db.take_a_place(sect, subject, brigade)
    if success:
        await callback.answer("✅ Место успешно занято!", show_alert=True)
    else:
        await callback.answer("⚠️ Не удалось занять место.", show_alert=True)



@router.callback_query(F.data == "how_to_queue")
async def how_to_queue(callback: types.CallbackQuery):
    await callback.message.edit_text(text="Чтобы занять очередь, введите команду: /take_a_place <Абревиатура предмета> <номер бригады>(только 1 раз) Пример: /take_a_place ОМВКС 31\n Обратите внимание, что вы можете занять очередь только на ближайшие 3 дня.\n", reply_markup=kb.main)
    await callback.answer()

@router.callback_query(F.data == "abbreviations")
async def abbreviations(callback: types.CallbackQuery):
    await callback.message.edit_text(text="Абревиатуры предметов:\n\n"
        "1. ASTRA - Безопасность Astra-Linux\n"
        "2. ББЛС - Безопасность беспроводных локальных сетей\n"
        "3. ЗОССУ - Защита операционных систем сетевых устройств\n"
        "4. ЗПИД - Защита программ и данных\n"
        "5. МИСКЗИ - Методы и средства криптографической защиты информации\n"
        "6. ОМВКС - Основы маршрутизации в компьютерных сетях\n"
        "7. ПАСЗИ - Программно-аппаратные средства защиты информации\n"
        "8. ОИПОИБ - Организационное и правовое обеспечение информационной безопасности\n", reply_markup=kb.main
    )

@router.message(Command("take_a_place"))
async def take_a_place(message: types.Message, db: Database):
    # Получаем профиль пользователя (в твоём коде get_user_info возвращает tuple/list)
    user_info = await db.get_user_info(message.from_user.id)
    # Берём sect и сохранённую бригаду (проверь индексы в своей реализации)
    sect = user_info[4] if user_info else None
    saved_brigade = user_info[6] if user_info else None

    text = message.text or ""
    # Разбираем команду: /take_a_place <subject> [<brigade>]
    # maxsplit=2 — гарантирует, что предмет = parts[1], а третьим может быть бригада (если есть)
    parts = text.split(maxsplit=2)

    # Если пользователь написал только /take_a_place
    if len(parts) < 2:
        await message.answer("⚠️ Неверный формат. Используйте:\n"
                             "/take_a_place <Абревиатура предмета> [номер бригады]\n\n"
                             "Примеры:\n"
                             "/take_a_place ASTRA 2\n"
                             "/take_a_place ASTRA")
        return

    # subject — всегда берём из аргументов
    _, subject = parts[0:2]
    subject = subject.strip().upper()

    # Если пользователь явно указал бригаду — используем её (и сохраним)
    brigade_to_use = None
    if len(parts) >= 3 and parts[2].strip() != "":
        # Попробуем распарсить третий аргумент как число
        try:
            brigade_to_use = int(parts[2].strip())
            # Сохраняем бригаду в профиле (удобство) — можно только сохранять при успехе.
        except ValueError:
            await message.answer("⚠️ Номер бригады должен быть числом. Например: /take_a_place ASTRA 2")
            return
    else:
        # Если не указали, пробуем взять из профиля
        if saved_brigade is not None:
            brigade_to_use = int(saved_brigade)

    # Если бригада всё ещё не определена — просим пользователя указать её отдельно
    if brigade_to_use is None:
        await message.answer("У вас не сохранена бригада. Укажите бригаду в команде:\n"
                             "/take_a_place <Абривиатура предмета> <номер бригады>\n\n"
                             "Пример: /take_a_place ASTRA 2")
        return

    # Теперь вызываем db.take_a_place с секцией, предметом и бригадой
    try:
        success = await db.take_a_place(sect, subject, brigade_to_use)
    except Exception as e:
        # Логируем и аккуратно сообщаем пользователю
        # (в продакшене лучше логировать в файл/систему логов)
        await message.answer("Произошла ошибка при записи в базу. Попробуйте позже.")
        print("take_a_place error:", e)
        return

    if success:
        # Сохраняем бригаду в профиле — если пользователь явно указал, или если ещё не было
        await db.save_brigade(brigade_to_use, message.from_user.id)
        await message.answer("✅ Место успешно занято!", reply_markup=kb.main)
    else:
        await message.answer("⚠️ Не удалось занять место. Возможно, вы уже записаны или нет пары в ближайшие дни.", reply_markup=kb.main)


@router.callback_query(F.data == "main")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=main_kb.main)