"""
Unit tests for duplicate detection and hashing.
"""

import sys
import unittest
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor, QImage

from utils.hashing import hash_files, hash_image, hash_text


class TestDeduplication(unittest.TestCase):
    """Tests for deterministic content hashing."""

    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    def test_text_hashing(self):
        h1 = hash_text("Hello World")
        h2 = hash_text("Hello World")
        h3 = hash_text("Different Text")

        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)

    def test_files_hashing_order_independent(self):
        f1 = ["C:\\Folder\\B.txt", "C:\\Folder\\A.txt"]
        f2 = ["c:\\folder\\a.txt", "c:\\folder\\b.txt"]

        h1 = hash_files(f1)
        h2 = hash_files(f2)
        self.assertEqual(h1, h2)

    def test_image_hashing(self):
        img1 = QImage(100, 100, QImage.Format_RGB32)
        img1.fill(QColor(255, 0, 0))

        img2 = QImage(100, 100, QImage.Format_RGB32)
        img2.fill(QColor(255, 0, 0))

        img3 = QImage(100, 100, QImage.Format_RGB32)
        img3.fill(QColor(0, 255, 0))

        h1 = hash_image(img1)
        h2 = hash_image(img2)
        h3 = hash_image(img3)

        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)


if __name__ == "__main__":
    unittest.main()
