"""
Application constants for ClipVault.
"""

APP_NAME = "ClipVault"
APP_DISPLAY_NAME = "ClipVault — Windows Rich Clipboard"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "Korvexa.app"
APP_WEBSITE = "https://korvexa.app"
APP_SUPPORT_EMAIL = "support@korvexa.app"
APP_AUTHOR = "Muhammad Umair"
APP_MUTEX_NAME = "ClipVault_SingleInstance_Mutex_98a72b"

# Clipboard Types
TYPE_TEXT = "text"
TYPE_HTML = "html"
TYPE_IMAGE = "image"
TYPE_FILE = "file"
TYPE_FILES = "files"
TYPE_URL = "url"
TYPE_MIXED = "mixed"

SUPPORTED_TYPES = [
    TYPE_TEXT,
    TYPE_HTML,
    TYPE_IMAGE,
    TYPE_FILE,
    TYPE_FILES,
    TYPE_URL,
    TYPE_MIXED,
]

# Retention Presets (in days, 0 = 1 hour, -1 = forever)
RETENTION_1_HOUR = "1 hour"
RETENTION_1_DAY = "1 day"
RETENTION_3_DAYS = "3 days"
RETENTION_7_DAYS = "7 days"
RETENTION_30_DAYS = "30 days"
RETENTION_90_DAYS = "90 days"
RETENTION_FOREVER = "Forever"

RETENTION_OPTIONS = [
    RETENTION_1_HOUR,
    RETENTION_1_DAY,
    RETENTION_3_DAYS,
    RETENTION_7_DAYS,
    RETENTION_30_DAYS,
    RETENTION_90_DAYS,
    RETENTION_FOREVER,
]

# Max Items Limits
MAX_ITEMS_OPTIONS = [100, 250, 500, 1000, 2500, 5000, 10000, 0]  # 0 = Unlimited

# Default Shortcuts
DEFAULT_SHORTCUT_POPUP = "Ctrl+Shift+V"
DEFAULT_SHORTCUT_PLAIN_PASTE = "Ctrl+Shift+Alt+V"

# Themes
THEME_SYSTEM = "System"
THEME_LIGHT = "Light"
THEME_DARK = "Dark"

THEMES = [THEME_SYSTEM, THEME_LIGHT, THEME_DARK]

# Window Dimensions
POPUP_WIDTH = 460
POPUP_HEIGHT = 560
POPUP_ITEM_HEIGHT = 68
THUMBNAIL_MAX_WIDTH = 320
THUMBNAIL_MAX_HEIGHT = 180

# Logging
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 3
