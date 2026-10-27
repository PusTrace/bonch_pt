#!/usr/bin/env python3
from logging import getLogger

from core.db import Database
from core.utils import format_own_schedule, format_teacher_schedule


class Schedule:
    def __init__(self) -> None:
        pass

    def run(self):
        pass

    async def schedule_main(message: types.Message, db: Database):
        user = await db.get_user_info(message.chat.id)
        if user:
            schedule = await db.get_today_schedule(user[4])
            await message.answer(
                text=format_own_schedule(schedule, "Расписание на сегодня"),
                reply_markup=kb.schedule,
            )

    async def schedule_teachers(
        message: types.Message, db: Database, state: FSMContext
    ):
        user = await db.get_user_info(message.chat.id)
        if not user:
            await message.answer("Ошибка доступа")
            return

        teachers_records = await db.get_distinct_teachers(user)
        buttons = [
            [KeyboardButton(text=rec["teacher"])]
            for rec in teachers_records
            if rec["teacher"] and rec["teacher"].strip()
        ]
        buttons.append([KeyboardButton(text="❌ Отмена")])

        teachers_kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

        await message.answer(
            "👨‍🏫 Выберите преподавателя: \n p.s. есть баг с физкультурой так что порядок пар может быть не верный",
            reply_markup=teachers_kb,
        )
        await state.set_state("waiting_for_teacher")

    async def teacher_schedule(message: types.Message, db: Database, state: FSMContext):
        teacher = message.text.strip()
        user = await db.get_user_info(message.chat.id)
        if not user:
            await message.answer("Ошибка доступа")
            return
        teachers_records = await db.get_distinct_teachers(user)
        valid_teachers = [
            rec["teacher"]
            for rec in teachers_records
            if rec["teacher"] and rec["teacher"].strip()
        ]

        if teacher not in valid_teachers:
            await message.answer("Неверный преподаватель. Выберите из списка выше.")
            return

        await state.clear()
        schedule = await db.get_teacher_schedule(teacher)

        if not schedule:
            await message.answer(
                "❌ Нет расписания для этого преподавателя.", reply_markup=kb.schedule
            )
            return

        await message.answer(
            format_teacher_schedule(schedule, f"Расписание преподавателя: {teacher}"),
            reply_markup=kb.schedule,
        )

    async def week_schedule(message: types.Message, db: Database):
        user = await db.get_user_info(message.chat.id)
        schedule = await db.get_week_schedule(user[4])

        if not schedule:
            await message.answer(
                "❌ Нет расписания для этой группы.", reply_markup=kb.schedule
            )
            return

        await message.answer(
            format_own_schedule(
                schedule, f"Расписание на неделю для группы: {user[4]}"
            ),
            reply_markup=kb.schedule,
        )


if __name____ == "__main__":
    Schedule().run()
