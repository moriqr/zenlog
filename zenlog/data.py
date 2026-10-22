"""Persistence and punch-clock business logic."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from zenlog.timeutil import DATE_FMT, ISO_FMT, now, parse_iso

DATA_FILE = Path(__file__).resolve().parent.parent / "punch_data.json"


def default_data() -> dict[str, Any]:
    return {
        "past_hours": 0.0,
        "past_hour_seeds": [],
        "status": "clocked_out",  # clocked_out | clocked_in | on_break
        "current_session": None,
        "current_break": None,
        "sessions": [],
        "breaks": [],
    }


class PunchData:
    def __init__(self, path: Path = DATA_FILE) -> None:
        self.path = path
        self.data = default_data()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.save()
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
        except (json.JSONDecodeError, OSError):
            loaded = {}
        base = default_data()
        base.update({k: loaded.get(k, v) for k, v in base.items()})
        if not isinstance(base["sessions"], list):
            base["sessions"] = []
        if not isinstance(base["breaks"], list):
            base["breaks"] = []
        if not isinstance(base["past_hour_seeds"], list):
            base["past_hour_seeds"] = []
        try:
            base["past_hours"] = float(base.get("past_hours") or 0.0)
        except (TypeError, ValueError):
            base["past_hours"] = 0.0

        # Migrate legacy single past_hours into seed history once.
        if base["past_hours"] and not base["past_hour_seeds"]:
            base["past_hour_seeds"].append(
                {
                    "id": str(uuid.uuid4()),
                    "date": date.today().strftime(DATE_FMT),
                    "hours": round(base["past_hours"], 4),
                    "note": "Migrated from previous past-hours seed",
                    "created_at": now().strftime(ISO_FMT),
                }
            )
        else:
            base["past_hours"] = round(
                sum(float(s.get("hours", 0)) for s in base["past_hour_seeds"]), 4
            )

        self.data = base
        self.save()

    def save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    @property
    def status(self) -> str:
        return self.data["status"]

    @property
    def past_hours(self) -> float:
        return float(self.data["past_hours"])

    def _sync_past_hours(self) -> None:
        self.data["past_hours"] = round(
            sum(float(s.get("hours", 0)) for s in self.data["past_hour_seeds"]), 4
        )

    def add_past_hours_seed(self, hours: float, note: str = "", on_date: str | None = None) -> None:
        entry = {
            "id": str(uuid.uuid4()),
            "date": on_date or date.today().strftime(DATE_FMT),
            "hours": round(float(hours), 4),
            "note": (note or "").strip(),
            "created_at": now().strftime(ISO_FMT),
        }
        self.data["past_hour_seeds"].append(entry)
        self._sync_past_hours()
        self.save()

    def session_hours_sum(self) -> float:
        return sum(float(s.get("duration_hours", 0)) for s in self.data["sessions"])

    def punched_hours(self) -> float:
        """Completed punch sessions only (no seeds)."""
        return self.session_hours_sum() + self.live_session_hours()

    def total_hours(self) -> float:
        """Grand total: punches + forgotten-hour seeds."""
        return self.past_hours + self.session_hours_sum() + self.live_session_hours()

    def live_session_hours(self) -> float:
        session = self.data.get("current_session")
        if not session or self.status == "clocked_out":
            return 0.0
        clock_in = parse_iso(session["clock_in"])
        end = now()
        raw = (end - clock_in).total_seconds() / 3600.0
        return max(0.0, raw - self._break_hours_between(clock_in, end))

    def _break_hours_between(self, start: datetime, end: datetime) -> float:
        total = 0.0
        for b in self.data["breaks"]:
            b_start = parse_iso(b["break_start"])
            b_end = parse_iso(b["break_end"])
            if b_start >= start and b_end <= end:
                total += float(b.get("duration_hours", 0))
        current = self.data.get("current_break")
        if current and self.status == "on_break":
            c_start = parse_iso(current["break_start"])
            if c_start >= start:
                total += max(0.0, (end - c_start).total_seconds() / 3600.0)
        return total

    def clock_in(self) -> None:
        if self.status != "clocked_out":
            return
        t = now()
        self.data["current_session"] = {
            "date": t.strftime(DATE_FMT),
            "clock_in": t.strftime(ISO_FMT),
        }
        self.data["status"] = "clocked_in"
        self.save()

    def clock_out(self) -> None:
        if self.status != "clocked_in" or not self.data["current_session"]:
            return
        t = now()
        session = self.data["current_session"]
        clock_in = parse_iso(session["clock_in"])
        duration_hours = (t - clock_in).total_seconds() / 3600.0
        duration_hours -= self._break_hours_between(clock_in, t)
        completed = {
            "date": session["date"],
            "clock_in": session["clock_in"],
            "clock_out": t.strftime(ISO_FMT),
            "duration_hours": round(max(0.0, duration_hours), 4),
            "type": "work",
        }
        self.data["sessions"].append(completed)
        self.data["current_session"] = None
        self.data["status"] = "clocked_out"
        self.save()

    def start_break(self) -> None:
        if self.status != "clocked_in":
            return
        t = now()
        self.data["current_break"] = {
            "date": t.strftime(DATE_FMT),
            "break_start": t.strftime(ISO_FMT),
        }
        self.data["status"] = "on_break"
        self.save()

    def end_break(self) -> None:
        if self.status != "on_break" or not self.data["current_break"]:
            return
        t = now()
        br = self.data["current_break"]
        start = parse_iso(br["break_start"])
        duration_hours = (t - start).total_seconds() / 3600.0
        completed = {
            "date": br["date"],
            "break_start": br["break_start"],
            "break_end": t.strftime(ISO_FMT),
            "duration_hours": round(duration_hours, 4),
            "type": "break",
        }
        self.data["breaks"].append(completed)
        self.data["current_break"] = None
        self.data["status"] = "clocked_in"
        self.save()

    def hours_on_date(self, day: date) -> float:
        key = day.strftime(DATE_FMT)
        total = sum(
            float(s.get("duration_hours", 0))
            for s in self.data["sessions"]
            if s.get("date") == key
        )
        session = self.data.get("current_session")
        if session and session.get("date") == key and self.status != "clocked_out":
            total += self.live_session_hours()
        return total

    def hours_in_range(self, start: date, end: date) -> float:
        total = 0.0
        cur = start
        while cur <= end:
            total += self.hours_on_date(cur)
            cur += timedelta(days=1)
        return total

    def delete_session(self, clock_in: str) -> bool:
        before = len(self.data["sessions"])
        self.data["sessions"] = [
            s for s in self.data["sessions"] if s.get("clock_in") != clock_in
        ]
        if len(self.data["sessions"]) == before:
            return False
        self.save()
        return True

    def delete_break(self, break_start: str) -> bool:
        before = len(self.data["breaks"])
        self.data["breaks"] = [
            b for b in self.data["breaks"] if b.get("break_start") != break_start
        ]
        if len(self.data["breaks"]) == before:
            return False
        self.save()
        return True

    def punches_on_date(self, day: date) -> list[dict[str, Any]]:
        key = day.strftime(DATE_FMT)
        rows: list[dict[str, Any]] = []
        for s in self.data["sessions"]:
            if s.get("date") != key:
                continue
            rows.append(
                {
                    "type": "Work",
                    "date": s["date"],
                    "start": s["clock_in"],
                    "end": s["clock_out"],
                    "duration_hours": float(s["duration_hours"]),
                    "sort_key": s["clock_out"],
                    "kind": "session",
                    "key": s["clock_in"],
                }
            )
        for b in self.data["breaks"]:
            if b.get("date") != key:
                continue
            rows.append(
                {
                    "type": "Break",
                    "date": b["date"],
                    "start": b["break_start"],
                    "end": b["break_end"],
                    "duration_hours": float(b["duration_hours"]),
                    "sort_key": b["break_end"],
                    "kind": "break",
                    "key": b["break_start"],
                }
            )
        session = self.data.get("current_session")
        if session and session.get("date") == key and self.status != "clocked_out":
            rows.append(
                {
                    "type": "Work (live)",
                    "date": key,
                    "start": session["clock_in"],
                    "end": now().strftime(ISO_FMT),
                    "duration_hours": self.live_session_hours(),
                    "sort_key": now().strftime(ISO_FMT),
                    "kind": None,
                    "key": None,
                }
            )
        rows.sort(key=lambda r: r["sort_key"])
        return rows

    def punches_in_range(self, start: date, end: date) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        cur = start
        while cur <= end:
            rows.extend(self.punches_on_date(cur))
            cur += timedelta(days=1)
        return rows

    def history_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for s in self.data["sessions"]:
            rows.append(
                {
                    "type": "Work",
                    "date": s["date"],
                    "start": s["clock_in"],
                    "end": s["clock_out"],
                    "duration_hours": float(s["duration_hours"]),
                    "sort_key": s["clock_out"],
                    "kind": "session",
                    "key": s["clock_in"],
                }
            )
        for b in self.data["breaks"]:
            rows.append(
                {
                    "type": "Break",
                    "date": b["date"],
                    "start": b["break_start"],
                    "end": b["break_end"],
                    "duration_hours": float(b["duration_hours"]),
                    "sort_key": b["break_end"],
                    "kind": "break",
                    "key": b["break_start"],
                }
            )
        rows.sort(key=lambda r: r["sort_key"], reverse=True)
        return rows

    def seed_rows(self) -> list[dict[str, Any]]:
        rows = list(self.data["past_hour_seeds"])
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows

