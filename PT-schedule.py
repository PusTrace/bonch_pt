import requests
from bs4 import BeautifulSoup

# URL расписания
url = "https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya?group=56160&date=2025-02-20"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Находим все блоки с расписанием
schedule_blocks = soup.find_all("div", {"class": "vt239 rasp-day rasp-day1"})

# Список с именами пар (например, пары с именами "1", "2" и т.д.)
pairs = ["1", "ФЗ", "2", "3", "4", "5", "6", "7"]

# Словарь для хранения пар
schedule_data = {}

# Индекс текущей пары
pair_index = 0

# Проходим по каждому блоку расписания
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
    
    # Проверяем, если есть пара для записи
    if pair_index < len(pairs):
        # Записываем информацию для текущей пары в словарь
        schedule_data[pairs[pair_index]] = {
            "Предмет": subject,
            "Преподаватель": teacher,
            "Аудитория": room,
            "Тип занятия": lesson_type
        }
        
        # Увеличиваем индекс для следующей пары
        pair_index += 1

# Выводим итоговое расписание
for pair, details in schedule_data.items():
    print(f"{pair}: {details}")
