"""
Unit tests for ImageService and thumbnail creation.
"""

import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from PySide6.QtCore import QCoreApplication, QThreadPool
from PySide6.QtGui import QColor, QImage

from services.image_service import ImageService
from storage.paths import StoragePaths


class TestImageService(unittest.TestCase):
    """Tests for image disk saving and Pillow thumbnail generation."""

    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    def test_process_and_save_image(self):
        # Create a test QImage
        img = QImage(640, 480, QImage.Format_RGB32)
        img.fill(QColor(0, 120, 212))

        service = ImageService()
        img_path, thumb_path, w, h = service.process_and_save_image(img)

        self.assertEqual(w, 640)
        self.assertEqual(h, 480)
        self.assertTrue(Path(img_path).exists())

        # Wait for thread pool thumbnail completion
        QThreadPool.globalInstance().waitForDone(2000)
        self.assertTrue(Path(thumb_path).exists())

        # Clean up created files
        try:
            os.remove(img_path)
            os.remove(thumb_path)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
