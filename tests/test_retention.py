"""
Unit tests for RetentionService calculation.
"""

from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from app.constants import RETENTION_1_DAY, RETENTION_1_HOUR, RETENTION_30_DAYS, RETENTION_FOREVER
from database.database import Database
from database.repositories import ClipboardRepository
from models.settings_model import AppSettings
from services.retention_service import RetentionService


class TestRetention(unittest.TestCase):
    """Tests for retention period timestamp calculations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_retention.db"
        self.db = Database(self.db_path)
        self.db.initialize()
        self.repo = ClipboardRepository(self.db)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_cutoff_calculation(self):
        settings_30d = AppSettings(retention_period=RETENTION_30_DAYS)
        service = RetentionService(self.repo, settings_30d)
        cutoff = service.calculate_cutoff_timestamp()
        self.assertIsNotNone(cutoff)

        settings_forever = AppSettings(retention_period=RETENTION_FOREVER)
        service.update_settings(settings_forever)
        cutoff_forever = service.calculate_cutoff_timestamp()
        self.assertIsNone(cutoff_forever)


if __name__ == "__main__":
    unittest.main()
