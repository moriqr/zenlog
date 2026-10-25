"""Cute reusable UI bits — cream windows with pink outlines."""

from __future__ import annotations

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
)


def cute_window(
    master: Any,
    *,
    title: str | None = None,
    fill: bool = True,
    pad: int = 10,
) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
    """
    Soft pink outer frame + cream inner paper (reference: pink wallpaper,
    white window, pink border). Returns (outer, inner).
    """
    outer = ctk.CTkFrame(
        master,
        fg_color=COLORS["blush"],
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
            corner_radius=CORNER_RADIUS - 4,
            height=36,
            border_width=0,
        )
        bar.pack(fill="x", padx=pad, pady=(pad, 6))
        bar.pack_propagate(False)
        ctk.CTkLabel(
            bar,
            text=f"♥  {title}",
            font=ctk.CTkFont(family=FONT_DISPLAY, size=13, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left", padx=12, fill="y")

    inner = ctk.CTkFrame(
        outer,
        fg_color=COLORS["card"],
        corner_radius=CORNER_RADIUS - 2,
        border_width=BORDER_WIDTH,
        border_color=COLORS["border"],
    )
    inner.pack(fill="both", expand=True, padx=pad, pady=(0 if title else pad, pad))
    return outer, inner


def cute_panel(
    master: Any,
    *,
    fg: str | None = None,
    chunky: bool = False,
    radius: int | None = None,
) -> ctk.CTkFrame:
    """Cream (or custom) box with a pink outline."""
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
    font_size: int = 13,
    bold: bool = True,
) -> ctk.CTkButton:
    """Cream/pink pill like the reference buttons — outline first, soft fill."""
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=height,
        corner_radius=CORNER_RADIUS_PILL,
        font=ctk.CTkFont(
            family=FONT_DISPLAY,
            size=font_size,
            weight="bold" if bold else "normal",
        ),
        fg_color=fg if fg is not None else COLORS["cream"],
        hover_color=hover if hover is not None else COLORS["blush"],
        text_color=COLORS["text"],
        border_width=BORDER_WIDTH,
        border_color=COLORS["border"],
        command=command,
    )


def page_title(master: Any, title: str, subtitle: str) -> None:
    ctk.CTkLabel(
        master,
        text=title,
        font=ctk.CTkFont(family=FONT_DISPLAY, size=22, weight="bold"),
        text_color=COLORS["text"],
    ).pack(anchor="w")
    ctk.CTkLabel(
        master,
        text=subtitle,
        font=ctk.CTkFont(family=FONT_BODY, size=13),
        text_color=COLORS["text_muted"],
    ).pack(anchor="w", pady=(2, 12))
