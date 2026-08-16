"""
Clipboard file reference model.
Stores metadata references to files copied to the clipboard without duplicating file contents.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


@dataclass
class ClipboardFile:
    """Represents a file or folder referenced in a clipboard entry."""

    id: Optional[int] = None
    clipboard_item_id: Optional[int] = None
    path: str = ""
    name: str = ""
    size: int = 0
    mime_type: Optional[str] = None
    is_dir: int = 0

    @classmethod
    def from_path(cls, file_path: str, clipboard_item_id: Optional[int] = None) -> "ClipboardFile":
        """Creates a ClipboardFile metadata object from a filesystem path."""
        p = Path(file_path)
        name = p.name or str(p)
        size = 0
        is_dir = 0

        try:
            if p.exists():
                if p.is_dir():
                    is_dir = 1
                else:
                    size = p.stat().st_size
        except Exception:
            pass

        return cls(
            clipboard_item_id=clipboard_item_id,
            path=str(p.resolve() if p.exists() else p),
            name=name,
            size=size,
            is_dir=is_dir,
        )

    @property
    def extension(self) -> str:
        """Returns lowercase file extension or [DIR] for directories."""
        if self.is_dir:
            return "Folder"
        p = Path(self.path)
        ext = p.suffix.lower()
        return ext[1:].upper() if ext.startswith(".") else ext.upper() or "FILE"

    @property
    def formatted_size(self) -> str:
        """Returns human-readable file size."""
        if self.is_dir:
            return "Directory"
        num = self.size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}".replace(".0", "")
            num /= 1024.0
        return f"{num:.1f} PB"
