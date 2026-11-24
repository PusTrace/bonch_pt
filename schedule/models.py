"""Dataclasses for schedule domain."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    date: str
    pair: str | None
    subject: str | None
    auditorium: str | None
    teacher: str | None
    lesson_type: str | None
    sect: str
    time_start: str | None = None
    time_end: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Lesson":
        return cls(
            date=str(data.get("date") or ""),
            pair=data.get("pair"),
            subject=data.get("subject"),
            auditorium=data.get("auditorium"),
            teacher=data.get("teacher"),
            lesson_type=data.get("lesson_type"),
            sect=str(data.get("sect") or ""),
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
        )
