"""
ClamAV GUI - A graphical interface for ClamAV Antivirus
"""
import sys
import os
import logging
from pathlib import Path

# Set up basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ClamAV-GUI")

# Now import Qt and other modules
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo
    from PySide6.QtGui import QIcon
    
    # Now that PySide6 is imported, we can import our modules that might use it
    from clamav_gui.main_window import ClamAVGUI
    from clamav_gui.lang.lang_manager import SimpleLanguageManager
    from clamav_gui.utils.logger import setup_logger
    from clamav_gui import __version__
    
    # Reconfigure logger with our custom setup
    logger = setup_logger("ClamAV-GUI", log_level="INFO")
    
except ImportError as e:
    logger.critical(f"Failed to import required modules: {e}")
    logger.critical("Please make sure all dependencies are installed with: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise

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
        from .resources import icons_rc  # noqa: F401
        app_icon = QIcon(":/icons/app_icon.png")
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
    except ImportError:
        logger.warning("Failed to load application icon")
    
    # Set up translations
    translator = QTranslator()
    lang_manager = SimpleLanguageManager()
    
    # Try to load system language
    system_lang = QLocale.system().name()
    if lang_manager.set_language(system_lang):
        logger.info(f"Using system language: {system_lang}")
    else:
        logger.warning(f"System language {system_lang} not available, using default")
    
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
        
        # Create and show main window
        window = ClamAVGUI(lang_manager=lang_manager)
        window.show()
        
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
