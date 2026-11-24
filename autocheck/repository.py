import json
from datetime import date

from redis.asyncio import Redis


class RedisDB:
    def __init__(self, url: str):
        self.redis = Redis.from_url(
            url,
            decode_responses=True,
        )

    async def get_schedule(self, sect: str, target_date: date) -> list[dict]:
        """Получает расписание группы на конкретную дату."""

        pattern = f"schedule:{sect}:{target_date.isoformat()}:*"
        keys = []

        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if not keys:
            return []

        values = await self.redis.mget(keys)

        schedule = [json.loads(value) for value in values if value is not None]

        schedule.sort(key=lambda item: int(item["pair"]))

        return schedule

    async def check_scheduler(
        self,
        current_date: date,
        sect: str = "ИКБ-31",
    ) -> tuple[list[dict], bool]:
        """Получает расписание на сегодня или на ближайшую будущую дату."""

        today_schedule = await self.get_schedule(sect, current_date)

        if today_schedule:
            return today_schedule, True

        next_dates = await self.redis.zrangebyscore(
            f"schedule:dates:{sect}",
            min=f"({current_date.toordinal()}",
            max="+inf",
            start=0,
            num=1,
        )

        if not next_dates:
            return [], False

        next_date = date.fromisoformat(next_dates[0])

        next_schedule = await self.get_schedule(sect, next_date)

        return next_schedule, False

    async def close(self):
        await self.redis.aclose()
