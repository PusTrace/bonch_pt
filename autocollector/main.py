import asyncio
import os
import random
from datetime import date, datetime, timedelta

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from repository import RedisDB


class Bonch:
    GROUPS_URL = (
        "https://www.sut.ru/studentu/raspisanie/"
        "raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya"
    )

    PAIRS = ["1", "2", "3", "4", "5", "6", "7"]

    def __init__(self, db: RedisDB):
        self.db = db
        self.session = self.create_session()

    def create_session(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.sut.ru/",
        }

        return httpx.AsyncClient(
            headers=headers,
            timeout=10,
            follow_redirects=True,
        )

    async def get_groups(self):
        response = await self.session.get(self.GROUPS_URL)
        response.raise_for_status()
        return response

    async def get_schedule(
        self,
        weekday: date,
        sect_number: str,
        timeout: float = 30,
        retry_delay: tuple[int, int] = (30, 60),
    ):
        url = f"{self.GROUPS_URL}?group={sect_number}&date={weekday.isoformat()}"

        for attempt in range(5):
            try:
                response = await self.session.get(
                    url,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                if attempt == 4:
                    raise

                delay = random.uniform(*retry_delay)

                print(f"Network error: {e}. Retry {attempt + 1}/5 in {delay:.1f}s")

                await asyncio.sleep(delay)

    def parse_groups(self, response) -> list[tuple[str, str]]:
        soup = BeautifulSoup(response.text, "html.parser")
        sects = soup.find_all("a", class_="vt256")

        groups = []

        for tag in sects:
            name = tag.get("data-nm")
            gid = tag.get("data-i")

            if name and gid:
                groups.append((name, gid))

        return groups

    def parse_schedule(
        self,
        response,
        cur_date: date,
        sect: str,
    ) -> list[tuple]:

        soup = BeautifulSoup(response.text, "html.parser")
        data = []

        week_start = cur_date - timedelta(days=cur_date.weekday())

        for day_offset in range(7):
            real_date = week_start + timedelta(days=day_offset)
            day_date = real_date.isoformat()

            day_class = f"rasp-day{day_offset + 1}"
            schedule_blocks = soup.find_all("div", {"class": day_class})

            pair_index = 0

            for block in schedule_blocks:
                subject = block.find("div", {"class": "vt240"})
                teacher = block.find("span", {"class": "teacher"})
                auditorium = block.find("div", {"class": "vt242"})
                lesson_type = block.find("div", {"class": "vt243"})

                if all(
                    item is None
                    for item in (
                        subject,
                        teacher,
                        auditorium,
                        lesson_type,
                    )
                ):
                    pair_index += 1
                    continue

                entry = (
                    day_date,
                    self.PAIRS[pair_index] if pair_index < len(self.PAIRS) else None,
                    subject.get_text(strip=True) if subject else None,
                    auditorium.get_text(strip=True) if auditorium else None,
                    teacher.get_text(strip=True) if teacher else None,
                    lesson_type.get_text(strip=True) if lesson_type else None,
                    sect,
                )

                data.append(entry)
                pair_index += 1

        return data

    async def run(self):
        """Однократная первичная загрузка расписания при запуске программы."""

        print("\n========== INITIAL SCHEDULE UPDATE ==========\n")

        await self.update_all_groups(
            qty_weeks=8, request_delay=(1, 3), group_delay=(3, 9)
        )

        print("\n========== INITIAL UPDATE COMPLETED ==========\n")

    async def close(self):
        await self.session.aclose()

    async def update_all_groups(
        self,
        qty_weeks: int = 3,
        request_delay: tuple = (20, 40),
        group_delay: tuple = (90, 180),
        only_my_group: bool = False,
    ):
        """Обновляет расписание всех групп на три недели."""

        response = await self.get_groups()
        sects = self.parse_groups(response)

        # Понедельник текущей недели
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        print(f"Found {len(sects)} groups")
        print(f"Starting from: {week_start}")

        for group_index, (sect, sect_number) in enumerate(sects, 1):
            if only_my_group == True and sect != "ИКБ-31":
                print(f"\n[{group_index}/{len(sects)}] Skipped Group: {sect}")
                continue
            print(f"\n[{group_index}/{len(sects)}] Group: {sect}")

            for week in range(qty_weeks):
                cur_date = week_start + timedelta(days=week * 7)

                try:
                    response = await self.get_schedule(
                        cur_date,
                        sect_number,
                        timeout=30,
                        retry_delay=(30, 60),
                    )

                    result = self.parse_schedule(
                        response,
                        cur_date,
                        sect,
                    )

                    await self.db.replace_schedule(
                        sect=sect,
                        week_start=cur_date,
                        data=result,
                    )

                    print(f"{sect}: week={cur_date}, inserted={len(result)}")

                except Exception as e:
                    print(f"Failed: group={sect}, week={cur_date}, error={e}")

                # Мягкая задержка между запросами
                delay = random.uniform(*request_delay)
                print(f"Next request in {delay:.1f}s")
                await asyncio.sleep(delay)

            # Более продолжительная задержка между группами
            delay = random.uniform(*group_delay)

            print(f"Group completed. Waiting {delay:.1f}s")
            await asyncio.sleep(delay)

    async def daemon(self):
        """Запускает обновление расписания каждое воскресенье в 03:00."""

        while True:
            now = datetime.now()

            # Ближайшее воскресенье в 03:00
            days_until_sunday = (6 - now.weekday()) % 7

            next_run = now.replace(
                hour=3,
                minute=0,
                second=0,
                microsecond=0,
            ) + timedelta(days=days_until_sunday)

            # Если воскресенье уже наступило после 03:00,
            # переносим запуск на следующую неделю
            if next_run <= now:
                next_run += timedelta(days=7)

            delay = (next_run - now).total_seconds()

            print(
                f"Next schedule update: {next_run}\nSleeping for {delay / 3600:.2f} hours"
            )

            await asyncio.sleep(delay)

            print("\n========== SCHEDULE UPDATE ==========")

            try:
                await self.update_all_groups()

                print("\nSchedule update completed")

            except Exception as e:
                print(f"Schedule update failed: {e}")

            print("Waiting for next Sunday...")


async def main():
    load_dotenv()

    db = RedisDB(url=os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    bonch = Bonch(db)

    try:
        # Первичная синхронизация при запуске
        try:
            await bonch.run()
        except Exception as e:
            print(f"Initial schedule update failed: {e}")

        # После первичной загрузки запускаем демон
        await bonch.daemon()

    finally:
        await bonch.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
