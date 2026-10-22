"""ZenLog application shell — navigation between Punch and Calendar pages."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from zenlog.data import PunchData
from zenlog.pages import CalendarPage, PunchPage
from zenlog.theme import COLORS, FONT_FAMILY

ICON_PATH = Path(__file__).resolve().parent.parent / "zenlog.ico.ico"


class ZenLogApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.store = PunchData()
        self._current_page = "punch"

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("ZenLog")
        self.geometry("860x860")
        self.minsize(760, 760)
        self.configure(fg_color=COLORS["bg"])
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
            except Exception:
                pass

        self._build_ui()
        self._show_page("punch")
        self._refresh()
        self.after(30_000, self._tick)

    def _tick(self) -> None:
        if self.store.status != "clocked_out":
            self._refresh()
        self.after(30_000, self._tick)

    def _build_ui(self) -> None:
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            brand,
            text="ZenLog",
            font=ctk.CTkFont(family=FONT_FAMILY, size=34, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Punch times are saved to disk — you can close the app anytime.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.pack(side="right", padx=(12, 0))

        self.punch_nav_btn = ctk.CTkButton(
            nav,
            text="Punch",
            width=100,
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=COLORS["lavender"],
            hover_color=COLORS["lavender_hover"],
            text_color=COLORS["text"],
            command=lambda: self._show_page("punch"),
        )
        self.punch_nav_btn.pack(side="left", padx=(0, 6))

        self.calendar_nav_btn = ctk.CTkButton(
            nav,
            text="Calendar",
            width=100,
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=COLORS["cream"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            command=lambda: self._show_page("calendar"),
        )
        self.calendar_nav_btn.pack(side="left")

        self.content = ctk.CTkFrame(outer, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        self.punch_page = PunchPage(self.content, self.store, on_change=self._refresh)
        self.calendar_page = CalendarPage(self.content, self.store, on_change=self._refresh)

    def _show_page(self, name: str) -> None:
        self._current_page = name
        self.punch_page.pack_forget()
        self.calendar_page.pack_forget()

        if name == "calendar":
            self.calendar_page.pack(fill="both", expand=True)
            self._style_nav(active="calendar")
            self.calendar_page.refresh()
        else:
            self.punch_page.pack(fill="both", expand=True)
            self._style_nav(active="punch")
            self.punch_page.refresh()

    def _style_nav(self, active: str) -> None:
        if active == "punch":
            self.punch_nav_btn.configure(
                fg_color=COLORS["lavender"],
                hover_color=COLORS["lavender_hover"],
            )
            self.calendar_nav_btn.configure(
                fg_color=COLORS["cream"],
                hover_color=COLORS["border"],
            )
        else:
            self.calendar_nav_btn.configure(
                fg_color=COLORS["lavender"],
                hover_color=COLORS["lavender_hover"],
            )
            self.punch_nav_btn.configure(
                fg_color=COLORS["cream"],
                hover_color=COLORS["border"],
            )

    def _refresh(self) -> None:
        self.punch_page.refresh()
        self.calendar_page.refresh()


def run() -> None:
    app = ZenLogApp()
    app.mainloop()
