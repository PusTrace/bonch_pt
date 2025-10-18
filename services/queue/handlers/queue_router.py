from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta


from core.db import Database
import services.queue.keyboards as kb
import core.keyboards as core_kb

router = Router(name="queue")


@router.callback_query(F.data == "queue_main")
async def queue_main(callback: types.CallbackQuery, db: Database):
    await callback.message.edit_reply_markup(reply_markup=kb.main)

    await callback.answer()

    
    
# callback хендлер
@router.callback_query(F.data.startswith("queue_"))
async def handle_queue_callback(callback: types.CallbackQuery, db: Database):
    thread_id = callback.message.message_thread_id
    if callback.data == "queue_today":
        date = datetime.now().date()
    elif callback.data == "queue_tomorrow":
        date = datetime.now().date() + timedelta(days=1)
    elif callback.data == "queue_day_after_tomorrow":
        date = datetime.now().date() + timedelta(days=2)
    
    queue = await db.get_queue(date)
    text_lines = ["📋 Очередь:\n"]
    for record in queue:
        text_lines.append(f"{record['id']:>2} | Бригада {record['brigade_number']:>2} | {record['subject']:<35}")
    
    await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        text="\n".join(text_lines),
        message_thread_id=thread_id
    )
    await callback.answer()  # закрывает спиннер на кнопке


@router.callback_query(F.data == "how_to_queue")
async def how_to_queue(callback: types.CallbackQuery):
    await callback.message.bot.send_message(chat_id=callback.message.chat.id, text="Чтобы занять очередь, введите команду: /take_a_place <Абревиатура предмета> <номер бригады>(только 1 раз) Пример: /take_a_place ОМВКС 31\n Обратите внимание, что вы можете занять очередь только на ближайшие 3 дня.\n")
    await callback.answer()

@router.callback_query(F.data == "abbreviations")
async def abbreviations(callback: types.CallbackQuery):
    await callback.message.bot.send_message(chat_id=callback.message.chat.id, text="Абревиатуры предметов:\n\n"
        "1. ASTRA - Безопасность Astra-Linux\n"
        "2. ББЛС - Безопасность беспроводных локальных сетей\n"
        "3. ЗОССУ - Защита операционных систем сетевых устройств\n"
        "4. ЗПИД - Защита программ и данных\n"
        "5. МИСКЗИ - Методы и средства криптографической защиты информации\n"
        "6. ОМВКС - Основы маршрутизации в компьютерных сетях\n"
        "7. ПАСЗИ - Программно-аппаратные средства защиты информации\n"
        "8. ОИПОИБ - Организационное и правовое обеспечение информационной безопасности\n"
    )

@router.message(Command("take_a_place"))
async def take_a_place(message: types.Message, db: Database):
    user_info = await db.get_user_info(message.from_user.id)
    sect = user_info[4]
    brigade = user_info[6]
    if brigade is None:
        text = message.text or ""
        parts = text.split()
        if len(parts) < 3:
            await message.answer("⚠️ Неверный формат. /take_a_place <Абревиатура предмета> <номер бригады>")
            return
        
        _, subject, brigade = parts

        try:
            brigade = int(brigade)
        except ValueError:
            await message.answer("⚠️ Номер бригады должен быть числом!")
            return

        success = await db.take_a_place(sect, subject, brigade)
        if success:
            await message.answer("✅ Место успешно занято!", reply_markup=kb.main)
        else:
            await message.answer("⚠️ Не удалось занять место. Возможно, вы уже записаны.", reply_markup=kb.main)
        await db.save_brigade(brigade, message.from_user.id)
        return
    else:
        text = message.text or ""
        parts = text.split()
        if len(parts) < 2:
            await message.answer("⚠️ Неверный формат. /take_a_place <Абревиатура предмета>")
            return

        _, subject = parts

        success = await db.take_a_place(sect, subject, brigade)
        if success:
            await message.answer("✅ Место успешно занято!", reply_markup=kb.main)
        else:
            await message.answer("⚠️ Не удалось занять место.", reply_markup=kb.main)
