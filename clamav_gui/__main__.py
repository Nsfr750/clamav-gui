"""
ClamAV GUI - A graphical interface for ClamAV Antivirus
"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

from clamav_gui.utils.logger import configure_logging, get_logger
configure_logging(logging.INFO)
logger = get_logger("ClamAV-GUI")

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo, QTimer, Qt, QCoreApplication
    from PySide6.QtGui import QIcon, QGuiApplication, QShortcut
    
    # Now that PySide6 is imported, we can import our modules that might use it
    from clamav_gui.main_window import ClamAVGUI
    from clamav_gui.lang.lang_manager import SimpleLanguageManager
    from clamav_gui import __version__
    from clamav_gui.ui.updates_ui import check_for_updates
    
    logger.info("Application starting...")
    
except ImportError as e:
    logging.critical(f"Failed to import required modules: {e}")
    logging.critical("Please make sure all dependencies are installed with: pip install -r requirements.txt")
    sys.exit(1)

def setup_application():
    """Set up the Qt application with translations and styles."""
    # Enable high DPI scaling
    os.environ["QT_SCALE_FACTOR"] = "1.0"
    # Force Windows platform plugin to avoid offscreen/headless mode
    if not os.environ.get("QT_QPA_PLATFORM"):
        os.environ["QT_QPA_PLATFORM"] = "windows"
    logger.info(f"Qt platform: {os.environ.get('QT_QPA_PLATFORM')}")
    
    # Force software OpenGL to avoid GPU/driver issues on some systems
    try:
        QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
    except Exception:
        pass
    
    app = QApplication(sys.argv)
    try:
        app.setQuitOnLastWindowClosed(False)
    except Exception:
        pass
    app.setApplicationName("ClamAV GUI")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Tuxxle")
    
    # Set application style
    try:
        app.setStyle('Windows')
    except Exception:
        app.setStyle('Fusion')
    
    # Set application icon
    try:
        # Try to load icon from assets folder
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
                logger.info("Successfully loaded application icon")
            else:
                logger.warning("Failed to load application icon: Invalid image file")
        else:
            logger.warning(f"Icon not found at: {icon_path}")
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
        
        # Create and show main window
        window = ClamAVGUI(lang_manager)
        window.show()
        try:
            # Ensure window is visible, normalized, centered, and focused
            window.showNormal()
            screen = QGuiApplication.primaryScreen()
            if screen is not None:
                geo = screen.availableGeometry()
                w, h = 960, 720
                x = geo.x() + (geo.width() - w) // 2
                y = geo.y() + (geo.height() - h) // 2
                window.resize(w, h)
                window.move(x, y)
            window.setWindowState((window.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
            window.raise_()
            window.activateWindow()
            try:
                def _ensure_visible():
                    try:
                        logger.info(f"Window visibility: visible={window.isVisible()}, active={window.isActiveWindow()}, minimized={window.isMinimized()}")
                        try:
                            # Diagnostics: list top-level widgets and their titles
                            from PySide6.QtWidgets import QApplication
                            tops = QApplication.topLevelWidgets()
                            titles = [getattr(w, 'windowTitle', lambda: '')() for w in tops]
                            logger.info(f"Top-level widgets: count={len(tops)} titles={titles}")
                        except Exception:
                            pass
                        if (not window.isVisible()) or window.isMinimized() or (not window.isActiveWindow()):
                            window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                            window.showNormal()
                            window.raise_()
                            window.activateWindow()
                            QTimer.singleShot(1000, lambda: (window.setWindowFlag(Qt.WindowStaysOnTopHint, False), window.show()))
                    except Exception:
                        pass
                QTimer.singleShot(1200, _ensure_visible)
                # Fallback: if still not active/visible, force maximize and on-top briefly
                def _force_maximize():
                    try:
                        if (not window.isVisible()) or window.isMinimized() or (not window.isActiveWindow()):
                            window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                            window.showMaximized()
                            window.raise_()
                            window.activateWindow()
                            QTimer.singleShot(1500, lambda: (window.setWindowFlag(Qt.WindowStaysOnTopHint, False), window.showNormal()))
                    except Exception:
                        pass
                QTimer.singleShot(2200, _force_maximize)

                # Global shortcut to bring window to front: Ctrl+Shift+M
                try:
                    sc = QShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_M, window)
                    def _bring_to_front():
                        try:
                            window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                            window.showNormal()
                            window.raise_()
                            window.activateWindow()
                            QTimer.singleShot(1000, lambda: (window.setWindowFlag(Qt.WindowStaysOnTopHint, False), window.show()))
                        except Exception:
                            pass
                    sc.activated.connect(_bring_to_front)
                except Exception:
                    pass

                # Stronger recovery: Ctrl+Shift+T to pin on top for 10s and maximize
                try:
                    sc2 = QShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_T, window)
                    def _strong_recovery():
                        try:
                            try:
                                window.setWindowOpacity(1.0)
                            except Exception:
                                pass
                            window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                            window.showMaximized()
                            window.raise_()
                            window.activateWindow()
                            # Keep on top for 10 seconds then restore normal
                            def _release_on_top():
                                try:
                                    window.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                                    window.showNormal()
                                    window.raise_()
                                    window.activateWindow()
                                except Exception:
                                    pass
                            QTimer.singleShot(10000, _release_on_top)
                        except Exception:
                            pass
                    sc2.activated.connect(_strong_recovery)
                except Exception:
                    pass
            except Exception:
                pass
        
            # One-time modal dialog to force visibility and confirm startup
            def _startup_modal():
                try:
                    QMessageBox.information(window, "ClamAV GUI", "Application started successfully. If you still can't see the main window, it may be off-screen. Try Win+Shift+Arrow to move it between monitors.")
                except Exception:
                    pass
            QTimer.singleShot(1600, _startup_modal)
            
            # Full-screen recovery with geometry logging
            def _fullscreen_recovery():
                try:
                    try:
                        scr = QGuiApplication.primaryScreen()
                        geo = scr.availableGeometry() if scr is not None else None
                        wgeo = window.frameGeometry()
                        logger.info(f"Screen geo: {geo if geo else 'N/A'}, Window geo before FS: {wgeo}")
                    except Exception:
                        pass
                    # Force full screen briefly
                    window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                    window.showFullScreen()
                    window.raise_()
                    window.activateWindow()
                    
                    def _restore_from_fullscreen():
                        try:
                            window.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                            window.showNormal()
                            # Recenter after restore
                            scr2 = QGuiApplication.primaryScreen()
                            if scr2 is not None:
                                g2 = scr2.availableGeometry()
                                w, h = 960, 720
                                x = g2.x() + (g2.width() - w) // 2
                                y = g2.y() + (g2.height() - h) // 2
                                window.resize(w, h)
                                window.move(x, y)
                            window.raise_()
                            window.activateWindow()
                            try:
                                wgeo2 = window.frameGeometry()
                                logger.info(f"Window geo after FS restore: {wgeo2}")
                            except Exception:
                                pass
                        except Exception:
                            pass
                    QTimer.singleShot(1400, _restore_from_fullscreen)
                except Exception:
                    pass
            QTimer.singleShot(2800, _fullscreen_recovery)
        except Exception:
            pass
        
        # Check for updates (non-blocking)
        if not getattr(sys, 'frozen', False):
            QTimer.singleShot(3000, lambda: check_for_updates(parent=window, current_version=__version__))
        
        # Start the application
        sys.exit(app.exec())
        
    except ImportError as e:
        logger.critical(f"Failed to import required modules: {e}")
        logger.critical("Please make sure all dependencies are installed with: pip install -r requirements.txt")
        QMessageBox.critical(
            None,
            "Missing Dependencies",
            f"Failed to import required modules:\n\n{e}\n\nPlease install dependencies with:\npip install -r requirements.txt"
        )
        sys.exit(1)
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
