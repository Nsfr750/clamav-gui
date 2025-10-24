"""
This module provides an about dialog for the ClamAV GUI application.
It displays version information, system details, and credits.
"""

from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser, QScrollArea, 
    QWidget, QFrame, QHBoxLayout, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6 import __version__ as QT_VERSION_STR
# PYQT_VERSION_STR is not available in PySide6, using PySide6 version instead
from PySide6.QtGui import QPixmap, QIcon, QDesktopServices

# Import version information
from clamav_gui.utils.version import (
    get_version, get_version_info, get_version_history,
    get_latest_changes, is_development, get_codename,
    __author__, __email__, __license__, __description__
)

# Import language manager
from clamav_gui.lang.lang_manager import SimpleLanguageManager
import os
import sys
import platform
from pathlib import Path
import logging

# Try to import psutil, but handle gracefully if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False
    logging.debug("psutil not available - some system info may be limited")

try:
    from wand.image import Image as WandImage
except ImportError:
    WandImage = None
    logging.warning("Wand library not found. Some features may be limited.")

logger = logging.getLogger(__name__)

class AboutDialog(QDialog):
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        try:
            # Initialize language manager with fallback
            self.language_manager = language_manager if language_manager else SimpleLanguageManager()
            
            # Set window title with fallback
            try:
                self.setWindowTitle(self.language_manager.tr("about.title", "About ClamAV GUI"))
            except Exception as e:
                logger.warning(f"Error setting window title: {e}")
                self.setWindowTitle("About ClamAV GUI")
                self.resize(400, 350)
                
        except Exception as e:
            logger.error(f"Error initializing AboutDialog: {e}")
            self.setWindowTitle("About")
            self.resize(600, 780)
        
        layout = QVBoxLayout(self)
        
        # App logo and title
        header = QHBoxLayout()
        
        # Load application logo
        logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            # Scale logo to a reasonable size while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            # Add some spacing
            logo_label.setContentsMargins(0, 0, 20, 0)
            header.addWidget(logo_label)
        else:
            # Add placeholder if logo not found
            print(f"Logo not found at: {logo_path}")
            logo_label = QLabel("LOGO")
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #666;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setFixedSize(128, 128)
            header.addWidget(logo_label)
        
        # App info
        app_info = QVBoxLayout()
        
        # Application title
        title = QLabel(self.language_manager.tr("about.title", "ClamAV GUI"))
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold;
            color: yellow;
            margin-bottom: 5px;
        """)
        
        # Version information
        try:
            version = get_version()
            version_text = f"Version {version}"
            
            # Try to get additional version info if available
            try:
                if callable(get_codename):
                    codename = get_codename()
                    if codename and codename != 'unknown':
                        version_text += f" {codename}"
                
                if callable(is_development):
                    status = "Development" if is_development() else "Stable"
                    version_text += f" ({status})"
                    
            except Exception as e:
                logger.debug(f"Could not get extended version info: {e}")
                
        except Exception as e:
            logger.error(f"Error getting version info: {e}")
            version_text = "Version Unknown"  # Final fallback
        version = QLabel(version_text)
        version.setStyleSheet("""
            color: yellow;
            font-size: 14px;
            margin-bottom: 10px;
        """)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        app_info.addWidget(title)
        app_info.addWidget(version)
        app_info.addStretch()
        
        header.addLayout(app_info)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Description
        description = QLabel(
            self.language_manager.tr(
                "about.description",
                "A graphical user interface for ClamAV antivirus.\n\n"
                "ClamAV GUI provides an easy-to-use interface for scanning files, "
                "updating virus definitions, and managing ClamAV settings."
            )
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: yellow;
            font-size: 14px;
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        """)
        layout.addWidget(description)
        
        # Create a scrollable area for system info
        # Set up scroll area
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # System info widget
        sys_info_widget = QWidget()
        sys_info_layout = QVBoxLayout(sys_info_widget)
        
        # System info title
        sys_info_title = QLabel(
            self.language_manager.tr("about.system_info", "<h3>System Information</h3>")
        )
        sys_info_title.setStyleSheet("margin-top: 10px;")
        sys_info_layout.addWidget(sys_info_title)
        
        # System info content
        sys_info = QTextBrowser()
        sys_info.setOpenLinks(True)
        sys_info.setStyleSheet("""
            QTextBrowser {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        sys_info.setHtml(self.get_system_info())
        sys_info_layout.addWidget(sys_info)
        
        # Set the widget to the scroll area
        scroll.setWidget(sys_info_widget)
        scroll.setWidgetResizable(True)
        
        # Add scroll area to the main layout
        layout.addWidget(scroll, 1)  # The 1 makes it take up remaining space
        sys_info.setStyleSheet("""
            QTextBrowser {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
                color: black;
            }
        """)
        sys_info_layout.addWidget(sys_info)
        
        # Set the widget to the scroll area
        scroll.setWidget(sys_info_widget)
        layout.addWidget(scroll, 1)  # The '1' makes it take available space
        
        # Copyright and license
        copyright = QLabel(
            self.language_manager.tr(
                "about.copyright",
                "© {year} {author} - All rights reserved\n"
                "Licensed under the {license} License"
            ).format(
                year="2025",
                author=__author__,
                license=__license__
            )
        )
        copyright.setStyleSheet("""
            color: yellow;
            font-size: 11px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #dee2e6;
        """)
        copyright.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright)
        
        # Buttons
        buttons = QHBoxLayout()
        
        # GitHub button
        github_btn = QPushButton("GitHub")
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://github.com/Nsfr750/ClamAV-GUI")))
        # Style GitHub button with blue background and white text
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #0366d6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
        """)
        
        # Close button
        close_btn = QPushButton(self.language_manager.tr("about.close", "Close"))
        close_btn.clicked.connect(self.accept)
        # Style Close button with red background and white text
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        
        # Add buttons to layout with proper spacing
        buttons.addStretch()
        buttons.addWidget(github_btn)
        buttons.addWidget(close_btn)
        
        # Add buttons layout to main layout with some spacing
        layout.addLayout(buttons)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Connect language change signal if language manager is available
        if hasattr(self, 'language_manager') and hasattr(self.language_manager, 'language_changed'):
            self.language_manager.language_changed.connect(self.retranslate_ui)
            
    def retranslate_ui(self, language_code=None):
        """Retranslate the UI when language changes."""
        try:
            # Update window title
            self.setWindowTitle(self.language_manager.tr("about.title", "About ClamAV GUI"))
            
            # Update other translatable elements here if needed
            if hasattr(self, 'title_label'):
                self.title_label.setText(self.language_manager.tr("about.title", "ClamAV GUI"))
                
            # Update version info
            if hasattr(self, 'version_label'):
                try:
                    version = get_version()
                    codename = get_codename()
                    status = "Development" if is_development() else "Stable"
                    version_format = self.language_manager.tr(
                        "about.version", 
                        "Version {version} {codename} ({status})"
                    )
                    version_text = version_format.format(
                        version=version,
                        codename=codename,
                        status=status
                    )
                    self.version_label.setText(version_text)
                except Exception as e:
                    logger.error(f"Error updating version info: {e}")
                    self.version_label.setText(f"Version {get_version()}")
                    
        except Exception as e:
            logger.error(f"Error retranslating UI: {e}")
    
    def get_system_info(self):
        """Generate HTML-formatted system information."""
        try:
            # Get system information
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            
            # Get Python information
            python_version = platform.python_version()
            python_implementation = platform.python_implementation()
            
            # Get PySide6 version
            from PySide6 import __version__ as pyside_version
            pyside6_version = QT_VERSION_STR
            
            # Get application information
            app_version = get_version()
            app_codename = get_codename()
            app_status = "Development" if is_development() else "Stable"
            
            # Format the information as HTML
            info = f"""
            <html>
            <body>
                <h3>Application</h3>
                <table>
                    <tr><td><b>Name:</b></td><td>ClamAV GUI</td></tr>
                    <tr><td><b>Version:</b></td><td>{app_version} {app_codename} ({app_status})</td></tr>
                </table>
                
                <h3>System</h3>
                <table>
                    <tr><td><b>OS:</b></td><td>{system} {release}</td></tr>
                    <tr><td><b>Version:</b></td><td>{version}</td></tr>
                    <tr><td><b>Machine:</b></td><td>{machine}</td></tr>
                    <tr><td><b>Processor:</b></td><td>{processor}</td></tr>
                </table>
                
                <h3>Python</h3>
                <table>
                    <tr><td><b>Version:</b></td><td>{python_implementation} {python_version}</td></tr>
                    <tr><td><b>PySide6:</b></td><td>{pyside6_version}</td></tr>
                </table>
            </body>
            </html>
            """
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return "<p>Error retrieving system information.</p>"
    