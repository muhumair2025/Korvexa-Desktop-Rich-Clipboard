"""
System tray integration for ClipVault.
Provides a persistent background tray icon with quick actions and pause monitoring options.
"""

from typing import Callable, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from app.constants import APP_DISPLAY_NAME
from clipboard.monitor import ClipboardMonitor
from ui.icons import IconProvider
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Tray")


class SystemTray(QObject):
    """Manages Windows System Tray icon and context menu."""

    open_popup_requested = Signal()
    open_settings_requested = Signal()
    clear_history_requested = Signal()
    about_requested = Signal()
    quit_requested = Signal()

    def __init__(
        self,
        monitor: ClipboardMonitor,
        is_dark: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._monitor = monitor
        self._is_dark = is_dark

        self._tray_icon = QSystemTrayIcon(parent)
        self._tray_icon.setToolTip(APP_DISPLAY_NAME)
        self._update_icon()

        self._setup_menu()
        self._tray_icon.activated.connect(self._on_tray_activated)

    def _update_icon(self) -> None:
        icon = IconProvider.get_icon("app", size=22, color="#0078d4")
        self._tray_icon.setIcon(icon)

    def _setup_menu(self) -> None:
        menu = QMenu()

        # Open Clipboard
        act_open = menu.addAction(
            IconProvider.get_icon("copy", size=14, is_dark=self._is_dark), "Open Clipboard"
        )
        act_open.triggered.connect(self.open_popup_requested.emit)

        # Settings
        act_settings = menu.addAction(
            IconProvider.get_icon("settings", size=14, is_dark=self._is_dark), "Settings..."
        )
        act_settings.triggered.connect(self.open_settings_requested.emit)

        menu.addSeparator()

        # Pause Monitoring Submenu
        pause_menu = menu.addMenu(
            IconProvider.get_icon("pause", size=14, is_dark=self._is_dark), "Pause Monitoring"
        )

        act_p5 = pause_menu.addAction("For 5 minutes")
        act_p5.triggered.connect(lambda: self._monitor.pause(minutes=5))

        act_p15 = pause_menu.addAction("For 15 minutes")
        act_p15.triggered.connect(lambda: self._monitor.pause(minutes=15))

        act_p30 = pause_menu.addAction("For 30 minutes")
        act_p30.triggered.connect(lambda: self._monitor.pause(minutes=30))

        act_p_indef = pause_menu.addAction("Until Resumed")
        act_p_indef.triggered.connect(lambda: self._monitor.pause(minutes=None))

        pause_menu.addSeparator()
        act_resume = pause_menu.addAction("Resume Monitoring")
        act_resume.triggered.connect(self._monitor.resume)

        # Clear History
        act_clear = menu.addAction(
            IconProvider.get_icon("clear", size=14, is_dark=self._is_dark), "Clear History"
        )
        act_clear.triggered.connect(self.clear_history_requested.emit)

        menu.addSeparator()

        # About
        act_about = menu.addAction("About ClipVault")
        act_about.triggered.connect(self.about_requested.emit)

        # Quit
        act_quit = menu.addAction("Quit")
        act_quit.triggered.connect(self.quit_requested.emit)

        self._tray_icon.setContextMenu(menu)

    def show(self) -> None:
        """Displays the system tray icon."""
        self._tray_icon.show()

    def hide(self) -> None:
        """Hides the system tray icon."""
        self._tray_icon.hide()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            self.open_popup_requested.emit()
