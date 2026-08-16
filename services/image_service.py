"""
Image processing and thumbnail generation service for ClipVault.
Saves clipboard images to disk and generates fast thumbnails in background threads using Pillow.
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Optional, Tuple
import uuid

from PIL import Image
from PySide6.QtCore import QRunnable, QThreadPool
from PySide6.QtGui import QImage

from app.constants import THUMBNAIL_MAX_HEIGHT, THUMBNAIL_MAX_WIDTH
from storage.paths import StoragePaths
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.ImageService")


class ThumbnailTask(QRunnable):
    """Background task to generate and save thumbnail image via Pillow."""

    def __init__(self, source_image_path: str, thumbnail_dest_path: str):
        super().__init__()
        self.source_image_path = source_image_path
        self.thumbnail_dest_path = thumbnail_dest_path

    def run(self) -> None:
        try:
            with Image.open(self.source_image_path) as img:
                # Convert RGBA to RGB for JPEG thumbnail if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    thumb = rgb_img
                else:
                    thumb = img.copy()

                thumb.thumbnail((THUMBNAIL_MAX_WIDTH, THUMBNAIL_MAX_HEIGHT), Image.Resampling.LANCZOS)
                Path(self.thumbnail_dest_path).parent.mkdir(parents=True, exist_ok=True)
                thumb.save(self.thumbnail_dest_path, "JPEG", quality=85)
        except Exception as e:
            logger.error(f"Thumbnail generation failed for {self.source_image_path}: {e}")


class ImageService:
    """Service for storing images and managing thumbnail creation."""

    def __init__(self):
        self._thread_pool = QThreadPool.globalInstance()

    def process_and_save_image(self, qimage: QImage) -> Tuple[str, str, int, int]:
        """
        Saves full-resolution QImage to disk and schedules background thumbnail generation.
        Returns tuple of (image_file_path, thumbnail_file_path, width, height).
        """
        now = datetime.now()
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m")
        unique_id = uuid.uuid4().hex

        # 1. Prepare storage paths
        media_base = StoragePaths.get_media_dir() / year_str / month_str
        media_base.mkdir(parents=True, exist_ok=True)
        image_path = media_base / f"{unique_id}.png"

        thumbnails_base = StoragePaths.get_thumbnails_dir()
        thumbnails_base.mkdir(parents=True, exist_ok=True)
        thumbnail_path = thumbnails_base / f"{unique_id}.jpg"

        width = qimage.width()
        height = qimage.height()

        # 2. Save full-res PNG
        qimage.save(str(image_path), "PNG")

        # 3. Queue thumbnail creation in background thread
        task = ThumbnailTask(str(image_path), str(thumbnail_path))
        self._thread_pool.start(task)

        return str(image_path), str(thumbnail_path), width, height
