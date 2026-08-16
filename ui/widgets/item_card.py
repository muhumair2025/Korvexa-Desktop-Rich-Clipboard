"""
ItemCard widget for displaying clipboard records matching native Windows clipboard (Win+V) flat card UI.
Provides multi-line text wrapping (2-3 lines), generous image preview thumbnails, and subtle action controls.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QContextMenuEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.constants import TYPE_FILE, TYPE_FILES, TYPE_HTML, TYPE_IMAGE, TYPE_TEXT, TYPE_URL
from models.clipboard_item import ClipboardItem
from ui.icons import IconProvider


def format_relative_time(iso_timestamp: str) -> str:
    """Formats an ISO timestamp into a human-friendly relative time string."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        delta = datetime.now() - dt
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "Just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h"
        days = hours // 24
        if days == 1:
            return "Yesterday"
        if days < 7:
            return f"{days}d"
        return dt.strftime("%b %d")
    except Exception:
        return ""


class ItemCard(QFrame):
    """Native Windows-style flat clipboard card."""

    item_selected = Signal(object)
    item_double_clicked = Signal(object)
    pin_toggled = Signal(object)
    delete_requested = Signal(object)
    context_menu_requested = Signal(object, QPoint)

    def __init__(
        self,
        item: ClipboardItem,
        is_selected: bool = False,
        is_dark: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.item = item
        self._is_selected = is_selected
        self._is_dark = is_dark

        self.setObjectName("ItemCard")
        self.setProperty("selected", "true" if is_selected else "false")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Dynamic card height: 116px for images, 68px for text/files/links
        if self.item.type == TYPE_IMAGE:
            self.setFixedHeight(116)
        else:
            self.setFixedHeight(68)

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 6, 6, 6)
        main_layout.setSpacing(8)

        # 1. Main Content Area (Image or Multi-line Text)
        if self.item.type == TYPE_IMAGE:
            self._content_widget = self._create_image_content()
        else:
            self._content_widget = self._create_text_content()

        self._content_widget.setMinimumWidth(0)
        self._content_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        main_layout.addWidget(self._content_widget, 1)

        # 2. Right Side: Top Action Buttons (Pin + More Options Menu) with guaranteed fixed width
        actions_container = QWidget(self)
        actions_container.setFixedWidth(24)
        actions_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(2)
        actions_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)

        # More Options (...) Button
        self._more_button = QPushButton(actions_container)
        self._more_button.setFixedSize(22, 22)
        self._more_button.setFlat(True)
        self._more_button.setObjectName("CardActionButton")
        self._more_button.setToolTip("More Options")
        self._more_button.setIcon(
            IconProvider.get_icon("dots", size=14, is_dark=self._is_dark)
        )
        self._more_button.clicked.connect(self._on_more_clicked)
        actions_layout.addWidget(self._more_button)

        # Pin Button
        self._pin_button = QPushButton(actions_container)
        self._pin_button.setFixedSize(22, 22)
        self._pin_button.setFlat(True)
        self._pin_button.setObjectName("CardActionButton")
        self._pin_button.setToolTip("Toggle Pin (Ctrl+P)")
        self._update_pin_icon()
        self._pin_button.clicked.connect(self._on_pin_clicked)
        actions_layout.addWidget(self._pin_button)

        actions_layout.addStretch()
        main_layout.addWidget(actions_container, 0, Qt.AlignRight | Qt.AlignTop)

    def _create_text_content(self) -> QWidget:
        """Creates clean 2-3 line wrapped text preview with smart breaks for long URLs & strings."""
        container = QWidget(self)
        container.setMinimumWidth(0)
        container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        raw_text = (self.item.plain_text or self.item.title or "Empty clipboard item").strip()

        # Add soft break hints for unbroken strings (URLs, GUIDs, hashes) so word wrap works cleanly
        def add_soft_breaks(text: str, max_chunk: int = 24) -> str:
            words = text.split(" ")
            processed_words = []
            for word in words:
                if len(word) > max_chunk:
                    sub = ""
                    for ch in word:
                        sub += ch
                        if ch in ("/", "\\", "?", "&", "=", ".", "-", "_", ":", "@", "%") or len(sub) >= max_chunk:
                            processed_words.append(sub)
                            sub = ""
                    if sub:
                        processed_words.append(sub)
                else:
                    processed_words.append(word)
            return " ".join(processed_words)

        processed_text = add_soft_breaks(raw_text)
        lines = [line.strip() for line in processed_text.splitlines() if line.strip()]
        display_snippet = " \n".join(lines[:3]) if lines else processed_text

        if len(display_snippet) > 160:
            display_snippet = display_snippet[:160] + "..."

        self._text_label = QLabel(display_snippet, container)
        self._text_label.setObjectName("CardTextLabel")
        self._text_label.setWordWrap(True)
        self._text_label.setMinimumWidth(0)
        self._text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._text_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)

        layout.addWidget(self._text_label)
        return container

    def _create_image_content(self) -> QWidget:
        """Creates generous image preview thumbnail directly on card without extra box."""
        container = QWidget(self)
        container.setMinimumWidth(0)
        container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._image_preview = QLabel(container)
        self._image_preview.setObjectName("ImageThumbnail")
        self._image_preview.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._image_preview.setMinimumWidth(0)
        self._image_preview.setMaximumWidth(240)

        self._load_thumbnail()
        layout.addWidget(self._image_preview)
        layout.addStretch()
        return container

    def _load_thumbnail(self) -> None:
        """Loads and scales thumbnail image smoothly directly onto card with safe bounds."""
        if hasattr(self, "_image_preview"):
            img_src = None
            if self.item.thumbnail_path and Path(self.item.thumbnail_path).exists():
                img_src = self.item.thumbnail_path
            elif self.item.image_path and Path(self.item.image_path).exists():
                img_src = self.item.image_path

            if img_src:
                orig = QPixmap(img_src)
                if not orig.isNull():
                    scaled = orig.scaled(
                        220, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self._image_preview.setPixmap(scaled)
                    self._image_preview.setFixedSize(scaled.size())
                    return

            pix = IconProvider.get_pixmap("image", size=36, is_dark=self._is_dark)
            self._image_preview.setPixmap(pix)
            self._image_preview.setFixedSize(36, 36)

    def _update_pin_icon(self) -> None:
        """Updates pin button state."""
        if self.item.is_pinned:
            icon = IconProvider.get_icon("pin_filled", size=14, color="#0078d4")
        else:
            icon = IconProvider.get_icon("pin", size=14, is_dark=self._is_dark)
        self._pin_button.setIcon(icon)

    def set_selected(self, selected: bool) -> None:
        """Updates visual selection state."""
        if self._is_selected != selected:
            self._is_selected = selected
            self.setProperty("selected", "true" if selected else "false")
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()

    def set_theme(self, is_dark: bool) -> None:
        """Updates theme-sensitive icons and colors."""
        self._is_dark = is_dark
        self._more_button.setIcon(
            IconProvider.get_icon("dots", size=14, is_dark=is_dark)
        )
        self._update_pin_icon()
        self._load_thumbnail()

    def _on_pin_clicked(self) -> None:
        self.pin_toggled.emit(self.item)

    def _on_more_clicked(self) -> None:
        # Show context menu near the more button
        btn_pos = self._more_button.mapToGlobal(QPoint(0, self._more_button.height()))
        self.context_menu_requested.emit(self.item, btn_pos)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.item_selected.emit(self.item)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.item_double_clicked.emit(self.item)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.context_menu_requested.emit(self.item, event.globalPos())
        event.accept()
