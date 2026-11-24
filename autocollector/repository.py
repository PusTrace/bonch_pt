import json
from datetime import date, timedelta

from redis.asyncio import Redis


class RedisDB:
    def __init__(self, url: str):
        self.redis = Redis.from_url(
            url,
            decode_responses=True,
        )

    async def insert_schedule(self, data: list[tuple]):
        async with self.redis.pipeline(transaction=True) as pipe:
            for item in data:
                if len(item) == 9:
                    (
                        date_str,
                        pair,
                        subject,
                        auditorium,
                        teacher,
                        lesson_type,
                        sect,
                        time_start,
                        time_end,
                    ) = item
                else:
                    (
                        date_str,
                        pair,
                        subject,
                        auditorium,
                        teacher,
                        lesson_type,
                        sect,
                    ) = item
                    time_start, time_end = None, None

                key = f"schedule:{sect}:{date_str}:{pair}:{time_start or ''}"

                value = {
                    "date": date_str,
                    "pair": pair,
                    "subject": subject,
                    "auditorium": auditorium,
                    "teacher": teacher,
                    "lesson_type": lesson_type,
                    "sect": sect,
                    "time_start": time_start,
                    "time_end": time_end,
                }

                pipe.set(key, json.dumps(value, ensure_ascii=False))

                pipe.zadd(
                    f"schedule:dates:{sect}",
                    {date_str: date.fromisoformat(date_str).toordinal()},
                )

            await pipe.execute()

    async def get_last_date(self, sect: str) -> date:
        result = await self.redis.zrevrange(
            f"schedule:dates:{sect}",
            0,
            0,
        )

        if result:
            return date.fromisoformat(result[0])

        return date.today()

    async def close(self):
        await self.redis.aclose()

    async def replace_schedule(
        self,
        sect: str,
        week_start: date,
        data: list[tuple],
    ):
        week_dates = [(week_start + timedelta(days=i)).isoformat() for i in range(7)]

        # Находим старые записи за эту неделю
        old_keys = []

        for day in week_dates:
            pattern = f"schedule:{sect}:{day}:*"

            async for key in self.redis.scan_iter(match=pattern):
                old_keys.append(key)

        # Удаляем старые записи и добавляем новые
        async with self.redis.pipeline(transaction=True) as pipe:
            if old_keys:
                pipe.delete(*old_keys)

            # Удаляем даты недели из индекса
            pipe.zrem(f"schedule:dates:{sect}", *week_dates)

            for item in data:
                if len(item) == 9:
                    (
                        date_str,
                        pair,
                        subject,
                        auditorium,
                        teacher,
                        lesson_type,
                        sect,
                        time_start,
                        time_end,
                    ) = item
                else:
                    (
                        date_str,
                        pair,
                        subject,
                        auditorium,
                        teacher,
                        lesson_type,
                        sect,
                    ) = item
                    time_start, time_end = None, None

                if pair is None:
                    continue

                key = f"schedule:{sect}:{date_str}:{pair}:{time_start or ''}"

                value = {
                    "date": date_str,
                    "pair": pair,
                    "subject": subject,
                    "auditorium": auditorium,
                    "teacher": teacher,
                    "lesson_type": lesson_type,
                    "sect": sect,
                    "time_start": time_start,
                    "time_end": time_end,
                }

                pipe.set(
                    key,
                    json.dumps(value, ensure_ascii=False),
                )

                pipe.zadd(
                    f"schedule:dates:{sect}",
                    {date_str: date.fromisoformat(date_str).toordinal()},
                )

            await pipe.execute()
