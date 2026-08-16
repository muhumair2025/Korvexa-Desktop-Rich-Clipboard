"""
Settings window for ClipVault.
Clean native tabbed configuration dialog for General, Clipboard, History, Privacy, Shortcuts,
Appearance, and Advanced preferences.
"""

import os
from pathlib import Path
import subprocess
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.constants import (
    MAX_ITEMS_OPTIONS,
    RETENTION_OPTIONS,
    THEMES,
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
)
from database.repositories import ClipboardRepository, SettingsRepository
from datetime import datetime
from models.settings_model import AppSettings
from services.backup_service import BackupService
from services.startup_service import StartupService
from storage.paths import StoragePaths
from ui.icons import IconProvider
from ui.widgets.shortcut_edit import ShortcutEdit


class SettingsWindow(QDialog):
    """Clean native settings dialog for ClipVault."""

    settings_updated = Signal(object)  # Emits AppSettings
    clear_history_requested = Signal()
    history_imported = Signal()

    def __init__(
        self,
        settings_repo: SettingsRepository,
        current_settings: AppSettings,
        clipboard_repo: Optional[ClipboardRepository] = None,
        is_dark: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._repo = settings_repo
        self._clipboard_repo = clipboard_repo
        self._settings = current_settings
        self._is_dark = is_dark

        self.setWindowTitle("ClipVault — Settings")
        self.resize(680, 540)
        self.setMinimumSize(600, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Tab Widget
        self._tabs = QTabWidget(self)

        self._tab_general = self._create_general_tab()
        self._tab_clipboard = self._create_clipboard_tab()
        self._tab_history = self._create_history_tab()
        self._tab_privacy = self._create_privacy_tab()
        self._tab_shortcuts = self._create_shortcuts_tab()
        self._tab_appearance = self._create_appearance_tab()
        self._tab_advanced = self._create_advanced_tab()

        self._tabs.addTab(self._tab_general, "General")
        self._tabs.addTab(self._tab_clipboard, "Clipboard")
        self._tabs.addTab(self._tab_history, "History")
        self._tabs.addTab(self._tab_privacy, "Privacy")
        self._tabs.addTab(self._tab_shortcuts, "Shortcuts")
        self._tabs.addTab(self._tab_appearance, "Appearance")
        self._tabs.addTab(self._tab_advanced, "Advanced")

        main_layout.addWidget(self._tabs, 1)

        # Bottom Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._btn_cancel = QPushButton("Cancel", self)
        self._btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self._btn_cancel)

        self._btn_save = QPushButton("Save", self)
        self._btn_save.setObjectName("PrimaryButton")
        self._btn_save.clicked.connect(self._save_settings)
        button_layout.addWidget(self._btn_save)

        main_layout.addLayout(button_layout)

    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp = QGroupBox("System Integration", widget)
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(8)

        self._chk_startup = QCheckBox("Start ClipVault automatically with Windows", grp)
        self._chk_tray = QCheckBox("Show ClipVault in system notification tray", grp)

        grp_layout.addWidget(self._chk_startup)
        grp_layout.addWidget(self._chk_tray)
        layout.addWidget(grp)

        layout.addStretch()
        return widget

    def _create_clipboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp = QGroupBox("Supported Clipboard Formats", widget)
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(8)

        self._chk_monitor = QCheckBox("Enable active clipboard monitoring", grp)
        self._chk_text = QCheckBox("Capture plain text", grp)
        self._chk_html = QCheckBox("Capture rich text / HTML", grp)
        self._chk_images = QCheckBox("Capture images & screenshots", grp)
        self._chk_files = QCheckBox("Capture files and folders (CF_HDROP metadata)", grp)
        self._chk_urls = QCheckBox("Capture web links & URLs", grp)

        grp_layout.addWidget(self._chk_monitor)
        grp_layout.addWidget(self._chk_text)
        grp_layout.addWidget(self._chk_html)
        grp_layout.addWidget(self._chk_images)
        grp_layout.addWidget(self._chk_files)
        grp_layout.addWidget(self._chk_urls)
        layout.addWidget(grp)

        layout.addStretch()
        return widget

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp = QGroupBox("History Retention & Limits", widget)
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(10)

        # Retention Period
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Keep clipboard history for:"))
        self._combo_retention = QComboBox(grp)
        self._combo_retention.addItems(RETENTION_OPTIONS)
        row1.addWidget(self._combo_retention)
        grp_layout.addLayout(row1)

        # Max Items Limit
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Maximum history items:"))
        self._combo_max_items = QComboBox(grp)
        for opt in MAX_ITEMS_OPTIONS:
            self._combo_max_items.addItem("Unlimited" if opt == 0 else f"{opt:,} items", opt)
        row2.addWidget(self._combo_max_items)
        grp_layout.addLayout(row2)

        self._chk_deduplicate = QCheckBox("Deduplicate identical clipboard entries (bump to top)", grp)
        grp_layout.addWidget(self._chk_deduplicate)

        layout.addWidget(grp)

        # Backup & Portability
        grp_backup = QGroupBox("Backup & Migration", widget)
        grp_backup_layout = QVBoxLayout(grp_backup)
        grp_backup_layout.setSpacing(8)

        lbl_desc = QLabel(
            "Export your full clipboard history, pinned clips, and image snapshots to migrate or restore on a new Windows installation.",
            grp_backup,
        )
        lbl_desc.setWordWrap(True)
        grp_backup_layout.addWidget(lbl_desc)

        backup_btn_row = QHBoxLayout()
        self._btn_export_backup = QPushButton("Export History Backup...", grp_backup)
        self._btn_export_backup.setIcon(
            IconProvider.get_icon("copy", size=14, is_dark=self._is_dark)
        )
        self._btn_export_backup.clicked.connect(self._on_export_backup)
        backup_btn_row.addWidget(self._btn_export_backup)

        self._btn_import_backup = QPushButton("Import History Backup...", grp_backup)
        self._btn_import_backup.setIcon(
            IconProvider.get_icon("paste", size=14, is_dark=self._is_dark)
        )
        self._btn_import_backup.clicked.connect(self._on_import_backup)
        backup_btn_row.addWidget(self._btn_import_backup)

        backup_btn_row.addStretch()
        grp_backup_layout.addLayout(backup_btn_row)

        layout.addWidget(grp_backup)
        layout.addStretch()
        return widget

    def _create_privacy_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        grp_sensitive = QGroupBox("Sensitive Data Detection (Heuristic)", widget)
        grp_sens_layout = QVBoxLayout(grp_sensitive)
        grp_sens_layout.setSpacing(6)

        self._chk_detect_sensitive = QCheckBox("Detect passwords, API keys, and access tokens", grp_sensitive)
        self._chk_save_sensitive = QCheckBox("Save detected sensitive data (unchecked = do not save)", grp_sensitive)

        grp_sens_layout.addWidget(self._chk_detect_sensitive)
        grp_sens_layout.addWidget(self._chk_save_sensitive)
        layout.addWidget(grp_sensitive)

        # Ignored Applications
        grp_ignored = QGroupBox("Ignored Applications", widget)
        grp_ign_layout = QVBoxLayout(grp_ignored)
        grp_ign_layout.setSpacing(6)

        grp_ign_layout.addWidget(QLabel("Do not save clipboard items copied from:"))
        self._list_ignored = QListWidget(grp_ignored)
        grp_ign_layout.addWidget(self._list_ignored)

        btn_row = QHBoxLayout()
        self._btn_add_app = QPushButton("Add Application...", grp_ignored)
        self._btn_add_app.clicked.connect(self._add_ignored_app)
        btn_row.addWidget(self._btn_add_app)

        self._btn_remove_app = QPushButton("Remove", grp_ignored)
        self._btn_remove_app.clicked.connect(self._remove_ignored_app)
        btn_row.addWidget(self._btn_remove_app)

        btn_row.addStretch()
        grp_ign_layout.addLayout(btn_row)
        layout.addWidget(grp_ignored)

        return widget

    def _create_shortcuts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp = QGroupBox("Global Keyboard Shortcuts", widget)
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(10)

        # Open Popup
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Open Clipboard Popup:"))
        self._edit_shortcut_popup = ShortcutEdit(self._settings.shortcut_popup, grp)
        row1.addWidget(self._edit_shortcut_popup)
        grp_layout.addLayout(row1)

        # Paste Plain Text
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Paste as Plain Text:"))
        self._edit_shortcut_plain = ShortcutEdit(self._settings.shortcut_plain_paste, grp)
        row2.addWidget(self._edit_shortcut_plain)
        grp_layout.addLayout(row2)

        grp_layout.addWidget(
            QLabel("Click on a shortcut box and press the desired key combination.")
        )
        layout.addWidget(grp)
        layout.addStretch()
        return widget

    def _create_appearance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp = QGroupBox("Application Theme", widget)
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(10)

        row = QHBoxLayout()
        row.addWidget(QLabel("Theme:"))
        self._combo_theme = QComboBox(grp)
        self._combo_theme.addItems(THEMES)
        row.addWidget(self._combo_theme)
        grp_layout.addLayout(row)

        grp_layout.addWidget(
            QLabel("System mode automatically adapts to your Windows light or dark color preference.")
        )
        layout.addWidget(grp)
        layout.addStretch()
        return widget

    def _create_advanced_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        grp = QGroupBox("Storage & Maintenance", widget)
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(10)

        btn_open_storage = QPushButton("Open Storage Folder in Explorer", grp)
        btn_open_storage.clicked.connect(self._open_storage_folder)
        grp_layout.addWidget(btn_open_storage)

        btn_clear_history = QPushButton("Clear All Clipboard History (Keep Pinned)", grp)
        btn_clear_history.clicked.connect(self._confirm_clear_history)
        grp_layout.addWidget(btn_clear_history)

        layout.addWidget(grp)
        layout.addStretch()
        return widget

    def _load_values(self) -> None:
        """Populates UI controls with active settings values."""
        s = self._settings

        self._chk_startup.setChecked(StartupService.is_startup_enabled())
        self._chk_tray.setChecked(s.show_tray_icon)

        self._chk_monitor.setChecked(s.monitor_clipboard)
        self._chk_text.setChecked(s.save_text)
        self._chk_html.setChecked(s.save_html)
        self._chk_images.setChecked(s.save_images)
        self._chk_files.setChecked(s.save_files)
        self._chk_urls.setChecked(s.save_urls)

        # Retention combo
        idx_ret = self._combo_retention.findText(s.retention_period)
        if idx_ret >= 0:
            self._combo_retention.setCurrentIndex(idx_ret)

        # Max items combo
        for i in range(self._combo_max_items.count()):
            if self._combo_max_items.itemData(i) == s.max_items:
                self._combo_max_items.setCurrentIndex(i)
                break

        self._chk_deduplicate.setChecked(s.deduplicate)

        self._chk_detect_sensitive.setChecked(s.detect_sensitive)
        self._chk_save_sensitive.setChecked(s.save_sensitive)

        self._list_ignored.clear()
        for app in s.ignored_apps:
            self._list_ignored.addItem(app)

        self._edit_shortcut_popup.setText(s.shortcut_popup)
        self._edit_shortcut_plain.setText(s.shortcut_plain_paste)

        idx_theme = self._combo_theme.findText(s.theme)
        if idx_theme >= 0:
            self._combo_theme.setCurrentIndex(idx_theme)

    def _add_ignored_app(self) -> None:
        """Adds an application executable name to the ignore list."""
        app_name, ok = QInputDialog.getText(
            self, "Add Ignored Application", "Executable name (e.g. keepass.exe):"
        )
        if ok and app_name.strip():
            clean = app_name.strip().lower()
            if not clean.endswith(".exe"):
                clean += ".exe"
            self._list_ignored.addItem(clean)

    def _remove_ignored_app(self) -> None:
        item = self._list_ignored.currentItem()
        if item:
            self._list_ignored.takeItem(self._list_ignored.row(item))

    def _open_storage_folder(self) -> None:
        app_dir = StoragePaths.get_app_dir()
        if app_dir.exists():
            subprocess.run(["explorer", str(app_dir)])

    def _confirm_clear_history(self) -> None:
        res = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear unpinned clipboard history?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if res == QMessageBox.Yes:
            self.clear_history_requested.emit()
            QMessageBox.information(self, "Success", "Clipboard history cleared.")

    def _save_settings(self) -> None:
        """Collects values and saves to database."""
        ignored = [
            self._list_ignored.item(i).text()
            for i in range(self._list_ignored.count())
        ]

        startup_enabled = self._chk_startup.isChecked()
        StartupService.set_startup_enabled(startup_enabled)

        new_settings = AppSettings(
            start_with_windows=startup_enabled,
            show_tray_icon=self._chk_tray.isChecked(),
            monitor_clipboard=self._chk_monitor.isChecked(),
            save_text=self._chk_text.isChecked(),
            save_html=self._chk_html.isChecked(),
            save_images=self._chk_images.isChecked(),
            save_files=self._chk_files.isChecked(),
            save_urls=self._chk_urls.isChecked(),
            retention_period=self._combo_retention.currentText(),
            max_items=self._combo_max_items.currentData(),
            deduplicate=self._chk_deduplicate.isChecked(),
            detect_sensitive=self._chk_detect_sensitive.isChecked(),
            save_sensitive=self._chk_save_sensitive.isChecked(),
            ignored_apps=ignored,
            shortcut_popup=self._edit_shortcut_popup.text(),
            shortcut_plain_paste=self._edit_shortcut_plain.text(),
            theme=self._combo_theme.currentText(),
        )

        self._repo.save_settings(new_settings)
        self._settings = new_settings
        self.settings_updated.emit(new_settings)
        self.accept()

    def _on_export_backup(self) -> None:
        """Handles exporting clipboard history backup archive."""
        if not self._clipboard_repo:
            QMessageBox.warning(self, "Export Error", "Clipboard database repository is unavailable.")
            return

        default_name = f"ClipVault_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Clipboard History Backup",
            default_name,
            "Zip Backup Archives (*.zip);;All Files (*.*)",
        )
        if not file_path:
            return

        success, count, msg = BackupService.export_backup(file_path, self._clipboard_repo)
        if success:
            QMessageBox.information(
                self,
                "Backup Exported Successfully",
                f"Successfully exported {count} clipboard records and media files to:\n\n{file_path}",
            )
        else:
            QMessageBox.warning(self, "Export Failed", msg)

    def _on_import_backup(self) -> None:
        """Handles importing clipboard history from backup archive."""
        if not self._clipboard_repo:
            QMessageBox.warning(self, "Import Error", "Clipboard database repository is unavailable.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Clipboard History Backup",
            "",
            "Zip Backup Archives (*.zip);;All Files (*.*)",
        )
        if not file_path:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Import",
            "Importing this backup will restore historical clipboard items, pinned clips, and media snapshots.\n\nDo you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return

        success, count, msg = BackupService.import_backup(file_path, self._clipboard_repo)
        if success:
            QMessageBox.information(
                self,
                "Backup Restored",
                f"Successfully imported {count} items into your clipboard history.",
            )
            self.history_imported.emit()
        else:
            QMessageBox.critical(self, "Import Failed", msg)
