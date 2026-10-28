"""Cute reusable UI bits — lace page frame, cream windows, soft pills."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Any, Callable

import customtkinter as ctk

from zenlog.theme import (
    BORDER_WIDTH,
    BORDER_WIDTH_CHUNKY,
    COLORS,
    CORNER_RADIUS,
    CORNER_RADIUS_PILL,
    FONT_BODY,
    FONT_DISPLAY,
    FONT_DISPLAY_BOLD,
    PAGE_BORDER_PATH,
    PUNCH_BORDER_INSET_FRAC,
    PUNCH_BORDER_PATH,
)


def attach_page_border(
    host: ctk.CTk | ctk.CTkFrame,
    *,
    border_path: Any = None,
) -> ctk.CTkLabel | None:
    """
    Pixel-art lace PNG as the overall page frame.
    Uses nearest-neighbor + cover crop so roses/lace stay crisp (no stretch warp).
    Drawn on top so the frame isn't covered by the pink fill.
    """
    path = Path(border_path) if border_path else PAGE_BORDER_PATH
    if not path.is_file():
        return None
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None

    source = Image.open(path).convert("RGBA")
    label = ctk.CTkLabel(host, text="", fg_color="transparent")
    label.place(x=0, y=0, relwidth=1, relheight=1)

    state: dict[str, Any] = {"img": None, "w": 0, "h": 0}

    def _paint(_event: object | None = None) -> None:
        w = max(host.winfo_width(), 2)
        h = max(host.winfo_height(), 2)
        if w < 40 or h < 40:
            return
        if w == state["w"] and h == state["h"] and state["img"] is not None:
            return
        state["w"], state["h"] = w, h
        # Cover + crop keeps aspect; NEAREST keeps pixel lace sharp
        fitted = ImageOps.fit(
            source,
            (w, h),
            method=Image.Resampling.NEAREST,
            centering=(0.5, 0.5),
        )
        ctk_img = ctk.CTkImage(light_image=fitted, dark_image=fitted, size=(w, h))
        state["img"] = ctk_img
        label.configure(image=ctk_img)

    host.bind("<Configure>", _paint)
    label.bind("<Configure>", _paint)
    host.after(40, _paint)
    return label


def lace_frame(
    master: Any,
    *,
    border_path: Any = None,
    inset_frac: float | None = None,
    size: int = 460,
) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
    """
    Square lace PNG around a middle content block (not a full-page overlay).

    Drawn on a Canvas (same idea as polka dots) so it stays above the CTkFrame
    draw layer. Content pad sits on top in the hole so buttons stay clickable.
    """
    path = Path(border_path) if border_path else PUNCH_BORDER_PATH
    frac = PUNCH_BORDER_INSET_FRAC if inset_frac is None else inset_frac

    host = ctk.CTkFrame(master, fg_color="transparent", width=size, height=size)
    host.pack_propagate(False)

    bg = COLORS["bg"]
    canvas = tk.Canvas(host, bg=bg, highlightthickness=0, bd=0)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    pad = ctk.CTkFrame(host, fg_color="transparent")
    inner = 1.0 - 2.0 * frac
    pad.place(relx=0.5, rely=0.5, anchor="center", relwidth=inner, relheight=inner)

    # Above CTkFrame's internal canvas, under the content pad
    try:
        canvas.lift(host._canvas)  # type: ignore[attr-defined]
    except (tk.TclError, AttributeError):
        try:
            canvas.lift()
        except tk.TclError:
            pass
    try:
        pad.lift(canvas)
    except tk.TclError:
        try:
            pad.lift()
        except tk.TclError:
            pass

    state: dict[str, Any] = {"photo": None, "w": 0, "h": 0, "source": None}
    if path.is_file():
        try:
            from PIL import Image

            state["source"] = Image.open(path).convert("RGBA")
        except ImportError:
            state["source"] = None

    def _stack(_event: object | None = None) -> None:
        try:
            canvas.lift(host._canvas)  # type: ignore[attr-defined]
            pad.lift(canvas)
        except (tk.TclError, AttributeError):
            pass

    def _paint(_event: object | None = None) -> None:
        w = max(host.winfo_width(), 2)
        h = max(host.winfo_height(), 2)
        if w < 40 or h < 40:
            return
        if w == state["w"] and h == state["h"] and state["photo"] is not None:
            return
        state["w"], state["h"] = w, h
        canvas.delete("lace")
        canvas.create_rectangle(0, 0, w, h, fill=bg, outline="", tags="lace")
        src = state["source"]
        if src is None:
            return
        try:
            from PIL import Image, ImageTk
        except ImportError:
            return
        # Exact resize (host is square) — keep the full frame, no cover-crop
        side = min(w, h)
        resized = src.resize((side, side), Image.Resampling.NEAREST)
        r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
        base = Image.new("RGBA", (side, side), (r, g, b, 255))
        composited = Image.alpha_composite(base, resized).convert("RGB")
        photo = ImageTk.PhotoImage(composited)
        state["photo"] = photo  # keep ref
        x0 = (w - side) // 2
        y0 = (h - side) // 2
        canvas.create_image(x0, y0, anchor="nw", image=photo, tags="lace")
        _stack()

    host.bind("<Configure>", _paint, add="+")
    host.bind("<Configure>", _stack, add="+")
    host.after(40, _paint)
    host.after(50, _stack)
    return host, pad


def attach_polka_dots(
    host: ctk.CTk | ctk.CTkFrame,
    *,
    color: str | None = None,
    dot: str | None = None,
    spacing: int = 22,
    radius: int = 3,
) -> tk.Canvas:
    """Pink wallpaper with soft white polka dots, behind existing children."""
    bg = color or COLORS["bg"]
    dot_color = dot or "#FFFFFF"
    canvas = tk.Canvas(host, bg=bg, highlightthickness=0, bd=0)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)
    try:
        canvas.lower()
    except tk.TclError:
        pass

    def _paint(_event: object | None = None) -> None:
        canvas.delete("dot")
        w = max(canvas.winfo_width(), 2)
        h = max(canvas.winfo_height(), 2)
        canvas.create_rectangle(0, 0, w, h, fill=bg, outline="", tags="dot")
        row = 0
        y = spacing // 2
        while y < h + spacing:
            x_off = (spacing // 2) if row % 2 else 0
            x = x_off + spacing // 2
            while x < w + spacing:
                canvas.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=dot_color,
                    outline="",
                    tags="dot",
                )
                x += spacing
            y += spacing
            row += 1

    canvas.bind("<Configure>", _paint)
    host.after(1, _paint)
    return canvas


def cute_window(
    master: Any,
    *,
    title: str | None = None,
    fill: bool = True,
    pad: int = 12,
) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
    """
    Simple cream card with optional soft title bar.
    (Outer lace PNG is the decorative page frame — no nested scallops.)
    """
    outer = ctk.CTkFrame(
        master,
        fg_color=COLORS["card"],
        corner_radius=CORNER_RADIUS,
        border_width=BORDER_WIDTH_CHUNKY,
        border_color=COLORS["border"],
    )
    if fill:
        outer.pack(fill="both", expand=True)

    if title:
        bar = ctk.CTkFrame(
            outer,
            fg_color=COLORS["titlebar"],
            corner_radius=10,
            height=34,
        )
        bar.pack(fill="x", padx=10, pady=(10, 6))
        bar.pack_propagate(False)

        ctk.CTkLabel(
            bar,
            text=f"♥  {title.lower()}",
            font=ctk.CTkFont(family=FONT_DISPLAY_BOLD, size=13, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left", padx=10, fill="y")

        lights = ctk.CTkFrame(bar, fg_color="transparent")
        lights.pack(side="right", padx=10)
        for i, fill_c in enumerate(
            (COLORS["cream"], COLORS["cream"], COLORS["accent"])
        ):
            ctk.CTkLabel(
                lights,
                text="●",
                width=14,
                font=ctk.CTkFont(size=11),
                text_color=fill_c if i == 2 else COLORS["border_soft"],
            ).pack(side="left", padx=1)

    content = ctk.CTkFrame(outer, fg_color=COLORS["card"], corner_radius=8)
    content.pack(fill="both", expand=True, padx=pad, pady=(0 if title else pad, pad))
    return outer, content


def cute_panel(
    master: Any,
    *,
    fg: str | None = None,
    chunky: bool = False,
    radius: int | None = None,
) -> ctk.CTkFrame:
    """Cream (or custom) box with a soft outline."""
    return ctk.CTkFrame(
        master,
        fg_color=fg or COLORS["card"],
        corner_radius=radius if radius is not None else CORNER_RADIUS,
        border_width=BORDER_WIDTH_CHUNKY if chunky else BORDER_WIDTH,
        border_color=COLORS["border"],
    )


def pill_button(
    master: Any,
    text: str,
    *,
    command: Callable[[], None] | None = None,
    width: int = 100,
    height: int = 36,
    fg: str | None = None,
    hover: str | None = None,
    border_color: str | None = None,
    font_size: int = 13,
    bold: bool = True,
) -> ctk.CTkButton:
    """Cream pill with a chunky outline — soft coquette border, plain label."""
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=height,
        corner_radius=CORNER_RADIUS_PILL,
        font=ctk.CTkFont(
            family=FONT_DISPLAY_BOLD if bold else FONT_DISPLAY,
            size=font_size,
            weight="bold" if bold else "normal",
        ),
        fg_color=fg if fg is not None else COLORS["cream"],
        hover_color=hover if hover is not None else COLORS["blush"],
        text_color=COLORS["text"],
        border_width=BORDER_WIDTH_CHUNKY,
        border_color=border_color if border_color is not None else COLORS["border"],
        command=command,
    )


def page_title(master: Any, title: str, subtitle: str) -> None:
    """Soft lowercase page heading."""
    ctk.CTkLabel(
        master,
        text=title.lower(),
        font=ctk.CTkFont(family=FONT_DISPLAY_BOLD, size=22, weight="bold"),
        text_color=COLORS["text"],
    ).pack(anchor="w")
    ctk.CTkLabel(
        master,
        text=subtitle,
        font=ctk.CTkFont(family=FONT_BODY, size=13),
        text_color=COLORS["text_muted"],
    ).pack(anchor="w", pady=(2, 12))
