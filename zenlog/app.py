"""ZenLog application shell — navigation between Punch, Forgotten, History, and Calendar."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from zenlog.data import PunchData
from zenlog.pages import CalendarPage, ForgottenHoursPage, HistoryPage, PunchPage
from zenlog.theme import (
    COLORS,
    FONT_BODY,
    FONT_DISPLAY_BOLD,
    PAGE_BORDER_FRAC_X,
    PAGE_BORDER_FRAC_Y,
    PAGE_BORDER_INSET_X,
    PAGE_BORDER_INSET_Y,
)
from zenlog.widgets import attach_page_border, attach_polka_dots, pill_button

ICON_PATH = Path(__file__).resolve().parent.parent / "zenlog.ico.ico"


class ZenLogApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.store = PunchData()
        self._current_page = "punch"
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._border = None
        self._ui: ctk.CTkFrame | None = None

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("zenlog")
        self.geometry("920x900")
        self.minsize(820, 780)
        self.configure(fg_color=COLORS["bg"])
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
            except Exception:
                pass

        attach_polka_dots(self)
        self._border = attach_page_border(self)

        self._build_ui()
        self._stack_layers()
        self._show_page("punch")
        self._refresh()
        self.after(30_000, self._tick)
        self.bind("<Configure>", self._on_resize, add="+")

    def _stack_layers(self) -> None:
        """Wallpaper under lace under UI — keep content clickable."""
        try:
            if self._border is not None:
                self._border.lower()
            if self._ui is not None:
                self._ui.lift()
        except Exception:
            pass

    def _on_resize(self, _event: object | None = None) -> None:
        if self._ui is None:
            return
        w = max(self.winfo_width(), 1)
        h = max(self.winfo_height(), 1)
        pad_x = max(PAGE_BORDER_INSET_X, int(w * PAGE_BORDER_FRAC_X))
        pad_y = max(PAGE_BORDER_INSET_Y, int(h * PAGE_BORDER_FRAC_Y))
        self._ui.pack_configure(padx=pad_x, pady=pad_y)
        self._stack_layers()

    def _tick(self) -> None:
        if self.store.status != "clocked_out":
            self._refresh()
        self.after(30_000, self._tick)

    def _build_ui(self) -> None:
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(
            fill="both",
            expand=True,
            padx=PAGE_BORDER_INSET_X,
            pady=PAGE_BORDER_INSET_Y,
        )
        self._ui = outer

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            brand,
            text="♥  zenlog",
            font=ctk.CTkFont(family=FONT_DISPLAY_BOLD, size=34, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="punch times are saved to disk — close anytime ♡",
            font=ctk.CTkFont(family=FONT_BODY, size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.pack(side="right", padx=(12, 0))

        for key, label in (
            ("punch", "punch"),
            ("forgotten", "forgotten"),
            ("history", "history"),
            ("calendar", "calendar"),
        ):
            btn = pill_button(
                nav,
                label,
                width=108,
                height=36,
                bow=True,
                fg=COLORS["cream"],
                hover=COLORS["blush"],
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
                    fg_color=COLORS["blush"],
                    hover_color=COLORS["blush"],
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
