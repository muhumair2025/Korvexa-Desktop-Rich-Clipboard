"""
Storage paths manager for ClipVault.
Ensures all data directories are located inside %LOCALAPPDATA%\\ClipVault
and provides helper methods for path resolution.
"""

import os
from pathlib import Path


class StoragePaths:
    """Manages application storage paths in %LOCALAPPDATA%\\ClipVault."""

    _app_dir: Path | None = None

    @classmethod
    def get_app_dir(cls) -> Path:
        """Returns root storage directory: %LOCALAPPDATA%\\ClipVault"""
        if cls._app_dir is None:
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                base = Path(local_app_data)
            else:
                base = Path.home() / "AppData" / "Local"
            cls._app_dir = base / "ClipVault"
        return cls._app_dir

    @classmethod
    def get_database_dir(cls) -> Path:
        """Directory for SQLite database files."""
        return cls.get_app_dir() / "database"

    @classmethod
    def get_database_path(cls) -> Path:
        """Full path to SQLite database file."""
        return cls.get_database_dir() / "clipboard.db"

    @classmethod
    def get_media_dir(cls) -> Path:
        """Directory for stored full-resolution media (images)."""
        return cls.get_app_dir() / "media" / "images"

    @classmethod
    def get_thumbnails_dir(cls) -> Path:
        """Directory for cached image thumbnails."""
        return cls.get_app_dir() / "thumbnails"

    @classmethod
    def get_logs_dir(cls) -> Path:
        """Directory for application log files."""
        return cls.get_app_dir() / "logs"

    @classmethod
    def get_log_path(cls) -> Path:
        """Full path to clipvault.log."""
        return cls.get_logs_dir() / "clipvault.log"

    @classmethod
    def get_cache_dir(cls) -> Path:
        """Directory for temporary caches."""
        return cls.get_app_dir() / "cache"

    @classmethod
    def initialize_directories(cls) -> None:
        """Creates all required storage directories if they do not exist."""
        cls.get_database_dir().mkdir(parents=True, exist_ok=True)
        cls.get_media_dir().mkdir(parents=True, exist_ok=True)
        cls.get_thumbnails_dir().mkdir(parents=True, exist_ok=True)
        cls.get_logs_dir().mkdir(parents=True, exist_ok=True)
        cls.get_cache_dir().mkdir(parents=True, exist_ok=True)
