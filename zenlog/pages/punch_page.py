"""Punch page — clock in/out and break actions."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from zenlog.data import PunchData
from zenlog.theme import BTN_DECO, COLORS, FONT_BODY, FONT_DISPLAY, PUNCH_BORDER_ASPECT
from zenlog.timeutil import format_duration, format_time, parse_iso
from zenlog.widgets import lace_frame, nintendo_button, page_title, set_nintendo_enabled

# Win95 pink/white pads — shorter width, Comfortaa labels
BTN_WIDTH = 180
BTN_HEIGHT = 64
BTN_FONT_SIZE = 13
BTN_GAP = 10
# Portrait container matching punch-border.png aspect (1792×2400)
STATION_W = 440
STATION_H = int(round(STATION_W / PUNCH_BORDER_ASPECT))

# Map punch actions → kind key (colors + deco)
_PUNCH_KINDS = {
    "clock in": "clock_in",
    "clock out": "clock_out",
    "start break": "start_break",
    "end break": "end_break",
}


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
            "punch clock",
            "clock in and out here. breaks are logged separately and never count as work.",
        )

        station = ctk.CTkFrame(self, fg_color="transparent")
        station.pack(fill="both", expand=True)

        shell = ctk.CTkFrame(station, fg_color="transparent")
        shell.pack(expand=True)

        # Portrait punch-border.png — not the square 1x1 (avoids squash / damaged lace)
        outer, pad = lace_frame(shell, width=STATION_W, height=STATION_H)
        outer.pack(expand=True, padx=8, pady=8)
        outer.configure(width=STATION_W, height=STATION_H)

        # Balanced vertical rhythm inside the lace hole
        ctk.CTkFrame(pad, fg_color="transparent", height=1).pack(expand=True)

        status_block = ctk.CTkFrame(pad, fg_color="transparent")
        status_block.pack(fill="x", padx=12)

        self.status_label = ctk.CTkLabel(
            status_block,
            text="clocked out",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=20, weight="bold"),
            text_color=COLORS["text"],
        )
        self.status_label.pack()

        self.status_detail = ctk.CTkLabel(
            status_block,
            text="ready when you are ♡",
            font=ctk.CTkFont(family=FONT_BODY, size=12),
            text_color=COLORS["text_muted"],
        )
        self.status_detail.pack(pady=(4, 0))

        btns = ctk.CTkFrame(pad, fg_color="transparent")
        btns.pack(pady=(14, 0))

        self.clock_in_btn = self._make_punch_btn(btns, "clock in", self._on_clock_in)
        self.clock_in_btn.pack(pady=(0, BTN_GAP))

        self.clock_out_btn = self._make_punch_btn(btns, "clock out", self._on_clock_out)
        self.clock_out_btn.pack(pady=(0, BTN_GAP))

        self.start_break_btn = self._make_punch_btn(
            btns, "start break", self._on_start_break
        )
        self.start_break_btn.pack(pady=(0, BTN_GAP))

        self.end_break_btn = self._make_punch_btn(btns, "end break", self._on_end_break)
        self.end_break_btn.pack()

        ctk.CTkFrame(pad, fg_color="transparent", height=1).pack(expand=True)

    def _make_punch_btn(
        self,
        parent: ctk.CTkFrame,
        text: str,
        command: Callable[[], None],
    ) -> Any:
        kind = _PUNCH_KINDS[text]
        deco = BTN_DECO.get(kind, "")
        label = f"{deco}\n{text}" if deco else text
        return nintendo_button(
            parent,
            label,
            kind,
            width=BTN_WIDTH,
            height=BTN_HEIGHT,
            font_size=BTN_FONT_SIZE,
            command=command,
        )

    @staticmethod
    def _set_button_state(btn: Any, enabled: bool) -> None:
        set_nintendo_enabled(btn, enabled)

    def refresh(self) -> None:
        status = self.store.status
        session = self.store.data.get("current_session")
        current_break = self.store.data.get("current_break")

        if status == "clocked_out":
            self.status_label.configure(text="clocked out")
            self.status_detail.configure(text="ready when you are ♡")
        elif status == "clocked_in" and session:
            in_time = format_time(parse_iso(session["clock_in"]))
            live = format_duration(self.store.live_session_hours())
            self.status_label.configure(text=f"clocked in · {in_time}")
            self.status_detail.configure(text=f"working — {live} so far this session")
        elif status == "on_break" and current_break:
            br_time = format_time(parse_iso(current_break["break_start"]))
            self.status_label.configure(text=f"on break · {br_time}")
            self.status_detail.configure(text="end break before clocking out")
        else:
            self.status_label.configure(text="clocked out")
            self.status_detail.configure(text="ready when you are ♡")

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
