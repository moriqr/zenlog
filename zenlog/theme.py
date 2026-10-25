"""Shared visual tokens for the ZenLog UI — soft Neocities / coquette vibes."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

# Your palette, mapped like the soft-pink window reference:
#   #F7C7D9  wallpaper / outer blush
#   #FFF8E7  cream paper windows (boxes)
#   #E88BAE  cute borders + title bars
#   #AA84C6  soft purple accents (active / primary)
#   #F9E29B  tiny warm highlight only (not big surfaces)
#   #5E3D52  muted plum
#   #3D303E  ink
COLORS = {
    "bg": "#F7C7D9",
    "card": "#FFF8E7",
    "blush": "#F7C7D9",
    "lavender": "#AA84C6",
    "lavender_hover": "#9570B5",
    "pink": "#E88BAE",
    "pink_hover": "#D9789E",
    "mint": "#FFF8E7",
    "mint_hover": "#F7C7D9",
    "cream": "#FFF8E7",
    "peach": "#F7C7D9",
    "peach_hover": "#E88BAE",
    "text": "#3D303E",
    "text_muted": "#5E3D52",
    "border": "#E88BAE",
    "disabled": "#F7C7D9",
    "disabled_text": "#AA84C6",
    "today": "#FEF1C4",
    "selected": "#E8D4F5",
    "titlebar": "#F7C7D9",
}

# Clean cute outlines (like the reference windows)
BORDER_WIDTH = 2
BORDER_WIDTH_CHUNKY = 3
CORNER_RADIUS = 16
CORNER_RADIUS_PILL = 22

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
_fonts_loaded = False


def _load_bundled_fonts() -> None:
    """Register bundled TTFs so Fredoka / Comfortaa work without a system install."""
    global _fonts_loaded
    if _fonts_loaded or sys.platform != "win32":
        return
    if not _FONTS_DIR.is_dir():
        return

    FR_PRIVATE = 0x10
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    gdi32.AddFontResourceExW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.LPVOID,
    )
    gdi32.AddFontResourceExW.restype = ctypes.c_int

    for path in _FONTS_DIR.glob("*.ttf"):
        gdi32.AddFontResourceExW(str(path), FR_PRIVATE, None)
    _fonts_loaded = True


_load_bundled_fonts()

FONT_DISPLAY = "Fredoka"
FONT_BODY = "Comfortaa"
FONT_FAMILY = FONT_DISPLAY
