from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext


from core.db import Database
from core.states import RegistrationStates
import core.keyboards as kb
start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, db: Database):
        chats = await db.get_user(message.chat.id)
        if chats:
            await message.bot.send_message(
                chat_id=message.chat.id,
                text="С возвращением! 👋",
                reply_markup=kb.main,
                message_thread_id=message.message_thread_id
            )
        else:
            await message.answer("Привет! 👋 Похоже, вы здесь впервые.\n\nВведите вашу группу (например: ИКБ-31):")
            await state.set_state(RegistrationStates.waiting_for_group)


@start_router.message(RegistrationStates.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext, db: Database):
    group = message.text.strip()
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

@start_router.message(F.text == 'Написать свой сервис')
async def write_service(message: types.Message):
    await message.answer("Исходный код проекта: github.com/PusTrace/bonch_pt\n"
                         "Стать разработчиком: 1) прочитать README проекта, 2) написать с своим сервисом:t.me/PusTrace.")
    