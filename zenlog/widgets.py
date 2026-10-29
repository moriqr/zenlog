"""Cute reusable UI bits — lace page frame, cream windows, soft pills."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Any, Callable

import customtkinter as ctk

from zenlog.theme import (
    BG_PATH,
    BORDER_WIDTH,
    BORDER_WIDTH_CHUNKY,
    COLORS,
    CORNER_RADIUS,
    CORNER_RADIUS_PILL,
    FONT_BODY,
    FONT_DISPLAY,
    FONT_DISPLAY_BOLD,
    NINTENDO_BTNS,
    PUNCH_BORDER_ASPECT,
    PUNCH_BORDER_INSET_FRAC,
    PUNCH_BORDER_INSET_X,
    PUNCH_BORDER_INSET_Y,
    PUNCH_BORDER_PATH,
)


def attach_background(
    host: ctk.CTk | ctk.CTkFrame,
    *,
    bg_path: Any = None,
) -> ctk.CTkLabel | None:
    """Full-window dotted paper from assets/bg.jpg — no lace overlay."""
    paper_path = Path(bg_path) if bg_path else BG_PATH
    if not paper_path.is_file():
        return None
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None

    paper_src = Image.open(paper_path).convert("RGB")
    label = ctk.CTkLabel(host, text="", fg_color="transparent")
    label.place(x=0, y=0, relwidth=1, relheight=1)

    state: dict[str, Any] = {"img": None, "w": 0, "h": 0}

    def _stack() -> None:
        # Sit above CTk's solid fill, under packed UI (so dots show around cards)
        try:
            label.lift(host._canvas)  # type: ignore[attr-defined]
        except (tk.TclError, AttributeError):
            try:
                label.lift()
            except tk.TclError:
                pass

    def _paint(_event: object | None = None) -> None:
        w = max(host.winfo_width(), 2)
        h = max(host.winfo_height(), 2)
        if w < 40 or h < 40:
            return
        if w == state["w"] and h == state["h"] and state["img"] is not None:
            _stack()
            return
        state["w"], state["h"] = w, h
        fitted = ImageOps.fit(
            paper_src,
            (w, h),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        ctk_img = ctk.CTkImage(light_image=fitted, dark_image=fitted, size=(w, h))
        state["img"] = ctk_img
        label.configure(image=ctk_img)
        _stack()

    host.bind("<Configure>", _paint)
    label.bind("<Configure>", _paint)
    host.after(40, _paint)
    host.after(50, _stack)
    return label


def attach_page_border(
    host: ctk.CTk | ctk.CTkFrame,
    **kwargs: Any,
) -> ctk.CTkLabel | None:
    """Deprecated — use attach_background (dotted paper only)."""
    return attach_background(host, bg_path=kwargs.get("bg_path"))


def lace_frame(
    master: Any,
    *,
    border_path: Any = None,
    inset_frac: float | None = None,
    width: int | None = None,
    height: int | None = None,
    size: int | None = None,
) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
    """
    Punch-station lace from assets/punch-border.png (portrait).

    Keeps the border's native aspect so lace isn't squashed. Dotted paper
    fills the card; window wallpaper shows outside this host.
    """
    path = Path(border_path) if border_path else PUNCH_BORDER_PATH
    if size is not None and width is None and height is None:
        width = size
        height = size
    if width is None:
        width = 440
    if height is None:
        height = int(round(width / PUNCH_BORDER_ASPECT))

    inset_x = PUNCH_BORDER_INSET_X
    inset_y = PUNCH_BORDER_INSET_Y
    if inset_frac is not None:
        inset_x = inset_y = inset_frac

    host = ctk.CTkFrame(master, fg_color="transparent", width=width, height=height)
    host.pack_propagate(False)

    bg = COLORS["bg"]
    canvas = tk.Canvas(host, bg=bg, highlightthickness=0, bd=0)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    pad = ctk.CTkFrame(host, fg_color="transparent")
    pad.place(
        relx=0.5,
        rely=0.5,
        anchor="center",
        relwidth=max(0.2, 1.0 - 2.0 * inset_x),
        relheight=max(0.2, 1.0 - 2.0 * inset_y),
    )

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

    state: dict[str, Any] = {
        "photo": None,
        "w": 0,
        "h": 0,
        "source": None,
        "paper": None,
    }
    try:
        from PIL import Image

        if path.is_file():
            state["source"] = Image.open(path).convert("RGBA")
        if BG_PATH.is_file():
            state["paper"] = Image.open(BG_PATH).convert("RGBA")
    except ImportError:
        state["source"] = None
        state["paper"] = None

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
        r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
        try:
            from PIL import Image, ImageOps, ImageTk
        except ImportError:
            canvas.create_rectangle(0, 0, w, h, fill=bg, outline="", tags="lace")
            return

        if state["paper"] is not None:
            paper = ImageOps.fit(
                state["paper"],
                (w, h),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
        else:
            paper = Image.new("RGBA", (w, h), (r, g, b, 255))

        src = state["source"]
        if src is not None:
            # Fit portrait lace into the portrait host — no square squash
            lace = ImageOps.fit(
                src,
                (w, h),
                method=Image.Resampling.NEAREST,
                centering=(0.5, 0.5),
            )
            composited = Image.alpha_composite(paper, lace).convert("RGB")
        else:
            composited = paper.convert("RGB")

        photo = ImageTk.PhotoImage(composited)
        state["photo"] = photo
        canvas.create_image(0, 0, anchor="nw", image=photo, tags="lace")
        _stack()

    host.bind("<Configure>", _paint, add="+")
    host.bind("<Configure>", _stack, add="+")
    host.after(40, _paint)
    host.after(50, _stack)
    return host, pad


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


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def render_win95_shell(
    *,
    fg: str,
    border: str,
    width: int,
    height: int,
    enabled: bool = True,
    pressed: bool = False,
) -> Any:
    """
    Draw a Windows 95-style raised/sunken bevel button with Pillow.
    Square corners, light top-left / dark bottom-right (classic 3D chrome).
    Text is NOT baked in — CTk overlays emoticons with a Unicode font.
    """
    from PIL import Image, ImageDraw

    scale = 2
    w, h = width * scale, height * scale
    bevel = max(6 * scale, 10)  # thick Win95 chrome

    face = _hex_to_rgb(fg)
    edge = _hex_to_rgb(border)
    # Classic Win95 bevel lights — tinted pink/white to match the app
    hi = (255, 255, 255) if enabled else (230, 220, 224)
    mid_hi = _mix(face, (255, 255, 255), 0.55)
    lo = _mix(edge, (40, 20, 30), 0.35)
    outer = _mix(edge, (20, 10, 15), 0.55)
    if not enabled:
        face = _mix(face, (210, 200, 205), 0.4)
        lo = _mix(lo, (180, 170, 175), 0.35)

    # Pressed = inverted bevel (sunken)
    if pressed:
        hi, lo = lo, hi
        mid_hi, face = _mix(face, lo, 0.12), _mix(face, lo, 0.08)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer dark frame (Win95 always has a hard outer edge)
    draw.rectangle((0, 0, w - 1, h - 1), fill=outer + (255,))
    # Face fill
    draw.rectangle((scale, scale, w - 1 - scale, h - 1 - scale), fill=face + (255,))

    # Bevel lines (raised 3D)
    for i in range(bevel):
        # top + left highlight
        draw.line([(scale + i, scale + i), (w - 2 - scale - i, scale + i)], fill=hi + (255,))
        draw.line([(scale + i, scale + i), (scale + i, h - 2 - scale - i)], fill=hi + (255,))
        # bottom + right shadow
        draw.line(
            [(scale + i, h - 2 - scale - i), (w - 1 - scale - i, h - 2 - scale - i)],
            fill=lo + (255,),
        )
        draw.line(
            [(w - 2 - scale - i, scale + i), (w - 2 - scale - i, h - 1 - scale - i)],
            fill=lo + (255,),
        )

    # Soft inner wash so pink/white faces feel paper-like, not gray OS chrome
    wash = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(wash).rectangle(
        (bevel + scale, bevel + scale, w - 1 - bevel - scale, h - 1 - bevel - scale),
        fill=mid_hi + (35 if enabled else 15,),
    )
    img = Image.alpha_composite(img, wash)

    final = img.resize((width, height), Image.Resampling.NEAREST)  # keep chunky pixels
    return ctk.CTkImage(light_image=final, dark_image=final, size=(width, height))


# Back-compat alias
render_plastic_shell = render_win95_shell


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
    face: bool = False,
) -> ctk.CTkButton:
    """Soft nav/action pill (flat CTk). Punch faces use nintendo_button + Pillow."""
    face_fg = fg if fg is not None else COLORS["cream"]
    face_hover = hover if hover is not None else COLORS["blush"]
    rim_color = border_color if border_color is not None else COLORS["border"]
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
        fg_color=face_fg,
        hover_color=face_hover,
        text_color=COLORS["text"],
        text_color_disabled=COLORS["disabled_text"],
        border_width=BORDER_WIDTH_CHUNKY,
        border_color=rim_color,
        command=command,
    )


def nintendo_button(
    master: Any,
    text: str,
    kind: str,
    *,
    command: Callable[[], None] | None = None,
    width: int = 300,
    height: int = 56,
    font_size: int = 14,
) -> ctk.CTkFrame:
    """
    Win95-style bevel button (pink/white), drawn with Pillow.

    Emoticons/labels use Comfortaa (FONT_BODY).
    """
    palette = NINTENDO_BTNS.get(kind, NINTENDO_BTNS["clock_in"])
    normal_img = render_win95_shell(
        fg=palette["fg"], border=palette["border"], width=width, height=height, enabled=True
    )
    disabled_img = render_win95_shell(
        fg=palette["fg"], border=palette["border"], width=width, height=height, enabled=False
    )
    hover_img = render_win95_shell(
        fg=palette["hover"], border=palette["border"], width=width, height=height, enabled=True
    )
    pressed_img = render_win95_shell(
        fg=palette["hover"],
        border=palette["border"],
        width=width,
        height=height,
        enabled=True,
        pressed=True,
    )

    host = ctk.CTkFrame(master, fg_color="transparent", width=width, height=height)
    host.pack_propagate(False)

    shell = ctk.CTkLabel(host, text="", image=normal_img, fg_color="transparent")
    shell.place(x=0, y=0, relwidth=1, relheight=1)

    label = ctk.CTkLabel(
        host,
        text=text,
        font=ctk.CTkFont(family=FONT_BODY, size=font_size),
        text_color=COLORS["text"],
        fg_color="transparent",
        wraplength=max(40, width - 28),
        justify="center",
    )
    label.place(relx=0.5, rely=0.5, anchor="center")

    host._zen_enabled = True  # type: ignore[attr-defined]
    host._zen_command = command  # type: ignore[attr-defined]
    host._zen_shell = shell  # type: ignore[attr-defined]
    host._zen_label = label  # type: ignore[attr-defined]
    host._zen_img_normal = normal_img  # type: ignore[attr-defined]
    host._zen_img_disabled = disabled_img  # type: ignore[attr-defined]
    host._zen_img_hover = hover_img  # type: ignore[attr-defined]
    host._zen_img_pressed = pressed_img  # type: ignore[attr-defined]
    host._zen_border = palette["border"]  # type: ignore[attr-defined]
    host._zen_fg = palette["fg"]  # type: ignore[attr-defined]
    host._zen_hover = palette["hover"]  # type: ignore[attr-defined]

    def _click(_event: object | None = None) -> None:
        if not getattr(host, "_zen_enabled", True):
            return
        cb = getattr(host, "_zen_command", None)
        if cb is not None:
            cb()

    def _press(_event: object | None = None) -> None:
        if getattr(host, "_zen_enabled", True):
            shell.configure(image=host._zen_img_pressed)  # type: ignore[attr-defined]

    def _enter(_event: object | None = None) -> None:
        if getattr(host, "_zen_enabled", True):
            shell.configure(image=host._zen_img_hover)  # type: ignore[attr-defined]

    def _leave(_event: object | None = None) -> None:
        if getattr(host, "_zen_enabled", True):
            shell.configure(image=host._zen_img_normal)  # type: ignore[attr-defined]
        else:
            shell.configure(image=host._zen_img_disabled)  # type: ignore[attr-defined]

    for widget in (host, shell, label):
        widget.bind("<ButtonPress-1>", _press, add="+")
        widget.bind("<ButtonRelease-1>", _click, add="+")
        widget.bind("<Enter>", _enter, add="+")
        widget.bind("<Leave>", _leave, add="+")
        widget.configure(cursor="hand2")

    return host


def set_nintendo_enabled(btn: Any, enabled: bool) -> None:
    """Enable/disable a Pillow plastic face and swap its drawn art."""
    btn._zen_enabled = enabled  # type: ignore[attr-defined]
    shell = getattr(btn, "_zen_shell", None)
    label = getattr(btn, "_zen_label", None)
    if shell is not None:
        shell.configure(
            image=btn._zen_img_normal if enabled else btn._zen_img_disabled  # type: ignore[attr-defined]
        )
    if label is not None:
        label.configure(
            text_color=COLORS["text"] if enabled else COLORS["disabled_text"]
        )
    cursor = "hand2" if enabled else "arrow"
    for widget in (btn, shell, label):
        if widget is not None:
            try:
                widget.configure(cursor=cursor)
            except tk.TclError:
                pass


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
