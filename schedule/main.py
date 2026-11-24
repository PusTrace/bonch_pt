import asyncio
import json
import os
from datetime import date, timedelta

from dotenv import load_dotenv
from redis.asyncio import Redis


class Schedule:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_schedule(self, sect: str) -> list[dict]:
        """Получить всё расписание группы."""

        result = []

        async for key in self.redis.scan_iter(match=f"schedule:{sect}:*:*"):
            data = await self.redis.get(key)

            if data:
                result.append(json.loads(data))

        return sorted(
            result,
            key=lambda x: (x["date"], int(x["pair"] or 0)),
        )

    async def get_week_schedule(self, sect: str) -> list[dict]:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        schedule = await self.get_schedule(sect)

        return [
            item
            for item in schedule
            if monday.isoformat() <= item["date"] <= sunday.isoformat()
        ]

    async def get_teacher_schedule(self, teacher: str) -> list[dict]:
        """Найти расписание преподавателя во всех группах."""

        result = []

        async for key in self.redis.scan_iter(match="schedule:*:*:*"):
            data = await self.redis.get(key)

            if not data:
                continue

            item = json.loads(data)

            if item["teacher"] and teacher.lower() in item["teacher"].lower():
                result.append(item)

        return sorted(
            result,
            key=lambda x: (x["date"], int(x["pair"] or 0)),
        )

    def print_schedule(self, schedule: list[dict], title: str):
        print(f"\n{'=' * 60}")
        print(title)
        print("=" * 60)

        if not schedule:
            print("Расписание отсутствует.")
            return

        for item in schedule:
            print(
                f"\nДата: {item['date']}"
                f"\nПара: {item['pair']}"
                f"\nПредмет: {item['subject'] or '-'}"
                f"\nАудитория: {item['auditorium'] or '-'}"
                f"\nПреподаватель: {item['teacher'] or '-'}"
                f"\nТип: {item['lesson_type'] or '-'}"
                f"\nГруппа: {item['sect']}"
            )
            print("-" * 60)

    async def tui(self):
        while True:
            print("\n========== SCHEDULE ==========")
            print("2. Расписание на неделю")
            print("3. Расписание преподавателя")
            print("4. Всё расписание группы")
            print("0. Выход")

            choice = input("\nВыберите действие: ").strip()

            if choice == "0":
                break

            if choice in ("2", "4"):
                sect = input("Введите группу: ").strip()

                if not sect:
                    print("Группа не указана.")
                    continue

                elif choice == "2":
                    schedule = await self.get_week_schedule(sect)
                    title = f"Расписание на неделю: {sect}"

                else:
                    schedule = await self.get_schedule(sect)
                    title = f"Полное расписание: {sect}"

                self.print_schedule(schedule, title)

            elif choice == "3":
                teacher = input("Введите преподавателя: ").strip()

                if not teacher:
                    print("Преподаватель не указан.")
                    continue

                schedule = await self.get_teacher_schedule(teacher)

                self.print_schedule(
                    schedule,
                    f"Расписание преподавателя: {teacher}",
                )

            else:
                print("Неизвестная команда.")


async def main():
    load_dotenv()

    redis = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )

    try:
        await redis.ping()

        app = Schedule(redis)
        await app.tui()

    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
