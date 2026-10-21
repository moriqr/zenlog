"""
ZenLog — a cozy standalone punch-clock desktop app.

Clock Out while on break is disabled; end the break first, then clock out.
Break time is logged separately and never counted toward work hours.
Calendar / week / month views use punch sessions only — past-hour seeds are separate.
"""

from __future__ import annotations

import calendar
import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import customtkinter as ctk

DATA_FILE = Path(__file__).resolve().parent / "punch_data.json"

COLORS = {
    "bg": "#F5F0FA",
    "card": "#FFF8FC",
    "lavender": "#C9B8E8",
    "lavender_hover": "#B8A4DE",
    "pink": "#F5C6D0",
    "pink_hover": "#EFB0BE",
    "mint": "#B8E0D2",
    "mint_hover": "#A0D4C2",
    "cream": "#FFF5E6",
    "peach": "#FFD6C9",
    "peach_hover": "#FFC4B3",
    "text": "#5C4A6E",
    "text_muted": "#9A8AA8",
    "border": "#E8DCEF",
    "disabled": "#E5DEEB",
    "disabled_text": "#B0A4BC",
    "today": "#EDE4F7",
    "selected": "#D9C8F0",
}

TIME_FMT = "%I:%M %p"
DATE_FMT = "%Y-%m-%d"
ISO_FMT = "%Y-%m-%dT%H:%M:%S"
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def format_time(dt: datetime) -> str:
    return dt.strftime(TIME_FMT).lstrip("0")


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
                }
            )
        rows.sort(key=lambda r: r["sort_key"], reverse=True)
        return rows

    def seed_rows(self) -> list[dict[str, Any]]:
        rows = list(self.data["past_hour_seeds"])
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows


class ZenLogApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.store = PunchData()
        self.view_month = date.today().replace(day=1)
        self.selected_day: date | None = date.today()
        self.detail_mode = "day"  # day | week | month

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("ZenLog")
        self.geometry("860x860")
        self.minsize(760, 760)
        self.configure(fg_color=COLORS["bg"])

        self._build_ui()
        self._refresh()
        self.after(30_000, self._tick)

    def _tick(self) -> None:
        if self.store.status != "clocked_out":
            self._refresh()
        self.after(30_000, self._tick)

    def _build_ui(self) -> None:
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            outer,
            text="ZenLog",
            font=ctk.CTkFont(family="Segoe UI", size=34, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            outer,
            text="Punch times are saved to disk — you can close the app anytime.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 12))

        # Status + totals
        top = ctk.CTkFrame(outer, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))
        top.grid_columnconfigure((0, 1), weight=1, uniform="top")

        status_card = ctk.CTkFrame(
            top,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        status_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.status_label = ctk.CTkLabel(
            status_card,
            text="Clocked Out",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"],
        )
        self.status_label.pack(padx=18, pady=(14, 2), anchor="w")

        self.status_detail = ctk.CTkLabel(
            status_card,
            text="Ready when you are.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"],
        )
        self.status_detail.pack(padx=18, pady=(0, 14), anchor="w")

        total_card = ctk.CTkFrame(
            top,
            fg_color=COLORS["cream"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        total_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.punched_label = ctk.CTkLabel(
            total_card,
            text="Punched: 0h",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"],
        )
        self.punched_label.pack(padx=18, pady=(14, 2), anchor="w")

        self.total_label = ctk.CTkLabel(
            total_card,
            text="All-time (incl. seeds): 0h",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"],
        )
        self.total_label.pack(padx=18, pady=(0, 14), anchor="w")

        # Action buttons
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 6))
        btn_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="btns")

        self.clock_in_btn = ctk.CTkButton(
            btn_row,
            text="Clock In",
            height=42,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=self._on_clock_in,
        )
        self.clock_in_btn.grid(row=0, column=0, sticky="ew", padx=3, pady=3)

        self.clock_out_btn = ctk.CTkButton(
            btn_row,
            text="Clock Out",
            height=42,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=COLORS["pink"],
            hover_color=COLORS["pink_hover"],
            text_color=COLORS["text"],
            command=self._on_clock_out,
        )
        self.clock_out_btn.grid(row=0, column=1, sticky="ew", padx=3, pady=3)

        self.start_break_btn = ctk.CTkButton(
            btn_row,
            text="Start Break",
            height=42,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=COLORS["mint"],
            hover_color=COLORS["mint_hover"],
            text_color=COLORS["text"],
            command=self._on_start_break,
        )
        self.start_break_btn.grid(row=0, column=2, sticky="ew", padx=3, pady=3)

        self.end_break_btn = ctk.CTkButton(
            btn_row,
            text="End Break",
            height=42,
            corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=COLORS["peach"],
            hover_color=COLORS["peach_hover"],
            text_color=COLORS["text"],
            command=self._on_end_break,
        )
        self.end_break_btn.grid(row=0, column=3, sticky="ew", padx=3, pady=3)

        # Tabs
        self.tabs = ctk.CTkTabview(
            outer,
            fg_color=COLORS["card"],
            segmented_button_fg_color=COLORS["lavender"],
            segmented_button_selected_color=COLORS["lavender_hover"],
            segmented_button_selected_hover_color=COLORS["lavender_hover"],
            segmented_button_unselected_color=COLORS["cream"],
            segmented_button_unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.tabs.pack(fill="both", expand=True, pady=(8, 0))
        self.tabs.add("Calendar")
        self.tabs.add("Recent")
        self.tabs.add("Forgotten Hours")

        self._build_calendar_tab(self.tabs.tab("Calendar"))
        self._build_recent_tab(self.tabs.tab("Recent"))
        self._build_seeds_tab(self.tabs.tab("Forgotten Hours"))

    def _build_calendar_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        nav = ctk.CTkFrame(parent, fg_color="transparent")
        nav.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav,
            text="‹",
            width=40,
            height=32,
            corner_radius=10,
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=self._prev_month,
        ).grid(row=0, column=0, padx=(0, 6))

        self.month_label = ctk.CTkLabel(
            nav,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"],
        )
        self.month_label.grid(row=0, column=1)

        ctk.CTkButton(
            nav,
            text="›",
            width=40,
            height=32,
            corner_radius=10,
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=self._next_month,
        ).grid(row=0, column=2, padx=(6, 0))

        summary_row = ctk.CTkFrame(parent, fg_color="transparent")
        summary_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        summary_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="sum")

        ctk.CTkButton(
            summary_row,
            text="This Week",
            height=34,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS["mint"],
            hover_color=COLORS["mint_hover"],
            text_color=COLORS["text"],
            command=self._show_week_summary,
        ).grid(row=0, column=0, sticky="ew", padx=3)

        ctk.CTkButton(
            summary_row,
            text="Month So Far",
            height=34,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS["peach"],
            hover_color=COLORS["peach_hover"],
            text_color=COLORS["text"],
            command=self._show_month_summary,
        ).grid(row=0, column=1, sticky="ew", padx=3)

        ctk.CTkButton(
            summary_row,
            text="Selected Day",
            height=34,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=self._show_day_summary,
        ).grid(row=0, column=2, sticky="ew", padx=3)

        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        cal_wrap = ctk.CTkFrame(
            body,
            fg_color=COLORS["cream"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        cal_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.calendar_grid = ctk.CTkFrame(cal_wrap, fg_color="transparent")
        self.calendar_grid.pack(fill="both", expand=True, padx=10, pady=10)

        detail_wrap = ctk.CTkFrame(
            body,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        detail_wrap.grid(row=0, column=1, sticky="nsew")

        self.detail_title = ctk.CTkLabel(
            detail_wrap,
            text="Day detail",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text"],
        )
        self.detail_title.pack(anchor="w", padx=12, pady=(12, 2))

        self.detail_sub = ctk.CTkLabel(
            detail_wrap,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"],
        )
        self.detail_sub.pack(anchor="w", padx=12, pady=(0, 6))

        self.detail_list = ctk.CTkScrollableFrame(
            detail_wrap,
            fg_color="transparent",
        )
        self.detail_list.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    def _build_recent_tab(self, parent: ctk.CTkFrame) -> None:
        self.history_frame = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
        )
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _build_seeds_tab(self, parent: ctk.CTkFrame) -> None:
        form = ctk.CTkFrame(
            parent,
            fg_color=COLORS["cream"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        form.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            form,
            text="Add forgotten hours (not shown on calendar)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=14, pady=(12, 6))

        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 6))

        self.seed_hours_entry = ctk.CTkEntry(
            row,
            placeholder_text="Hours e.g. 2.5",
            height=34,
            corner_radius=10,
            border_color=COLORS["border"],
            fg_color=COLORS["card"],
            text_color=COLORS["text"],
            width=120,
        )
        self.seed_hours_entry.pack(side="left", padx=(0, 8))

        self.seed_date_entry = ctk.CTkEntry(
            row,
            placeholder_text="Date YYYY-MM-DD",
            height=34,
            corner_radius=10,
            border_color=COLORS["border"],
            fg_color=COLORS["card"],
            text_color=COLORS["text"],
            width=140,
        )
        self.seed_date_entry.pack(side="left", padx=(0, 8))
        self.seed_date_entry.insert(0, date.today().strftime(DATE_FMT))

        self.seed_note_entry = ctk.CTkEntry(
            row,
            placeholder_text="Optional note",
            height=34,
            corner_radius=10,
            border_color=COLORS["border"],
            fg_color=COLORS["card"],
            text_color=COLORS["text"],
        )
        self.seed_note_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            row,
            text="Add",
            width=80,
            height=34,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=self._on_add_seed,
        ).pack(side="right")

        self.seed_hint = ctk.CTkLabel(
            form,
            text="Seeds only affect the all-time total — never week/month calendar hours.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_muted"],
        )
        self.seed_hint.pack(anchor="w", padx=14, pady=(0, 12))

        self.seeds_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.seeds_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _set_button_state(self, btn: ctk.CTkButton, enabled: bool) -> None:
        btn.configure(state="normal" if enabled else "disabled")

    def _prev_month(self) -> None:
        y, m = self.view_month.year, self.view_month.month
        if m == 1:
            self.view_month = date(y - 1, 12, 1)
        else:
            self.view_month = date(y, m - 1, 1)
        self._render_calendar()

    def _next_month(self) -> None:
        y, m = self.view_month.year, self.view_month.month
        if m == 12:
            self.view_month = date(y + 1, 1, 1)
        else:
            self.view_month = date(y, m + 1, 1)
        self._render_calendar()

    def _select_day(self, day: date) -> None:
        self.selected_day = day
        self.detail_mode = "day"
        self._render_calendar()
        self._render_detail()

    def _show_day_summary(self) -> None:
        if self.selected_day is None:
            self.selected_day = date.today()
        self.detail_mode = "day"
        self._render_detail()

    def _show_week_summary(self) -> None:
        if self.selected_day is None:
            self.selected_day = date.today()
        self.detail_mode = "week"
        self._render_detail()

    def _show_month_summary(self) -> None:
        self.detail_mode = "month"
        self._render_detail()

    def _refresh(self) -> None:
        status = self.store.status
        session = self.store.data.get("current_session")
        current_break = self.store.data.get("current_break")

        if status == "clocked_out":
            self.status_label.configure(text="Clocked Out")
            self.status_detail.configure(text="Ready when you are.")
        elif status == "clocked_in" and session:
            in_time = format_time(parse_iso(session["clock_in"]))
            live = format_duration(self.store.live_session_hours())
            self.status_label.configure(text=f"Clocked In at {in_time}")
            self.status_detail.configure(text=f"Working — {live} so far this session.")
        elif status == "on_break" and current_break:
            br_time = format_time(parse_iso(current_break["break_start"]))
            self.status_label.configure(text=f"On Break since {br_time}")
            self.status_detail.configure(text="End break before clocking out.")
        else:
            self.status_label.configure(text="Clocked Out")
            self.status_detail.configure(text="Ready when you are.")

        punched = self.store.punched_hours()
        total = self.store.total_hours()
        self.punched_label.configure(text=f"Punched: {format_duration(punched)} ({punched:.2f}h)")
        self.total_label.configure(
            text=f"All-time (incl. seeds): {format_duration(total)} ({total:.2f}h)"
        )

        self._set_button_state(self.clock_in_btn, status == "clocked_out")
        self._set_button_state(self.clock_out_btn, status == "clocked_in")
        self._set_button_state(self.start_break_btn, status == "clocked_in")
        self._set_button_state(self.end_break_btn, status == "on_break")

        self._render_calendar()
        self._render_detail()
        self._render_history()
        self._render_seeds()

    def _render_calendar(self) -> None:
        for child in self.calendar_grid.winfo_children():
            child.destroy()

        self.month_label.configure(text=self.view_month.strftime("%B %Y"))

        for i, name in enumerate(WEEKDAYS):
            self.calendar_grid.grid_columnconfigure(i, weight=1, uniform="cal")
            ctk.CTkLabel(
                self.calendar_grid,
                text=name,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=COLORS["text_muted"],
            ).grid(row=0, column=i, pady=(0, 4))

        today = date.today()
        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(
            self.view_month.year, self.view_month.month
        )

        for r, week in enumerate(weeks, start=1):
            self.calendar_grid.grid_rowconfigure(r, weight=1)
            for c, day in enumerate(week):
                in_month = day.month == self.view_month.month
                hours = self.store.hours_on_date(day) if in_month else 0.0
                is_today = day == today
                is_selected = self.selected_day == day

                if is_selected and in_month:
                    bg = COLORS["selected"]
                elif is_today and in_month:
                    bg = COLORS["today"]
                else:
                    bg = COLORS["card"] if in_month else COLORS["disabled"]

                hours_text = format_duration(hours) if in_month and hours > 0 else "—"
                day_color = COLORS["text"] if in_month else COLORS["disabled_text"]
                cell = ctk.CTkButton(
                    self.calendar_grid,
                    text=f"{day.day}\n{hours_text}",
                    fg_color=bg,
                    hover_color=COLORS["lavender"] if in_month else COLORS["disabled"],
                    corner_radius=10,
                    border_width=1,
                    border_color=COLORS["border"],
                    text_color=day_color,
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    command=(lambda d=day: self._select_day(d)) if in_month else None,
                    state="normal" if in_month else "disabled",
                )
                cell.grid(row=r, column=c, sticky="nsew", padx=2, pady=2, ipady=10)

    def _render_detail(self) -> None:
        for child in self.detail_list.winfo_children():
            child.destroy()

        today = date.today()
        if self.detail_mode == "week":
            anchor = self.selected_day or today
            start, end = week_bounds(anchor)
            end_cap = min(end, today)
            rows = self.store.punches_in_range(start, end_cap)
            total = self.store.hours_in_range(start, end_cap)
            self.detail_title.configure(text="Week summary")
            self.detail_sub.configure(
                text=f"{start.strftime('%b %d')} – {end_cap.strftime('%b %d')}: "
                f"{format_duration(total)} ({total:.2f}h)"
            )
        elif self.detail_mode == "month":
            start = self.view_month
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = date(start.year, start.month, last_day)
            end_cap = min(end, today)
            rows = self.store.punches_in_range(start, end_cap)
            total = self.store.hours_in_range(start, end_cap)
            self.detail_title.configure(text="Month so far")
            self.detail_sub.configure(
                text=f"{start.strftime('%B %Y')} through {end_cap.strftime('%b %d')}: "
                f"{format_duration(total)} ({total:.2f}h)"
            )
        else:
            day = self.selected_day or today
            rows = self.store.punches_on_date(day)
            total = self.store.hours_on_date(day)
            self.detail_title.configure(text="Day detail")
            self.detail_sub.configure(
                text=f"{day.strftime('%A, %b %d')}: {format_duration(total)} ({total:.2f}h)"
            )

        if not rows:
            ctk.CTkLabel(
                self.detail_list,
                text="No punches in this range.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS["text_muted"],
            ).pack(anchor="w", padx=6, pady=10)
            return

        for i, row in enumerate(rows):
            bg = COLORS["cream"] if i % 2 == 0 else COLORS["bg"]
            line = ctk.CTkFrame(self.detail_list, fg_color=bg, corner_radius=8)
            line.pack(fill="x", pady=2)

            badge_color = COLORS["lavender"] if "Work" in row["type"] else COLORS["mint"]
            ctk.CTkLabel(
                line,
                text=row["type"],
                width=78,
                height=22,
                corner_radius=6,
                fg_color=badge_color,
                text_color=COLORS["text"],
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            ).pack(side="left", padx=(8, 4), pady=6)

            start_t = format_time(parse_iso(row["start"]))
            end_t = format_time(parse_iso(row["end"]))
            ctk.CTkLabel(
                line,
                text=f"{row['date']}  {start_t}–{end_t}  ·  {format_duration(row['duration_hours'])}",
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLORS["text"],
            ).pack(side="left", fill="x", expand=True, padx=(0, 8), pady=6)

    def _render_history(self) -> None:
        for child in self.history_frame.winfo_children():
            child.destroy()

        rows = self.store.history_rows()
        if not rows:
            ctk.CTkLabel(
                self.history_frame,
                text="No sessions yet — your cozy log will appear here.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["text_muted"],
            ).pack(padx=12, pady=16, anchor="w")
            return

        for i, row in enumerate(rows):
            bg = COLORS["cream"] if i % 2 == 0 else COLORS["bg"]
            line = ctk.CTkFrame(self.history_frame, fg_color=bg, corner_radius=10)
            line.pack(fill="x", padx=4, pady=3)

            type_color = COLORS["lavender"] if row["type"] == "Work" else COLORS["mint"]
            ctk.CTkLabel(
                line,
                text=row["type"],
                width=70,
                height=26,
                corner_radius=8,
                fg_color=type_color,
                text_color=COLORS["text"],
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            ).pack(side="left", padx=(10, 4), pady=8)

            start_dt = parse_iso(row["start"])
            end_dt = parse_iso(row["end"])
            cells = [
                (row["date"], 100),
                (format_time(start_dt), 100),
                (format_time(end_dt), 100),
                (format_duration(row["duration_hours"]), 80),
            ]
            for text, width in cells:
                ctk.CTkLabel(
                    line,
                    text=text,
                    width=width,
                    anchor="w",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=COLORS["text"],
                ).pack(side="left", padx=4, pady=8)

    def _render_seeds(self) -> None:
        for child in self.seeds_frame.winfo_children():
            child.destroy()

        rows = self.store.seed_rows()
        if not rows:
            ctk.CTkLabel(
                self.seeds_frame,
                text="No forgotten-hour entries yet.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["text_muted"],
            ).pack(padx=12, pady=16, anchor="w")
            return

        for i, row in enumerate(rows):
            bg = COLORS["cream"] if i % 2 == 0 else COLORS["bg"]
            line = ctk.CTkFrame(self.seeds_frame, fg_color=bg, corner_radius=10)
            line.pack(fill="x", padx=4, pady=3)

            ctk.CTkLabel(
                line,
                text=format_duration(float(row.get("hours", 0))),
                width=70,
                height=26,
                corner_radius=8,
                fg_color=COLORS["peach"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            ).pack(side="left", padx=(10, 4), pady=8)

            note = row.get("note") or "No note"
            created = row.get("created_at", "")
            created_txt = format_time(parse_iso(created)) if created else ""
            ctk.CTkLabel(
                line,
                text=f"{row.get('date', '')}  ·  {float(row.get('hours', 0)):g}h  ·  {note}"
                + (f"  (logged {created_txt})" if created_txt else ""),
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS["text"],
            ).pack(side="left", fill="x", expand=True, padx=4, pady=8)

    def _on_clock_in(self) -> None:
        self.store.clock_in()
        self._refresh()

    def _on_clock_out(self) -> None:
        self.store.clock_out()
        self._refresh()

    def _on_start_break(self) -> None:
        self.store.start_break()
        self._refresh()

    def _on_end_break(self) -> None:
        self.store.end_break()
        self._refresh()

    def _on_add_seed(self) -> None:
        raw = self.seed_hours_entry.get().strip()
        date_raw = self.seed_date_entry.get().strip() or date.today().strftime(DATE_FMT)
        note = self.seed_note_entry.get().strip()
        try:
            value = float(raw)
            if value <= 0:
                raise ValueError
        except ValueError:
            self.seed_hint.configure(text="Enter a positive number of hours.")
            return
        try:
            datetime.strptime(date_raw, DATE_FMT)
        except ValueError:
            self.seed_hint.configure(text="Date must be YYYY-MM-DD.")
            return

        self.store.add_past_hours_seed(value, note=note, on_date=date_raw)
        self.seed_hours_entry.delete(0, "end")
        self.seed_note_entry.delete(0, "end")
        self.seed_hint.configure(
            text=f"Added {value:g}h seed for {date_raw}. Seeds stay off the calendar."
        )
        self._refresh()


def main() -> None:
    app = ZenLogApp()
    app.mainloop()


if __name__ == "__main__":
    main()
