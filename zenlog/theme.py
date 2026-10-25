"""Shared visual tokens for the ZenLog UI — soft Neocities / coquette vibes."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

# Uniform soft palette:
#   #F7C7D9  wallpaper / soft fills / hovers
#   #FFF8E7  cream paper (boxes + buttons)
#   #AA84C6  OUTER borders only (not button fills)
#   #E88BAE  barely used (tiny accents only)
#   #F9E29B  tiny warm "today" highlight
#   #5E3D52  muted text
#   #3D303E  ink
COLORS = {
    "bg": "#F7C7D9",
    "card": "#FFF8E7",
    "blush": "#F7C7D9",
    # Kept for legacy keys — all map to soft cream / blush (no purple fills)
    "lavender": "#FFF8E7",
    "lavender_hover": "#F7C7D9",
    "pink": "#FFF8E7",
    "pink_hover": "#F7C7D9",
    "mint": "#FFF8E7",
    "mint_hover": "#F7C7D9",
    "cream": "#FFF8E7",
    "peach": "#FFF8E7",
    "peach_hover": "#F7C7D9",
    "text": "#3D303E",
    "text_muted": "#5E3D52",
    "border": "#AA84C6",  # purple outlines for buttons + boxes
    "border_soft": "#AA84C6",  # same purple (kept for older call sites)
    "disabled": "#F7C7D9",
    "disabled_text": "#5E3D52",
    "today": "#FEF1C4",
    "selected": "#F7C7D9",
    "titlebar": "#F7C7D9",
    "accent": "#E88BAE",  # rare accent (e.g. one traffic light)
}

BORDER_WIDTH = 3
BORDER_WIDTH_CHUNKY = 4
CORNER_RADIUS = 16
CORNER_RADIUS_PILL = 22
CORNER_RADIUS_SOFT = CORNER_RADIUS_PILL

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

# Bundled Fredoka TTFs register as "Fredoka Light" / "Fredoka Light SemiBold" on Windows.
FONT_DISPLAY = "Fredoka Light"
FONT_DISPLAY_BOLD = "Fredoka Light SemiBold"
FONT_BODY = "Comfortaa"
FONT_FAMILY = FONT_DISPLAY

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
PAGE_BORDER_PATH = ASSETS_DIR / "page-border.png"
PUNCH_BORDER_PATH = ASSETS_DIR / "1x1.png"
# Frame hole is ~12% x / ~9% y of the PNG — keep UI inside it
PAGE_BORDER_FRAC_X = 0.13
PAGE_BORDER_FRAC_Y = 0.11
PAGE_BORDER_INSET_X = 120
PAGE_BORDER_INSET_Y = 100
# Square 1x1 lace: hole starts ~56/500 from each edge
PUNCH_BORDER_INSET_FRAC = 0.12
