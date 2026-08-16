"""
Category filter bar for ClipVault.
Provides clean native filter tabs for All, Pinned, Text, Images, Files, Links.
"""

from typing import List, Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ui.icons import IconProvider


class CategoryBar(QWidget):
    """Horizontal filter category bar with native buttons and vector icons."""

    category_changed = Signal(str)

    CATEGORIES = [
        ("All", "copy"),
        ("Pinned", "pin"),
        ("Text", "text"),
        ("Images", "image"),
        ("Files", "file"),
        ("Links", "url"),
    ]

    def __init__(self, is_dark: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._is_dark = is_dark
        self._buttons: List[QPushButton] = []
        self._active_category = "All"

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for name, icon_name in self.CATEGORIES:
            btn = QPushButton(name)
            btn.setIcon(IconProvider.get_icon(icon_name, size=14, is_dark=self._is_dark))
            btn.setCheckable(True)
            btn.setFocusPolicy(self.focusPolicy())
            btn.clicked.connect(lambda checked=False, cat=name: self._on_button_clicked(cat))

            if name == "All":
                btn.setChecked(True)

            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

    def _on_button_clicked(self, category: str) -> None:
        self._active_category = category
        for btn in self._buttons:
            btn.setChecked(btn.text() == category)
        self.category_changed.emit(category)

    def set_theme(self, is_dark: bool) -> None:
        """Updates icons when theme switches."""
        self._is_dark = is_dark
        for btn, (name, icon_name) in zip(self._buttons, self.CATEGORIES):
            btn.setIcon(IconProvider.get_icon(icon_name, size=14, is_dark=is_dark))

    def set_active_category(self, category: str) -> None:
        """Programmatically sets the active category filter."""
        self._active_category = category
        for btn in self._buttons:
            btn.setChecked(btn.text() == category)
        self.category_changed.emit(category)
