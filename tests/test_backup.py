"""
Unit tests for ClipVault Backup and Restore service.
"""

from pathlib import Path
import tempfile
import unittest
import zipfile

from database.database import Database
from database.repositories import ClipboardRepository
from models.clipboard_file import ClipboardFile
from models.clipboard_item import ClipboardItem
from services.backup_service import BackupService


class TestBackupService(unittest.TestCase):
    """Tests for export and import of backup zip archives."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # DB 1 (Source)
        self.db1_path = self.temp_path / "source.db"
        self.db1 = Database(str(self.db1_path))
        self.db1.initialize()
        self.repo1 = ClipboardRepository(self.db1)

        # DB 2 (Target for import)
        self.db2_path = self.temp_path / "target.db"
        self.db2 = Database(str(self.db2_path))
        self.db2.initialize()
        self.repo2 = ClipboardRepository(self.db2)

    def tearDown(self):
        self.db1.close()
        self.db2.close()
        self.temp_dir.cleanup()

    def test_export_and_import_backup(self):
        # 1. Create source items
        dummy_img = self.temp_path / "test_image.png"
        dummy_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRdummy_test_image_data")

        dummy_thumb = self.temp_path / "test_thumb.png"
        dummy_thumb.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRdummy_test_thumb_data")

        item1 = ClipboardItem(
            type="text",
            plain_text="Hello World Note",
            title="Hello World Note",
            is_pinned=1,
            content_hash="hash_note_1",
        )
        item2 = ClipboardItem(
            type="html",
            plain_text="Rich text",
            html_content="<b>Rich text</b>",
            title="Rich text",
            is_pinned=0,
            content_hash="hash_html_2",
        )
        item3 = ClipboardItem(
            type="image",
            title="Image",
            image_path=str(dummy_img),
            thumbnail_path=str(dummy_thumb),
            is_pinned=1,
            content_hash="hash_img_3",
        )
        item4 = ClipboardItem(
            type="file",
            title="document.pdf",
            content_hash="hash_file_4",
            files=[
                ClipboardFile(
                    path=r"C:\Docs\document.pdf",
                    name="document.pdf",
                    size=1024,
                    is_dir=0,
                )
            ],
        )

        self.repo1.insert_item(item1)
        self.repo1.insert_item(item2)
        self.repo1.insert_item(item3)
        self.repo1.insert_item(item4)

        # 2. Export backup
        backup_zip = self.temp_path / "test_backup.zip"
        success, count, msg = BackupService.export_backup(str(backup_zip), self.repo1)

        self.assertTrue(success)
        self.assertEqual(count, 4)
        self.assertTrue(backup_zip.exists())

        # Verify zip structure
        with zipfile.ZipFile(backup_zip, "r") as zf:
            names = zf.namelist()
            self.assertIn("manifest.json", names)
            self.assertIn(f"media/images/{dummy_img.name}", names)
            self.assertIn(f"media/thumbnails/{dummy_thumb.name}", names)

        # 3. Import backup into clean repo2
        imp_success, imp_count, imp_msg = BackupService.import_backup(str(backup_zip), self.repo2)
        self.assertTrue(imp_success)
        self.assertEqual(imp_count, 4)

        # Verify restored items in target database
        restored = self.repo2.get_items()
        self.assertEqual(len(restored), 4)

        types = [it.type for it in restored]
        self.assertIn("text", types)
        self.assertIn("html", types)
        self.assertIn("image", types)
        self.assertIn("file", types)

        pinned = [it for it in restored if it.is_pinned]
        self.assertEqual(len(pinned), 2)


if __name__ == "__main__":
    unittest.main()
