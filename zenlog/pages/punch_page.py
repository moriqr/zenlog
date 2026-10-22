"""Punch page — clock actions, recent history, and forgotten-hour seeds."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox

from zenlog.data import PunchData
from zenlog.theme import COLORS, FONT_FAMILY
from zenlog.timeutil import DATE_FMT, format_duration, format_time, parse_iso


class PunchPage(ctk.CTkFrame):
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
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Punch clock",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            self,
            text="Clock in and out here. Breaks are logged separately and never count as work.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 12))

        top = ctk.CTkFrame(self, fg_color="transparent")
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=COLORS["text"],
        )
        self.status_label.pack(padx=18, pady=(14, 2), anchor="w")

        self.status_detail = ctk.CTkLabel(
            status_card,
            text="Ready when you are.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=COLORS["text"],
        )
        self.punched_label.pack(padx=18, pady=(14, 2), anchor="w")

        self.total_label = ctk.CTkLabel(
            total_card,
            text="All-time (incl. seeds): 0h",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_muted"],
        )
        self.total_label.pack(padx=18, pady=(0, 14), anchor="w")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 6))
        btn_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="btns")

        self.clock_in_btn = ctk.CTkButton(
            btn_row,
            text="Clock In",
            height=42,
            corner_radius=12,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            fg_color=COLORS["peach"],
            hover_color=COLORS["peach_hover"],
            text_color=COLORS["text"],
            command=self._on_end_break,
        )
        self.end_break_btn.grid(row=0, column=3, sticky="ew", padx=3, pady=3)

        self.tabs = ctk.CTkTabview(
            self,
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
        self.tabs.add("Recent")
        self.tabs.add("Forgotten Hours")

        self.history_frame = ctk.CTkScrollableFrame(
            self.tabs.tab("Recent"),
            fg_color="transparent",
        )
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_seeds_tab(self.tabs.tab("Forgotten Hours"))

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
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
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
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=self._on_add_seed,
        ).pack(side="right")

        self.seed_hint = ctk.CTkLabel(
            form,
            text="Seeds only affect the all-time total — never week/month calendar hours.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_muted"],
        )
        self.seed_hint.pack(anchor="w", padx=14, pady=(0, 12))

        self.seeds_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.seeds_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    @staticmethod
    def _set_button_state(btn: ctk.CTkButton, enabled: bool) -> None:
        btn.configure(state="normal" if enabled else "disabled")

    def refresh(self) -> None:
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

        self._render_history()
        self._render_seeds()

    def _render_history(self) -> None:
        for child in self.history_frame.winfo_children():
            child.destroy()

        rows = self.store.history_rows()
        if not rows:
            ctk.CTkLabel(
                self.history_frame,
                text="No sessions yet — your cozy log will appear here.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
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
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
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
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                    text_color=COLORS["text"],
                ).pack(side="left", padx=4, pady=8)

            if row.get("kind") and row.get("key"):
                ctk.CTkButton(
                    line,
                    text="Delete",
                    width=64,
                    height=26,
                    corner_radius=8,
                    fg_color=COLORS["pink"],
                    hover_color=COLORS["pink_hover"],
                    text_color=COLORS["text"],
                    font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                    command=lambda r=row: self._on_delete_punch(r),
                ).pack(side="right", padx=(4, 10), pady=8)

    def _render_seeds(self) -> None:
        for child in self.seeds_frame.winfo_children():
            child.destroy()

        rows = self.store.seed_rows()
        if not rows:
            ctk.CTkLabel(
                self.seeds_frame,
                text="No forgotten-hour entries yet.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
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
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            ).pack(side="left", padx=(10, 4), pady=8)

            note = row.get("note") or "No note"
            created = row.get("created_at", "")
            created_txt = format_time(parse_iso(created)) if created else ""
            ctk.CTkLabel(
                line,
                text=f"{row.get('date', '')}  ·  {float(row.get('hours', 0)):g}h  ·  {note}"
                + (f"  (logged {created_txt})" if created_txt else ""),
                anchor="w",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=COLORS["text"],
            ).pack(side="left", fill="x", expand=True, padx=4, pady=8)

    def _on_clock_in(self) -> None:
        self.store.clock_in()
        self.on_change()

    def _on_clock_out(self) -> None:
        self.store.clock_out()
        self.on_change()

    def _on_start_break(self) -> None:
        self.store.start_break()
        self.on_change()

    def _on_end_break(self) -> None:
        self.store.end_break()
        self.on_change()

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
        self.on_change()
