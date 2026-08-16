"""
Text editor modal dialog for modifying saved clipboard text snippets.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.clipboard_item import ClipboardItem


class TextEditorDialog(QDialog):
    """Simple clean native dialog for editing a clipboard item's text."""

    text_saved = Signal(int, str)  # item_id, new_text

    def __init__(self, item: ClipboardItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.item = item

        self.setWindowTitle("Edit Clipboard Item")
        self.resize(460, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Edit text content:"))

        self._editor = QPlainTextEdit(self)
        self._editor.setPlainText(self.item.plain_text or "")
        layout.addWidget(self._editor, 1)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save", self)
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _on_save(self) -> None:
        new_text = self._editor.toPlainText()
        if self.item.id:
            self.text_saved.emit(self.item.id, new_text)
        self.accept()
