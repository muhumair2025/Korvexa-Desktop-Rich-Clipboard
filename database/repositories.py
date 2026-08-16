"""
Data access repositories for Clipboard Items, Files, and Settings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from models.clipboard_file import ClipboardFile
from models.clipboard_item import ClipboardItem
from models.settings_model import AppSettings
from utils.logging_config import get_logger
from .database import Database

logger = get_logger("ClipVault.Database.Repositories")


class ClipboardRepository:
    """Repository handling all database operations for ClipboardItem and ClipboardFile."""

    def __init__(self, db: Optional[Database] = None):
        self._db = db or Database.get_instance()

    def _row_to_item(self, row: Any) -> ClipboardItem:
        """Converts an SQLite Row object to a ClipboardItem dataclass."""
        return ClipboardItem(
            id=row["id"],
            type=row["type"],
            plain_text=row["plain_text"],
            html_content=row["html_content"],
            image_path=row["image_path"],
            thumbnail_path=row["thumbnail_path"],
            title=row["title"],
            preview_text=row["preview_text"],
            mime_types=row["mime_types"],
            content_hash=row["content_hash"],
            is_pinned=row["is_pinned"],
            is_sensitive=row["is_sensitive"],
            source_app=row["source_app"],
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            use_count=row["use_count"],
            expires_at=row["expires_at"],
        )

    def _row_to_file(self, row: Any) -> ClipboardFile:
        """Converts an SQLite Row object to a ClipboardFile dataclass."""
        return ClipboardFile(
            id=row["id"],
            clipboard_item_id=row["clipboard_item_id"],
            path=row["path"],
            name=row["name"],
            size=row["size"],
            mime_type=row["mime_type"],
            is_dir=row["is_dir"],
        )

    def insert_item(self, item: ClipboardItem) -> int:
        """Inserts a new clipboard item and associated file references."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO clipboard_items (
                    type, plain_text, html_content, image_path, thumbnail_path,
                    title, preview_text, mime_types, content_hash, is_pinned,
                    is_sensitive, source_app, created_at, last_used_at, use_count, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.type,
                    item.plain_text,
                    item.html_content,
                    item.image_path,
                    item.thumbnail_path,
                    item.title,
                    item.preview_text,
                    item.mime_types,
                    item.content_hash,
                    item.is_pinned,
                    item.is_sensitive,
                    item.source_app,
                    item.created_at,
                    item.last_used_at,
                    item.use_count,
                    item.expires_at,
                ),
            )
            item_id = cursor.lastrowid
            item.id = item_id

            # Insert associated file references if present
            if item.files:
                for file_obj in item.files:
                    cursor.execute(
                        """
                        INSERT INTO clipboard_files (
                            clipboard_item_id, path, name, size, mime_type, is_dir
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item_id,
                            file_obj.path,
                            file_obj.name,
                            file_obj.size,
                            file_obj.mime_type,
                            file_obj.is_dir,
                        ),
                    )

            return item_id

    def update_item(self, item: ClipboardItem) -> None:
        """Updates an existing clipboard item."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE clipboard_items SET
                    type = ?, plain_text = ?, html_content = ?, image_path = ?,
                    thumbnail_path = ?, title = ?, preview_text = ?, mime_types = ?,
                    content_hash = ?, is_pinned = ?, is_sensitive = ?, source_app = ?,
                    last_used_at = ?, use_count = ?, expires_at = ?
                WHERE id = ?
                """,
                (
                    item.type,
                    item.plain_text,
                    item.html_content,
                    item.image_path,
                    item.thumbnail_path,
                    item.title,
                    item.preview_text,
                    item.mime_types,
                    item.content_hash,
                    item.is_pinned,
                    item.is_sensitive,
                    item.source_app,
                    item.last_used_at,
                    item.use_count,
                    item.expires_at,
                    item.id,
                ),
            )

    def touch_duplicate(self, item_id: int) -> None:
        """Increments use_count and updates last_used_at to current timestamp."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                """
                UPDATE clipboard_items
                SET last_used_at = ?, use_count = use_count + 1
                WHERE id = ?
                """,
                (now, item_id),
            )

    def get_by_hash(self, content_hash: str) -> Optional[ClipboardItem]:
        """Finds existing item by content hash."""
        if not content_hash:
            return None
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM clipboard_items WHERE content_hash = ? ORDER BY id DESC LIMIT 1",
                (content_hash,),
            )
            row = cursor.fetchone()
            if row:
                item = self._row_to_item(row)
                item.files = self.get_files_for_item(item.id)
                return item
            return None

    def get_by_id(self, item_id: int) -> Optional[ClipboardItem]:
        """Retrieves item by primary key."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clipboard_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                item = self._row_to_item(row)
                item.files = self.get_files_for_item(item.id)
                return item
            return None

    def get_files_for_item(self, item_id: int) -> List[ClipboardFile]:
        """Retrieves all associated file references for an item."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM clipboard_files WHERE clipboard_item_id = ? ORDER BY id ASC",
                (item_id,),
            )
            return [self._row_to_file(r) for r in cursor.fetchall()]

    def get_items(
        self,
        category: str = "All",
        search_query: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> List[ClipboardItem]:
        """
        Retrieves paginated clipboard items sorted by pinned status and last used timestamp.
        Filters by category (All, Pinned, Text, Images, Files, Links) and search query.
        """
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            params: List[Any] = []
            conditions: List[str] = []

            # Category filter
            cat_lower = category.lower()
            if cat_lower == "pinned":
                conditions.append("is_pinned = 1")
            elif cat_lower == "text":
                conditions.append("type IN ('text', 'html')")
            elif cat_lower == "images":
                conditions.append("type = 'image'")
            elif cat_lower == "files":
                conditions.append("type IN ('file', 'files')")
            elif cat_lower == "links":
                conditions.append("type = 'url'")

            # Search query filter
            if search_query.strip():
                q = f"%{search_query.strip()}%"
                conditions.append(
                    """
                    (plain_text LIKE ? OR title LIKE ? OR preview_text LIKE ? OR id IN (
                        SELECT clipboard_item_id FROM clipboard_files WHERE name LIKE ? OR path LIKE ?
                    ))
                    """
                )
                params.extend([q, q, q, q, q])

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            sql = f"""
                SELECT * FROM clipboard_items
                {where_clause}
                ORDER BY is_pinned DESC, last_used_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            items: List[ClipboardItem] = []
            for row in rows:
                item = self._row_to_item(row)
                if item.type in ("file", "files"):
                    item.files = self.get_files_for_item(item.id)
                items.append(item)

            return items

    def toggle_pin(self, item_id: int) -> bool:
        """Toggles the pinned status of an item. Returns new pinned boolean."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_pinned FROM clipboard_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if not row:
                return False
            new_val = 0 if row["is_pinned"] else 1
            cursor.execute("UPDATE clipboard_items SET is_pinned = ? WHERE id = ?", (new_val, item_id))
            return bool(new_val)

    def delete_item(self, item_id: int) -> bool:
        """Deletes a single item by id."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
            return cursor.rowcount > 0

    def clear_all(self, keep_pinned: bool = True) -> int:
        """Clears clipboard history. If keep_pinned is True, pinned items are preserved."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            if keep_pinned:
                cursor.execute("DELETE FROM clipboard_items WHERE is_pinned = 0")
            else:
                cursor.execute("DELETE FROM clipboard_items")
            return cursor.rowcount

    def cleanup_retention(self, cutoff_iso: str, max_items: int = 1000) -> int:
        """
        Removes expired or old unpinned items exceeding retention date or max count limit.
        Returns count of removed items.
        """
        deleted_count = 0
        with self._db.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Delete expired unpinned items
            if cutoff_iso:
                cursor.execute(
                    """
                    DELETE FROM clipboard_items
                    WHERE is_pinned = 0 AND created_at < ?
                    """,
                    (cutoff_iso,),
                )
                deleted_count += cursor.rowcount

            # 2. Trim excess items beyond max_items limit (protecting pinned items)
            if max_items > 0:
                cursor.execute(
                    """
                    DELETE FROM clipboard_items
                    WHERE is_pinned = 0 AND id NOT IN (
                        SELECT id FROM clipboard_items
                        ORDER BY is_pinned DESC, last_used_at DESC
                        LIMIT ?
                    )
                    """,
                    (max_items,),
                )
                deleted_count += cursor.rowcount

        return deleted_count

    def get_count(self) -> int:
        """Returns total number of items in history."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM clipboard_items")
            row = cursor.fetchone()
            return row["count"] if row else 0


class SettingsRepository:
    """Repository handling key-value application settings persistence."""

    def __init__(self, db: Optional[Database] = None):
        self._db = db or Database.get_instance()

    def load_settings(self) -> AppSettings:
        """Loads all settings from database, returning default AppSettings on empty/missing keys."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            if not rows:
                default_settings = AppSettings()
                self.save_settings(default_settings)
                return default_settings

            settings_dict = {row["key"]: row["value"] for row in rows}
            return AppSettings.from_dict(settings_dict)

    def save_settings(self, settings: AppSettings) -> None:
        """Persists all AppSettings fields into the settings table."""
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            data = settings.to_dict()
            for key, val in data.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, str(val)),
                )
