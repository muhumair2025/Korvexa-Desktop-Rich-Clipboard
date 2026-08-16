"""
URL detection and formatting utilities.
"""

from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """Extracts root domain from a given URL for clean display."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc
        if not netloc:
            # Handle URLs missing scheme
            if "/" in url:
                netloc = url.split("/")[0]
            else:
                netloc = url
        return netloc.lower()
    except Exception:
        return url
