import os
import random
import time
from datetime import datetime, timedelta

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


class PostgreSQLDB:
    def __init__(self, password):
        self.conn = psycopg2.connect(
            host="192.168.88.50", database="bonch", user="postgres", password=password
        )
        self.cur = self.conn.cursor()

    def insert_schedule(self, data):
        for item in data:
            self.cur.execute(
                """
                INSERT INTO schedule (date, pair, subject, auditorium, teacher, lesson_type, sect)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date, pair, sect) DO NOTHING
                """,
                item,
            )

    def get_last_date(self, sect):
        self.cur.execute("SELECT MAX(date) FROM schedule WHERE sect=%s", (sect,))
        result = self.cur.fetchone()
        return result[0] if result[0] else datetime.now().date()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()


class Bonch:
    def __init__(self, db: PostgreSQLDB):
        self.db = db
        self.session = self.create_session()

    def run(self):
        resp = self.get_groups()
        sects = self.parse_groups(resp)
        for sect, sect_number in sects:
            cur_date = self.db.get_last_date(sect)
            for i in range(5):  # TODO: unlimited cicle until schedule exist
                resp = self.get_schedule(cur_date, sect_number)
                result = self.parse_schedule(resp, cur_date)
                self.db.insert_schedule(result)
                self.db.commit()
                time.sleep(random.uniform(6, 12))
            time.sleep(random.uniform(60, 120))

    def test_run(self, parse_range: int):
        resp = self.get_groups()
        sects = self.parse_groups(resp)
        for sect, sect_number in sects:
            if sect == "ИКБ-31":
                cur_date = self.db.get_last_date(sect)
                for i in range(parse_range):
                    resp = self.get_schedule(cur_date, sect_number)
                    result = self.parse_schedule(resp, cur_date, sect)
                    cur_date += timedelta(days=7)
                    print(f"range i: {i}\n\n")
                    print(f"len result: {len(result)}")
                    self.db.insert_schedule(result)
                    self.db.commit()
            else:
                continue

    def create_session(self):
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
        return session

    def get_groups(self):
        url = "https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya"
        response = self.session.get(url)
        return response

    def get_schedule(self, weekday, sect_number):
        url_date = weekday.strftime("%Y-%m-%d")
        url = f"https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya?group={sect_number}&date={url_date}"

        for attempt in range(5):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}. Sleep 15-45 s...")
                time.sleep(random.uniform(15, 45))

    def parse_schedule(self, response, cur_date, sect):
        pairs = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
        ]  # TODO: remake from static pairs to getter pairs
        soup = BeautifulSoup(response.text, "html.parser")
        data = []

        # TODO: get sect by id="group_name" get value

        # TODO: table in class=vt236
        # TODO: table header in class=vt244 vt244a
        # TODO: table body in vt244b
        # TODO: table rows in vt244 but it strange rows because rows not day row its pairs row all rows have class vt244
        # TODO: pair index and time in vt239(container for index and time) vt283(pair index) and in vt239 time in <br>start time <br> end time
        # TODO: vt239 rasp-day rasp-day1 - its first container of first day of first pair. vt258 its container in container
        # TODO: vt240 its subject
        # TODO: vt241 its teacher container but in teacher container have container teacher and title is his full name text his short name
        # TODO: vt242 its auditorium
        # TODO: vt243 its lesson type
        # TODO: if in rasp-day doesnt exist vt240 and other firts pair doesn exist

        week_start = cur_date - timedelta(days=cur_date.weekday())
        for day_offset in range(7):
            real_date = week_start + timedelta(days=day_offset)
            day_date = real_date.strftime("%Y-%m-%d")
            day_class = f"rasp-day{day_offset + 1}"
            schedule_blocks = soup.find_all("div", {"class": day_class})

            pair_index = 0
            for block in schedule_blocks:
                subject = block.find("div", {"class": "vt240"})
                teacher = block.find("span", {"class": "teacher"})
                auditorium = block.find("div", {"class": "vt242"})
                lesson_type = block.find("div", {"class": "vt243"})

                if (
                    subject is None
                    and teacher is None
                    and auditorium is None
                    and lesson_type is None
                ):
                    pair_index += 1
                    continue

                entry = (
                    day_date,
                    pairs[pair_index] if pair_index < len(pairs) else None,
                    subject.get_text(strip=True) if subject is not None else None,
                    auditorium.get_text(strip=True) if auditorium is not None else None,
                    teacher.get_text(strip=True) if teacher is not None else None,
                    lesson_type.get_text(strip=True)
                    if lesson_type is not None
                    else None,
                    sect,
                )
                data.append(entry)
                pair_index += 1
        return data

    def parse_groups(self, response) -> list[tuple]:
        soup = BeautifulSoup(response.text, "html.parser")
        sects = soup.find_all("a", class_="vt256")

        groups = []
        for tag in sects:
            name = tag.get("data-nm")
            gid = tag.get("data-i")
            if name and gid:
                data = (name, gid)
                groups.append(data)

        return groups


if __name__ == "__main__":
    load_dotenv()
    password = os.getenv("DB_PASSWORD")
    db = PostgreSQLDB(password)
    try:
        bonch = Bonch(db)
        bonch.test_run(parse_range=15)
        db.close()
    except Exception as e:
        print(f"error {e}")
        db.close()
