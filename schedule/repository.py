import json
from datetime import date, datetime, timedelta
from typing import Any

from models import Lesson


class RedisDB:
    def __init__(self, redis: Any):
        self.redis = redis

    async def get_schedule(self, sect: str) -> list[Lesson]:
        """Получить всё расписание группы (из Redis)."""

        result: list[Lesson] = []

        async for key in self.redis.scan_iter(match=f"schedule:{sect}:*:*"):
            data = await self.redis.get(key)

            if data:
                result.append(Lesson.from_dict(json.loads(data)))

        def sort_key(x: Lesson):
            ts = x.time_start or "99:99"
            try:
                pair_n = int(str(x.pair)) if x.pair is not None else 10**9
            except ValueError:
                pair_n = 10**9
            return (x.date, ts, pair_n)

        return sorted(result, key=sort_key)

    async def get_week_schedule(self, sect: str) -> list[Lesson]:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        schedule = await self.get_schedule(sect)

        return [
            item
            for item in schedule
            if monday.isoformat() <= item.date <= sunday.isoformat()
        ]

    async def get_teacher_schedule(self, teacher: str) -> list[Lesson]:
        """Найти расписание преподавателя во всех группах (из Redis)."""

        result: list[Lesson] = []
        needle = teacher.lower()

        async for key in self.redis.scan_iter(match="schedule:*:*:*"):
            data = await self.redis.get(key)

            if not data:
                continue

            item = Lesson.from_dict(json.loads(data))

            if item.teacher and needle in item.teacher.lower():
                result.append(item)

        def sort_key(x: Lesson):
            ts = x.time_start or "99:99"
            try:
                pair_n = int(str(x.pair)) if x.pair is not None else 10**9
            except ValueError:
                pair_n = 10**9
            return (x.date, ts, pair_n)

        return sorted(result, key=sort_key)

    async def get_protection_lessons(
        self, group: str | None = None, week_only: bool = True
    ) -> list[Lesson]:
        """Для protection: пары преподавателей (без лекций). Если group задан — только преподаватели этой группы."""
        if group:
            base = await self.get_week_schedule(group) if week_only else await self.get_schedule(group)
            teachers = {
                (item.teacher or "").strip()
                for item in base
                if (item.teacher or "").strip()
                and "лекц" not in (item.lesson_type or "").strip().lower()
            }
        else:
            teachers = None

        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        result: list[Lesson] = []
        async for key in self.redis.scan_iter(match="schedule:*:*:*"):
            data = await self.redis.get(key)
            if not data:
                continue
            item = Lesson.from_dict(json.loads(data))
            if not item.teacher or not item.teacher.strip():
                continue
            lt = (item.lesson_type or "").strip().lower()
            if "лекц" in lt:
                continue
            if teachers is not None and item.teacher.strip() not in teachers:
                continue
            if week_only:
                if not (monday.isoformat() <= item.date <= sunday.isoformat()):
                    continue
            result.append(item)

        def sort_key(x: Lesson):
            ts = x.time_start or "99:99"
            try:
                pair_n = int(str(x.pair)) if x.pair is not None else 10**9
            except ValueError:
                pair_n = 10**9
            return (x.date, ts, pair_n)

        return sorted(result, key=sort_key)

    async def log_command(self, user_id: int | None, command: str, args: str = "") -> None:
        """Лог вызова команды в Redis (список последних событий)."""
        if user_id is None:
            user_id = 0
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "command": command,
            "args": args[:500],
        }
        key = "bot:command_log"
        try:
            await self.redis.lpush(key, json.dumps(entry, ensure_ascii=False))
            await self.redis.ltrim(key, 0, 999)
        except Exception:
            pass

    async def set_user_group(self, user_id: int, group: str) -> None:
        await self.redis.set(f"bot:user_group:{user_id}", group.strip())

    async def get_user_group(self, user_id: int) -> str | None:
        val = await self.redis.get(f"bot:user_group:{user_id}")
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None
