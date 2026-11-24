"""Tests for schedule.formatters with sample data (no Redis)."""
from models import Lesson
from formatters import (
    format_schedule_group,
    format_schedule_protection,
    format_schedule_teacher,
)


SAMPLE_GROUP = [
    Lesson(
        date="2026-11-24",
        pair="3",
        subject="Тестовый предмет",
        auditorium="Ауд. 101",
        teacher="Иванов И. И.",
        lesson_type="Лекция",
        sect="ИКБ-31",
    ),
]


def test_format_group():
    text = format_schedule_group(SAMPLE_GROUP, "Расписание группы ИКБ-31")
    assert "Расписание группы ИКБ-31" in text
    assert "Тестовый предмет" in text
    assert "Иванов И. И." in text
    assert "Ауд. 101" in text


def test_format_group_empty():
    text = format_schedule_group([], "Пусто")
    assert "Пусто" in text
    assert "Расписание отсутствует" in text


def test_format_teacher_multiple_groups():
    lessons = [
        Lesson(
            date="2026-11-25",
            pair="2",
            subject="Сети",
            auditorium="Ауд. 305",
            teacher="Сидоров С. С.",
            lesson_type="Практика",
            sect="ИКБ-31",
        ),
        Lesson(
            date="2026-11-25",
            pair="2",
            subject="Сети",
            auditorium="Ауд. 305",
            teacher="Сидоров С. С.",
            lesson_type="Практика",
            sect="ИКБ-32",
        ),
    ]
    text = format_schedule_teacher(lessons, "Преподаватель: Сидоров")
    assert "Преподаватель: Сидоров" in text
    assert "Сети" in text
    assert "ИКБ-31" in text and "ИКБ-32" in text
    # В теле (после заголовка) имя преподавателя из данных не дублируем строкой преподавателя — проверяем отсутствие ФИО из Lesson
    body = text.split("</b>\n\n", 1)[-1] if "</b>" in text else text
    assert "Сидоров С. С." not in body


def test_format_protection_placeholder():
    assert "Расписание отсутствует" in format_schedule_protection([], "x")