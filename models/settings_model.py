"""
Settings model for ClipVault preferences.
"""

from dataclasses import dataclass, field
import json
from typing import List

from app.constants import (
    DEFAULT_SHORTCUT_POPUP,
    DEFAULT_SHORTCUT_PLAIN_PASTE,
    RETENTION_30_DAYS,
    THEME_SYSTEM,
)


@dataclass
class AppSettings:
    """Strongly typed application configuration settings."""

    # General
    start_with_windows: bool = True
    show_tray_icon: bool = True
    play_sound: bool = False

    # Clipboard Formats
    monitor_clipboard: bool = True
    save_text: bool = True
    save_html: bool = True
    save_images: bool = True
    save_files: bool = True
    save_urls: bool = True
    max_text_size_kb: int = 2048  # 2MB max text length per item

    # History & Retention
    retention_period: str = RETENTION_30_DAYS
    max_items: int = 1000
    deduplicate: bool = True

    # Privacy
    detect_sensitive: bool = True
    save_sensitive: bool = False  # If False, do not save detected sensitive data
    ignored_apps: List[str] = field(
        default_factory=lambda: ["keepass.exe", "1password.exe", "bitwarden.exe"]
    )

    # Shortcuts
    shortcut_popup: str = DEFAULT_SHORTCUT_POPUP
    shortcut_plain_paste: str = DEFAULT_SHORTCUT_PLAIN_PASTE

    # Appearance
    theme: str = THEME_SYSTEM  # System, Light, Dark

    # Advanced
    restore_previous_clipboard: bool = False
    paste_delay_ms: int = 40

    def to_dict(self) -> dict:
        """Serializes settings to dictionary."""
        return {
            "start_with_windows": self.start_with_windows,
            "show_tray_icon": self.show_tray_icon,
            "play_sound": self.play_sound,
            "monitor_clipboard": self.monitor_clipboard,
            "save_text": self.save_text,
            "save_html": self.save_html,
            "save_images": self.save_images,
            "save_files": self.save_files,
            "save_urls": self.save_urls,
            "max_text_size_kb": self.max_text_size_kb,
            "retention_period": self.retention_period,
            "max_items": self.max_items,
            "deduplicate": self.deduplicate,
            "detect_sensitive": self.detect_sensitive,
            "save_sensitive": self.save_sensitive,
            "ignored_apps": json.dumps(self.ignored_apps),
            "shortcut_popup": self.shortcut_popup,
            "shortcut_plain_paste": self.shortcut_plain_paste,
            "theme": self.theme,
            "restore_previous_clipboard": self.restore_previous_clipboard,
            "paste_delay_ms": self.paste_delay_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        """Constructs AppSettings from a dictionary."""
        ignored = data.get("ignored_apps", "[]")
        if isinstance(ignored, str):
            try:
                ignored_list = json.loads(ignored)
            except Exception:
                ignored_list = ["keepass.exe", "1password.exe", "bitwarden.exe"]
        else:
            ignored_list = ignored

        def _to_bool(val: any, default: bool) -> bool:
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return bool(val)
            s = str(val).strip().lower()
            if s in ("true", "1", "yes", "on"):
                return True
            if s in ("false", "0", "no", "off"):
                return False
            return default

        return cls(
            start_with_windows=_to_bool(data.get("start_with_windows"), False),
            show_tray_icon=_to_bool(data.get("show_tray_icon"), True),
            play_sound=_to_bool(data.get("play_sound"), False),
            monitor_clipboard=_to_bool(data.get("monitor_clipboard"), True),
            save_text=_to_bool(data.get("save_text"), True),
            save_html=_to_bool(data.get("save_html"), True),
            save_images=_to_bool(data.get("save_images"), True),
            save_files=_to_bool(data.get("save_files"), True),
            save_urls=_to_bool(data.get("save_urls"), True),
            max_text_size_kb=int(data.get("max_text_size_kb", 2048)),
            retention_period=str(data.get("retention_period", RETENTION_30_DAYS)),
            max_items=int(data.get("max_items", 1000)),
            deduplicate=_to_bool(data.get("deduplicate"), True),
            detect_sensitive=_to_bool(data.get("detect_sensitive"), True),
            save_sensitive=_to_bool(data.get("save_sensitive"), False),
            ignored_apps=ignored_list,
            shortcut_popup=str(data.get("shortcut_popup", DEFAULT_SHORTCUT_POPUP)),
            shortcut_plain_paste=str(data.get("shortcut_plain_paste", DEFAULT_SHORTCUT_PLAIN_PASTE)),
            theme=str(data.get("theme", THEME_SYSTEM)),
            restore_previous_clipboard=_to_bool(data.get("restore_previous_clipboard"), False),
            paste_delay_ms=int(data.get("paste_delay_ms", 40)),
        )
