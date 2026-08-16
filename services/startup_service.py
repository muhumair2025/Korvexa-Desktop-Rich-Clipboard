"""
Windows autostart registry manager for ClipVault.
Manages HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run entries.
"""

import os
import sys
import winreg
from utils.logging_config import get_logger

logger = get_logger("ClipVault.Services.Startup")

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "ClipVault"


class StartupService:
    """Manages Windows startup registry key."""

    @staticmethod
    def get_executable_command() -> str:
        """Returns command string to launch ClipVault on system login."""
        if getattr(sys, "frozen", False):
            # PyInstaller compiled executable
            return f'"{sys.executable}"'
        else:
            # Running from source
            main_script = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            return f'"{python_exe}" "{main_script}"'

    @classmethod
    def is_startup_enabled(cls) -> bool:
        """Checks if ClipVault is registered in HKCU Run key."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ
            ) as key:
                value, _ = winreg.QueryValueEx(key, APP_REG_NAME)
                return bool(value)
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking startup registry: {e}")
            return False

    @classmethod
    def set_startup_enabled(cls, enabled: bool) -> bool:
        """Enables or disables ClipVault autostart on Windows login."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                if enabled:
                    cmd = cls.get_executable_command()
                    winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
                    logger.info(f"Registered Windows startup command: {cmd}")
                else:
                    try:
                        winreg.DeleteValue(key, APP_REG_NAME)
                        logger.info("Removed ClipVault from Windows startup registry.")
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            logger.error(f"Error setting startup registry: {e}", exc_info=True)
            return False
