"""Formatters: convert schedule data into Telegram HTML text."""
import html
from collections import defaultdict
from datetime import datetime

from models import Lesson



WEEKDAY_RU = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}


def _safe(value: str | None) -> str:
    if value is None or value == "":
        return "-"
    return html.escape(str(value))


def _format_day_header(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        wd = WEEKDAY_RU.get(dt.weekday(), "")
        return f"{wd}, {dt.strftime('%d.%m')}".strip(", ")
    except (ValueError, TypeError):
        return _safe(date_str)


def _pair_time(time_start: str | None, time_end: str | None) -> str:
    if time_start and time_end:
        return f"{time_start}-{time_end}"
    if time_start:
        return str(time_start)
    return "--:--"


def _group_lessons(lessons: list[Lesson]) -> list[tuple[tuple, list[Lesson]]]:
    groups: dict[tuple, list[Lesson]] = defaultdict(list)
    for item in lessons:
        key = (item.date, item.pair, item.subject, item.lesson_type, item.teacher)
        groups[key].append(item)
    ordered_keys = sorted(groups.keys(), key=lambda k: (k[0] or "", str(k[1] or "")))
    return [(k, groups[k]) for k in ordered_keys]


def format_schedule_group(lessons: list[Lesson], title: str) -> str:
    """Расписание для группы: время, пара [тип] предмет, преподаватель, аудитория. Группу не выводим."""
    if not lessons:
        return f"<b>{html.escape(title)}</b>\n\nРасписание отсутствует."

    grouped_by_day: dict[str, list[tuple[tuple, list[Lesson]]]] = defaultdict(list)
    for key, group in _group_lessons(lessons):
        grouped_by_day[key[0] or ""].append((key, group))

    text = f"<b>{html.escape(title)}</b>\n\n"

    for date_str in sorted(grouped_by_day.keys()):
        day_header = _format_day_header(date_str)
        text += f"<b>{html.escape(day_header)}</b>\n\n"

        for key, group in sorted(
            grouped_by_day[date_str],
            key=lambda x: (
                (x[1][0].time_start or "99:99") if x[1] else "99:99",
                str(x[0][1] or ""),
            ),
        ):
            _, pair, subject, lesson_type, teacher = key
            time_range = _pair_time(group[0].time_start, group[0].time_end)
            pair_s = str(pair) if pair else "-"
            subject_s = subject or "-"
            lesson_type_s = (lesson_type or "").strip()
            teacher_s = teacher or "-"

            type_prefix = f"[{lesson_type_s}] " if lesson_type_s else ""

            aud = group[0].auditorium or "-"

            text += f"{html.escape(time_range)}\n"
            text += f"{html.escape(pair_s)}. {html.escape(type_prefix)}{html.escape(subject_s)}\n"
            text += f"  {html.escape(teacher_s)}\n"
            text += f"  {html.escape(aud)}\n\n"

        if len(text) > 3900:
            text += "… (обрезано)"
            break

    return text.rstrip()


def format_schedule_teacher(lessons: list[Lesson], title: str) -> str:
    """Расписание преподавателя: время, пара [тип] предмет (преподавателя не пишем), аудитории и группы списком."""
    if not lessons:
        return f"<b>{html.escape(title)}</b>\n\nРасписание отсутствует."

    grouped_by_day: dict[str, list[tuple[tuple, list[Lesson]]]] = defaultdict(list)
    for key, group in _group_lessons(lessons):
        grouped_by_day[key[0] or ""].append((key, group))

    text = f"<b>{html.escape(title)}</b>\n\n"

    for date_str in sorted(grouped_by_day.keys()):
        day_header = _format_day_header(date_str)
        text += f"<b>{html.escape(day_header)}</b>\n\n"

        for key, group in sorted(
            grouped_by_day[date_str],
            key=lambda x: (
                (x[1][0].time_start or "99:99") if x[1] else "99:99",
                str(x[0][1] or ""),
            ),
        ):
            _, pair, subject, lesson_type, _teacher = key
            time_range = _pair_time(group[0].time_start, group[0].time_end)
            pair_s = str(pair) if pair else "-"
            subject_s = subject or "-"
            lesson_type_s = (lesson_type or "").strip()

            type_prefix = f"[{lesson_type_s}] " if lesson_type_s else ""

            by_aud: dict[str, list[str]] = defaultdict(list)
            for it in group:
                aud = it.auditorium or "-"
                by_aud[aud].append(it.sect or "-")

            text += f"{html.escape(time_range)}\n"
            text += f"{html.escape(pair_s)}. {html.escape(type_prefix)}{html.escape(subject_s)}\n"
            for aud, sects in by_aud.items():
                aud_s = html.escape(aud)
                sects_s = ", ".join(html.escape(s) for s in sects)
                text += f"  {aud_s} ({sects_s})\n"
            text += "\n"

        if len(text) > 3900:
            text += "… (обрезано)"
            break

    return text.rstrip()


def format_schedule_protection(
    lessons: list[Lesson], title: str, main_group: str | None = None
) -> str:
    """Формат: Понедельник дата; блоки по парам 'N. время', список 'группа ауд препод'.
    Если задан main_group, записи этой группы идут первыми в списке пары."""
    if not lessons:
        return f"<b>{html.escape(title)}</b>\n\nРасписание отсутствует."

    # group by day, then by (pair)
    by_day: dict[str, dict[str, list[Lesson]]] = defaultdict(lambda: defaultdict(list))
    for item in lessons:
        d = item.date or ""
        p = item.pair or ""
        by_day[d][p].append(item)

    text = f"<b>{html.escape(title)}</b>\n\n"

    for date_str in sorted(by_day.keys()):
        day_header = _format_day_header(date_str)
        text += f"<b>{html.escape(day_header)}</b>\n\n"

        pairs_in_day = sorted(
            by_day[date_str].keys(),
            key=lambda x: (
                (by_day[date_str][x][0].time_start or "99:99") if by_day[date_str][x] else "99:99",
                str(x),
            ),
        )
        for pair in pairs_in_day:
            items = by_day[date_str][pair]
            time_range = _pair_time(items[0].time_start, items[0].time_end) if items else "--:--"
            pair_s = pair or "-"
            items = by_day[date_str][pair]
            # unique by (sect, auditorium, teacher)
            seen: set[tuple[str, str, str]] = set()
            uniq: list[Lesson] = []
            for it in items:
                key = (it.sect or "-", it.auditorium or "-", it.teacher or "-")
                if key not in seen:
                    seen.add(key)
                    uniq.append(it)
            # main_group first
            if main_group:
                mg = main_group.strip()
                uniq.sort(
                    key=lambda it: 0 if (it.sect or "").strip().lower() == mg.lower() else 1
                )

            text += f"{html.escape(pair_s)}. {html.escape(time_range)}\n"
            for it in uniq:
                g = _safe(it.sect)
                a = _safe(it.auditorium)
                t = _safe(it.teacher)
                text += f"{g} {a} {t}\n"
            text += "\n"

        if len(text) > 3900:
            text += "… (обрезано)"
            break

    return text.rstrip()