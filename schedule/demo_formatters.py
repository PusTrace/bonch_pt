"""Демо: format_schedule_group / format_schedule_teacher / format_schedule_protection."""

from formatters import (
    format_schedule_group,
    format_schedule_protection,
    format_schedule_teacher,
)
from models import Lesson


def main() -> None:
    group_lessons = [
        Lesson(
            date="2026-11-24",
            pair="3",
            subject="Тестовый предмет",
            auditorium="Ауд. 101",
            teacher="Иванов И. И.",
            lesson_type="Лекция",
            sect="ИКБ-31",
        ),
        Lesson(
            date="2026-11-24",
            pair="4",
            subject="Другое занятие",
            auditorium="Ауд. 202",
            teacher="Петров П. П.",
            lesson_type="Практика",
            sect="ИКБ-31",
        ),
    ]

    teacher_lessons = [
        Lesson(
            date="2026-11-25",
            pair="2",
            subject="Сети и телекоммуникации",
            auditorium="Ауд. 305",
            teacher="Сидоров С. С.",
            lesson_type="Практика",
            sect="ИКБ-31",
        ),
        Lesson(
            date="2026-11-25",
            pair="2",
            subject="Сети и телекоммуникации",
            auditorium="Ауд. 305",
            teacher="Сидоров С. С.",
            lesson_type="Практика",
            sect="ИКБ-32",
        ),
        Lesson(
            date="2026-11-25",
            pair="2",
            subject="Сети и телекоммуникации",
            auditorium="Ауд. 306",
            teacher="Сидоров С. С.",
            lesson_type="Практика",
            sect="ИКБ-33",
        ),
    ]

    protection_lessons = [
        Lesson(
            date="2026-11-24",
            pair="1",
            subject="Физика",
            auditorium="Ауд. 101",
            teacher="Иванов И. И.",
            lesson_type="Лекция",
            sect="ИКБ-31",
        ),
        Lesson(
            date="2026-11-24",
            pair="1",
            subject="Физика",
            auditorium="Ауд. 102",
            teacher="Петров П. П.",
            lesson_type="Лекция",
            sect="ИКБ-32",
        ),
        Lesson(
            date="2026-11-24",
            pair="1",
            subject="Физика",
            auditorium="Ауд. 103",
            teacher="Сидоров С. С.",
            lesson_type="Лекция",
            sect="ИКБ-33",
        ),
        Lesson(
            date="2026-11-24",
            pair="2",
            subject="Мат. анализ",
            auditorium="Ауд. 201",
            teacher="Кузнецов К. К.",
            lesson_type="Практика",
            sect="ИКБ-31",
        ),
        Lesson(
            date="2026-11-25",
            pair="1",
            subject="Физика",
            auditorium="Ауд. 103",
            teacher="Сидоров С. С.",
            lesson_type="Лекция",
            sect="ИКБ-33",
        ),
        Lesson(
            date="2026-11-25",
            pair="2",
            subject="Мат. анализ",
            auditorium="Ауд. 201",
            teacher="Кузнецов К. К.",
            lesson_type="Практика",
            sect="ИКБ-31",
        ),
    ]

    print("=== format_schedule_group ===")
    print(format_schedule_group(group_lessons, "Расписание группы ИКБ-31"))

    print("\n\n=== format_schedule_teacher ===")
    print(
        format_schedule_teacher(
            teacher_lessons, "Расписание преподавателя: Сидоров С. С."
        )
    )

    print("\n\n=== format_schedule_protection (main_group=ИКБ-31) ===")
    print(
        format_schedule_protection(
            protection_lessons, "Защита/обзор", main_group="ИКБ-31"
        )
    )


if __name__ == "__main__":
    main()
