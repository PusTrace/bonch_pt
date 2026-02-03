# core/utils.py
from datetime import datetime

WEEKDAYS_RU = {
    0: "Понедельник",
    1: "Вторник", 
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

# Время пар
PAIR_TIMES = {
    1: "9:00–10:35",
    2: "10:45–12:20",
    3: "13:00–14:35",
    4: "14:45–16:20",
    5: "16:30–18:05",
    6: "18:15–19:50"
}

def format_own_schedule(schedule: list, title: str = None) -> str:
    """Форматирует расписание в читаемый вид"""
    if not schedule:
        return "📋 Пар нет"
    
    lines = []
    if title:
        lines.append(f"📋 {title}\n")
    
    current_date = None
    
    for date, pair, subject, auditorium, teacher, lesson_type in schedule:
        # Парсим дату
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        else:
            date_obj = date
        
        # Если новая дата — добавляем заголовок
        if current_date != date_obj:
            current_date = date_obj
            weekday = WEEKDAYS_RU[date_obj.weekday()]
            day = date_obj.day
            month = MONTHS_RU[date_obj.month]
            year = date_obj.year
            
            if lines:  # Пустая строка между днями
                lines.append("")
            
            lines.append(f"{weekday}, {day} {month} {year}\n")
        
        # Время пары
        time = PAIR_TIMES.get(int(pair), "")
        lines.append(f"{time}")
        
        # Номер и название
        lines.append(f"{pair}. {subject}")
        
        # Тип занятия
        lines.append(f"    {lesson_type}")
        
        # Преподаватель
        lines.append(f"    {teacher}")
        
        # Аудитория
        lines.append(f"    {auditorium}")
        lines.append("")  # Пустая строка после пары
    
    return "\n".join(lines)


def format_teacher_schedule(schedule: list, title: str = None) -> str:
    """Форматирует расписание в читаемый вид"""
    if not schedule:
        return "📋 Пар нет"
    
    lines = []
    if title:
        lines.append(f"📋 {title}")
    
    current_date = None
    i = 0
    
    while i < len(schedule):
        date, pair, subject, auditorium, lesson_type, sect = schedule[i]
        
        # Парсим дату
        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        else:
            date_obj = date
        
        # Если новая дата — добавляем заголовок
        if current_date != date_obj:
            current_date = date_obj
            weekday = WEEKDAYS_RU[date_obj.weekday()]
            day = date_obj.day
            month = MONTHS_RU[date_obj.month]
            year = date_obj.year
            
            lines.append("")
            lines.append(f"{weekday}, {day} {month} {year}\n")
        
        # Собираем все группы для одинаковых пар
        groups = [sect]
        j = i + 1
        
        while j < len(schedule):
            next_date, next_pair, next_subject, next_aud, next_type, next_sect = schedule[j]
            
            if (next_date == date and next_pair == pair and 
                next_subject == subject and next_aud == auditorium and 
                next_type == lesson_type):
                groups.append(next_sect)
                j += 1
            else:
                break
        
        # Собираем пару в одну строку с переносами внутри
        time = PAIR_TIMES.get(int(pair), "")
        pair_text = f"{time}\n{pair}. {subject}\n    {lesson_type}\n    Группы: {', '.join(groups)}\n    {auditorium}"
        lines.append(pair_text)
        lines.append("")  # Пустая строка после пары
        
        i = j
    
    return "\n".join(lines)

from collections import defaultdict

def group_by_prefix(rows):
    data = defaultdict(list)
    for prefix, number in rows:
        data[prefix].append(number)
    return data
