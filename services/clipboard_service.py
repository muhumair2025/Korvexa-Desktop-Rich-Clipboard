"""
Main clipboard capture pipeline service for ClipVault.
Orchestrates clipboard reading, format filtering, privacy checks, hashing, deduplication,
image storage, and database persistence.
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QClipboard

from clipboard.monitor import ClipboardMonitor
from clipboard.reader import ClipboardReader
from database.repositories import ClipboardRepository
from models.clipboard_item import ClipboardItem
from models.settings_model import AppSettings
from services.image_service import ImageService
from services.privacy_service import PrivacyService
from utils.hashing import hash_files, hash_image, hash_text
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.ClipboardService")


class ClipboardService(QObject):
    """Coordinates clipboard event processing pipeline and persistence."""

    item_added = Signal(object)  # Emits ClipboardItem

    def __init__(
        self,
        clipboard: QClipboard,
        monitor: ClipboardMonitor,
        repository: ClipboardRepository,
        privacy_service: PrivacyService,
        image_service: ImageService,
        settings: Optional[AppSettings] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._clipboard = clipboard
        self._monitor = monitor
        self._repository = repository
        self._privacy_service = privacy_service
        self._image_service = image_service
        self._settings = settings or AppSettings()

        # Connect to monitor signal
        self._monitor.clipboard_changed.connect(self.process_clipboard_change)

    def update_settings(self, settings: AppSettings) -> None:
        """Updates active settings."""
        self._settings = settings
        self._privacy_service.update_settings(settings)

    def process_clipboard_change(self) -> None:
        """Pipeline handler invoked on clipboard change."""
        if not self._settings.monitor_clipboard:
            return

        try:
            result = ClipboardReader.read_clipboard(self._clipboard)
            if not result:
                return

            item, qimage = result

            # 1. Format Filter Check
            if item.type == "text" and not self._settings.save_text:
                return
            if item.type == "html" and not self._settings.save_html:
                return
            if item.type == "image" and not self._settings.save_images:
                return
            if item.type in ("file", "files") and not self._settings.save_files:
                return
            if item.type == "url" and not self._settings.save_urls:
                return

            # 2. Text Size Limit Check
            if item.plain_text:
                max_bytes = self._settings.max_text_size_kb * 1024
                if len(item.plain_text.encode("utf-8", errors="ignore")) > max_bytes:
                    logger.info("Skipping clipboard item: text exceeds max size limit.")
                    return

            # 3. Privacy & Sensitive Check
            eval_text = item.plain_text or item.html_content or ""
            if not self._privacy_service.should_save_item(item.source_app, eval_text):
                return

            # Mark sensitive flag if detected
            if self._privacy_service.is_sensitive_content(eval_text):
                item.is_sensitive = 1

            # 4. Generate Content Hash for Duplicate Detection
            content_hash = ""
            if item.type in ("file", "files") and item.files:
                content_hash = hash_files([f.path for f in item.files])
            elif item.type == "image" and qimage:
                content_hash = hash_image(qimage)
            elif item.type == "html" and item.html_content:
                content_hash = hash_text(item.html_content)
            elif item.plain_text:
                content_hash = hash_text(item.plain_text)

            item.content_hash = content_hash

            # 5. Duplicate Check
            if self._settings.deduplicate and content_hash:
                existing = self._repository.get_by_hash(content_hash)
                if existing:
                    logger.info(f"Duplicate clipboard item detected (ID: {existing.id}). Touching record.")
                    self._repository.touch_duplicate(existing.id)
                    existing.last_used_at = item.last_used_at
                    existing.use_count += 1
                    self.item_added.emit(existing)
                    return

            # 6. Image Processing (if image)
            if item.type == "image" and qimage:
                img_path, thumb_path, w, h = self._image_service.process_and_save_image(qimage)
                item.image_path = img_path
                item.thumbnail_path = thumb_path
                item.title = "Image"
                item.preview_text = "Image"

            # 7. Persist to Database
            item_id = self._repository.insert_item(item)
            item.id = item_id
            logger.info(f"Captured new clipboard item (ID: {item_id}, Type: {item.type}).")

            # 8. Notify UI
            self.item_added.emit(item)

        except Exception as e:
            logger.error(f"Error processing clipboard change: {e}", exc_info=True)
