"""
Global hotkey manager for Windows using native RegisterHotKey Win32 API.
Listens for system-wide keyboard shortcuts even when ClipVault is not in focus.
"""

import ctypes
from ctypes import wintypes
from typing import Callable, Dict, Optional, Tuple
from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, Signal

from utils.logging_config import get_logger

logger = get_logger("ClipVault.Hotkeys")

user32 = ctypes.windll.user32

# Modifiers
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312

# Key map for common virtual keys
VK_MAP = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46, "G": 0x47,
    "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C, "M": 0x4D, "N": 0x4E,
    "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54, "U": 0x55,
    "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59, "Z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34, "5": 0x35, "6": 0x36,
    "7": 0x37, "8": 0x38, "9": 0x39,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "SPACE": 0x20, "TAB": 0x09, "ENTER": 0x0D, "ESC": 0x1B, "ESCAPE": 0x1B,
    "INSERT": 0x2D, "DELETE": 0x2E, "HOME": 0x24, "END": 0x23,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22, "`": 0xC0, "~": 0xC0,
}


def parse_hotkey_string(hotkey_str: str) -> Optional[Tuple[int, int]]:
    """
    Parses a string like 'Ctrl+Shift+V' into (modifiers, vk_code).
    """
    if not hotkey_str:
        return None

    parts = [p.strip().upper() for p in hotkey_str.split("+")]
    modifiers = 0
    key_code = None

    for part in parts:
        if part in ("CTRL", "CONTROL"):
            modifiers |= MOD_CONTROL
        elif part == "SHIFT":
            modifiers |= MOD_SHIFT
        elif part in ("ALT", "MENU"):
            modifiers |= MOD_ALT
        elif part in ("WIN", "WINDOWS", "SUPER"):
            modifiers |= MOD_WIN
        else:
            if part in VK_MAP:
                key_code = VK_MAP[part]
            elif len(part) == 1:
                key_code = ord(part)

    if key_code is None:
        return None

    return modifiers, key_code


class WinNativeEventFilter(QAbstractNativeEventFilter):
    """Intercepts Windows WM_HOTKEY messages dispatched to the Qt application."""

    def __init__(self, callback: Callable[[int], None]):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG" or event_type == "windows_generic_MSG":
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY:
                hotkey_id = int(msg.wParam)
                self.callback(hotkey_id)
                return True, 0
        return False, 0


class GlobalHotkeyManager(QObject):
    """Manages system-wide global hotkeys using RegisterHotKey Win32 API."""

    hotkey_triggered = Signal(int)  # Emits hotkey_id

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._registered_hotkeys: Dict[int, str] = {}
        self._next_id = 1000

        # Install native event filter
        self._native_filter = WinNativeEventFilter(self._on_native_hotkey)
        QCoreApplication.instance().installNativeEventFilter(self._native_filter)

    def _on_native_hotkey(self, hotkey_id: int) -> None:
        """Invoked when a WM_HOTKEY message is intercepted."""
        if hotkey_id in self._registered_hotkeys:
            logger.debug(f"Global hotkey triggered: {self._registered_hotkeys[hotkey_id]} (ID: {hotkey_id})")
            self.hotkey_triggered.emit(hotkey_id)

    def register_hotkey(self, hotkey_str: str) -> Optional[int]:
        """
        Registers a global shortcut. Returns the integer hotkey ID or None on failure.
        """
        parsed = parse_hotkey_string(hotkey_str)
        if not parsed:
            logger.warning(f"Could not parse hotkey string: '{hotkey_str}'")
            return None

        modifiers, vk_code = parsed
        hotkey_id = self._next_id
        self._next_id += 1

        user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        user32.RegisterHotKey.restype = wintypes.BOOL

        # Register with MOD_NOREPEAT flag if supported
        success = user32.RegisterHotKey(0, hotkey_id, modifiers | MOD_NOREPEAT, vk_code)
        if not success:
            # Retry without MOD_NOREPEAT
            success = user32.RegisterHotKey(0, hotkey_id, modifiers, vk_code)

        if success:
            self._registered_hotkeys[hotkey_id] = hotkey_str
            logger.info(f"Registered global hotkey '{hotkey_str}' with ID {hotkey_id}.")
            return hotkey_id
        else:
            logger.warning(f"Failed to register global hotkey '{hotkey_str}' (may be in use by another application).")
            return None

    def unregister_hotkey(self, hotkey_id: int) -> bool:
        """Unregisters a specific global hotkey."""
        if hotkey_id in self._registered_hotkeys:
            user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.UnregisterHotKey.restype = wintypes.BOOL
            res = bool(user32.UnregisterHotKey(0, hotkey_id))
            name = self._registered_hotkeys.pop(hotkey_id, "")
            logger.info(f"Unregistered global hotkey '{name}' (ID: {hotkey_id}).")
            return res
        return False

    def unregister_all(self) -> None:
        """Unregisters all active global shortcuts."""
        for hotkey_id in list(self._registered_hotkeys.keys()):
            self.unregister_hotkey(hotkey_id)
