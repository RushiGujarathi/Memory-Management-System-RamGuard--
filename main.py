"""
RAMGuard — Smart & Safe Windows Memory Optimization
Entry point: initialises the application, database, and main window.

Usage:
    python main.py

Requirements:
    pip install PyQt6 psutil
"""

import sys
import os

# ── Ensure project root is on the Python path ──
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor

from utils.logger import setup_logger
from database.database import initialize_database
from config.app_config import AppConfig
from ui.main_window import MainWindow

logger = setup_logger("RAMGuard")


def show_splash(app: QApplication) -> QSplashScreen:
    """Show a minimal branded splash screen while the app loads."""
    pixmap = QPixmap(480, 200)
    pixmap.fill(QColor("#060d17"))

    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.showMessage(
        "🛡  RAMGuard\nSmart & Safe Windows Memory Optimization\n\nInitializing…",
        Qt.AlignmentFlag.AlignCenter,
        QColor("#38bdf8"),
    )
    splash.show()
    app.processEvents()
    return splash


def main() -> int:
    logger.info("=" * 60)
    logger.info("RAMGuard starting up")
    logger.info("Python: %s", sys.version)
    logger.info("Platform: %s", sys.platform)
    logger.info("=" * 60)

    # ── Qt application ──
    app = QApplication(sys.argv)
    app.setApplicationName("RAMGuard")
    app.setApplicationDisplayName("RAMGuard — Smart & Safe Memory Optimization")
    app.setOrganizationName("RAMGuard")
    app.setOrganizationDomain("ramguard.local")
    app.setFont(QFont("Segoe UI", 10))

    # ── Splash screen ──
    splash = show_splash(app)

    try:
        # ── Initialise database ──
        logger.info("Initialising database…")
        initialize_database()

        # ── Load configuration ──
        logger.info("Loading configuration…")
        config = AppConfig()

        # ── Build main window ──
        logger.info("Building main window…")
        window = MainWindow(config)

    except Exception as e:
        logger.critical("Fatal error during startup: %s", e, exc_info=True)
        splash.close()
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "RAMGuard — Startup Error",
            f"RAMGuard failed to start:\n\n{e}\n\n"
            "Please check the log file in the 'logs' directory for details.",
        )
        return 1

    splash.close()
    window.show()

    logger.info("RAMGuard started successfully.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
