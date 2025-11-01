"""
ClamAV GUI - A graphical interface for ClamAV Antivirus
"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

from clamav_gui.utils.logger import configure_logging, get_logger, ensure_logs_dir
configure_logging(logging.INFO)
logger = get_logger("ClamAV-GUI")

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo
    from PySide6.QtGui import QIcon
    
    # Now that PySide6 is imported, we can import our modules that might use it
    from clamav_gui.main_window import ClamAVGUI
    from clamav_gui.lang.lang_manager import SimpleLanguageManager
    from clamav_gui import __version__
    from clamav_gui.ui.updates_ui import check_for_updates
    from clamav_gui.utils.virus_db import VirusDBUpdater
    
    # Ensure logs directory exists and log its path
    try:
        logs_dir = ensure_logs_dir()
        logger.info(f"Logs directory: {logs_dir}")
    except Exception:
        pass
    logger.info("Application starting...")
    
except ImportError as e:
    logging.critical(f"Failed to import required modules: {e}")
    logging.critical("Please make sure all dependencies are installed with: pip install -r requirements.txt")
    sys.exit(1)

def setup_application():
    """Set up the Qt application with translations and styles."""
    # Enable high DPI scaling
    os.environ["QT_SCALE_FACTOR"] = "1.0"
    
    app = QApplication(sys.argv)
    app.setApplicationName("ClamAV GUI")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Tuxxle")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application icon
    try:
        # Try multiple possible icon locations
        possible_icon_paths = [
            # New location in assets/ folder
            Path(__file__).parent / "assets" / "icon.png",
            Path(__file__).parent / "assets" / "icon.ico",
        ]

        icon_loaded = False
        for icon_path in possible_icon_paths:
            if icon_path.exists():
                app_icon = QIcon(str(icon_path))
                if not app_icon.isNull():
                    app.setWindowIcon(app_icon)
                    logger.info(f"Successfully loaded application icon from: {icon_path}")
                    icon_loaded = True
                    break

        if not icon_loaded:
            logger.warning("No valid application icon found in any of the expected locations")

    except Exception as e:
        logger.warning(f"Failed to load application icon: {e}")
    
    # Set up translations
    translator = QTranslator()
    lang_manager = SimpleLanguageManager()
    
    # Try to load system language
    system_lang = QLocale.system().name()
    # Try exact match first (e.g., 'en_US')
    if not lang_manager.set_language(system_lang):
        # If exact match fails, try language code only (e.g., 'en')
        lang_code = system_lang.split('_')[0]
        if not lang_manager.set_language(lang_code):
            # Fall back to English if system language is not available
            logger.warning(f"System language {system_lang} not available, falling back to English")
            lang_manager.set_language('en')
        else:
            logger.info(f"Using language: {lang_code}")
    else:
        logger.info(f"Using system language: {system_lang}")
    
    # Load Qt's built-in translations
    qt_translator = QTranslator()
    qt_translator.load(
        f"qtbase_{system_lang.split('_')[0]}",
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    )
    app.installTranslator(qt_translator)
    
    return app, lang_manager

def main():
    """Main entry point for the application."""
    try:
        # Set up the application
        app, lang_manager = setup_application()
        
        # Create and show main window (ClamAVGUI with full mode functionality)
        window = ClamAVGUI(lang_manager)
        window.show()

        # One-time sigtool info refresh at startup (non-blocking)
        try:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: VirusDBUpdater().refresh_sig_info())
        except Exception:
            pass
        
        # Check for updates (non-blocking)
        if not getattr(sys, 'frozen', False):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: check_for_updates(parent=window, current_version=__version__))
        
        # Start the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"A critical error occurred and the application must close.\n\nError: {str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
