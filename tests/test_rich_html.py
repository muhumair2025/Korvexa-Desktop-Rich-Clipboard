"""
Unit tests for Rich HTML and plain text dual-representation.
"""

import sys
import unittest
from PySide6.QtGui import QClipboard, QGuiApplication

from clipboard.writer import ClipboardWriter
from models.clipboard_item import ClipboardItem


class TestRichHTML(unittest.TestCase):
    """Tests for HTML dual-representation and restoration."""

    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication(sys.argv)
        cls.clipboard = QGuiApplication.clipboard()

    def test_html_item_structure(self):
        item = ClipboardItem(
            type="html",
            plain_text="Bold text and Normal text",
            html_content="<b>Bold text</b> and Normal text",
            title="Bold text and Normal text",
        )
        self.assertEqual(item.type, "html")
        self.assertIn("<b>", item.html_content)
        self.assertEqual(item.plain_text, "Bold text and Normal text")

    def test_write_html_to_clipboard(self):
        item = ClipboardItem(
            type="html",
            plain_text="Sample Rich Text Preview",
            html_content="<h1>Header</h1><p>Rich Paragraph</p>",
        )
        res = ClipboardWriter.write_item(self.clipboard, item, as_plain_text=False)
        self.assertTrue(res)

        mime = self.clipboard.mimeData()
        self.assertTrue(mime.hasHtml() or mime.hasText())

    def test_write_html_as_plain_text(self):
        item = ClipboardItem(
            type="html",
            plain_text="Sample Plain Text",
            html_content="<b>Sample Plain Text</b>",
        )
        res = ClipboardWriter.write_item(self.clipboard, item, as_plain_text=True)
        self.assertTrue(res)

        mime = self.clipboard.mimeData()
        self.assertEqual(mime.text(), "Sample Plain Text")


if __name__ == "__main__":
    unittest.main()
