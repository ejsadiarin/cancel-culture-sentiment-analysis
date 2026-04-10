from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone


@dataclass(slots=True)
class DateRange:
    start: datetime
    end: datetime

    def includes(self, value: datetime | None) -> bool:
        if value is None:
            return False
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return self.start <= value <= self.end


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def build_date_range(start_date: str, end_date: str) -> DateRange:
    start = datetime.combine(parse_iso_date(start_date), time.min, tzinfo=timezone.utc)
    end = datetime.combine(parse_iso_date(end_date), time.max, tzinfo=timezone.utc)
    if end < start:
        raise ValueError("end-date must be the same as or after start-date")
    return DateRange(start=start, end=end)
