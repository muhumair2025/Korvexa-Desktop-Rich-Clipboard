"""
Unit tests for SQLite database layer and repositories.
"""

import os
from pathlib import Path
import tempfile
import unittest

from database.database import Database
from database.repositories import ClipboardRepository, SettingsRepository
from models.clipboard_file import ClipboardFile
from models.clipboard_item import ClipboardItem
from models.settings_model import AppSettings


class TestDatabaseRepositories(unittest.TestCase):
    """Tests for ClipboardRepository and SettingsRepository."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_clipboard.db"
        self.db = Database(self.db_path)
        self.db.initialize()
        self.repo = ClipboardRepository(self.db)
        self.settings_repo = SettingsRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_insert_and_get_text_item(self):
        item = ClipboardItem(
            type="text",
            plain_text="Hello ClipVault Test",
            title="Hello ClipVault Test",
            preview_text="Hello ClipVault Test",
            content_hash="test_hash_1",
        )
        item_id = self.repo.insert_item(item)
        self.assertIsNotNone(item_id)
        self.assertGreater(item_id, 0)

        retrieved = self.repo.get_by_id(item_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.plain_text, "Hello ClipVault Test")
        self.assertEqual(retrieved.type, "text")
        self.assertEqual(retrieved.content_hash, "test_hash_1")

    def test_insert_with_files(self):
        file_obj1 = ClipboardFile(
            path="C:\\test\\doc1.pdf",
            name="doc1.pdf",
            size=1024,
            is_dir=0,
        )
        file_obj2 = ClipboardFile(
            path="C:\\test\\folder1",
            name="folder1",
            size=0,
            is_dir=1,
        )

        item = ClipboardItem(
            type="files",
            title="2 Files",
            preview_text="doc1.pdf, folder1",
            files=[file_obj1, file_obj2],
        )
        item_id = self.repo.insert_item(item)

        retrieved = self.repo.get_by_id(item_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved.files), 2)
        self.assertEqual(retrieved.files[0].name, "doc1.pdf")
        self.assertEqual(retrieved.files[1].is_dir, 1)

    def test_toggle_pin(self):
        item = ClipboardItem(type="text", plain_text="Pinned note")
        item_id = self.repo.insert_item(item)

        # Initially unpinned
        retrieved = self.repo.get_by_id(item_id)
        self.assertEqual(retrieved.is_pinned, 0)

        # Toggle to pinned
        is_pinned = self.repo.toggle_pin(item_id)
        self.assertTrue(is_pinned)
        self.assertEqual(self.repo.get_by_id(item_id).is_pinned, 1)

        # Toggle back to unpinned
        is_pinned = self.repo.toggle_pin(item_id)
        self.assertFalse(is_pinned)
        self.assertEqual(self.repo.get_by_id(item_id).is_pinned, 0)

    def test_search_and_filter(self):
        self.repo.insert_item(ClipboardItem(type="text", plain_text="git commit -m initial"))
        self.repo.insert_item(ClipboardItem(type="text", plain_text="python main.py"))
        self.repo.insert_item(ClipboardItem(type="url", plain_text="https://github.com/project"))

        # Search for git
        results = self.repo.get_items(search_query="git")
        self.assertEqual(len(results), 2)  # git commit and github.com

        # Filter by Links
        link_results = self.repo.get_items(category="Links")
        self.assertEqual(len(link_results), 1)
        self.assertEqual(link_results[0].plain_text, "https://github.com/project")

    def test_clear_all_with_pinned(self):
        id1 = self.repo.insert_item(ClipboardItem(type="text", plain_text="Item 1", is_pinned=0))
        id2 = self.repo.insert_item(ClipboardItem(type="text", plain_text="Item 2 (Pinned)", is_pinned=1))

        self.repo.clear_all(keep_pinned=True)

        self.assertIsNone(self.repo.get_by_id(id1))
        self.assertIsNotNone(self.repo.get_by_id(id2))

    def test_settings_persistence(self):
        settings = AppSettings(
            start_with_windows=True,
            show_tray_icon=False,
            max_items=5000,
            theme="Dark",
            ignored_apps=["custom.exe"],
        )
        self.settings_repo.save_settings(settings)

        loaded = self.settings_repo.load_settings()
        self.assertTrue(loaded.start_with_windows)
        self.assertFalse(loaded.show_tray_icon)
        self.assertEqual(loaded.max_items, 5000)
        self.assertEqual(loaded.theme, "Dark")
        self.assertIn("custom.exe", loaded.ignored_apps)


if __name__ == "__main__":
    unittest.main()
