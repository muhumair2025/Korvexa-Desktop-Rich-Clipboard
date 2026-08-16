"""
Unit tests for file reference metadata and CF_HDROP generation.
"""

from pathlib import Path
import tempfile
import unittest

from clipboard.windows_clipboard import create_hdrop_buffer
from models.clipboard_file import ClipboardFile


class TestFiles(unittest.TestCase):
    """Tests for file metadata and CF_HDROP buffer generation."""

    def test_clipboard_file_from_path(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Hello file test")
            f_path = f.name

        try:
            cf = ClipboardFile.from_path(f_path)
            self.assertEqual(cf.name, Path(f_path).name)
            self.assertEqual(cf.extension, "TXT")
            self.assertEqual(cf.is_dir, 0)
            self.assertGreater(cf.size, 0)
            self.assertIn("B", cf.formatted_size)
        finally:
            Path(f_path).unlink(missing_ok=True)

    def test_hdrop_buffer_creation(self):
        paths = ["C:\\test\\file1.txt", "C:\\test\\file2.pdf"]
        buf = create_hdrop_buffer(paths)
        self.assertIsNotNone(buf)
        self.assertGreater(len(buf), 20)  # Header + UTF-16 characters + double null


if __name__ == "__main__":
    unittest.main()
