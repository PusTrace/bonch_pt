import asyncio
import os

from dotenv import load_dotenv
from formatters import (
    format_schedule_group,
    format_schedule_protection,
    format_schedule_teacher,
)
from redis.asyncio import Redis

from repository import RedisDB


async def main() -> None:
    load_dotenv()

    redis = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )

    try:
        await redis.ping()
        app = RedisDB(redis)

        while True:
            print("\n========== SCHEDULE ==========")
            print("2. Расписание на неделю")
            print("3. Расписание преподавателя")
            print("5. Защита (по группе, неделя)")
            print("0. Выход")

            choice = input("\nВыберите действие: ").strip()

            if choice == "0":
                break

            if choice == "2":
                sect = input("Введите группу: ").strip()

                if not sect:
                    print("Группа не указана.")
                    continue

                lessons = await app.get_week_schedule(sect)
                title = f"Расписание на неделю: {sect}"
                print(format_schedule_group(lessons, title))

            elif choice == "3":
                teacher = input("Введите преподавателя: ").strip()

                if not teacher:
                    print("Преподаватель не указан.")
                    continue

                lessons = await app.get_teacher_schedule(teacher)
                print(
                    format_schedule_teacher(
                        lessons, f"Расписание преподавателя: {teacher}"
                    )
                )

            elif choice == "5":
                sect = input("Введите группу: ").strip()

                if not sect:
                    print("Группа не указана.")
                    continue

                lessons = await app.get_protection_lessons(group=sect, week_only=True)
                print(
                    format_schedule_protection(
                        lessons, f"Защита/обзор — {sect}", main_group=sect
                    )
                )

            else:
                print("Неизвестная команда.")

    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())

