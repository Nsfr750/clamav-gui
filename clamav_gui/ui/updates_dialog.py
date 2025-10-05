"""
Update dialog for checking and displaying ClamAV GUI updates.
"""
import os
import sys
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextBrowser, QProgressBar, 
                             QApplication, QStyle, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QUrl
from PySide6.QtGui import QDesktopServices

# Import version information
from clamav_gui.utils.version import get_version, get_latest_version_info

# Setup logger
logger = logging.getLogger(__name__)

class UpdateChecker(QObject):
    """Worker thread for checking updates in the background."""
    update_available = Signal(dict)
    error_occurred = Signal(str)
    finished = Signal()
    progress_updated = Signal(int, str)

    def __init__(self):
        """Initialize the update checker."""
        super().__init__()
        self._is_running = False

    def check_for_updates(self):
        """Check for updates."""
        self._is_running = True
        try:
            self.progress_updated.emit(10, self.tr("Checking for updates..."))
            
            # Get current version
            current_version = get_version()
            self.progress_updated.emit(30, self.tr("Checking latest version..."))
            
            # Get latest version info
            latest_info = get_latest_version_info()
            
            if not latest_info or 'version' not in latest_info:
                self.error_occurred.emit(self.tr("Failed to get version information"))
                return
                
            self.progress_updated.emit(70, self.tr("Preparing update information..."))
            
            # Compare versions
            latest_version = latest_info.get('version')
            is_update_available = latest_version != current_version
            
            # Prepare update info
            update_info = {
                'current_version': current_version,
                'latest_version': latest_version,
                'is_update_available': is_update_available,
                'release_notes': latest_info.get('release_notes', ''),
                'download_url': latest_info.get('download_url', 'https://github.com/Nsfr750/clamav-gui/releases/latest')
            }
            
            self.progress_updated.emit(90, self.tr("Update check complete"))
            self.update_available.emit(update_info)
            
        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            self.error_occurred.emit(str(e))
        finally:
            self._is_running = False
            self.finished.emit()
            self.progress_updated.emit(100, self.tr("Done"))

class UpdatesDialog(QDialog):
    """Dialog for checking and displaying updates."""
    
    def __init__(self, parent=None):
        """Initialize the updates dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(self.tr("Check for Updates"))
        self.setMinimumSize(500, 400)
        
        # Initialize UI
        self.init_ui()
        
        # Initialize update checker
        self.update_checker = UpdateChecker()
        self.update_thread = QThread()
        self.update_checker.moveToThread(self.update_thread)
        
        # Connect signals
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.error_occurred.connect(self.on_error_occurred)
        self.update_checker.finished.connect(self.update_thread.quit)
        self.update_checker.progress_updated.connect(self.on_progress_updated)
        
        # Start the update check
        self.check_for_updates()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel(self.tr("Checking for updates..."))
        self.status_label.setWordWrap(True)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Release notes
        self.release_notes_label = QLabel(self.tr("Release Notes:"))
        self.release_notes = QTextBrowser()
        self.release_notes.setReadOnly(True)
        self.release_notes.setOpenExternalLinks(True)
        
        # Update button
        self.update_button = QPushButton(self.tr("Download Update"))
        self.update_button.clicked.connect(self.download_update)
        self.update_button.setVisible(False)
        
        # Close button
        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.clicked.connect(self.close)
        
        # Button box
        button_box = QDialogButtonBox()
        button_box.addButton(self.update_button, QDialogButtonBox.ActionRole)
        button_box.addButton(self.close_button, QDialogButtonBox.RejectRole)
        
        # Add widgets to layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.release_notes_label)
        layout.addWidget(self.release_notes)
        layout.addWidget(button_box)
    
    def check_for_updates(self):
        """Start the update check process."""
        if not self.update_thread.isRunning():
            self.update_thread.started.connect(self.update_checker.check_for_updates)
            self.update_thread.start()
    
    def on_update_available(self, update_info):
        """Handle update available signal.
        
        Args:
            update_info: Dictionary containing update information
        """
        current_version = update_info.get('current_version', 'unknown')
        latest_version = update_info.get('latest_version', 'unknown')
        is_update_available = update_info.get('is_update_available', False)
        release_notes = update_info.get('release_notes', '')
        
        if is_update_available:
            self.status_label.setText(
                self.tr("A new version is available!\n")
                + self.tr("Current version: {}\n").format(current_version)
                + self.tr("Latest version: {}").format(latest_version)
            )
            self.update_button.setVisible(True)
        else:
            self.status_label.setText(
                self.tr("You are using the latest version.\n")
                + self.tr("Version: {}").format(current_version)
            )
            self.update_button.setVisible(False)
        
        # Display release notes
        if release_notes:
            self.release_notes.setHtml(release_notes)
        else:
            self.release_notes.setPlainText(
                self.tr("No release notes available.")
            )
    
    def on_error_occurred(self, error_message):
        """Handle error signal.
        
        Args:
            error_message: Error message
        """
        self.status_label.setText(
            self.tr("Error checking for updates: {}").format(error_message)
        )
        self.update_button.setVisible(False)
    
    def on_progress_updated(self, value, message):
        """Update progress bar and status.
        
        Args:
            value: Progress value (0-100)
            message: Status message
        """
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
    
    def download_update(self):
        """Open the download URL in the default browser."""
        url = "https://github.com/Nsfr750/clamav-gui/releases/latest"
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(
                self,
                self.tr("Open URL Failed"),
                self.tr("Could not open the download page. Please visit: {}").format(url)
            )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.update_thread.isRunning():
            self.update_thread.quit()
            self.update_thread.wait()
        super().closeEvent(event)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = UpdatesDialog()
    dialog.show()
    sys.exit(app.exec())
