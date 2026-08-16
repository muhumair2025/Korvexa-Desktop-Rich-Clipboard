"""
Database schema migrations for ClipVault.
Sets up tables, indexes, and full-text search virtual tables.
"""

import sqlite3
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Database.Migrations")

SCHEMA_V1 = """
-- Core clipboard items table
CREATE TABLE IF NOT EXISTS clipboard_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    plain_text TEXT,
    html_content TEXT,
    image_path TEXT,
    thumbnail_path TEXT,
    title TEXT,
    preview_text TEXT,
    mime_types TEXT,
    content_hash TEXT,
    is_pinned INTEGER DEFAULT 0,
    is_sensitive INTEGER DEFAULT 0,
    source_app TEXT,
    created_at TEXT NOT NULL,
    last_used_at TEXT NOT NULL,
    use_count INTEGER DEFAULT 1,
    expires_at TEXT
);

-- File references table (one-to-many relationship with clipboard_items)
CREATE TABLE IF NOT EXISTS clipboard_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clipboard_item_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    size INTEGER DEFAULT 0,
    mime_type TEXT,
    is_dir INTEGER DEFAULT 0,
    FOREIGN KEY (clipboard_item_id)
        REFERENCES clipboard_items(id)
        ON DELETE CASCADE
);

-- Key-value settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Indexes for ultra-fast querying and sorting
CREATE INDEX IF NOT EXISTS idx_items_last_used ON clipboard_items(last_used_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_type ON clipboard_items(type);
CREATE INDEX IF NOT EXISTS idx_items_pinned ON clipboard_items(is_pinned);
CREATE INDEX IF NOT EXISTS idx_items_content_hash ON clipboard_items(content_hash);
CREATE INDEX IF NOT EXISTS idx_items_created_at ON clipboard_items(created_at);
CREATE INDEX IF NOT EXISTS idx_files_item_id ON clipboard_files(clipboard_item_id);
"""

# FTS5 Virtual Table for full-text search
FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS clipboard_fts USING fts5(
    item_id UNINDEXED,
    plain_text,
    title,
    preview_text,
    tokenize = 'unicode61'
);

-- Triggers to synchronize FTS index with clipboard_items table
CREATE TRIGGER IF NOT EXISTS trg_items_ai AFTER INSERT ON clipboard_items BEGIN
    INSERT INTO clipboard_fts(item_id, plain_text, title, preview_text)
    VALUES (new.id, new.plain_text, new.title, new.preview_text);
END;

CREATE TRIGGER IF NOT EXISTS trg_items_ad AFTER DELETE ON clipboard_items BEGIN
    DELETE FROM clipboard_fts WHERE item_id = old.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_items_au AFTER UPDATE ON clipboard_items BEGIN
    DELETE FROM clipboard_fts WHERE item_id = old.id;
    INSERT INTO clipboard_fts(item_id, plain_text, title, preview_text)
    VALUES (new.id, new.plain_text, new.title, new.preview_text);
END;
"""


def run_migrations(conn: sqlite3.Connection) -> None:
    """Executes database schema setup and FTS migrations."""
    cursor = conn.cursor()
    try:
        # Enable WAL mode and Foreign Keys
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA synchronous = NORMAL;")

        # Run primary schema
        cursor.executescript(SCHEMA_V1)

        # Run FTS5 schema (wrapped in try-except in case FTS5 is not compiled in exotic environments)
        try:
            cursor.executescript(FTS_SCHEMA)
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 setup skipped (will fallback to standard LIKE queries): {e}")

        conn.commit()
        logger.info("Database schema migrations completed successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Database migration failed: {e}", exc_info=True)
        raise
