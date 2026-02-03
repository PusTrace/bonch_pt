from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from core.db import Database
import core.keyboards as kb
from core.utils import group_by_prefix

router = Router(name="user")

@router.message(F.text == "Мои данные")
async def user_progress(message: types.Message, db: Database):
    user = await db.get_user_info(message.chat.id)

    if not user:
        await message.answer("У вас нет информации о пользователе.", reply_markup=kb.user)
        return

    result = f"Имя: {user['username']}\nГруппа: {user['sect']}\nБригада: {user['brigade']}\n\n"
    await message.answer(result, reply_markup=kb.user)

@router.message(F.text == "Сменить группу")
async def change_group(message: types.Message, state: FSMContext, db: Database):
    rows = await db.get_distinct_sects()
    groups = group_by_prefix(rows)

    await state.update_data(groups=groups)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=p)] for p in groups.keys()] +
                 [[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

    await message.answer("Выбери буквенную часть группы:", reply_markup=keyboard)
    await state.set_state("waiting_for_prefix")

@router.message(StateFilter("waiting_for_prefix"))
async def choose_number(message: types.Message, state: FSMContext):
    prefix = message.text
    data = await state.get_data()
    groups = data["groups"]

    if prefix not in groups:
        await message.answer("Выбери группу с клавиатуры")
        return

    numbers = groups[prefix]

    await state.update_data(prefix=prefix)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=n)] for n in numbers] +
                 [[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

    await message.answer(f"Теперь выбери номер для {prefix}:", reply_markup=keyboard)
    await state.set_state("waiting_for_number")


@router.message(StateFilter("waiting_for_number"))
async def process_new_group(message: types.Message, state: FSMContext, db: Database):
    number = message.text
    data = await state.get_data()

    prefix = data["prefix"]
    groups = data["groups"]

    if number not in groups[prefix]:
        await message.answer("Выбери номер с клавиатуры")
        return

    full_group = f"{prefix}-{number}"

    await db.update_user_group(
        message.chat.id,
        message.from_user.username,
        message.from_user.full_name, 
        full_group)
    await message.answer(
        f"Ваша группа успешно изменена на: {full_group}",
        reply_markup=kb.main
    )
    await state.clear()

    
@router.message(F.text == "Сменить бригаду")
async def change_brigade(message: types.Message, state: FSMContext):
    await message.answer("Введите новую бригаду:", reply_markup=kb.cancel_keyboard())
    await state.set_state("waiting_for_brigade")
    
@router.message(StateFilter("waiting_for_brigade"))
async def process_new_brigade(message: types.Message, state: FSMContext, db: Database):
    new_brigade = int(message.text)
    await db.update_user_brigade(message.chat.id, new_brigade)
    await message.answer(f"Ваша бригада успешно изменена на: {new_brigade}", reply_markup=kb.user)
    await state.clear()
    
@router.message(F.text == "Удалить мои данные")
async def remove_user_data(message: types.Message, db: Database):
    chat_id = message.chat.id
    await db.remove_user_data(chat_id)
    await message.answer(f"Ваши данные были удалены, нажмите /start чтобы снова пользоваться ботом", reply_markup=types.ReplyKeyboardRemove())
    
