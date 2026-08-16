"""
Clipboard reader for ClipVault.
Inspects QMimeData and Windows native clipboard formats to construct a ClipboardItem.
"""

from typing import List, Optional, Tuple
from PySide6.QtCore import QMimeData
from PySide6.QtGui import QClipboard, QImage

from models.clipboard_file import ClipboardFile
from models.clipboard_item import ClipboardItem
from utils.logging_config import get_logger
from .mime_parser import (
    determine_primary_type,
    extract_file_paths_from_mime,
    extract_text_from_html,
    is_valid_url,
)
from .windows_clipboard import get_foreground_window, get_process_name_for_hwnd

logger = get_logger("ClipVault.Clipboard.Reader")


class ClipboardReader:
    """Reads current clipboard content and constructs rich ClipboardItem model."""

    @classmethod
    def read_clipboard(
        cls,
        clipboard: QClipboard,
        source_app: Optional[str] = None,
    ) -> Optional[Tuple[ClipboardItem, Optional[QImage]]]:
        """
        Extracts all rich representations from active clipboard.
        Returns a tuple of (ClipboardItem, Optional[QImage]) or None if empty/unsupported.
        """
        try:
            mime_data = clipboard.mimeData()
            if mime_data is None:
                return None

            formats = mime_data.formats()
            if not formats:
                return None

            # Detect source process if not provided
            if not source_app:
                hwnd = get_foreground_window()
                source_app = get_process_name_for_hwnd(hwnd)

            # 1. Extract Files & Folders
            file_paths = extract_file_paths_from_mime(mime_data)
            clipboard_files: List[ClipboardFile] = []
            if file_paths:
                for path in file_paths:
                    clipboard_files.append(ClipboardFile.from_path(path))

            # 2. Extract Image
            qimage: Optional[QImage] = None
            has_image = False
            if mime_data.hasImage() or "image/png" in formats or "image/jpeg" in formats:
                img_data = clipboard.image()
                if not img_data.isNull():
                    qimage = img_data
                    has_image = True
                else:
                    # Try reading image from mimeData
                    img_variant = mime_data.imageData()
                    if img_variant and not img_variant.isNull():
                        qimage = img_variant
                        has_image = True

            # 3. Extract HTML & Plain Text
            html_content: Optional[str] = None
            plain_text: Optional[str] = None

            if mime_data.hasHtml() or "text/html" in formats:
                raw_html = mime_data.html()
                if raw_html and raw_html.strip():
                    html_content = raw_html

            if mime_data.hasText() or "text/plain" in formats:
                raw_text = mime_data.text()
                if raw_text is not None:
                    plain_text = raw_text

            # If plain text is empty but HTML exists, extract plain text from HTML
            if not plain_text and html_content:
                plain_text = extract_text_from_html(html_content)

            # Determine primary item type
            primary_type = determine_primary_type(
                mime_data=mime_data,
                file_paths=file_paths,
                has_image=has_image,
                has_html=bool(html_content),
                plain_text=plain_text or "",
            )

            # Skip empty content
            if (
                not plain_text
                and not html_content
                and not has_image
                and not clipboard_files
            ):
                return None

            # Construct preview text and title
            title = None
            preview = None

            if primary_type in ("file", "files"):
                if len(clipboard_files) == 1:
                    title = clipboard_files[0].name
                    preview = clipboard_files[0].path
                else:
                    title = f"{len(clipboard_files)} Files"
                    preview = ", ".join(f.name for f in clipboard_files[:3])
            elif primary_type == "image":
                title = "Image"
                preview = "Image"
            elif primary_type == "url" and plain_text:
                title = plain_text.strip()
                preview = plain_text.strip()
            elif primary_type == "html" and html_content:
                stripped = " ".join(extract_text_from_html(html_content).split())
                title = (stripped[:90] + "...") if len(stripped) > 90 else stripped
                preview = title
            elif plain_text:
                clean = " ".join(plain_text.split())
                title = (clean[:90] + "...") if len(clean) > 90 else clean
                preview = title

            item = ClipboardItem(
                type=primary_type,
                plain_text=plain_text,
                html_content=html_content,
                title=title,
                preview_text=preview,
                source_app=source_app,
                files=clipboard_files,
            )
            item.mime_types_list = formats

            return item, qimage

        except Exception as e:
            logger.error(f"Error reading clipboard formats: {e}", exc_info=True)
            return None
