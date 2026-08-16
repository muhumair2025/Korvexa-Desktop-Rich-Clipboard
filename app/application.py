"""
Main application controller for ClipVault.
Manages single instance protection, services initialization, hotkey binding,
theme changes, and application lifecycle.
"""

import sys
from typing import Optional
from PySide6.QtCore import QObject, QSharedMemory, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.constants import (
    APP_DISPLAY_NAME,
    APP_MUTEX_NAME,
    APP_NAME,
    APP_ORGANIZATION,
    APP_VERSION,
)
from app.theme import ThemeManager
from clipboard.monitor import ClipboardMonitor
from database.database import Database
from database.repositories import ClipboardRepository, SettingsRepository
from hotkeys.global_hotkey import GlobalHotkeyManager
from models.clipboard_item import ClipboardItem
from models.settings_model import AppSettings
from services.clipboard_service import ClipboardService
from services.history_service import HistoryService
from services.image_service import ImageService
from services.paste_service import PasteService
from services.privacy_service import PrivacyService
from services.retention_service import RetentionService
from storage.paths import StoragePaths
from ui.icons import IconProvider
from ui.tray import SystemTray
from utils.logging_config import get_logger
from windows.about_window import AboutWindow
from windows.clipboard_popup import ClipboardPopup
from windows.settings_window import SettingsWindow
from windows.text_editor import TextEditorDialog

logger = get_logger("ClipVault.App")


class ClipVaultApp(QObject):
    """Core application controller."""

    def __init__(self, qapp: QApplication):
        super().__init__()
        self.qapp = qapp
        self._shared_memory: Optional[QSharedMemory] = None

        self._init_metadata()

    def _init_metadata(self) -> None:
        self.qapp.setApplicationName(APP_NAME)
        self.qapp.setApplicationDisplayName(APP_DISPLAY_NAME)
        self.qapp.setApplicationVersion(APP_VERSION)
        self.qapp.setOrganizationName(APP_ORGANIZATION)
        self.qapp.setQuitOnLastWindowClosed(False)

        # Set default application window icon
        app_icon = IconProvider.get_icon("app", size=32, color="#0078d4")
        self.qapp.setWindowIcon(app_icon)

    def check_single_instance(self) -> bool:
        """Verifies no other ClipVault instance is running."""
        self._shared_memory = QSharedMemory(APP_MUTEX_NAME)
        if not self._shared_memory.create(1):
            logger.warning("Another instance of ClipVault is already running.")
            return False
        return True

    def initialize_and_run(self) -> int:
        """Initializes all subsystems and starts application execution."""
        StoragePaths.initialize_directories()

        # 1. Database & Repositories
        self.db = Database.get_instance()
        self.db.initialize()

        self.clipboard_repo = ClipboardRepository(self.db)
        self.settings_repo = SettingsRepository(self.db)
        self.settings = self.settings_repo.load_settings()

        # 2. Theme Manager
        self.theme_manager = ThemeManager.get_instance(self.settings.theme)
        self.theme_manager.apply_theme(self.qapp)

        # 2.1 Sync Windows Autostart
        if self.settings.start_with_windows and not StartupService.is_startup_enabled():
            StartupService.set_startup_enabled(True)

        # 3. System Clipboard & Monitor
        self.q_clipboard = self.qapp.clipboard()
        self.clipboard_monitor = ClipboardMonitor(self.q_clipboard, self)

        # 4. Background Services
        self.image_service = ImageService()
        self.privacy_service = PrivacyService(self.settings)
        self.history_service = HistoryService(self.clipboard_repo)
        self.retention_service = RetentionService(self.clipboard_repo, self.settings, self)
        self.retention_service.start()

        self.paste_service = PasteService(
            self.q_clipboard, self.clipboard_monitor, self.settings, self
        )

        self.clipboard_service = ClipboardService(
            clipboard=self.q_clipboard,
            monitor=self.clipboard_monitor,
            repository=self.clipboard_repo,
            privacy_service=self.privacy_service,
            image_service=self.image_service,
            settings=self.settings,
            parent=self,
        )

        # 5. UI Windows
        is_dark = self.theme_manager.is_dark
        self.popup = ClipboardPopup(
            self.history_service, self.paste_service, is_dark=is_dark
        )
        self.popup.settings_requested.connect(self.show_settings)
        self.popup.edit_item_requested.connect(self.show_text_editor)

        # Update popup when a new item is captured
        self.clipboard_service.item_added.connect(lambda item: self.popup.reload_items())

        # 6. System Tray
        self.tray = SystemTray(self.clipboard_monitor, is_dark=is_dark)
        self.tray.open_popup_requested.connect(self.show_popup)
        self.tray.open_settings_requested.connect(self.show_settings)
        self.tray.clear_history_requested.connect(self.clear_history)
        self.tray.about_requested.connect(self.show_about)
        self.tray.quit_requested.connect(self.quit_app)

        if self.settings.show_tray_icon:
            self.tray.show()

        # 7. Global Hotkeys
        self.hotkey_manager = GlobalHotkeyManager(self)
        self._register_hotkeys()
        self.hotkey_manager.hotkey_triggered.connect(self._on_hotkey_triggered)

        # 8. Initial clipboard check
        self.clipboard_service.process_clipboard_change()

        logger.info(f"{APP_DISPLAY_NAME} initialized successfully.")
        return self.qapp.exec()

    def _register_hotkeys(self) -> None:
        """Registers configured global shortcuts."""
        self.hotkey_manager.unregister_all()

        # Primary popup shortcut
        self._hk_popup_id = self.hotkey_manager.register_hotkey(self.settings.shortcut_popup)
        # Plain text paste shortcut
        self._hk_plain_id = self.hotkey_manager.register_hotkey(self.settings.shortcut_plain_paste)

    def _on_hotkey_triggered(self, hotkey_id: int) -> None:
        """Handles hotkey execution."""
        if hotkey_id == self._hk_popup_id:
            self.show_popup()

    def show_popup(self) -> None:
        """Displays clipboard picker window."""
        self.popup.show_at_smart_position()

    def show_settings(self) -> None:
        """Displays modal settings dialog."""
        dialog = SettingsWindow(
            self.settings_repo,
            self.settings,
            clipboard_repo=self.clipboard_repo,
            is_dark=self.theme_manager.is_dark,
        )
        dialog.settings_updated.connect(self._on_settings_updated)
        dialog.clear_history_requested.connect(self.clear_history)
        dialog.history_imported.connect(self.popup.reload_items)
        dialog.exec()

    def show_text_editor(self, item: ClipboardItem) -> None:
        """Displays text editor modal."""
        dialog = TextEditorDialog(item)
        dialog.text_saved.connect(self._on_item_text_saved)
        dialog.exec()

    def _on_item_text_saved(self, item_id: int, new_text: str) -> None:
        self.history_service.update_item_text(item_id, new_text)
        self.popup.reload_items()

    def show_about(self) -> None:
        """Displays About dialog."""
        dialog = AboutWindow(is_dark=self.theme_manager.is_dark)
        dialog.exec()

    def clear_history(self) -> None:
        """Clears all unpinned history."""
        self.history_service.clear_history(keep_pinned=True)
        self.popup.reload_items()

    def _on_settings_updated(self, new_settings: AppSettings) -> None:
        """Applies updated configuration settings."""
        self.settings = new_settings
        self.clipboard_service.update_settings(new_settings)
        self.privacy_service.update_settings(new_settings)
        self.paste_service.update_settings(new_settings)
        self.retention_service.update_settings(new_settings)

        # Update Theme
        self.theme_manager.apply_theme(self.qapp, new_settings.theme)
        is_dark = self.theme_manager.is_dark
        self.popup.set_theme(is_dark)

        # Update Tray visibility
        if new_settings.show_tray_icon:
            self.tray.show()
        else:
            self.tray.hide()

        # Update Hotkeys
        self._register_hotkeys()
        logger.info("Application settings reloaded and applied.")

    def quit_app(self) -> None:
        """Cleans up and terminates application."""
        logger.info("Exiting ClipVault...")
        self.clipboard_monitor.cleanup()
        self.hotkey_manager.unregister_all()
        self.retention_service.stop()
        self.tray.hide()
        self.qapp.quit()
