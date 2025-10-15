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
    chat_id = callback.message.chat.id
    thread_id = getattr(callback.message, "message_thread_id", None)

    saved = await db.get_service_topic("queue")

    # Если запрос вернул список — берём первую запись
    if isinstance(saved, list):
        if len(saved) == 0:
            saved = None  # пустой список — значит, ничего нет
        else:
            saved = saved[0]

    if thread_id is not None:
        if saved is None:
            # первый вызов — сохраняем топик
            await db.set_service_topic("queue", chat_id, thread_id)
            await callback.message.answer("Сервис закреплён за этим топиком ✅")
        else:
            saved_thread_id = saved["thread_id"]
            if saved_thread_id != thread_id:
                await callback.answer("⚠️ Этот сервис уже закреплён за другим топиком.", show_alert=True)
                return

        # Отправляем сообщение в нужный топик
        await callback.bot.send_message(
            chat_id=chat_id,
            text="Панель управления очередью:",
            reply_markup=kb.main,
            message_thread_id=thread_id
        )
    else:
        await callback.message.answer("Панель управления очередью:", reply_markup=kb.kb_inline)

    await callback.answer()

    
    
# callback хендлер
@router.callback_query(F.data.startswith("queue_"))
async def handle_queue_callback(callback: types.CallbackQuery, db: Database):
    thread_id = callback.message.message_thread_id
    if callback.data == "queue_today":
        date = datetime.now().date()
    else:
        date = datetime.now().date() + timedelta(days=1)
    
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
    await callback.message.answer("Чтобы занять очередь, введите команду: /take_a_place <Абривиатура предмета> <номер бригады> \n"
                         "Пример: /take_a_place ОМВКС 31\n"
                         "Обратите внимание, что вы можете занять очередь только на ближайшие 2 дня.\n",)
    

@router.message(Command("take_a_place"))
async def take_a_place(message: types.Message, db: Database):
    text = message.text or ""
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Неверный формат. Используйте: /take_a_place <Абревиатура> <номер бригады>")
        return

    _, subject, brigade_number = parts

    try:
        brigade_number = int(brigade_number)
    except ValueError:
        await message.answer("⚠️ Номер бригады должен быть числом!")
        return

    success = await db.take_a_place(message.from_user.id, subject, brigade_number)
    if success:
        await message.answer("✅ Место успешно занято!", reply_markup=kb.main)
    else:
        await message.answer("⚠️ Не удалось занять место. Возможно, вы уже записаны.", reply_markup=kb.main)
