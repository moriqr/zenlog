"""Shared visual tokens for the ZenLog UI — lace stationery on dotted pink paper."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

# Sampled from assets/bg.jpg + soft cream paper:
#   #FDE3EC  dotted pink wallpaper
#   #FFF8F5  cream paper (cards)
#   #8B5A6B  dusty rose rim
#   #3D2A32  ink
COLORS = {
    "bg": "#FDE3EC",
    "card": "#FFF8F5",
    "blush": "#F2C4D0",
    "lavender": "#E8D4DC",
    "lavender_hover": "#DDBFC9",
    "pink": "#F0B8C6",
    "pink_hover": "#E5A3B4",
    "mint": "#E8D4DC",
    "mint_hover": "#DDBFC9",
    "cream": "#FFF8F5",
    "peach": "#F2C4D0",
    "peach_hover": "#E8B0BE",
    "sky": "#F0D0D8",
    "sky_hover": "#E5BCC6",
    "butter": "#F6E4E8",
    "butter_hover": "#EBD0D6",
    "text": "#3D2A32",
    "text_muted": "#6B4A56",
    "border": "#8B5A6B",
    "border_soft": "#C49AA8",
    "disabled": "#E8D5DE",
    "disabled_text": "#9A7A8A",
    "today": "#F6E4E8",
    "selected": "#F2C4D0",
    "titlebar": "#FFFCFB",
    "accent": "#C47A90",
}

# Punch buttons — pink + white only (Win95 bevel faces via Pillow)
NINTENDO_BTNS = {
    "clock_in": {"fg": "#FFF8FB", "hover": "#FFE6EE", "border": "#8B5A6B"},
    "clock_out": {"fg": "#F7C9D4", "hover": "#F0B0C0", "border": "#8B5A6B"},
    "start_break": {"fg": "#FFF8FB", "hover": "#FFE6EE", "border": "#8B5A6B"},
    "end_break": {"fg": "#F7C9D4", "hover": "#F0B0C0", "border": "#8B5A6B"},
}

# Cute deco marks for buttons (short = nav, long = punch faces)
BTN_DECO = {
    "punch": "𝜗ৎ",
    "forgotten": "𑣲⋆",
    "history": "⋆˚꩜｡",
    "calendar": "꒰১ ໒꒱",
    "clock_in": "⋆｡‧˚ʚ🍓ɞ˚‧｡⋆",
    "clock_out": ". ݁⋆ ۶ৎ ݁˖ . ݁",
    "start_break": "꒰১ ໒꒱",
    "end_break": "(˶˃ ᵕ ˂˶)",
}

BORDER_WIDTH = 3
BORDER_WIDTH_CHUNKY = 5
BORDER_WIDTH_FACE = 7  # thick SNES plastic rim
CORNER_RADIUS = 16
CORNER_RADIUS_PILL = 24
CORNER_RADIUS_SOFT = CORNER_RADIUS_PILL
CORNER_RADIUS_FACE = 30  # rounded capsule — Nintendo face-button vibe

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
BG_PATH = ASSETS_DIR / "bg.jpg"
PUNCH_BORDER_PATH = ASSETS_DIR / "punch-border.png"
# Portrait punch-border hole — keep controls inside the lace rim
PUNCH_BORDER_INSET_X = 0.12
PUNCH_BORDER_INSET_Y = 0.10
PUNCH_BORDER_INSET_FRAC = 0.11  # fallback when a single frac is used
# Native asset aspect (1792×2400)
PUNCH_BORDER_ASPECT = 1792 / 2400
