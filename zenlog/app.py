"""ZenLog application shell — navigation between Punch, Forgotten, History, and Calendar."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from zenlog.data import PunchData
from zenlog.pages import CalendarPage, ForgottenHoursPage, HistoryPage, PunchPage
from zenlog.theme import (
    BTN_DECO,
    COLORS,
    FONT_BODY,
    FONT_DISPLAY_BOLD,
)
from zenlog.widgets import attach_background, pill_button

ICON_PATH = Path(__file__).resolve().parent.parent / "zenlog.ico.ico"


class ZenLogApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.store = PunchData()
        self._current_page = "punch"
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._wallpaper = None
        self._ui: ctk.CTkFrame | None = None

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("zenlog")
        self.geometry("960x980")
        self.minsize(780, 860)
        self.configure(fg_color=COLORS["bg"])
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
            except Exception:
                pass

        self._wallpaper = attach_background(self)

        self._build_ui()
        self._stack_layers()
        self._show_page("punch")
        self._refresh()
        self.after(30_000, self._tick)
        self.bind("<Configure>", self._on_resize, add="+")

    def _stack_layers(self) -> None:
        """Dotted paper above window fill, under UI — dots show around the punch card."""
        try:
            if self._wallpaper is not None:
                try:
                    self._wallpaper.lift(self._canvas)  # type: ignore[attr-defined]
                except Exception:
                    self._wallpaper.lift()
            if self._ui is not None:
                self._ui.lift()
        except Exception:
            pass

    def _on_resize(self, _event: object | None = None) -> None:
        self._stack_layers()

    def _tick(self) -> None:
        if self.store.status != "clocked_out":
            self._refresh()
        self.after(30_000, self._tick)

    def _build_ui(self) -> None:
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=28, pady=24)
        self._ui = outer

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(fill="x")

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
        nav.pack(fill="x", pady=(10, 0))

        nav_faces = (
            ("punch", "punch", COLORS["pink"], COLORS["pink_hover"]),
            ("forgotten", "forgotten", COLORS["cream"], COLORS["butter_hover"]),
            ("history", "history", COLORS["blush"], COLORS["peach_hover"]),
            ("calendar", "calendar", COLORS["lavender"], COLORS["lavender_hover"]),
        )
        for key, label, fg, hover in nav_faces:
            deco = BTN_DECO.get(key, "")
            btn = pill_button(
                nav,
                f"{deco} {label}" if deco else label,
                width=128,
                height=36,
                fg=fg,
                hover=hover,
                command=lambda k=key: self._show_page(k),
            )
            btn.pack(side="left", padx=(0, 8))
            self._nav_btns[key] = btn
            btn._zen_fg = fg  # type: ignore[attr-defined]
            btn._zen_hover = hover  # type: ignore[attr-defined]

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
            face = getattr(btn, "_zen_fg", COLORS["cream"])
            hover = getattr(btn, "_zen_hover", COLORS["blush"])
            if key == active:
                btn.configure(
                    fg_color=hover,
                    hover_color=hover,
                    border_color=COLORS["accent"],
                )
            else:
                btn.configure(
                    fg_color=face,
                    hover_color=hover,
                    border_color=COLORS["border"],
                )

    def _refresh(self) -> None:
        self.punch_page.refresh()
        self.forgotten_page.refresh()
        self.history_page.refresh()
        self.calendar_page.refresh()


def run() -> None:
    app = ZenLogApp()
    app.mainloop()
