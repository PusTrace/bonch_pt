import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
import os
import time
import random

def connect_db(password):
    conn = psycopg2.connect(
        host="localhost",
        database="bonch",
        user="postgres",
        password=password
    )
    cursor = conn.cursor()
    return conn, cursor

def push_schedule_to_db(cursor, entry, sect):
    cursor.execute(
        """
        INSERT INTO schedule (date, pair, subject, auditorium, teacher, lesson_type, sect)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date, pair, sect) DO NOTHING
        """,
        entry + (sect,)
    )


def parse_bonch(session, cursor, current_date, sect, sect_number):
    pairs = ["1", "2", "3", "4", "5", "6", "7"]
    base_date = current_date

    for week in range(5):
        week_date = base_date + timedelta(weeks=week)
        week_start = week_date - timedelta(days=week_date.weekday())

        url_date = week_start.strftime('%Y-%m-%d')
        url = f"https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya?group={sect_number}&date={url_date}"
        print("WEEK:", url_date)


        for attempt in range(5):  # 5 попыток
            try:
                response = session.get(url, timeout=10)
                break
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}. Sleep 15-45 s...")
                time.sleep(random.uniform(15, 45))
        else:
            print(f"Skip url after retries: {url}")
            continue

        
        if response.status_code != 200:
            print(f"Ошибка {response.status_code} при загрузке {url}")
            continue

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
                
                if subject is None and teacher is None and auditorium is None and lesson_type is None:
                    pair_index += 1
                    continue

                entry = (
                    day_date,
                    pairs[pair_index] if pair_index < len(pairs) else None,
                    subject.get_text(strip=True) if subject is not None else None,
                    auditorium.get_text(strip=True) if auditorium is not None else None,
                    teacher.get_text(strip=True) if teacher is not None else None,
                    lesson_type.get_text(strip=True) if lesson_type is not None else None)
                print(entry)
                push_schedule_to_db(cursor, entry, sect)
                pair_index += 1
                
        current_date += timedelta(weeks=1)
        time.sleep(random.uniform(1, 3))
    time.sleep(random.uniform(3, 9))



def last_date_from_db(cursor, sect):
    cursor.execute("SELECT MAX(date) FROM schedule WHERE sect=%s", (sect,))
    result = cursor.fetchone()
    return result[0] if result[0] else datetime.now().date()


def parse_groups(session):
    url = "https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya"
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    sects = soup.find_all("a", class_="vt256")

    groups = {}
    for tag in sects:
        name = tag.get("data-nm")
        gid = tag.get("data-i")
        if name and gid:
            groups[name] = gid

    return groups

    
def init_requirments():
    load_dotenv()
    password = os.getenv("DB_PASSWORD")
    conn, cursor = connect_db(password)
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

    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(cookies)
    return session, conn, cursor

    
if __name__ == "__main__":
    i = 0
    for i in range(5):
        print(f"\n{i}\n")
        session, conn, cursor = init_requirments()
        sects = parse_groups(session)
        for sect, sect_number in sects.items():
            print(f"\nsect: {sect}")
            current_date = last_date_from_db(cursor, sect)
            parse_bonch(session, cursor, current_date, sect, sect_number)
            conn.commit()
        cursor.close()
        conn.close()
        time.sleep(random.uniform(120, 240))