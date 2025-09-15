import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
import os

def connect_db(password):
    conn = psycopg2.connect(
        host="localhost",
        database="bonch",
        user="postgres",
        password=password
    )
    cursor = conn.cursor()
    return conn, cursor

def push_schedule_to_db(cursor, entry):
    cursor.execute(
        """
        INSERT INTO schedule (date, pair, subject, auditorium, teacher, lesson_type, sect)
        VALUES (%s, %s, %s, %s, %s, %s, 'IKB-31')
        ON CONFLICT (date, pair) DO NOTHING
        """,
        entry
    )


def parse_bonch(cursor, current_date, duration):
    pairs = ["1", "2", "3", "4", "5", "6", "7"]

    for week in range(duration):
        week_start = current_date - timedelta(days=current_date.weekday())  
        url_date = week_start.strftime('%Y-%m-%d')
        url = f"https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya?group=56160&date={url_date}"

        cookies = {
            "PHPSESSID": "b524092011e6cd2d9b22e7eb18063e55"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Dnt": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.sut.ru/",
        }

        response = requests.get(url, headers=headers, cookies=cookies)
        
        if response.status_code != 200:
            print(f"Ошибка {response.status_code} при загрузке {url}")
            continue

        print(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')

        
        for day_offset in range(7):
            real_date = week_start + timedelta(days=day_offset)
            day_date = real_date.strftime('%Y-%m-%d')
            day_class = f"rasp-day{day_offset + 1}"
            schedule_blocks = soup.find_all("div", {"class": day_class})

            pair_index = 0
            for block in schedule_blocks:
                subject = block.find("div", {"class": "vt240"})
                teacher = block.find("span", {"class": "teacher"})
                auditorium = block.find("div", {"class": "vt242"})
                lesson_type = block.find("div", {"class": "vt243"})

                print(day_date,
                    pairs[pair_index] if pair_index < len(pairs) else None,
                    subject.get_text(strip=True) if subject is not None else None,
                    auditorium.get_text(strip=True) if auditorium is not None else None,
                    teacher.get_text(strip=True) if teacher is not None else None,
                    lesson_type.get_text(strip=True) if lesson_type is not None else None)
                
                if not all([subject, teacher, auditorium, lesson_type]):
                    print("Пропущено:")
                    if not subject:
                        print("  ❌ Нет предмета")
                    if not teacher:
                        print("  ❌ Нет преподавателя")
                    if not auditorium:
                        print("  ❌ Нет аудитории")
                    if not lesson_type:
                        print("  ❌ Нет типа занятия")
                    pair_index += 1
                    
                    a = input("Press Enter to continue: ")
                    if a.strip() == "":
                        continue
                    else:
                        quit()


                entry = (
                    day_date,
                    pairs[pair_index] if pair_index < len(pairs) else None,
                    subject.get_text(strip=True),
                    auditorium.get_text(strip=True),
                    teacher.get_text(strip=True),
                    lesson_type.get_text(strip=True)
                )
                
                push_schedule_to_db(cursor, entry)
                pair_index += 1
                
        current_date += timedelta(weeks=1)



def last_date_from_db(cursor):
    cursor.execute("SELECT MAX(date) FROM schedule WHERE sect='IKB-32'")
    result = cursor.fetchone()
    return result[0].date() if result[0] else datetime.strptime("2025-09-01", "%Y-%m-%d").date()


if __name__ == "__main__":
    load_dotenv()
    password = os.getenv("DB_PASSWORD")
    conn, cursor = connect_db(password)
    current_date = last_date_from_db(cursor)
    duration = 1
    parse_bonch(cursor, current_date, duration)
    conn.commit()
    conn.close()
