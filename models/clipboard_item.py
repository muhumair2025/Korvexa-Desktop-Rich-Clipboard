"""
Clipboard item model representing a captured clipboard history record.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import Any, List, Optional


@dataclass
class ClipboardItem:
    """Represents a single clipboard history entry with rich format support."""

    id: Optional[int] = None
    type: str = "text"  # text, html, image, file, files, url, mixed
    plain_text: Optional[str] = None
    html_content: Optional[str] = None
    image_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    title: Optional[str] = None
    preview_text: Optional[str] = None
    mime_types: Optional[str] = None  # JSON list of MIME types
    content_hash: Optional[str] = None
    is_pinned: int = 0
    is_sensitive: int = 0
    source_app: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used_at: str = field(default_factory=lambda: datetime.now().isoformat())
    use_count: int = 1
    expires_at: Optional[str] = None

    # Transient runtime-only fields (not stored in clipboard_items table directly)
    files: List[Any] = field(default_factory=list)

    @property
    def mime_types_list(self) -> List[str]:
        """Returns decoded list of MIME types."""
        if not self.mime_types:
            return []
        try:
            return json.loads(self.mime_types)
        except Exception:
            return [self.mime_types]

    @mime_types_list.setter
    def mime_types_list(self, values: List[str]) -> None:
        """Sets JSON-encoded list of MIME types."""
        self.mime_types = json.dumps(values)

    @property
    def display_title(self) -> str:
        """Returns a user-friendly single-line display title for the UI."""
        if self.type == "image":
            return "Image"
        if self.type in ("file", "files"):
            if self.files:
                if len(self.files) == 1:
                    return getattr(self.files[0], "name", "File")
                return f"{len(self.files)} Files"
            return "File(s)"
        if self.type == "url" and self.plain_text:
            return self.plain_text.strip()

        raw = self.plain_text or self.title or self.preview_text or ""
        cleaned = " ".join(raw.split())
        if len(cleaned) > 90:
            return cleaned[:90] + "..."
        return cleaned or "Clipboard item"

    @property
    def display_preview(self) -> str:
        """Returns clean single-line snippet preview."""
        return self.display_title
