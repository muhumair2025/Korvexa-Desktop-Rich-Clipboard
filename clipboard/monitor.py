"""
Event-driven clipboard monitor for ClipVault.
Combines QClipboard.dataChanged and Win32 WM_CLIPBOARDUPDATE for reliable notification.
Includes self-echo suppression and pause timer support.
"""

from ctypes import wintypes
from datetime import datetime, timedelta
import threading
from typing import Optional
from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, QTimer, Signal
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtWidgets import QWidget

from utils.logging_config import get_logger
from .windows_clipboard import WM_CLIPBOARDUPDATE, add_clipboard_listener, remove_clipboard_listener

logger = get_logger("ClipVault.Clipboard.Monitor")


class WinClipboardEventFilter(QAbstractNativeEventFilter):
    """Intercepts native Windows WM_CLIPBOARDUPDATE messages."""

    def __init__(self, on_update_callback):
        super().__init__()
        self.on_update_callback = on_update_callback

    def nativeEventFilter(self, event_type, message):
        if event_type in (b"windows_generic_MSG", "windows_generic_MSG"):
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_CLIPBOARDUPDATE:
                self.on_update_callback()
        return False, 0


class ClipboardMonitor(QObject):
    """Monitors Windows clipboard for real changes and notifies listeners."""

    clipboard_changed = Signal()

    def __init__(self, clipboard: QClipboard, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._clipboard = clipboard
        self._is_paused = False
        self._pause_until: Optional[datetime] = None
        self._suppress_internal_writes = False
        self._last_processed_time = 0.0
        self._pause_timer = QTimer(self)
        self._pause_timer.timeout.connect(self._check_pause_timer)

        # Debounce timer to coalesce rapid multi-format burst updates (e.g. Snipping Tool)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(120)
        self._debounce_timer.timeout.connect(self._emit_clipboard_changed)

        # 1. Connect Qt QClipboard dataChanged
        self._clipboard.dataChanged.connect(self._on_clipboard_data_changed)

        # 2. Native Windows AddClipboardFormatListener
        self._listener_hwnd = 0
        self._native_filter: Optional[WinClipboardEventFilter] = None
        self._setup_native_listener()

        logger.info("ClipboardMonitor initialized with native WM_CLIPBOARDUPDATE, debounce, and QClipboard.dataChanged")

    def _setup_native_listener(self) -> None:
        """Sets up Win32 AddClipboardFormatListener on a hidden widget."""
        try:
            self._listener_widget = QWidget()
            self._listener_widget.winId()  # Ensure native HWND is created
            self._listener_hwnd = int(self._listener_widget.winId())

            self._native_filter = WinClipboardEventFilter(self._on_clipboard_data_changed)
            app = QCoreApplication.instance()
            if app:
                app.installNativeEventFilter(self._native_filter)

            success = add_clipboard_listener(self._listener_hwnd)
            if success:
                logger.info(f"Registered native AddClipboardFormatListener on HWND {self._listener_hwnd}")
            else:
                logger.warning("AddClipboardFormatListener returned False")
        except Exception as e:
            logger.error(f"Failed to setup native clipboard listener: {e}", exc_info=True)

    def _check_pause_timer(self) -> None:
        """Checks if temporary pause duration has expired."""
        if self._pause_until and datetime.now() >= self._pause_until:
            logger.info("Pause duration expired. Resuming clipboard monitoring.")
            self.resume()

    def pause(self, minutes: Optional[int] = None) -> None:
        """Pauses clipboard monitoring indefinitely or for specified minutes."""
        self._is_paused = True
        if minutes is not None and minutes > 0:
            self._pause_until = datetime.now() + timedelta(minutes=minutes)
            self._pause_timer.start(1000)
            logger.info(f"Clipboard monitoring paused for {minutes} minutes.")
        else:
            self._pause_until = None
            self._pause_timer.stop()
            logger.info("Clipboard monitoring paused indefinitely.")

    def resume(self) -> None:
        """Resumes clipboard monitoring."""
        self._is_paused = False
        self._pause_until = None
        self._pause_timer.stop()
        logger.info("Clipboard monitoring resumed.")

    @property
    def is_paused(self) -> bool:
        """Returns whether monitoring is currently paused."""
        return self._is_paused

    def set_internal_write_flag(self, active: bool) -> None:
        """Sets or clears the echo-suppression flag when ClipVault itself writes to clipboard."""
        self._suppress_internal_writes = active

    def _on_clipboard_data_changed(self) -> None:
        """Invoked on clipboard changes."""
        if self._is_paused:
            return

        if self._suppress_internal_writes:
            logger.debug("Suppressed clipboard change triggered by internal ClipVault write.")
            return

        # Restart debounce timer to coalesce rapid multi-format burst updates
        self._debounce_timer.start()

    def _emit_clipboard_changed(self) -> None:
        """Emits clipboard change after debounce interval has elapsed."""
        if not self._is_paused and not self._suppress_internal_writes:
            self.clipboard_changed.emit()

    def cleanup(self) -> None:
        """Removes native clipboard listener."""
        if self._listener_hwnd:
            remove_clipboard_listener(self._listener_hwnd)
            self._listener_hwnd = 0
