"""
Unit tests for clipboard MIME parser and reader.
"""

import sys
import unittest
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QMimeData, QUrl

from clipboard.mime_parser import (
    determine_primary_type,
    extract_file_paths_from_mime,
    extract_text_from_html,
    is_valid_url,
)


class TestClipboardReader(unittest.TestCase):
    """Tests for MIME parsing and content type resolution."""

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication(sys.argv)

    def test_extract_text_from_html(self):
        html = "<p>Hello <b>World</b> from <i>ClipVault</i></p>"
        extracted = extract_text_from_html(html)
        self.assertEqual(extracted, "Hello World from ClipVault")

    def test_is_valid_url(self):
        self.assertTrue(is_valid_url("https://github.com/example/project"))
        self.assertTrue(is_valid_url("http://example.com:8080/test"))
        self.assertTrue(is_valid_url("mailto:support@clipvault.local"))
        self.assertTrue(is_valid_url("google.com/search"))
        self.assertFalse(is_valid_url("Hello World this is not a URL"))
        self.assertFalse(is_valid_url("https://with spaces.com"))

    def test_extract_file_paths_from_mime(self):
        mime = QMimeData()
        urls = [
            QUrl.fromLocalFile("C:/projects/app.py"),
            QUrl.fromLocalFile("C:/projects/readme.md"),
        ]
        mime.setUrls(urls)

        paths = extract_file_paths_from_mime(mime)
        self.assertEqual(len(paths), 2)
        self.assertIn("C:\\projects\\app.py", [p.replace("/", "\\") for p in paths])

    def test_determine_primary_type(self):
        mime = QMimeData()

        # Files precedence
        t = determine_primary_type(mime, ["C:\\file1.txt"], False, False, "")
        self.assertEqual(t, "file")

        t = determine_primary_type(mime, ["C:\\file1.txt", "C:\\file2.txt"], False, False, "")
        self.assertEqual(t, "files")

        # Image precedence
        t = determine_primary_type(mime, [], True, True, "some text")
        self.assertEqual(t, "image")

        # HTML precedence
        t = determine_primary_type(mime, [], False, True, "some text")
        self.assertEqual(t, "html")

        # URL precedence
        t = determine_primary_type(mime, [], False, False, "https://example.com")
        self.assertEqual(t, "url")

        # Plain text
        t = determine_primary_type(mime, [], False, False, "Normal text")
        self.assertEqual(t, "text")


if __name__ == "__main__":
    unittest.main()
