"""
Automatic retention and history cleanup service for ClipVault.
Periodically purges expired and excess unpinned clipboard items.
"""

from datetime import datetime, timedelta
from typing import Optional
from PySide6.QtCore import QObject, QTimer

from app.constants import (
    RETENTION_1_DAY,
    RETENTION_1_HOUR,
    RETENTION_3_DAYS,
    RETENTION_7_DAYS,
    RETENTION_30_DAYS,
    RETENTION_90_DAYS,
    RETENTION_FOREVER,
)
from database.repositories import ClipboardRepository
from models.settings_model import AppSettings
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.Retention")


class RetentionService(QObject):
    """Manages automatic history pruning and retention policy enforcement."""

    def __init__(
        self,
        repository: ClipboardRepository,
        settings: Optional[AppSettings] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._repository = repository
        self._settings = settings or AppSettings()

        # Run cleanup every 30 minutes
        self._timer = QTimer(self)
        self._timer.setInterval(30 * 60 * 1000)
        self._timer.timeout.connect(self.run_cleanup)

    def start(self) -> None:
        """Starts periodic cleanup timer and runs initial cleanup."""
        self._timer.start()
        self.run_cleanup()

    def stop(self) -> None:
        """Stops the periodic timer."""
        self._timer.stop()

    def update_settings(self, settings: AppSettings) -> None:
        """Updates active settings."""
        self._settings = settings
        self.run_cleanup()

    def calculate_cutoff_timestamp(self) -> Optional[str]:
        """Calculates cutoff ISO timestamp based on configured retention period."""
        period = self._settings.retention_period
        now = datetime.now()

        if period == RETENTION_1_HOUR:
            cutoff = now - timedelta(hours=1)
        elif period == RETENTION_1_DAY:
            cutoff = now - timedelta(days=1)
        elif period == RETENTION_3_DAYS:
            cutoff = now - timedelta(days=3)
        elif period == RETENTION_7_DAYS:
            cutoff = now - timedelta(days=7)
        elif period == RETENTION_30_DAYS:
            cutoff = now - timedelta(days=30)
        elif period == RETENTION_90_DAYS:
            cutoff = now - timedelta(days=90)
        elif period == RETENTION_FOREVER:
            return None
        else:
            cutoff = now - timedelta(days=30)

        return cutoff.isoformat()

    def run_cleanup(self) -> int:
        """Executes database pruning for expired items while protecting pinned items."""
        try:
            cutoff_iso = self.calculate_cutoff_timestamp()
            deleted = self._repository.cleanup_retention(
                cutoff_iso=cutoff_iso or "",
                max_items=self._settings.max_items,
            )
            if deleted > 0:
                logger.info(f"Retention cleanup purged {deleted} unpinned clipboard items.")
            return deleted
        except Exception as e:
            logger.error(f"Error during retention cleanup: {e}", exc_info=True)
            return 0
