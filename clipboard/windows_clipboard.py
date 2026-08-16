"""
Native Windows API ctypes interface for ClipVault.
Implements low-level Win32 clipboard listener, format registers, SendInput keyboard synthesis,
foreground window focus restoration, and process identification.
"""

import ctypes
from ctypes import wintypes
import os
import struct
from typing import List, Optional, Tuple

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = getattr(ctypes.windll, "psapi", None)

# Windows Clipboard Formats
CF_TEXT = 1
CF_BITMAP = 2
CF_DIB = 8
CF_UNICODETEXT = 13
CF_HDROP = 15
CF_DIBV5 = 17

# Windows Messages
WM_CLIPBOARDUPDATE = 0x031D
WM_HOTKEY = 0x0312

# Key event flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_V = 0x56

# DROPFILES structure for CF_HDROP
class DROPFILES(ctypes.Structure):
    _fields_ = [
        ("pFiles", wintypes.DWORD),  # Offset of file list from beginning of structure
        ("pt", wintypes.POINT),      # Drop point coordinates
        ("fNC", wintypes.BOOL),      # Non-client area flag
        ("fWide", wintypes.BOOL),    # Unicode flag (True = UTF-16, False = ANSI)
    ]

# Win32 SendInput Structures (64-bit safe)
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("mi", MOUSEINPUT),
            ("hi", HARDWAREINPUT),
        ]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT),
    ]


def register_clipboard_format(format_name: str) -> int:
    """Registers or looks up a custom Windows clipboard format (e.g. 'HTML Format')."""
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    return user32.RegisterClipboardFormatW(format_name)


HTML_FORMAT_ID = register_clipboard_format("HTML Format")


def get_foreground_window() -> int:
    """Returns handle of currently active foreground window."""
    user32.GetForegroundWindow.restype = wintypes.HWND
    return user32.GetForegroundWindow()


def set_foreground_window(hwnd: int) -> bool:
    """Restores focus to specified window handle using AttachThreadInput and AllowSetForegroundWindow."""
    if not hwnd or hwnd == 0:
        return False

    try:
        ASFW_ANY = wintypes.DWORD(0xFFFFFFFF)
        if hasattr(user32, "AllowSetForegroundWindow"):
            user32.AllowSetForegroundWindow(ASFW_ANY)
    except Exception:
        pass

    current_thread = kernel32.GetCurrentThreadId()
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)

    attached = False
    if current_thread != target_thread and target_thread != 0:
        attached = bool(user32.AttachThreadInput(current_thread, target_thread, True))

    try:
        if bool(user32.IsIconic(hwnd)):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        else:
            user32.BringWindowToTop(hwnd)
        return bool(user32.SetForegroundWindow(hwnd))
    finally:
        if attached:
            user32.AttachThreadInput(current_thread, target_thread, False)


def make_window_topmost(hwnd: int) -> bool:
    """Forces window handle to be top-level topmost above all modal windows and dialogues."""
    if not hwnd or hwnd == 0:
        return False
    try:
        HWND_TOPMOST = wintypes.HWND(-1)
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        SWP_SHOWWINDOW = 0x0040

        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL
        return bool(
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
        )
    except Exception:
        return False


def get_process_name_for_hwnd(hwnd: int) -> str:
    """Retrieves executable name (e.g. 'chrome.exe', 'notepad.exe') for a given window handle."""
    if not hwnd or hwnd == 0:
        return ""

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h_proc:
        return ""

    try:
        buffer = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if hasattr(kernel32, "QueryFullProcessImageNameW"):
            kernel32.QueryFullProcessImageNameW.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.LPWSTR,
                ctypes.POINTER(wintypes.DWORD),
            ]
            if kernel32.QueryFullProcessImageNameW(h_proc, 0, buffer, ctypes.byref(size)):
                full_path = buffer.value
                return os.path.basename(full_path).lower()
        return ""
    finally:
        kernel32.CloseHandle(h_proc)


def send_paste_input() -> bool:
    """
    Synthesizes native Ctrl + V key combination into active application via Win32 SendInput,
    first ensuring modifier keys (Shift, Alt, Win) are released.
    """
    # 7 keyboard inputs: Shift Up, Alt Up, Win Up, Ctrl Down, V Down, V Up, Ctrl Up
    inputs = (INPUT * 7)()

    # 1. Shift Up (release modifier if held from hotkey)
    inputs[0].type = 1  # INPUT_KEYBOARD
    inputs[0].ki.wVk = VK_SHIFT
    inputs[0].ki.dwFlags = KEYEVENTF_KEYUP

    # 2. Alt Up
    inputs[1].type = 1
    inputs[1].ki.wVk = VK_MENU
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP

    # 3. Win Up
    inputs[2].type = 1
    inputs[2].ki.wVk = VK_LWIN
    inputs[2].ki.dwFlags = KEYEVENTF_KEYUP

    # 4. Ctrl Down
    inputs[3].type = 1
    inputs[3].ki.wVk = VK_CONTROL
    inputs[3].ki.dwFlags = 0

    # 5. V Down
    inputs[4].type = 1
    inputs[4].ki.wVk = VK_V
    inputs[4].ki.dwFlags = 0

    # 6. V Up
    inputs[5].type = 1
    inputs[5].ki.wVk = VK_V
    inputs[5].ki.dwFlags = KEYEVENTF_KEYUP

    # 7. Ctrl Up
    inputs[6].type = 1
    inputs[6].ki.wVk = VK_CONTROL
    inputs[6].ki.dwFlags = KEYEVENTF_KEYUP

    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT

    sent = user32.SendInput(7, inputs, ctypes.sizeof(INPUT))
    return sent == 7


def add_clipboard_listener(hwnd: int) -> bool:
    """Subscribes a window handle to receive WM_CLIPBOARDUPDATE messages."""
    user32.AddClipboardFormatListener.argtypes = [wintypes.HWND]
    user32.AddClipboardFormatListener.restype = wintypes.BOOL
    return bool(user32.AddClipboardFormatListener(hwnd))


def remove_clipboard_listener(hwnd: int) -> bool:
    """Unsubscribes a window handle from WM_CLIPBOARDUPDATE messages."""
    user32.RemoveClipboardFormatListener.argtypes = [wintypes.HWND]
    user32.RemoveClipboardFormatListener.restype = wintypes.BOOL
    return bool(user32.RemoveClipboardFormatListener(hwnd))


def create_hdrop_buffer(file_paths: List[str]) -> bytes:
    """
    Creates binary DROPFILES buffer for CF_HDROP clipboard format.
    Format is DROPFILES structure followed by null-separated UTF-16 file paths, terminated by double null.
    """
    dropfiles = DROPFILES()
    dropfiles.pFiles = ctypes.sizeof(DROPFILES)
    dropfiles.pt.x = 0
    dropfiles.pt.y = 0
    dropfiles.fNC = False
    dropfiles.fWide = True  # UTF-16

    # Convert paths to null-terminated UTF-16 strings
    encoded_paths = b"".join((p + "\0").encode("utf-16le") for p in file_paths)
    # Double null terminator
    encoded_paths += b"\0\0"

    header_bytes = ctypes.string_at(ctypes.byref(dropfiles), ctypes.sizeof(DROPFILES))
    return header_bytes + encoded_paths


def set_native_hdrop_clipboard(file_paths: List[str]) -> bool:
    """Directly sets CF_HDROP format in Windows clipboard for reliable Explorer paste."""
    if not file_paths:
        return False

    buffer_data = create_hdrop_buffer(file_paths)
    size = len(buffer_data)

    GMEM_MOVEABLE = 0x0002
    GMEM_ZEROINIT = 0x0040
    GHND = GMEM_MOVEABLE | GMEM_ZEROINIT

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    h_global = kernel32.GlobalAlloc(GHND, size)
    if not h_global:
        return False

    ptr = kernel32.GlobalLock(h_global)
    if not ptr:
        kernel32.GlobalFree(h_global)
        return False

    ctypes.memmove(ptr, buffer_data, size)
    kernel32.GlobalUnlock(h_global)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE

    if not user32.OpenClipboard(0):
        kernel32.GlobalFree(h_global)
        return False

    try:
        user32.EmptyClipboard()
        res = user32.SetClipboardData(CF_HDROP, h_global)
        return bool(res)
    finally:
        user32.CloseClipboard()
