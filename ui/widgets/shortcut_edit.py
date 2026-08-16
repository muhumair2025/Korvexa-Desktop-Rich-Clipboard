"""
Shortcut editor key recorder widget for ClipVault settings.
Allows interactive capture of keyboard shortcuts like Ctrl+Shift+V.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit, QWidget

from hotkeys.global_hotkey import VK_MAP


class ShortcutEdit(QLineEdit):
    """Interactive key sequence recorder for hotkey configuration."""

    shortcut_changed = Signal(str)

    def __init__(self, current_shortcut: str = "Ctrl+Shift+V", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setText(current_shortcut)
        self.setReadOnly(True)
        self.setPlaceholderText("Press shortcut keys...")
        self.setAlignment(Qt.AlignCenter)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        # Ignore standalone modifier keys
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        # Escape clears or resets
        if key == Qt.Key_Escape:
            self.clearFocus()
            return

        parts = []
        if modifiers & Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.MetaModifier:
            parts.append("Win")

        # Key text resolution
        key_str = None
        for name, code in VK_MAP.items():
            if key == getattr(Qt, f"Key_{name}", None) or key == code:
                key_str = name
                break

        if not key_str:
            key_text = event.text().upper()
            if key_text and key_text.isprintable():
                key_str = key_text
            else:
                # Direct key code fallback
                if Qt.Key_A <= key <= Qt.Key_Z:
                    key_str = chr(key)
                elif Qt.Key_0 <= key <= Qt.Key_9:
                    key_str = chr(key)
                elif Qt.Key_F1 <= key <= Qt.Key_F12:
                    key_str = f"F{key - Qt.Key_F1 + 1}"

        if key_str:
            parts.append(key_str)
            combo = "+".join(parts)
            self.setText(combo)
            self.shortcut_changed.emit(combo)
            self.clearFocus()
        else:
            super().keyPressEvent(event)
