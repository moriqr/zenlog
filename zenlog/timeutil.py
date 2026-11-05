"""Date/time helpers used across data and UI layers."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

TIME_FMT = "%I:%M %p"
DATE_FMT = "%Y-%m-%d"
ISO_FMT = "%Y-%m-%dT%H:%M:%S"
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def format_time(dt: datetime) -> str:
    """12-hour clock with am/pm, e.g. '9:05 am'."""
    return dt.strftime(TIME_FMT).lstrip("0").lower()


def parse_time(value: str) -> time:
    """Parse '9:05 am', '9:05am', or '21:05' (24-hour still accepted)."""
    raw = " ".join(value.strip().split())
    if not raw:
        raise ValueError("empty time")
    # Normalize "9:05am" → "9:05 am" so %p can match
    lowered = raw.lower()
    if lowered.endswith("am") or lowered.endswith("pm"):
        meridiem = lowered[-2:]
        body = raw[:-2].strip()
        raw = f"{body} {meridiem.upper()}"
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"unrecognized time: {value!r}")


def format_duration(hours: float) -> str:
    total_minutes = int(round(max(0.0, hours) * 60))
    h, m = divmod(total_minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value, ISO_FMT)


def week_bounds(d: date) -> tuple[date, date]:
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end
