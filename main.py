"""
ClipVault — Advanced Windows Rich Clipboard Manager.
Main entry point.
"""

import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.application import ClipVaultApp
from utils.logging_config import setup_logging

logger = setup_logging()


def exception_hook(exctype, value, traceback):
    """Global unhandled exception hook to prevent silent crashes."""
    logger.critical("Unhandled exception:", exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)


def main():
    sys.excepthook = exception_hook

    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)

    app_controller = ClipVaultApp(qapp)

    # Check Single Instance
    if not app_controller.check_single_instance():
        QMessageBox.information(
            None,
            "ClipVault",
            "ClipVault is already running in your system tray.\nPress Ctrl + Shift + V to open.",
        )
        sys.exit(0)

    exit_code = app_controller.initialize_and_run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
