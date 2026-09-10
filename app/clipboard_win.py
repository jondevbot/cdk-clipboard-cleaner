"""Win32 CF_UNICODETEXT clipboard (works under Wine)."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL
user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalSize.restype = ctypes.c_size_t


class ClipboardError(RuntimeError):
    pass


def _open(retries: int = 20, delay: float = 0.05) -> None:
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return
        time.sleep(delay)
    raise ClipboardError("OpenClipboard failed")


def get_text() -> str:
    _open()
    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return ""
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return ""
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return ""
        try:
            size = kernel32.GlobalSize(handle)
            raw = ctypes.string_at(ptr, size)
        finally:
            kernel32.GlobalUnlock(handle)
        # UTF-16LE, typically NUL-terminated
        return raw.decode("utf-16-le", errors="replace").split("\x00", 1)[0]
    finally:
        user32.CloseClipboard()


def set_text(text: str) -> None:
    payload = text.replace("\n", "\r\n")
    data = payload.encode("utf-16-le") + b"\x00\x00"
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data))
    if not handle:
        raise ClipboardError("GlobalAlloc failed")
    ptr = kernel32.GlobalLock(handle)
    if not ptr:
        raise ClipboardError("GlobalLock failed")
    try:
        ctypes.memmove(ptr, data, len(data))
    finally:
        kernel32.GlobalUnlock(handle)
    _open()
    try:
        if not user32.EmptyClipboard():
            raise ClipboardError("EmptyClipboard failed")
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise ClipboardError("SetClipboardData failed")
        handle = None  # clipboard now owns the HGLOBAL
    finally:
        user32.CloseClipboard()
