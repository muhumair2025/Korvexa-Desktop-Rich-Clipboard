"""
Privacy and security heuristic detection service for ClipVault.
Detects sensitive clipboard data patterns and verifies source application whitelist/blacklist.
"""

import re
from typing import List, Optional

from models.settings_model import AppSettings
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.Privacy")

# Heuristic patterns for sensitive credentials
SENSITIVE_PATTERNS = [
    # Private keys
    re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    # JWT Tokens
    re.compile(r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+"),
    # AWS Access Keys
    re.compile(r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
    # GitHub Personal Access Tokens
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"),
    # Generic API Keys / Secrets / Passwords
    re.compile(
        r"(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key|client[_-]?secret|password|passwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.\$\@\!\%]{8,}['\"]?",
        re.IGNORECASE,
    ),
    # Bearer Tokens
    re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
    # Credit Card Numbers (13-19 digits formatted)
    re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b(?:\d{4}[ -]?){2}\d{5}\b"),
]


class PrivacyService:
    """Evaluates privacy filters and sensitive data heuristics."""

    def __init__(self, settings: Optional[AppSettings] = None):
        self._settings = settings or AppSettings()

    def update_settings(self, settings: AppSettings) -> None:
        """Updates internal reference to active settings."""
        self._settings = settings

    def is_application_ignored(self, source_app: Optional[str]) -> bool:
        """Checks if the originating application is in the user's ignored applications list."""
        if not source_app:
            return False

        app_name_lower = source_app.strip().lower()
        for ignored in self._settings.ignored_apps:
            ignored_lower = ignored.strip().lower()
            if ignored_lower and (
                app_name_lower == ignored_lower
                or app_name_lower.endswith(f"\\{ignored_lower}")
                or app_name_lower.endswith(f"/{ignored_lower}")
            ):
                return True
        return False

    def is_sensitive_content(self, text: Optional[str]) -> bool:
        """
        Runs heuristic pattern matching across text to detect passwords, tokens, and keys.
        """
        if not text or not self._settings.detect_sensitive:
            return False

        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                return True

        return False

    def should_save_item(self, source_app: Optional[str], text: Optional[str]) -> bool:
        """
        Determines whether an item should be saved based on application ignore list and privacy rules.
        """
        if self.is_application_ignored(source_app):
            logger.info("Skipping clipboard capture: originating process is in ignored applications list.")
            return False

        if self.is_sensitive_content(text):
            if not self._settings.save_sensitive:
                logger.info("Skipping clipboard capture: sensitive data detected and save_sensitive is disabled.")
                return False

        return True
