import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os

# Путь к JSON файлу для хранения расписания
json_file = "schedule.json"

# Функция для загрузки данных из JSON, если они есть
def load_schedule_data():
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

# Функция для сохранения данных в JSON
def save_schedule_data(data):
    # Сортируем данные по дате
    sorted_data = {key: data[key] for key in sorted(data.keys())}
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(sorted_data, file, ensure_ascii=False, indent=4)

# Начальная дата
current_date = datetime(2025, 2, 17)

# Загружаем существующее расписание из JSON
schedule_data = load_schedule_data()

# Список с именами пар (например, пары с именами "1", "ФЗ", "2", "3", и т.д.)
pairs = ["1", "ФЗ", "2", "3", "4", "5", "6", "7"]

# Ограничение на 7 дней
for week in range(4):  # Для каждой из 4 недель
    # Формируем URL с новой датой
    url_date = current_date.strftime('%Y-%m-%d')
    
    # Проверяем, есть ли уже данные за эту дату
    if url_date in schedule_data:
        print(f"Данные для {url_date} уже существуют, пропускаем парсинг.")
        current_date += timedelta(weeks=1)
        continue  # Пропускаем парсинг, если данные уже есть
    
    # Формируем URL
    url = f"https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya?group=56160&date={url_date}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Для каждого дня в текущей неделе
    week_schedule = {}  # Расписание для всей недели
    for day_offset in range(7):
        # Используем текущую дату для записи
        day_date = current_date.strftime('%Y-%m-%d')  # Форматируем дату в строку

        # Находим блоки с парами для текущего дня
        day_class = f"rasp-day{day_offset + 1}"  # Например, rasp-day1, rasp-day2, ...
        schedule_blocks = soup.find_all("div", {"class": day_class})

        # Список для хранения расписания этого дня
        day_schedule = {}
        pair_index = 0

        # Проходим по каждому блоку с парой в текущем дне
        for block in schedule_blocks:
            # Безопасно извлекаем данные, проверяя наличие элемента
            subject = block.find("div", {"class": "vt240"})
            teacher = block.find("span", {"class": "teacher"})
            room = block.find("div", {"class": "vt242"})
            lesson_type = block.find("div", {"class": "vt243"})

            # Если хотя бы один элемент отсутствует, пропускаем блок
            if not subject or not teacher or not room or not lesson_type:
                # Если пара пустая, пропускаем текущий элемент и идём к следующей
                if pair_index < len(pairs):
                    pair_index += 1
                continue

            # Извлекаем текст из элементов
            subject = subject.get_text(strip=True)
            teacher = teacher.get_text(strip=True)
            room = room.get_text(strip=True)
            lesson_type = lesson_type.get_text(strip=True)

            # Если есть пара для записи
            if pair_index < len(pairs):
                # Записываем информацию для текущей пары в словарь
                day_schedule[pairs[pair_index]] = {
                    "Предмет": subject,
                    "Преподаватель": teacher,
                    "Аудитория": room,
                    "Тип занятия": lesson_type
                }

                # Увеличиваем индекс для следующей пары
                pair_index += 1

        # Добавляем информацию по текущей дате в недельное расписание
        if day_date:
            week_schedule[day_date] = day_schedule

        # Переходим к следующему дню
        current_date += timedelta(days=1)

    # Сохраняем данные на неделю в основной словарь расписания
    schedule_data.update(week_schedule)

    # Переходим к следующей неделе
    current_date += timedelta(weeks=1)

# Сохраняем обновленные данные в JSON
save_schedule_data(schedule_data)

