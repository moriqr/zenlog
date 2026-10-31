"""Forgotten hours page — add and list past-hour seeds (not on calendar)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox

from zenlog.data import PunchData
from zenlog.theme import BORDER_WIDTH, COLORS, FONT_BODY, FONT_DISPLAY
from zenlog.timeutil import DATE_FMT, format_duration, format_time, parse_iso
from zenlog.widgets import cute_panel, cute_window, page_title, pill_button


class ForgottenHoursPage(ctk.CTkFrame):
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
            "forgotten hours",
            "log hours you forgot to punch. edit or delete a seed if you logged it wrong. these count toward the all-time total only — never the calendar.",
        )

        _, wrap = cute_window(self, title="forgotten seeds")

        form = cute_panel(wrap, fg=COLORS["card"], chunky=True)
        form.pack(fill="x", padx=10, pady=(10, 8))

        ctk.CTkLabel(
            form,
            text="add forgotten hours",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=13, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=14, pady=(12, 6))

        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 6))

        self.seed_hours_entry = ctk.CTkEntry(
            row,
            placeholder_text="Hours e.g. 2.5",
            height=34,
            corner_radius=12,
            border_width=BORDER_WIDTH,
            border_color=COLORS["border"],
            fg_color=COLORS["cream"],
            text_color=COLORS["text"],
            width=120,
        )
        self.seed_hours_entry.pack(side="left", padx=(0, 8))

        self.seed_date_entry = ctk.CTkEntry(
            row,
            placeholder_text="Date YYYY-MM-DD",
            height=34,
            corner_radius=12,
            border_width=BORDER_WIDTH,
            border_color=COLORS["border"],
            fg_color=COLORS["cream"],
            text_color=COLORS["text"],
            width=140,
        )
        self.seed_date_entry.pack(side="left", padx=(0, 8))
        self.seed_date_entry.insert(0, date.today().strftime(DATE_FMT))

        self.seed_note_entry = ctk.CTkEntry(
            row,
            placeholder_text="Optional note",
            height=34,
            corner_radius=12,
            border_width=BORDER_WIDTH,
            border_color=COLORS["border"],
            fg_color=COLORS["cream"],
            text_color=COLORS["text"],
        )
        self.seed_note_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        pill_button(
            row,
            "add",
            width=80,
            height=34,
            command=self._on_add_seed,
        ).pack(side="right")

        self.seed_hint = ctk.CTkLabel(
            form,
            text="Seeds only affect the all-time total — never week/month calendar hours.",
            font=ctk.CTkFont(family=FONT_BODY, size=11),
            text_color=COLORS["text_muted"],
        )
        self.seed_hint.pack(anchor="w", padx=14, pady=(0, 8))

        self.seeds_total_label = ctk.CTkLabel(
            form,
            text="Forgotten seeds total: 0h",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=13, weight="bold"),
            text_color=COLORS["text"],
        )
        self.seeds_total_label.pack(anchor="w", padx=14, pady=(0, 12))

        self.seeds_frame = ctk.CTkScrollableFrame(wrap, fg_color="transparent")
        self.seeds_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    def refresh(self) -> None:
        self._render_seeds()

    def _render_seeds(self) -> None:
        for child in self.seeds_frame.winfo_children():
            child.destroy()

        rows = self.store.seed_rows()
        seeds_total = self.store.past_hours
        self.seeds_total_label.configure(
            text=f"Forgotten seeds total: {format_duration(seeds_total)} ({seeds_total:.2f}h)"
        )

        if not rows:
            ctk.CTkLabel(
                self.seeds_frame,
                text="No forgotten-hour entries yet.",
                font=ctk.CTkFont(family=FONT_BODY, size=13),
                text_color=COLORS["text_muted"],
            ).pack(padx=12, pady=16, anchor="w")
            return

        for i, row in enumerate(rows):
            bg = COLORS["cream"] if i % 2 == 0 else COLORS["blush"]
            line = cute_panel(self.seeds_frame, fg=bg, radius=12)
            line.pack(fill="x", padx=4, pady=3)

            ctk.CTkLabel(
                line,
                text=format_duration(float(row.get("hours", 0))),
                width=70,
                height=26,
                corner_radius=10,
                fg_color=COLORS["blush"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(family=FONT_DISPLAY, size=11, weight="bold"),
            ).pack(side="left", padx=(10, 4), pady=8)

            note = row.get("note") or "No note"
            created = row.get("created_at", "")
            created_txt = format_time(parse_iso(created)) if created else ""
            ctk.CTkLabel(
                line,
                text=f"{row.get('date', '')}  ·  {float(row.get('hours', 0)):g}h  ·  {note}"
                + (f"  (logged {created_txt})" if created_txt else ""),
                anchor="w",
                font=ctk.CTkFont(family=FONT_BODY, size=12),
                text_color=COLORS["text"],
            ).pack(side="left", fill="x", expand=True, padx=4, pady=8)

            seed_id = row.get("id")
            if seed_id:
                actions = ctk.CTkFrame(line, fg_color="transparent")
                actions.pack(side="right", padx=(4, 10), pady=8)

                pill_button(
                    actions,
                    "edit",
                    width=64,
                    height=26,
                    font_size=11,
                    command=lambda r=row: self._on_edit_seed(r),
                ).pack(side="left", padx=(0, 6))

                pill_button(
                    actions,
                    "delete",
                    width=64,
                    height=26,
                    font_size=11,
                    command=lambda r=row: self._on_delete_seed(r),
                ).pack(side="left")

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

    def _on_edit_seed(self, row: dict[str, Any]) -> None:
        seed_id = row.get("id")
        if not seed_id:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit forgotten hours")
        dialog.geometry("420x300")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["bg"])

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=18)

        ctk.CTkLabel(
            body,
            text="Fix forgotten hours",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            body,
            text="Change the hours, date, or note for this seed.",
            font=ctk.CTkFont(family=FONT_BODY, size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 12))

        form = cute_panel(body)
        form.pack(fill="x")

        fields: dict[str, ctk.CTkEntry] = {}
        specs = [
            ("hours", "Hours", f"{float(row.get('hours', 0)):g}"),
            ("date", "Date", str(row.get("date") or date.today().strftime(DATE_FMT))),
            ("note", "Note", str(row.get("note") or "")),
        ]
        for key_name, title, value in specs:
            row_f = ctk.CTkFrame(form, fg_color="transparent")
            row_f.pack(fill="x", padx=14, pady=6)
            ctk.CTkLabel(
                row_f,
                text=title,
                width=80,
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
            text_color=COLORS["text_muted"],
        )
        hint.pack(anchor="w", pady=(8, 0))

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.pack(fill="x", pady=(14, 0))

        def _save() -> None:
            raw = fields["hours"].get().strip()
            date_raw = fields["date"].get().strip() or date.today().strftime(DATE_FMT)
            note = fields["note"].get().strip()
            try:
                value = float(raw)
                if value <= 0:
                    raise ValueError
            except ValueError:
                hint.configure(text="Enter a positive number of hours.")
                return
            try:
                datetime.strptime(date_raw, DATE_FMT)
            except ValueError:
                hint.configure(text="Date must be YYYY-MM-DD.")
                return
            try:
                ok = self.store.update_past_hours_seed(
                    seed_id, value, note=note, on_date=date_raw
                )
            except ValueError as exc:
                hint.configure(text=str(exc))
                return
            if not ok:
                hint.configure(text="Could not find that seed to update.")
                return
            dialog.destroy()
            self.on_change()

        pill_button(
            actions,
            "cancel",
            width=100,
            height=34,
            command=dialog.destroy,
        ).pack(side="right", padx=(8, 0))

        pill_button(
            actions,
            "save",
            width=100,
            height=34,
            command=_save,
        ).pack(side="right")

        dialog.bind("<Return>", lambda _e: _save())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        fields["hours"].focus_set()

    def _on_delete_seed(self, row: dict[str, Any]) -> None:
        seed_id = row.get("id")
        if not seed_id:
            return

        hours = float(row.get("hours", 0))
        note = row.get("note") or "No note"
        confirmed = messagebox.askyesno(
            "Delete forgotten hours",
            f"Delete this forgotten-hours seed?\n\n"
            f"{row.get('date', '')}  ·  {format_duration(hours)}  ·  {note}",
            parent=self.winfo_toplevel(),
        )
        if not confirmed:
            return

        if self.store.delete_past_hours_seed(seed_id):
            self.on_change()
