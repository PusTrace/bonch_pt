"""Tests for Schedule repository logic using mocked Redis data."""
import asyncio
import json

from repository import RedisDB


class FakeRedis:
    def __init__(self, items: dict[str, str]):
        self._items = items

    async def scan_iter(self, match: str):
        for k in self._items.keys():
            if _match_simple(k, match):
                yield k

    async def get(self, key: str):
        return self._items.get(key)


def _match_simple(key: str, pattern: str) -> bool:
    if pattern == "schedule:*:*:*":
        return key.startswith("schedule:") and key.count(":") >= 3
    sect_part = pattern.split("*", 1)[0]
    return key.startswith(sect_part) and key.startswith("schedule:")


def test_get_schedule_filters_by_sect_and_sorts():
    async def run():
        sect = "ИКБ-31"
        d1 = "2026-11-24"
        d2 = "2026-11-23"
        items = {
            f"schedule:{sect}:{d1}:4": json.dumps(
                {
                    "date": d1,
                    "pair": "4",
                    "subject": "B",
                    "auditorium": "A1",
                    "teacher": "T1",
                    "lesson_type": "Л",
                    "sect": sect,
                },
                ensure_ascii=False,
            ),
            f"schedule:{sect}:{d1}:3": json.dumps(
                {
                    "date": d1,
                    "pair": "3",
                    "subject": "A",
                    "auditorium": "A2",
                    "teacher": "T2",
                    "lesson_type": "П",
                    "sect": sect,
                },
                ensure_ascii=False,
            ),
            f"schedule:{sect}:{d2}:1": json.dumps(
                {
                    "date": d2,
                    "pair": "1",
                    "subject": "C",
                    "auditorium": "A3",
                    "teacher": "T3",
                    "lesson_type": "Л",
                    "sect": sect,
                },
                ensure_ascii=False,
            ),
            "schedule:OTHER:2026-11-24:1": json.dumps(
                {
                    "date": "2026-11-24",
                    "pair": "1",
                    "subject": "X",
                    "auditorium": "X",
                    "teacher": "T",
                    "lesson_type": "Л",
                    "sect": "OTHER",
                },
                ensure_ascii=False,
            ),
        }

        repo = RedisDB(FakeRedis(items))
        lessons = await repo.get_schedule(sect)

        assert [l.date for l in lessons] == [d2, d1, d1]
        assert [l.pair for l in lessons] == ["1", "3", "4"]
        assert all(l.sect == sect for l in lessons)

    asyncio.run(run())


def test_get_teacher_schedule_matches_substring_case_insensitive():
    async def run():
        items = {
            "schedule:ИКБ-31:2026-11-24:3": json.dumps(
                {
                    "date": "2026-11-24",
                    "pair": "3",
                    "subject": "A",
                    "auditorium": "1",
                    "teacher": "Иванов Иван Иванович",
                    "lesson_type": "Л",
                    "sect": "ИКБ-31",
                },
                ensure_ascii=False,
            ),
            "schedule:ИКБ-32:2026-11-24:4": json.dumps(
                {
                    "date": "2026-11-24",
                    "pair": "4",
                    "subject": "B",
                    "auditorium": "2",
                    "teacher": "Петров П. П.",
                    "lesson_type": "П",
                    "sect": "ИКБ-32",
                },
                ensure_ascii=False,
            ),
        }
        repo = RedisDB(FakeRedis(items))

        lessons = await repo.get_teacher_schedule("иванов")
        assert len(lessons) == 1
        assert lessons[0].teacher == "Иванов Иван Иванович"

    asyncio.run(run())
