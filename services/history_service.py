"""
History management service for ClipVault.
Provides high-level methods for querying, filtering, pinning, deleting, and modifying clipboard entries.
"""

from typing import List, Optional
from database.repositories import ClipboardRepository
from models.clipboard_item import ClipboardItem
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.HistoryService")


class HistoryService:
    """Provides business logic operations on clipboard history."""

    def __init__(self, repository: ClipboardRepository):
        self._repository = repository

    def get_items(
        self,
        category: str = "All",
        search_query: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> List[ClipboardItem]:
        """Retrieves paginated items matching category filter and search query."""
        return self._repository.get_items(
            category=category,
            search_query=search_query,
            limit=limit,
            offset=offset,
        )

    def toggle_pin(self, item_id: int) -> bool:
        """Toggles pinned status for an item."""
        return self._repository.toggle_pin(item_id)

    def delete_item(self, item_id: int) -> bool:
        """Deletes a single item by id."""
        return self._repository.delete_item(item_id)

    def clear_history(self, keep_pinned: bool = True) -> int:
        """Clears history while preserving pinned items if requested."""
        return self._repository.clear_all(keep_pinned=keep_pinned)

    def update_item_text(self, item_id: int, new_text: str) -> bool:
        """Updates text content of an existing item."""
        item = self._repository.get_by_id(item_id)
        if not item:
            return False

        item.plain_text = new_text
        clean = " ".join(new_text.split())
        item.title = (clean[:100] + "...") if len(clean) > 100 else clean
        item.preview_text = new_text[:300]
        self._repository.update_item(item)
        return True

    def get_count(self) -> int:
        """Returns total count of items."""
        return self._repository.get_count()
