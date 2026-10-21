"""Win32 CF_UNICODETEXT clipboard (works under Wine)."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

CF_DIB = 8
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
user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
user32.RegisterClipboardFormatW.restype = wintypes.UINT

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


def _read_format(fmt: int) -> bytes:
    if not user32.IsClipboardFormatAvailable(fmt):
        return b""
    handle = user32.GetClipboardData(fmt)
    if not handle:
        return b""
    ptr = kernel32.GlobalLock(handle)
    if not ptr:
        return b""
    try:
        size = kernel32.GlobalSize(handle)
        if not size:
            return b""
        return ctypes.string_at(ptr, size)
    finally:
        kernel32.GlobalUnlock(handle)


def _dib_to_bmp(dib: bytes) -> bytes:
    if len(dib) < 40:
        return b""
    header_size = int.from_bytes(dib[0:4], "little")
    bitcount = int.from_bytes(dib[14:16], "little")
    colors = int.from_bytes(dib[32:36], "little") if len(dib) >= 36 else 0
    if colors == 0 and 0 < bitcount <= 8:
        colors = 1 << bitcount
    palette = colors * 4 if bitcount <= 8 else 0
    off = 14 + header_size + palette
    size = 14 + len(dib)
    file_header = b"BM" + size.to_bytes(4, "little") + b"\x00\x00\x00\x00" + off.to_bytes(4, "little")
    return file_header + dib


def get_image_bytes() -> tuple[str, bytes]:
    """Return (suffix, bytes) for a clipboard screenshot, or ('', b'')."""
    _open()
    try:
        for name in ("PNG", "image/png"):
            fmt = user32.RegisterClipboardFormatW(name)
            raw = _read_format(fmt)
            if raw.startswith(b"\x89PNG"):
                end = raw.find(b"IEND")
                if end != -1:
                    raw = raw[: end + 8]
                return ".png", raw
        dib = _read_format(CF_DIB)
        bmp = _dib_to_bmp(dib)
        if bmp.startswith(b"BM"):
            return ".bmp", bmp
        return "", b""
    finally:
        user32.CloseClipboard()


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


def _html_clipboard(fragment: str) -> bytes:
    """Windows HTML Format. Offsets are byte offsets into this UTF-8 payload."""
    fragment_bytes = fragment.encode("utf-8")
    start_marker = b"<!--StartFragment-->"
    end_marker = b"<!--EndFragment-->"
    head = (
        "Version:0.9\r\n"
        "StartHTML:{start_html:08d}\r\n"
        "EndHTML:{end_html:08d}\r\n"
        "StartFragment:{start_frag:08d}\r\n"
        "EndFragment:{end_frag:08d}\r\n"
    )
    # Header length is fixed because the numbers are zero-padded to 8 digits.
    header = head.format(start_html=0, end_html=0, start_frag=0, end_frag=0).encode("ascii")
    prefix = b"<html><body>\r\n" + start_marker
    suffix = end_marker + b"\r\n</body></html>"
    start_html = len(header)
    start_frag = start_html + len(prefix)
    end_frag = start_frag + len(fragment_bytes)
    end_html = end_frag + len(suffix)
    header = head.format(
        start_html=start_html,
        end_html=end_html,
        start_frag=start_frag,
        end_frag=end_frag,
    ).encode("ascii")
    return header + prefix + fragment_bytes + suffix


def set_text(text: str, html: str | None = None) -> None:
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
    html_handle = None
    html_fmt = 0
    if html:
        html_bytes = _html_clipboard(html)
        html_handle = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(html_bytes) + 1)
        if not html_handle:
            raise ClipboardError("GlobalAlloc failed")
        hptr = kernel32.GlobalLock(html_handle)
        if not hptr:
            raise ClipboardError("GlobalLock failed")
        try:
            ctypes.memmove(hptr, html_bytes, len(html_bytes))
        finally:
            kernel32.GlobalUnlock(html_handle)
        html_fmt = user32.RegisterClipboardFormatW("HTML Format")
    _open()
    try:
        if not user32.EmptyClipboard():
            raise ClipboardError("EmptyClipboard failed")
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise ClipboardError("SetClipboardData failed")
        handle = None
        if html_handle:
            if not user32.SetClipboardData(html_fmt, html_handle):
                raise ClipboardError("SetClipboardData HTML failed")
            html_handle = None
    finally:
        user32.CloseClipboard()
