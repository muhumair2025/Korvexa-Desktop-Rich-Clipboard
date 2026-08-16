"""
MIME inspector and content type detector for ClipVault.
Determines format priority, extracts plain text from HTML, and identifies URLs and files.
"""

from html.parser import HTMLParser
import re
from typing import List, Optional, Tuple
from urllib.parse import unquote, urlparse
from PySide6.QtCore import QMimeData

from app.constants import (
    TYPE_FILE,
    TYPE_FILES,
    TYPE_HTML,
    TYPE_IMAGE,
    TYPE_TEXT,
    TYPE_URL,
)


class HTMLTextExtractor(HTMLParser):
    """Simple parser to extract clean plain text representation from HTML snippets."""

    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)

    def get_text(self) -> str:
        return " ".join("".join(self.text_parts).split())


def extract_text_from_html(html_content: str) -> str:
    """Extracts stripped plain text from HTML markup."""
    if not html_content:
        return ""
    parser = HTMLTextExtractor()
    try:
        parser.feed(html_content)
        return parser.get_text()
    except Exception:
        # Fallback to regex tag strip
        return re.sub(r"<[^>]+>", " ", html_content).strip()


URL_REGEX = re.compile(
    r"^(https?://|ftp://|mailto:)[a-zA-Z0-9\-\._~:/?#\[\]@!$&'\(\)\*\+,;=%]+$",
    re.IGNORECASE,
)


def is_valid_url(text: str) -> bool:
    """Validates if a text string is a valid standalone web or email URL."""
    if not text:
        return False
    stripped = text.strip()
    if "\n" in stripped or "\r" in stripped or " " in stripped:
        return False
    if URL_REGEX.match(stripped):
        return True
    # Check domain format (e.g. github.com/user/repo)
    if re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\-]*\.[a-zA-Z]{2,}(/.*)?$", stripped):
        return True
    return False


def extract_file_paths_from_mime(mime_data: QMimeData) -> List[str]:
    """Extracts local filesystem paths from QMimeData text/uri-list or urls."""
    paths: List[str] = []
    if mime_data.hasUrls():
        for url in mime_data.urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
            else:
                s = url.toString()
                if s.startswith("file:///"):
                    clean = unquote(s[8:] if s[9:11] == ":/" else s[7:])
                    paths.append(clean.replace("/", "\\"))

    if not paths and mime_data.hasFormat("text/uri-list"):
        raw_data = mime_data.data("text/uri-list").data().decode("utf-8", errors="ignore")
        for line in raw_data.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                if line.startswith("file:///"):
                    clean = unquote(line[8:] if line[9:11] == ":/" else line[7:])
                    paths.append(clean.replace("/", "\\"))

    return [p for p in paths if p]


def determine_primary_type(
    mime_data: QMimeData,
    file_paths: List[str],
    has_image: bool,
    has_html: bool,
    plain_text: str,
) -> str:
    """
    Determines the primary clipboard item type according to format richness hierarchy:
    Files > Images > HTML > URLs > Text
    """
    if file_paths:
        return TYPE_FILES if len(file_paths) > 1 else TYPE_FILE

    if has_image:
        return TYPE_IMAGE

    if has_html:
        return TYPE_HTML

    if plain_text and is_valid_url(plain_text):
        return TYPE_URL

    return TYPE_TEXT
