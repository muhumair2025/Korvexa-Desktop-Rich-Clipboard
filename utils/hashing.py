"""
Hashing utilities for duplicate detection in ClipVault.
Generates deterministic fingerprints for text, HTML, image data, and file lists.
"""

import hashlib
from typing import List, Optional
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage


def hash_text(text: str) -> str:
    """Calculates SHA-256 hash for plain text or HTML."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def hash_image(qimage: QImage) -> str:
    """Calculates deterministic SHA-256 hash from QImage raw pixel data."""
    if qimage.isNull():
        return ""
    try:
        # Normalize image to consistent Format_ARGB32 to prevent format variation mismatch
        converted = qimage.convertToFormat(QImage.Format_ARGB32)
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        converted.save(buffer, "PNG")
        raw_bytes = bytes(byte_array.data())
        return hashlib.sha256(raw_bytes).hexdigest()
    except Exception:
        # Fallback to geometry and format hash
        return hashlib.sha256(f"{qimage.width()}x{qimage.height()}".encode()).hexdigest()


def hash_files(file_paths: List[str]) -> str:
    """Calculates SHA-256 hash for a list of file paths."""
    if not file_paths:
        return ""
    normalized = "\n".join(sorted(os_path.lower() for os_path in file_paths))
    return hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()
