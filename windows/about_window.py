"""
About window for ClipVault.
Displays version, organization details, developer credits, website & support links,
and a quick keyboard shortcuts reference.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import (
    APP_AUTHOR,
    APP_DISPLAY_NAME,
    APP_ORGANIZATION,
    APP_SUPPORT_EMAIL,
    APP_VERSION,
    APP_WEBSITE,
)
from ui.icons import IconProvider


class AboutWindow(QDialog):
    """About ClipVault information dialog."""

    def __init__(self, is_dark: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._is_dark = is_dark

        self.setWindowTitle("About ClipVault")
        self.setFixedSize(480, 430)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header with app icon and title
        header = QHBoxLayout()
        header.setSpacing(14)

        icon_label = QLabel(self)
        icon_label.setPixmap(
            IconProvider.get_pixmap("app", size=48, color="#0078d4")
        )
        header.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel(APP_DISPLAY_NAME, self)
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        title_layout.addWidget(title)

        version = QLabel(f"Version {APP_VERSION} (64-bit)", self)
        version.setObjectName("TimeLabel")
        title_layout.addWidget(version)

        header.addLayout(title_layout)
        header.addStretch()
        layout.addLayout(header)

        # Organization, Developer & Support Info Frame
        info_frame = QFrame(self)
        info_frame.setObjectName("ItemCard")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(5)

        lbl_dev = QLabel(f"<b>Developer:</b> {APP_AUTHOR}", info_frame)
        lbl_org = QLabel(f"<b>Organization:</b> {APP_ORGANIZATION}", info_frame)
        
        lbl_web = QLabel(
            f'<b>Website:</b> <a style="color:#0078d4; text-decoration:none;" href="{APP_WEBSITE}">{APP_WEBSITE}</a>',
            info_frame,
        )
        lbl_web.setOpenExternalLinks(True)

        lbl_email = QLabel(
            f'<b>Support:</b> <a style="color:#0078d4; text-decoration:none;" href="mailto:{APP_SUPPORT_EMAIL}">{APP_SUPPORT_EMAIL}</a>',
            info_frame,
        )
        lbl_email.setOpenExternalLinks(True)

        info_layout.addWidget(lbl_dev)
        info_layout.addWidget(lbl_org)
        info_layout.addWidget(lbl_web)
        info_layout.addWidget(lbl_email)
        layout.addWidget(info_frame)

        # Shortcuts Guide Frame
        guide_frame = QFrame(self)
        guide_frame.setObjectName("ItemCard")
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setContentsMargins(12, 10, 12, 10)
        guide_layout.setSpacing(4)

        guide_layout.addWidget(QLabel("<b>Keyboard Navigation & Shortcuts:</b>"))
        guide_layout.addWidget(QLabel("• <b>Ctrl + Shift + V</b> — Open Clipboard Picker"))
        guide_layout.addWidget(QLabel("• <b>Single Click / Enter</b> — Paste Selected Item"))
        guide_layout.addWidget(QLabel("• <b>Shift + Enter</b> — Paste as Plain Text"))
        guide_layout.addWidget(QLabel("• <b>Ctrl + P</b> — Toggle Pin Item"))
        guide_layout.addWidget(QLabel("• <b>Delete</b> — Delete Item from History"))
        guide_layout.addWidget(QLabel("• <b>Esc</b> — Close Picker Window"))

        layout.addWidget(guide_frame)
        layout.addStretch()

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Close", self)
        btn_close.setObjectName("PrimaryButton")
        btn_close.setFixedWidth(90)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
