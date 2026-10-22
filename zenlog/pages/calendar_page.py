"""Calendar page — month grid and day/week/month punch detail."""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox

from zenlog.data import PunchData
from zenlog.theme import COLORS, FONT_FAMILY
from zenlog.timeutil import WEEKDAYS, format_duration, format_time, parse_iso, week_bounds


class CalendarPage(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        store: PunchData,
        on_change: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.store = store
        self.on_change = on_change
        self.view_month = date.today().replace(day=1)
        self.selected_day: date | None = date.today()
        self.detail_mode = "day"  # day | week | month
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Calendar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            self,
            text="Browse punch sessions by day, week, or month. Past-hour seeds stay off this view.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 12))

        card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="both", expand=True)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        nav = ctk.CTkFrame(card, fg_color="transparent")
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
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

        summary_row = ctk.CTkFrame(card, fg_color="transparent")
        summary_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        summary_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="sum")

        ctk.CTkButton(
            summary_row,
            text="This Week",
            height=34,
            corner_radius=10,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=self._show_day_summary,
        ).grid(row=0, column=2, sticky="ew", padx=3)

        body = ctk.CTkFrame(card, fg_color="transparent")
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS["text"],
        )
        self.detail_title.pack(anchor="w", padx=12, pady=(12, 2))

        self.detail_sub = ctk.CTkLabel(
            detail_wrap,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_muted"],
        )
        self.detail_sub.pack(anchor="w", padx=12, pady=(0, 6))

        self.detail_list = ctk.CTkScrollableFrame(
            detail_wrap,
            fg_color="transparent",
        )
        self.detail_list.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    def refresh(self) -> None:
        self._render_calendar()
        self._render_detail()

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

    def _render_calendar(self) -> None:
        for child in self.calendar_grid.winfo_children():
            child.destroy()

        self.month_label.configure(text=self.view_month.strftime("%B %Y"))

        for i, name in enumerate(WEEKDAYS):
            self.calendar_grid.grid_columnconfigure(i, weight=1, uniform="cal")
            ctk.CTkLabel(
                self.calendar_grid,
                text=name,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
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
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
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
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
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
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            ).pack(side="left", padx=(8, 4), pady=6)

            start_t = format_time(parse_iso(row["start"]))
            end_t = format_time(parse_iso(row["end"]))
            ctk.CTkLabel(
                line,
                text=f"{row['date']}  {start_t}–{end_t}  ·  {format_duration(row['duration_hours'])}",
                anchor="w",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=COLORS["text"],
            ).pack(side="left", fill="x", expand=True, padx=(0, 4), pady=6)

            if row.get("kind") and row.get("key"):
                ctk.CTkButton(
                    line,
                    text="Delete",
                    width=58,
                    height=22,
                    corner_radius=6,
                    fg_color=COLORS["pink"],
                    hover_color=COLORS["pink_hover"],
                    text_color=COLORS["text"],
                    font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                    command=lambda r=row: self._on_delete_punch(r),
                ).pack(side="right", padx=(0, 8), pady=6)

    def _on_delete_punch(self, row: dict[str, Any]) -> None:
        kind = row.get("kind")
        key = row.get("key")
        if not kind or not key:
            return

        start_t = format_time(parse_iso(row["start"]))
        end_t = format_time(parse_iso(row["end"]))
        label = "work session" if kind == "session" else "break"
        confirmed = messagebox.askyesno(
            "Delete punch",
            f"Delete this {label}?\n\n"
            f"{row['date']}  {start_t}–{end_t}  ·  {format_duration(row['duration_hours'])}",
            parent=self.winfo_toplevel(),
        )
        if not confirmed:
            return

        deleted = (
            self.store.delete_session(key)
            if kind == "session"
            else self.store.delete_break(key)
        )
        if deleted:
            self.on_change()
