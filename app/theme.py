"""
Theme manager and native stylesheets for ClipVault.
Supports System (auto-detect), Light, and Dark modes with clean, minimal native Windows GUI aesthetics.
"""

import sys
import winreg
from typing import Optional
import darkdetect
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app.constants import THEME_DARK, THEME_LIGHT, THEME_SYSTEM
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Theme")


def is_windows_dark_mode() -> bool:
    """Detects if Windows system theme is set to Dark Mode."""
    try:
        detected = darkdetect.isDark()
        if detected is not None:
            return bool(detected)
    except Exception:
        pass

    # Registry fallback
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except Exception:
        return False


# Minimal native Light Theme Stylesheet
LIGHT_STYLESHEET = """
/* ClipVault Native Light Theme */
QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    color: #1f1f1f;
    background-color: #f9f9f9;
}

QDialog, QMainWindow, #PopupWindow {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
}

/* Header & Search */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
    color: #111111;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 1px solid #0078d4;
    background-color: #ffffff;
}

/* Push Buttons */
QPushButton {
    background-color: #f3f3f3;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    padding: 5px 12px;
    color: #1f1f1f;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e8e8e8;
    border-color: #c0c0c0;
}

QPushButton:pressed {
    background-color: #dedede;
    border-color: #a0a0a0;
}

QPushButton:disabled {
    background-color: #f8f8f8;
    color: #a0a0a0;
    border-color: #e5e5e5;
}

QPushButton#PrimaryButton {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #005a9e;
}

QPushButton#PrimaryButton:hover {
    background-color: #106ebe;
}

QPushButton#PrimaryButton:pressed {
    background-color: #005a9e;
}

/* Category Filter Bar */
QTabBar::tab {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 6px 12px;
    color: #555555;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #0078d4;
    border-bottom: 2px solid #0078d4;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    color: #111111;
    background-color: #f0f0f0;
}

/* Scroll Area & Lists */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background: #f0f0f0;
    width: 10px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #c8c8c8;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #a8a8a8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Item Cards - Windows Native Flat Style */
#ItemCard {
    background-color: #ffffff;
    border: 1px solid #e2e2e2;
    border-radius: 4px;
    padding: 6px 10px;
}

#ItemCard:hover {
    border: 1px solid #808080;
    background-color: #ffffff;
}

#ItemCard[selected="true"] {
    background-color: #ffffff;
    border: 2px solid #0078d4;
}

QLabel#CardTextLabel {
    color: #1a1a1a;
    font-size: 13px;
    font-family: "Segoe UI", Arial, sans-serif;
}

QPushButton#CardActionButton {
    background-color: transparent;
    border: none;
    border-radius: 3px;
    padding: 2px;
}

QPushButton#CardActionButton:hover {
    background-color: #e5e5e5;
}

QLabel#ImageThumbnail {
    background-color: transparent;
    border: none;
    padding: 0px;
}

QLabel#TimeLabel {
    color: #777777;
    font-size: 11px;
}

QLabel#TitleLabel {
    color: #111111;
    font-size: 12px;
    font-weight: 500;
}

/* Menus & Tooltips */
QMenu {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    padding: 4px;
    border-radius: 4px;
}

QMenu::item {
    padding: 5px 24px 5px 10px;
    border-radius: 3px;
    color: #1f1f1f;
}

QMenu::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #e5e5e5;
    margin: 4px 6px;
}

QToolTip {
    background-color: #ffffff;
    color: #111111;
    border: 1px solid #cccccc;
    padding: 4px 8px;
    border-radius: 3px;
}

/* Settings Tabs */
QTabWidget::pane {
    border: 1px solid #dcdcdc;
    background-color: #ffffff;
    border-radius: 4px;
    top: -1px;
}

QGroupBox {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #333333;
}

QCheckBox {
    spacing: 8px;
    color: #222222;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px 8px;
    color: #111111;
    min-height: 24px;
}

QComboBox:focus {
    border: 1px solid #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}
"""


# Minimal native Dark Theme Stylesheet
DARK_STYLESHEET = """
/* ClipVault Native Dark Theme */
QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    color: #e6e6e6;
    background-color: #202020;
}

QDialog, QMainWindow, #PopupWindow {
    background-color: #1e1e1e;
    border: 1px solid #3c3c3c;
}

/* Header & Search */
QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
    color: #ffffff;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 1px solid #4cc2ff;
    background-color: #2d2d2d;
}

/* Push Buttons */
QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 5px 12px;
    color: #e6e6e6;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #383838;
    border-color: #555555;
}

QPushButton:pressed {
    background-color: #262626;
    border-color: #333333;
}

QPushButton:disabled {
    background-color: #222222;
    color: #666666;
    border-color: #333333;
}

QPushButton#PrimaryButton {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #106ebe;
}

QPushButton#PrimaryButton:hover {
    background-color: #106ebe;
}

QPushButton#PrimaryButton:pressed {
    background-color: #005a9e;
}

/* Category Filter Bar */
QTabBar::tab {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 6px 12px;
    color: #aaaaaa;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #4cc2ff;
    border-bottom: 2px solid #4cc2ff;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    color: #ffffff;
    background-color: #2a2a2a;
}

/* Scroll Area & Lists */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background: #252525;
    width: 10px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #444444;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Item Cards - Windows Native Flat Style */
#ItemCard {
    background-color: #2b2b2b;
    border: 1px solid #383838;
    border-radius: 4px;
    padding: 6px 10px;
}

#ItemCard:hover {
    border: 1px solid #666666;
    background-color: #2b2b2b;
}

#ItemCard[selected="true"] {
    background-color: #2b2b2b;
    border: 2px solid #0078d4;
}

QLabel#CardTextLabel {
    color: #f0f0f0;
    font-size: 13px;
    font-family: "Segoe UI", Arial, sans-serif;
}

QPushButton#CardActionButton {
    background-color: transparent;
    border: none;
    border-radius: 3px;
    padding: 2px;
}

QPushButton#CardActionButton:hover {
    background-color: #3d3d3d;
}

QLabel#ImageThumbnail {
    background-color: transparent;
    border: none;
    padding: 0px;
}

QLabel#TimeLabel {
    color: #888888;
    font-size: 11px;
}

QLabel#TitleLabel {
    color: #e6e6e6;
    font-size: 12px;
    font-weight: 500;
}

/* Menus & Tooltips */
QMenu {
    background-color: #252525;
    border: 1px solid #3c3c3c;
    padding: 4px;
    border-radius: 4px;
}

QMenu::item {
    padding: 5px 24px 5px 10px;
    border-radius: 3px;
    color: #e6e6e6;
}

QMenu::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #383838;
    margin: 4px 6px;
}

QToolTip {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #444444;
    padding: 4px 8px;
    border-radius: 3px;
}

/* Settings Tabs */
QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #222222;
    border-radius: 4px;
    top: -1px;
}

QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #cccccc;
}

QCheckBox {
    spacing: 8px;
    color: #dddddd;
}

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px 8px;
    color: #ffffff;
    min-height: 24px;
}

QComboBox:focus {
    border: 1px solid #4cc2ff;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}
"""


class ThemeManager(QObject):
    """Manages dynamic stylesheet switching and system theme tracking."""

    theme_changed = Signal(str)

    _instance: Optional["ThemeManager"] = None

    def __init__(self, current_preference: str = THEME_SYSTEM):
        super().__init__()
        self._current_preference = current_preference
        self._is_dark = False

    @classmethod
    def get_instance(cls, preference: str = THEME_SYSTEM) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls(preference)
        return cls._instance

    @property
    def is_dark(self) -> bool:
        """Returns True if the active applied theme is Dark."""
        return self._is_dark

    def get_effective_theme(self) -> str:
        """Calculates active theme (Light or Dark) based on preference and Windows setting."""
        if self._current_preference == THEME_DARK:
            return THEME_DARK
        elif self._current_preference == THEME_LIGHT:
            return THEME_LIGHT
        else:
            return THEME_DARK if is_windows_dark_mode() else THEME_LIGHT

    def apply_theme(self, app: QApplication, preference: Optional[str] = None) -> None:
        """Applies stylesheet and palette to QApplication."""
        if preference:
            self._current_preference = preference

        effective = self.get_effective_theme()
        self._is_dark = (effective == THEME_DARK)

        if self._is_dark:
            app.setStyleSheet(DARK_STYLESHEET)
            logger.info("Applied Dark Theme stylesheet.")
        else:
            app.setStyleSheet(LIGHT_STYLESHEET)
            logger.info("Applied Light Theme stylesheet.")

        self.theme_changed.emit(effective)
