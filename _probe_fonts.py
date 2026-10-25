import ctypes
from ctypes import wintypes
from pathlib import Path

FR_PRIVATE = 0x10
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
gdi32.AddFontResourceExW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID)
gdi32.AddFontResourceExW.restype = ctypes.c_int

fonts = Path(r"C:\projects\zenlog\zenlog\fonts")
for p in sorted(fonts.glob("*.ttf")):
    n = gdi32.AddFontResourceExW(str(p), FR_PRIVATE, None)
    print("loaded", p.name, "->", n)

import tkinter as tk
from tkinter import font as tkfont

root = tk.Tk()
root.withdraw()
families = set(tkfont.families())
for name in ("Fredoka", "Comfortaa", "Fredoka One", "Segoe UI"):
    print(name, "available=", name in families)
for f in sorted(families):
    if "fred" in f.lower() or "comfort" in f.lower():
        print("match:", repr(f))
root.destroy()
