"""
Clipboard popup picker window for ClipVault.
Provides a fast, compact, keyboard-first clipboard picker dialog with multi-monitor DPI clamping,
smooth keyboard navigation, context menus, and click-outside dismissal.
"""

import os
from pathlib import Path
import subprocess
from typing import List, Optional
from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QCursor, QDesktopServices, QGuiApplication, QKeyEvent, QMouseEvent, QScreen
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.constants import (
    POPUP_HEIGHT,
    POPUP_WIDTH,
    TYPE_FILE,
    TYPE_FILES,
    TYPE_HTML,
    TYPE_IMAGE,
    TYPE_TEXT,
    TYPE_URL,
)
from clipboard.windows_clipboard import get_foreground_window, make_window_topmost, user32
from models.clipboard_item import ClipboardItem
from services.history_service import HistoryService
from services.paste_service import PasteService
from ui.icons import IconProvider
from ui.widgets.category_bar import CategoryBar
from ui.widgets.item_card import ItemCard
from ui.widgets.search_bar import SearchBar
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Windows.Popup")


class ClipboardPopup(QWidget):
    """Compact frameless clipboard picker window."""

    settings_requested = Signal()
    edit_item_requested = Signal(object)  # Emits ClipboardItem

    def __init__(
        self,
        history_service: HistoryService,
        paste_service: PasteService,
        is_dark: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.history_service = history_service
        self.paste_service = paste_service
        self._is_dark = is_dark

        self._items: List[ClipboardItem] = []
        self._item_widgets: List[ItemCard] = []
        self._selected_index = -1
        self._active_category = "All"
        self._active_search_query = ""

        # Timer for outside click dismissal without stealing OS activation
        self._outside_click_timer = QTimer(self)
        self._outside_click_timer.setInterval(40)
        self._outside_click_timer.timeout.connect(self._check_click_outside)

        self._setup_window_flags()
        self._setup_ui()

    def _setup_window_flags(self) -> None:
        """Configures frameless on-top tool window flags without stealing OS activation."""
        self.setObjectName("PopupWindow")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.resize(POPUP_WIDTH, POPUP_HEIGHT)

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 1. Top Header: Search Bar + Settings Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self._search_bar = SearchBar(is_dark=self._is_dark, parent=self)
        self._search_bar.text_changed.connect(self._on_search_text_changed)
        self._search_bar.up_pressed.connect(self._select_previous)
        self._search_bar.down_pressed.connect(self._select_next)
        self._search_bar.page_up_pressed.connect(self._page_up)
        self._search_bar.page_down_pressed.connect(self._page_down)
        self._search_bar.enter_pressed.connect(self._paste_selected_normal)
        self._search_bar.plain_enter_pressed.connect(self._paste_selected_plain)
        self._search_bar.delete_pressed.connect(self._delete_selected)
        self._search_bar.escape_pressed.connect(self.hide_popup)
        header_layout.addWidget(self._search_bar, 1)

        self._btn_clear_all = QPushButton(self)
        self._btn_clear_all.setFixedSize(30, 30)
        self._btn_clear_all.setIcon(
            IconProvider.get_icon("delete", size=15, is_dark=self._is_dark)
        )
        self._btn_clear_all.setToolTip("Clear all unpinned clipboard history")
        self._btn_clear_all.clicked.connect(self._on_clear_all_clicked)
        header_layout.addWidget(self._btn_clear_all)

        self._settings_button = QPushButton(self)
        self._settings_button.setFixedSize(30, 30)
        self._settings_button.setIcon(
            IconProvider.get_icon("settings", size=16, is_dark=self._is_dark)
        )
        self._settings_button.setToolTip("Settings")
        self._settings_button.clicked.connect(self._on_settings_clicked)
        header_layout.addWidget(self._settings_button)

        main_layout.addLayout(header_layout)

        # 2. Category Filter Bar
        self._category_bar = CategoryBar(is_dark=self._is_dark, parent=self)
        self._category_bar.category_changed.connect(self._on_category_changed)
        main_layout.addWidget(self._category_bar)

        # 3. Scrollable List of Item Cards
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._scroll_content = QWidget()
        self._list_layout = QVBoxLayout(self._scroll_content)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(3)

        # Empty State Container (Korvexa App Branding)
        self._empty_container = QWidget(self._scroll_content)
        empty_layout = QVBoxLayout(self._empty_container)
        empty_layout.setContentsMargins(20, 50, 20, 50)
        empty_layout.setSpacing(8)
        empty_layout.setAlignment(Qt.AlignCenter)

        empty_icon = QLabel(self._empty_container)
        empty_icon.setPixmap(IconProvider.get_pixmap("app", size=42, color="#0078d4"))
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)

        empty_title = QLabel("ClipVault", self._empty_container)
        empty_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0078d4;")
        empty_title.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel(
            "Your clipboard history is empty.\nCopy text, screenshots, or files anywhere in Windows.",
            self._empty_container,
        )
        empty_desc.setObjectName("TimeLabel")
        empty_desc.setAlignment(Qt.AlignCenter)
        empty_desc.setWordWrap(True)
        empty_layout.addWidget(empty_desc)

        empty_link = QLabel(
            '<a style="color:#0078d4; text-decoration:none; font-size:11px;" href="https://korvexa.app">korvexa.app</a>',
            self._empty_container,
        )
        empty_link.setAlignment(Qt.AlignCenter)
        empty_link.setOpenExternalLinks(True)
        empty_layout.addWidget(empty_link)

        self._list_layout.addWidget(self._empty_container)
        self._list_layout.addStretch()

        self._scroll_area.setWidget(self._scroll_content)
        main_layout.addWidget(self._scroll_area, 1)

    def set_theme(self, is_dark: bool) -> None:
        """Updates theme-sensitive icons across popup controls."""
        self._is_dark = is_dark
        self._btn_clear_all.setIcon(
            IconProvider.get_icon("delete", size=15, is_dark=is_dark)
        )
        self._settings_button.setIcon(
            IconProvider.get_icon("settings", size=16, is_dark=is_dark)
        )
        self._category_bar.set_theme(is_dark)
        for widget in self._item_widgets:
            widget.set_theme(is_dark)

    def show_at_smart_position(self) -> None:
        """
        Calculates optimal on-screen position near mouse or active window,
        ensuring the popup is 100% clamped within the active monitor's available geometry.
        """
        # 1. Capture target window handle before showing popup
        target_hwnd = get_foreground_window()
        self.paste_service.set_target_window(target_hwnd)

        # 2. Smart non-overlapping position calculation
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        width = self.width()
        height = self.height()

        # Vertical placement: Place BELOW active input field / cursor with 20px clearance
        # If not enough room below, place ABOVE the input field.
        gap = 20
        if cursor_pos.y() + gap + height <= screen_geo.bottom() - 10:
            y = cursor_pos.y() + gap
        elif cursor_pos.y() - gap - height >= screen_geo.top() + 10:
            y = cursor_pos.y() - gap - height
        else:
            y = max(screen_geo.top() + 10, min(cursor_pos.y() + gap, screen_geo.bottom() - height - 10))

        # Horizontal placement: Align near cursor with slight offset, clamped within monitor bounds
        x = cursor_pos.x() - 30
        x = max(screen_geo.left() + 10, min(x, screen_geo.right() - width - 10))

        self.move(x, y)

        # 3. Reload items & display without stealing OS focus from light-dismiss windows
        self._search_bar.clear()
        self.reload_items()
        self.show()
        self.raise_()
        make_window_topmost(int(self.winId()))
        self._outside_click_timer.start()

    def hide_popup(self) -> None:
        """Hides clipboard popup."""
        self._outside_click_timer.stop()
        self.hide()

    def _check_click_outside(self) -> None:
        """Detects mouse clicks outside popup geometry and auto-dismisses."""
        if not self.isVisible():
            self._outside_click_timer.stop()
            return
        # Check if left (0x01) or right (0x02) mouse button is pressed
        if bool(user32.GetAsyncKeyState(0x01) & 0x8000) or bool(user32.GetAsyncKeyState(0x02) & 0x8000):
            cursor_pos = QCursor.pos()
            if not self.geometry().contains(cursor_pos):
                self.hide_popup()

    def reload_items(self) -> None:
        """Queries history service and rebuilds item cards list."""
        self._items = self.history_service.get_items(
            category=self._active_category,
            search_query=self._active_search_query,
            limit=50,
            offset=0,
        )

        # Clear existing cards
        for widget in self._item_widgets:
            self._list_layout.removeWidget(widget)
            widget.deleteLater()
        self._item_widgets.clear()

        if not self._items:
            self._empty_container.show()
            self._selected_index = -1
            return

        self._empty_container.hide()

        # Build cards
        for i, item in enumerate(self._items):
            card = ItemCard(
                item=item,
                is_selected=(i == 0),
                is_dark=self._is_dark,
                parent=self._scroll_content,
            )
            card.item_selected.connect(self._on_card_selected)
            card.item_double_clicked.connect(self._on_card_double_clicked)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.delete_requested.connect(self._on_delete_item)
            card.context_menu_requested.connect(self._show_item_context_menu)

            self._list_layout.insertWidget(i, card)
            self._item_widgets.append(card)

        self._selected_index = 0

    def _select_index(self, index: int) -> None:
        """Selects item at given index and scrolls into view."""
        if not self._item_widgets:
            return

        index = max(0, min(index, len(self._item_widgets) - 1))
        if self._selected_index == index:
            return

        if 0 <= self._selected_index < len(self._item_widgets):
            self._item_widgets[self._selected_index].set_selected(False)

        self._selected_index = index
        selected_card = self._item_widgets[index]
        selected_card.set_selected(True)
        self._scroll_area.ensureWidgetVisible(selected_card)

    def _select_previous(self) -> None:
        self._select_index(self._selected_index - 1)

    def _select_next(self) -> None:
        self._select_index(self._selected_index + 1)

    def _page_up(self) -> None:
        self._select_index(self._selected_index - 5)

    def _page_down(self) -> None:
        self._select_index(self._selected_index + 5)

    def _get_selected_item(self) -> Optional[ClipboardItem]:
        if 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    def _paste_selected_normal(self) -> None:
        item = self._get_selected_item()
        if item:
            self.hide_popup()
            self.paste_service.execute_paste(item, as_plain_text=False)

    def _paste_selected_plain(self) -> None:
        item = self._get_selected_item()
        if item:
            self.hide_popup()
            self.paste_service.execute_paste(item, as_plain_text=True)

    def _delete_selected(self) -> None:
        item = self._get_selected_item()
        if item:
            self._on_delete_item(item)

    def _on_card_selected(self, item: ClipboardItem) -> None:
        """Single-click immediately pastes item into active application."""
        self.hide_popup()
        self.paste_service.execute_paste(item, as_plain_text=False)

    def _on_card_double_clicked(self, item: ClipboardItem) -> None:
        self.hide_popup()
        self.paste_service.execute_paste(item, as_plain_text=False)

    def _on_pin_toggled(self, item: ClipboardItem) -> None:
        new_val = self.history_service.toggle_pin(item.id)
        item.is_pinned = 1 if new_val else 0
        self.reload_items()

    def _on_delete_item(self, item: ClipboardItem) -> None:
        self.history_service.delete_item(item.id)
        self.reload_items()

    def _on_search_text_changed(self, text: str) -> None:
        self._active_search_query = text
        self.reload_items()

    def _on_category_changed(self, category: str) -> None:
        self._active_category = category
        self.reload_items()

    def _on_clear_all_clicked(self) -> None:
        """Prompts confirmation dialog and clears unpinned clipboard history."""
        reply = QMessageBox.question(
            self,
            "Clear Clipboard History",
            "Are you sure you want to clear all unpinned items from clipboard history?\n\nPinned clips will be kept.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.history_service.clear_history(keep_pinned=True)
            self.reload_items()

    def _on_settings_clicked(self) -> None:
        self.hide_popup()
        self.settings_requested.emit()

    def _show_item_context_menu(self, item: ClipboardItem, global_pos: QPoint) -> None:
        """Displays rich format-specific context menu."""
        menu = QMenu(self)

        # 1. Primary Paste
        act_paste = menu.addAction(
            IconProvider.get_icon("paste", size=14, is_dark=self._is_dark), "Paste"
        )
        act_paste.triggered.connect(lambda: self._trigger_paste(item, as_plain_text=False))

        # 2. Paste as Plain Text (if HTML or URL or Text)
        if item.type in (TYPE_HTML, TYPE_URL, TYPE_TEXT):
            act_plain = menu.addAction(
                IconProvider.get_icon("text", size=14, is_dark=self._is_dark),
                "Paste as Plain Text",
            )
            act_plain.triggered.connect(lambda: self._trigger_paste(item, as_plain_text=True))

        menu.addSeparator()

        # Format-specific actions
        if item.type == TYPE_IMAGE and item.image_path:
            act_open = menu.addAction(
                IconProvider.get_icon("image", size=14, is_dark=self._is_dark), "Open Image"
            )
            act_open.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(item.image_path)))

            act_save_as = menu.addAction(
                IconProvider.get_icon("copy", size=14, is_dark=self._is_dark), "Save Image As..."
            )
            act_save_as.triggered.connect(lambda: self._save_image_as(item.image_path))

        elif item.type in (TYPE_FILE, TYPE_FILES) and item.files:
            act_open = menu.addAction(
                IconProvider.get_icon("file", size=14, is_dark=self._is_dark), "Open File"
            )
            act_open.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(item.files[0].path)))

            act_open_dir = menu.addAction(
                IconProvider.get_icon("folder", size=14, is_dark=self._is_dark), "Open Containing Folder"
            )
            act_open_dir.triggered.connect(lambda: self._open_containing_folder(item.files[0].path))

        elif item.type == TYPE_URL and item.plain_text:
            act_open_browser = menu.addAction(
                IconProvider.get_icon("url", size=14, is_dark=self._is_dark), "Open in Browser"
            )
            act_open_browser.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(item.plain_text)))

        elif item.type in (TYPE_TEXT, TYPE_HTML):
            act_edit = menu.addAction(
                IconProvider.get_icon("edit", size=14, is_dark=self._is_dark), "Edit Text..."
            )
            act_edit.triggered.connect(lambda: self.edit_item_requested.emit(item))

        menu.addSeparator()

        # Pin / Unpin
        pin_title = "Unpin" if item.is_pinned else "Pin"
        act_pin = menu.addAction(
            IconProvider.get_icon("pin", size=14, is_dark=self._is_dark), pin_title
        )
        act_pin.triggered.connect(lambda: self._on_pin_toggled(item))

        # Delete
        act_del = menu.addAction(
            IconProvider.get_icon("delete", size=14, is_dark=self._is_dark), "Delete"
        )
        act_del.triggered.connect(lambda: self._on_delete_item(item))

        menu.exec(global_pos)

    def _trigger_paste(self, item: ClipboardItem, as_plain_text: bool = False) -> None:
        self.hide_popup()
        self.paste_service.execute_paste(item, as_plain_text=as_plain_text)

    def _save_image_as(self, source_path: str) -> None:
        dest_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image As", "clipboard_image.png", "PNG Image (*.png);;All Files (*.*)"
        )
        if dest_path and os.path.exists(source_path):
            import shutil
            shutil.copyfile(source_path, dest_path)

    def _open_containing_folder(self, file_path: str) -> None:
        if os.path.exists(file_path):
            subprocess.run(["explorer", "/select,", os.path.abspath(file_path)])

    def changeEvent(self, event: QEvent) -> None:
        """Auto-close popup when user clicks outside (window loses activation)."""
        if event.type() == QEvent.ActivationChange and not self.isActiveWindow():
            self.hide_popup()
        super().changeEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Escape:
            self.hide_popup()
            event.accept()
        elif key == Qt.Key_P and (modifiers & Qt.ControlModifier):
            item = self._get_selected_item()
            if item:
                self._on_pin_toggled(item)
            event.accept()
        elif key == Qt.Key_F and (modifiers & Qt.ControlModifier):
            self._search_bar.set_focus()
            event.accept()
        else:
            super().keyPressEvent(event)
