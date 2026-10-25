"""History page — view, edit, and delete logged work sessions and breaks."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox

from zenlog.data import PunchData
from zenlog.theme import BORDER_WIDTH, COLORS, FONT_BODY, FONT_DISPLAY
from zenlog.timeutil import DATE_FMT, format_duration, format_time, parse_iso
from zenlog.widgets import cute_panel, cute_window, page_title, pill_button


class HistoryPage(ctk.CTkFrame):
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
        page_title(
            self,
            "History",
            "All punched work and break sessions. Edit a row to fix wrong times, or delete a mistake.",
        )

        totals = cute_panel(self, chunky=True)
        totals.pack(fill="x", pady=(0, 12))

        self.punched_label = ctk.CTkLabel(
            totals,
            text="Punched: 0h",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=14, weight="bold"),
            text_color=COLORS["text"],
        )
        self.punched_label.pack(pady=(10, 0))

        self.total_label = ctk.CTkLabel(
            totals,
            text="All-time (incl. forgotten seeds): 0h",
            font=ctk.CTkFont(family=FONT_BODY, size=12),
            text_color=COLORS["text_muted"],
        )
        self.total_label.pack(pady=(2, 10))

        _, card = cute_window(self, title="session log")

        self.history_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh(self) -> None:
        punched = self.store.punched_hours()
        total = self.store.total_hours()
        self.punched_label.configure(
            text=f"Punched: {format_duration(punched)} ({punched:.2f}h)"
        )
        self.total_label.configure(
            text=f"All-time (incl. forgotten seeds): {format_duration(total)} ({total:.2f}h)"
        )

        for child in self.history_frame.winfo_children():
            child.destroy()

        rows = self.store.history_rows()
        if not rows:
            ctk.CTkLabel(
                self.history_frame,
                text="No sessions yet — your cozy log will appear here.",
                font=ctk.CTkFont(family=FONT_BODY, size=13),
                text_color=COLORS["text_muted"],
            ).pack(padx=12, pady=16, anchor="w")
            return

        for i, row in enumerate(rows):
            bg = COLORS["cream"] if i % 2 == 0 else COLORS["blush"]
            line = cute_panel(self.history_frame, fg=bg, radius=12)
            line.pack(fill="x", padx=4, pady=3)

            type_color = COLORS["lavender"] if row["type"] == "Work" else COLORS["blush"]
            ctk.CTkLabel(
                line,
                text=row["type"],
                width=70,
                height=26,
                corner_radius=10,
                fg_color=type_color,
                text_color=COLORS["text"],
                font=ctk.CTkFont(family=FONT_DISPLAY, size=11, weight="bold"),
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
                    font=ctk.CTkFont(family=FONT_BODY, size=12),
                    text_color=COLORS["text"],
                ).pack(side="left", padx=4, pady=8)

            if row.get("kind") and row.get("key"):
                actions = ctk.CTkFrame(line, fg_color="transparent")
                actions.pack(side="right", padx=(4, 10), pady=8)

                pill_button(
                    actions,
                    "Edit",
                    width=64,
                    height=26,
                    font_size=11,
                    fg=COLORS["lavender"],
                    hover=COLORS["lavender_hover"],
                    command=lambda r=row: self._on_edit_punch(r),
                ).pack(side="left", padx=(0, 6))

                pill_button(
                    actions,
                    "Delete",
                    width=64,
                    height=26,
                    font_size=11,
                    fg=COLORS["pink"],
                    hover=COLORS["pink_hover"],
                    command=lambda r=row: self._on_delete_punch(r),
                ).pack(side="left")

    def _on_edit_punch(self, row: dict[str, Any]) -> None:
        kind = row.get("kind")
        key = row.get("key")
        if not kind or not key:
            return

        start_dt = parse_iso(row["start"])
        end_dt = parse_iso(row["end"])
        label = "work session" if kind == "session" else "break"

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {label}")
        dialog.geometry("420x280")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["bg"])

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=18)

        ctk.CTkLabel(
            body,
            text=f"Fix {label} times",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            body,
            text="Use date YYYY-MM-DD and time HH:MM (24-hour).",
            font=ctk.CTkFont(family=FONT_BODY, size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 12))

        form = cute_panel(body)
        form.pack(fill="x")

        fields: dict[str, ctk.CTkEntry] = {}
        specs = [
            ("date", "Date", start_dt.strftime(DATE_FMT)),
            ("start", "Start (HH:MM)", start_dt.strftime("%H:%M")),
            ("end", "End (HH:MM)", end_dt.strftime("%H:%M")),
        ]
        for key_name, title, value in specs:
            row_f = ctk.CTkFrame(form, fg_color="transparent")
            row_f.pack(fill="x", padx=14, pady=6)
            ctk.CTkLabel(
                row_f,
                text=title,
                width=120,
                anchor="w",
                font=ctk.CTkFont(family=FONT_DISPLAY, size=12, weight="bold"),
                text_color=COLORS["text"],
            ).pack(side="left")
            entry = ctk.CTkEntry(
                row_f,
                height=32,
                corner_radius=10,
                border_width=BORDER_WIDTH,
                border_color=COLORS["border"],
                fg_color=COLORS["cream"],
                text_color=COLORS["text"],
            )
            entry.pack(side="left", fill="x", expand=True)
            entry.insert(0, value)
            fields[key_name] = entry

        hint = ctk.CTkLabel(
            body,
            text="",
            font=ctk.CTkFont(family=FONT_BODY, size=11),
            text_color=COLORS["pink_hover"],
        )
        hint.pack(anchor="w", pady=(8, 0))

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.pack(fill="x", pady=(14, 0))

        def _parse_fields() -> tuple[datetime, datetime] | None:
            date_raw = fields["date"].get().strip()
            start_raw = fields["start"].get().strip()
            end_raw = fields["end"].get().strip()
            try:
                day = datetime.strptime(date_raw, DATE_FMT).date()
            except ValueError:
                hint.configure(text="Date must be YYYY-MM-DD.")
                return None
            try:
                start_t = datetime.strptime(start_raw, "%H:%M").time()
                end_t = datetime.strptime(end_raw, "%H:%M").time()
            except ValueError:
                hint.configure(text="Times must be HH:MM (24-hour).")
                return None
            start = datetime.combine(day, start_t)
            end = datetime.combine(day, end_t)
            if end <= start:
                hint.configure(text="End time must be after start time.")
                return None
            return start, end

        def _save() -> None:
            parsed = _parse_fields()
            if not parsed:
                return
            start, end = parsed
            try:
                ok = (
                    self.store.update_session(key, start, end)
                    if kind == "session"
                    else self.store.update_break(key, start, end)
                )
            except ValueError as exc:
                hint.configure(text=str(exc))
                return
            if not ok:
                hint.configure(text="Could not find that punch to update.")
                return
            dialog.destroy()
            self.on_change()

        pill_button(
            actions,
            "Cancel",
            width=100,
            height=34,
            command=dialog.destroy,
        ).pack(side="right", padx=(8, 0))

        pill_button(
            actions,
            "Save",
            width=100,
            height=34,
            fg=COLORS["lavender"],
            hover=COLORS["lavender_hover"],
            command=_save,
        ).pack(side="right")

        dialog.bind("<Return>", lambda _e: _save())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        fields["start"].focus_set()

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
