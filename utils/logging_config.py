"""
Privacy-safe logging configuration for ClipVault.
Ensures only technical operational logs are recorded without logging sensitive
clipboard contents, passwords, API keys, or text data.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from app.constants import LOG_MAX_BYTES, LOG_BACKUP_COUNT
from storage.paths import StoragePaths


def setup_logging() -> logging.Logger:
    """Configures application logger with rotating file handler and console output."""
    StoragePaths.initialize_directories()
    log_path = StoragePaths.get_log_path()

    logger = logging.getLogger("ClipVault")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # File handler (Rotating)
        file_handler = RotatingFileHandler(
            str(log_path),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s:%(threadName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)

        # Console handler for debugging
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "[%(levelname)s] %(name)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "ClipVault") -> logging.Logger:
    """Returns logger instance with specified sub-name."""
    return logging.getLogger(name)
