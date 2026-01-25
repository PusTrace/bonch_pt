from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from core.db import Database
import services.user.keyboards as kb

router = Router(name="user")

@router.message(F.text == "Мои данные")
async def user_progress(message: types.Message, db: Database):
    user = await db.get_user_info(message.chat.id)

    if not user:
        await message.answer("У вас нет информации о пользователе.", reply_markup=kb.main)
        return

    result = f"Имя: {user['username']}\nГруппа: {user['sect']}\nБригада: {user['brigade']}\n\n"
    await message.answer(result, reply_markup=kb.main)

@router.message(F.text == "Сменить группу")
async def change_group(message: types.Message, state: FSMContext):
    await message.answer("Введите новую группу:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state("waiting_for_group")
    
@router.message(StateFilter("waiting_for_group"))
async def process_new_group(message: types.Message, state: FSMContext, db: Database):
    new_group = message.text
    await db.update_user_group(message.chat.id, new_group)
    await message.answer(f"Ваша группа успешно изменена на: {new_group}", reply_markup=kb.main)
    await state.clear()
    
@router.message(F.text == "Сменить бригаду")
async def change_brigade(message: types.Message, state: FSMContext):
    await message.answer("Введите новую бригаду:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state("waiting_for_brigade")
    
@router.message(StateFilter("waiting_for_brigade"))
async def process_new_brigade(message: types.Message, state: FSMContext, db: Database):
    new_brigade = int(message.text)
    await db.update_user_brigade(message.chat.id, new_brigade)
    await message.answer(f"Ваша бригада успешно изменена на: {new_brigade}", reply_markup=kb.main)
    await state.clear()
    
@router.message(F.text == "Удалить мои данные")
async def remove_user_data(message: types.Message, db: Database):
    chat_id = message.chat.id
    await db.remove_user_data(chat_id)
    await message.answer(f"Ваши данные были удалены, нажмите /start чтобы снова пользоваться ботом", reply_markup=types.ReplyKeyboardRemove())