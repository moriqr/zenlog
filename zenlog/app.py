"""ZenLog application shell — navigation between Punch, Forgotten, History, and Calendar."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from zenlog.data import PunchData
from zenlog.pages import CalendarPage, ForgottenHoursPage, HistoryPage, PunchPage
from zenlog.theme import COLORS, FONT_BODY, FONT_DISPLAY
from zenlog.widgets import pill_button

ICON_PATH = Path(__file__).resolve().parent.parent / "zenlog.ico.ico"


class ZenLogApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.store = PunchData()
        self._current_page = "punch"
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_btns: dict[str, ctk.CTkButton] = {}

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("ZenLog")
        self.geometry("900x860")
        self.minsize(800, 760)
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
            font=ctk.CTkFont(family=FONT_DISPLAY, size=34, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Punch times are saved to disk — you can close the app anytime.",
            font=ctk.CTkFont(family=FONT_BODY, size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.pack(side="right", padx=(12, 0))

        for key, label in (
            ("punch", "Punch"),
            ("forgotten", "Forgotten"),
            ("history", "History"),
            ("calendar", "Calendar"),
        ):
            btn = pill_button(
                nav,
                label,
                width=100,
                height=36,
                command=lambda k=key: self._show_page(k),
            )
            btn.pack(side="left", padx=(0, 6))
            self._nav_btns[key] = btn

        self.content = ctk.CTkFrame(outer, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        self.punch_page = PunchPage(self.content, self.store, on_change=self._refresh)
        self.forgotten_page = ForgottenHoursPage(
            self.content, self.store, on_change=self._refresh
        )
        self.history_page = HistoryPage(self.content, self.store, on_change=self._refresh)
        self.calendar_page = CalendarPage(self.content, self.store, on_change=self._refresh)
        self._pages = {
            "punch": self.punch_page,
            "forgotten": self.forgotten_page,
            "history": self.history_page,
            "calendar": self.calendar_page,
        }

    def _show_page(self, name: str) -> None:
        self._current_page = name
        for page in self._pages.values():
            page.pack_forget()

        page = self._pages[name]
        page.pack(fill="both", expand=True)
        page.refresh()
        self._style_nav(active=name)

    def _style_nav(self, active: str) -> None:
        for key, btn in self._nav_btns.items():
            if key == active:
                btn.configure(
                    fg_color=COLORS["lavender"],
                    hover_color=COLORS["lavender_hover"],
                )
            else:
                btn.configure(
                    fg_color=COLORS["cream"],
                    hover_color=COLORS["blush"],
                )

    def _refresh(self) -> None:
        self.punch_page.refresh()
        self.forgotten_page.refresh()
        self.history_page.refresh()
        self.calendar_page.refresh()


def run() -> None:
    app = ZenLogApp()
    app.mainloop()
