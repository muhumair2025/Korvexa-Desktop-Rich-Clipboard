"""
Paste execution service for ClipVault.
Restores clipboard content, refocuses the previous application window, and sends simulated Ctrl+V.
"""

from typing import Optional
from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QClipboard, QGuiApplication

from clipboard.monitor import ClipboardMonitor
from clipboard.windows_clipboard import send_paste_input, set_foreground_window
from clipboard.writer import ClipboardWriter
from models.clipboard_item import ClipboardItem
from models.settings_model import AppSettings
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.PasteService")


class PasteService(QObject):
    """Coordinates restoring clipboard content and sending native paste events to target windows."""

    def __init__(
        self,
        clipboard: QClipboard,
        monitor: ClipboardMonitor,
        settings: Optional[AppSettings] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._clipboard = clipboard
        self._monitor = monitor
        self._settings = settings or AppSettings()
        self._target_hwnd: Optional[int] = None

    def set_target_window(self, hwnd: int) -> None:
        """Stores the window handle of the application that was active before ClipVault opened."""
        self._target_hwnd = hwnd

    def update_settings(self, settings: AppSettings) -> None:
        """Updates active settings."""
        self._settings = settings

    def execute_paste(self, item: ClipboardItem, as_plain_text: bool = False) -> bool:
        """
        Restores the selected item to the real Windows clipboard, focuses the previous
        application, and sends a native Ctrl+V key event.
        """
        try:
            # 1. Temporarily suppress clipboard change echo
            self._monitor.set_internal_write_flag(True)

            # 2. Write item to real Windows clipboard
            written = ClipboardWriter.write_item(
                self._clipboard, item, as_plain_text=as_plain_text
            )
            if not written:
                self._monitor.set_internal_write_flag(False)
                return False

            # 3. Restore target window focus
            if self._target_hwnd:
                set_foreground_window(self._target_hwnd)

            # 4. Dispatch simulated Ctrl+V input after target window has activated
            delay_ms = max(50, self._settings.paste_delay_ms)
            QTimer.singleShot(delay_ms, self._dispatch_send_input)

            return True

        except Exception as e:
            self._monitor.set_internal_write_flag(False)
            logger.error(f"Error during execute_paste: {e}", exc_info=True)
            return False

    def _dispatch_send_input(self) -> None:
        """Dispatches SendInput Ctrl+V and clears suppression flag."""
        try:
            send_paste_input()
        finally:
            # Re-enable monitor echo processing after a brief delay
            QTimer.singleShot(250, lambda: self._monitor.set_internal_write_flag(False))
