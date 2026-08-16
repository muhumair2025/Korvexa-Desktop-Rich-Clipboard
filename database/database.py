"""
SQLite database connection and lifecycle manager for ClipVault.
Provides thread-safe connections, WAL mode initialization, and transaction management.
"""

import contextlib
from pathlib import Path
import sqlite3
import threading
from typing import Generator, Optional

from storage.paths import StoragePaths
from utils.logging_config import get_logger
from .migrations import run_migrations

logger = get_logger("ClipVault.Database")


class Database:
    """Manages SQLite database connections and lifecycle."""

    _instance: Optional["Database"] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = Path(db_path) if db_path else StoragePaths.get_database_path()
        self._local = threading.local()
        self._initialized = False

    @classmethod
    def get_instance(cls, db_path: Optional[Path] = None) -> "Database":
        """Singleton instance accessor."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path)
            return cls._instance

    def initialize(self) -> None:
        """Initializes database files, directory, and executes migrations."""
        with self._lock:
            if self._initialized:
                return

            StoragePaths.initialize_directories()
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            with self.get_connection() as conn:
                run_migrations(conn)

            self._initialized = True
            logger.info(f"Database initialized at {self._db_path}")

    def get_raw_connection(self) -> sqlite3.Connection:
        """Returns or creates a thread-local SQLite connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(
                str(self._db_path),
                timeout=30.0,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            self._local.connection = conn
        return self._local.connection

    @contextlib.contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing thread-local SQLite connection with auto-commit/rollback."""
        conn = self.get_raw_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close(self) -> None:
        """Closes thread-local connection if open."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            try:
                self._local.connection.close()
            except Exception:
                pass
            self._local.connection = None
