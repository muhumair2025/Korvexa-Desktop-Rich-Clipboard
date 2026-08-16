"""
Keyboard-friendly search bar widget for ClipVault popup.
Includes clear button, search icon, and key event forwarding for seamless list navigation.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QToolButton,
    QWidget,
)

from ui.icons import IconProvider


class SearchBar(QWidget):
    """Custom search bar with clear action and keyboard navigation forwarding."""

    text_changed = Signal(str)
    up_pressed = Signal()
    down_pressed = Signal()
    page_up_pressed = Signal()
    page_down_pressed = Signal()
    enter_pressed = Signal()
    plain_enter_pressed = Signal()  # Shift+Enter or Ctrl+Enter
    delete_pressed = Signal()
    escape_pressed = Signal()

    def __init__(self, is_dark: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._is_dark = is_dark
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._line_edit = QLineEdit(self)
        self._line_edit.setPlaceholderText("Search clipboard history...")
        self._line_edit.setClearButtonEnabled(True)
        self._line_edit.textChanged.connect(self.text_changed.emit)

        # Install custom key event filter on line edit
        self._line_edit.keyPressEvent = self._handle_key_press

        layout.addWidget(self._line_edit)

    def _handle_key_press(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Up:
            self.up_pressed.emit()
            event.accept()
            return
        elif key == Qt.Key_Down:
            self.down_pressed.emit()
            event.accept()
            return
        elif key == Qt.Key_PageUp:
            self.page_up_pressed.emit()
            event.accept()
            return
        elif key == Qt.Key_PageDown:
            self.page_down_pressed.emit()
            event.accept()
            return
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if modifiers & (Qt.ShiftModifier | Qt.ControlModifier):
                self.plain_enter_pressed.emit()
            else:
                self.enter_pressed.emit()
            event.accept()
            return
        elif key == Qt.Key_Delete and (modifiers & Qt.ShiftModifier):
            self.delete_pressed.emit()
            event.accept()
            return
        elif key == Qt.Key_Escape:
            self.escape_pressed.emit()
            event.accept()
            return

        # Default line edit behavior for normal typing
        QLineEdit.keyPressEvent(self._line_edit, event)

    def text(self) -> str:
        """Returns current search text."""
        return self._line_edit.text()

    def clear(self) -> None:
        """Clears search input."""
        self._line_edit.clear()

    def set_focus(self) -> None:
        """Focuses and selects all text in search bar."""
        self._line_edit.setFocus()
        self._line_edit.selectAll()
