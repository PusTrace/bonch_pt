# services/cancel.py
# Глобальный обработчик отмены.
# Перехватывает "❌ Отмена" в любом состоянии и возвращает на main.

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import core.keyboards as kb

router = Router(name="cancel")


@router.message(F.text == "❌ Отмена")
async def global_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    await message.answer("Отменено.", reply_markup=kb.main)