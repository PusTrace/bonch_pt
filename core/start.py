from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext


from core.db import Database
from core.states import RegistrationStates
import core.keyboards as kb
import services.keyboards as service_kb
start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, db: Database):
        user = await db.get_user_info(message.chat.id)
        if user:
            schedule = await db.get_today_schedule(user[4])
            text_lines = ["📋 Расписание на сегодня:\n"]
            for date, pair, subject, auditorium, teacher, lesson_type in schedule:
                text_lines.append(f"{pair:>2}. {subject:<35} | {auditorium:>16} | {teacher:<20} | {lesson_type:<15}")
            await message.answer("\n".join(text_lines), reply_markup=kb.main)
        else:
            await message.answer("Привет! 👋 Похоже, вы здесь впервые.\n\nВведите вашу группу (например: ИКБ-31):")
            await state.set_state(RegistrationStates.waiting_for_group)


@start_router.message(RegistrationStates.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext, db: Database):
    group = message.text.strip().upper()
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id != user_id:
        await db.add_user(
            message.chat.id,
            message.chat.username,
            message.chat.full_name,
            group
        )

        await state.clear()
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=f"Отлично! Группа '{group}' сохранена ✅",
            reply_markup=kb.main,
            message_thread_id=message.message_thread_id
        )
    else:
        await db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            group
        )

        await state.clear()
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=f"Отлично! Группа '{group}' сохранена ✅",
            reply_markup=kb.main,
            message_thread_id=message.message_thread_id
        )

@start_router.callback_query(F.data == 'other')
async def other(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=service_kb.main)

@start_router.callback_query(F.data == 'became_developer')
async def became_developer(callback: types.CallbackQuery, db: Database):
    await callback.message.answer("Чтобы стать разработчиком, выполните следующие шаги:\n"
                                   "1) Прочитайте README проекта. github.com/PusTrace/bonch_pt\n"
                                   "2) Напишите: t.me/PusTrace.")
    user = await db.get_user_info(callback.message.chat.id)
    schedule = await db.get_today_schedule(user[4])
    text_lines = ["📋 Расписание на сегодня:\n"]
    for date, pair, subject, auditorium, teacher, lesson_type in schedule:
        text_lines.append(f"{pair:>2}. {subject:<35} | {auditorium:>16} | {teacher:<20} | {lesson_type:<15}")
    await callback.message.answer("\n".join(text_lines), reply_markup=kb.main)