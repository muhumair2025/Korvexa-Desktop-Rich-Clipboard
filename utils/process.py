"""
Process and active window helper utilities.
"""

from typing import Optional
from clipboard.windows_clipboard import get_foreground_window, get_process_name_for_hwnd


def get_active_process_name() -> str:
    """Returns executable name of active foreground process (e.g. 'chrome.exe')."""
    hwnd = get_foreground_window()
    return get_process_name_for_hwnd(hwnd)
