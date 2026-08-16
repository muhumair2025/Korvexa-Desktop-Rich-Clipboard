"""
Clipboard writer for ClipVault.
Restores rich formats, HTML, images, and native CF_HDROP file buffers to the Windows clipboard.
"""

from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QByteArray, QMimeData, QUrl
from PySide6.QtGui import QClipboard, QImage

from models.clipboard_item import ClipboardItem
from utils.logging_config import get_logger
from .windows_clipboard import set_native_hdrop_clipboard

logger = get_logger("ClipVault.Clipboard.Writer")


class ClipboardWriter:
    """Restores ClipboardItem representations onto the active Windows clipboard."""

    @classmethod
    def write_item(
        cls,
        clipboard: QClipboard,
        item: ClipboardItem,
        as_plain_text: bool = False,
    ) -> bool:
        """
        Writes the given ClipboardItem to the Windows clipboard.
        If as_plain_text is True, forces plain text mode regardless of original type.
        """
        try:
            if as_plain_text or item.type == "text":
                return cls.write_plain_text(clipboard, item.plain_text or "")

            if item.type == "html":
                return cls.write_html(clipboard, item.html_content or "", item.plain_text or "")

            if item.type == "image":
                return cls.write_image(clipboard, item.image_path)

            if item.type in ("file", "files"):
                file_paths = [f.path for f in item.files if hasattr(f, "path")]
                return cls.write_files(clipboard, file_paths)

            if item.type == "url":
                return cls.write_plain_text(clipboard, item.plain_text or "")

            # Fallback to plain text
            return cls.write_plain_text(clipboard, item.plain_text or "")

        except Exception as e:
            logger.error(f"Failed to write item to clipboard: {e}", exc_info=True)
            return False

    @classmethod
    def write_plain_text(cls, clipboard: QClipboard, text: str) -> bool:
        """Sets plain text on the clipboard."""
        mime_data = QMimeData()
        mime_data.setText(text)
        clipboard.setMimeData(mime_data)
        return True

    @classmethod
    def write_html(cls, clipboard: QClipboard, html: str, plain_text: str = "") -> bool:
        """Sets both HTML and fallback plain text on the clipboard."""
        mime_data = QMimeData()
        if html:
            mime_data.setHtml(html)
        if plain_text:
            mime_data.setText(plain_text)
        elif html:
            # Fallback text if plain text is empty
            mime_data.setText(html)
        clipboard.setMimeData(mime_data)
        return True

    @classmethod
    def write_image(cls, clipboard: QClipboard, image_path: Optional[str]) -> bool:
        """Loads image file from disk and sets it onto the clipboard."""
        if not image_path:
            return False

        path = Path(image_path)
        if not path.exists():
            logger.warning(f"Image file does not exist on disk: {image_path}")
            return False

        qimage = QImage(str(path))
        if qimage.isNull():
            logger.warning(f"Could not decode image from file: {image_path}")
            return False

        clipboard.setImage(qimage)
        return True

    @classmethod
    def write_files(cls, clipboard: QClipboard, file_paths: List[str]) -> bool:
        """
        Restores files to clipboard using both QMimeData (URLs) and native Win32 CF_HDROP.
        """
        if not file_paths:
            return False

        # First set QMimeData URLs
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(p) for p in file_paths]
        mime_data.setUrls(urls)
        clipboard.setMimeData(mime_data)

        # Also set native Windows CF_HDROP for 100% Explorer compatibility
        try:
            set_native_hdrop_clipboard(file_paths)
        except Exception as e:
            logger.warning(f"Native CF_HDROP write fallback: {e}")

        return True
