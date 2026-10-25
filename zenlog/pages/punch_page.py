"""Punch page — clock in/out and break actions."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from zenlog.data import PunchData
from zenlog.theme import COLORS, FONT_BODY, FONT_DISPLAY
from zenlog.timeutil import format_duration, format_time, parse_iso
from zenlog.widgets import cute_window, page_title, pill_button

BTN_WIDTH = 340
BTN_HEIGHT = 72
BTN_FONT_SIZE = 22


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
        page_title(
            self,
            "Punch clock",
            "Clock in and out here. Breaks are logged separately and never count as work.",
        )

        station = ctk.CTkFrame(self, fg_color="transparent")
        station.pack(fill="both", expand=True)

        wrap = ctk.CTkFrame(station, fg_color="transparent")
        wrap.pack(expand=True)

        outer, pad = cute_window(wrap, title="punch station", fill=False)
        outer.pack(expand=True, padx=8, pady=8)

        status_block = ctk.CTkFrame(pad, fg_color="transparent")
        status_block.pack(fill="x", padx=28, pady=(20, 8))

        self.status_label = ctk.CTkLabel(
            status_block,
            text="Clocked Out",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=26, weight="bold"),
            text_color=COLORS["text"],
        )
        self.status_label.pack()

        self.status_detail = ctk.CTkLabel(
            status_block,
            text="Ready when you are.",
            font=ctk.CTkFont(family=FONT_BODY, size=14),
            text_color=COLORS["text_muted"],
        )
        self.status_detail.pack(pady=(4, 0))

        btns = ctk.CTkFrame(pad, fg_color="transparent")
        btns.pack(padx=28, pady=(16, 24))

        self.clock_in_btn = self._make_punch_btn(
            btns,
            "CLOCK IN",
            COLORS["lavender"],
            COLORS["lavender_hover"],
            self._on_clock_in,
        )
        self.clock_in_btn.pack(pady=(0, 12))

        self.clock_out_btn = self._make_punch_btn(
            btns,
            "CLOCK OUT",
            COLORS["pink"],
            COLORS["pink_hover"],
            self._on_clock_out,
        )
        self.clock_out_btn.pack(pady=(0, 12))

        self.start_break_btn = self._make_punch_btn(
            btns,
            "START BREAK",
            COLORS["cream"],
            COLORS["blush"],
            self._on_start_break,
        )
        self.start_break_btn.pack(pady=(0, 12))

        self.end_break_btn = self._make_punch_btn(
            btns,
            "END BREAK",
            COLORS["blush"],
            COLORS["pink"],
            self._on_end_break,
        )
        self.end_break_btn.pack()

    def _make_punch_btn(
        self,
        parent: ctk.CTkFrame,
        text: str,
        fg: str,
        hover: str,
        command: Callable[[], None],
    ) -> ctk.CTkButton:
        return pill_button(
            parent,
            text,
            width=BTN_WIDTH,
            height=BTN_HEIGHT,
            font_size=BTN_FONT_SIZE,
            fg=fg,
            hover=hover,
            command=command,
        )

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
            self.status_label.configure(text=f"Clocked In · {in_time}")
            self.status_detail.configure(text=f"Working — {live} so far this session.")
        elif status == "on_break" and current_break:
            br_time = format_time(parse_iso(current_break["break_start"]))
            self.status_label.configure(text=f"On Break · {br_time}")
            self.status_detail.configure(text="End break before clocking out.")
        else:
            self.status_label.configure(text="Clocked Out")
            self.status_detail.configure(text="Ready when you are.")

        self._set_button_state(self.clock_in_btn, status == "clocked_out")
        self._set_button_state(self.clock_out_btn, status == "clocked_in")
        self._set_button_state(self.start_break_btn, status == "clocked_in")
        self._set_button_state(self.end_break_btn, status == "on_break")

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
