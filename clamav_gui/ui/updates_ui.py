"""
Update UI for ClamAV GUI.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox, 
    QDialogButtonBox, QProgressDialog, QApplication, QTextBrowser, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QUrl
from PySide6.QtGui import QIcon, QDesktopServices

import logging
import webbrowser

from clamav_gui.utils.updates import UpdateChecker
from clamav_gui.lang.lang_manager import SimpleLanguageManager

logger = logging.getLogger(__name__)

class UpdatesDialog(QDialog):
    """Dialog for checking and applying updates."""
    
    def __init__(self, parent=None, current_version="1.0.0"):
        super().__init__(parent)
        self.current_version = current_version
        self.setWindowTitle(self.tr("Check for Updates"))
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel(self.tr("Checking for updates..."))
        layout.addWidget(self.status_label)
        
        # Update info
        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(True)
        layout.addWidget(self.info_browser)
        
        # Buttons
        self.button_box = QDialogButtonBox()
        self.update_button = QPushButton(self.tr("Update Now"))
        self.update_button.setVisible(False)
        self.update_button.clicked.connect(self.download_update)
        
        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.clicked.connect(self.close)
        
        self.button_box.addButton(self.update_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(self.close_button, QDialogButtonBox.ButtonRole.RejectRole)
        
        # Start checking for updates
        self.check_for_updates()
    
    def check_for_updates(self):
        """Check for updates."""
        try:
            import clamav_gui
            self.checker = UpdateChecker(current_version=clamav_gui.__version__)
            self.checker.update_available.connect(self.on_update_available)
            self.checker.no_update_available.connect(self.on_no_update_available)
            self.checker.error_occurred.connect(self.on_error)  # Changed to on_error to match the actual method name
            self.checker.start()
        except Exception as e:
            logger.error(f"Error initializing update checker: {e}")
            self.on_error(str(e))  # Changed to on_error to match the actual method name
    
    def on_update_available(self, version, release_notes, download_url):
        """Handle when an update is available."""
        self.status_label.setText(self.tr(f"Version {version} is available! (Current: {self.current_version})"))
        self.info_browser.setHtml(release_notes)
        self.update_button.setVisible(True)
        self.download_url = download_url
    
    def on_no_update_available(self):
        """Handle when no update is available."""
        self.status_label.setText(self.tr("You have the latest version."))
        self.info_browser.setPlainText(self.tr("No updates are currently available."))
    
    def on_error(self, error_message):
        """Handle errors during update check."""
        self.status_label.setText(self.tr("Error checking for updates"))
        self.info_browser.setPlainText(error_message)
    
    def download_update(self):
        """Open the download URL in the default web browser."""
        if hasattr(self, 'download_url'):
            QDesktopServices.openUrl(QUrl(self.download_url))

class UpdateDialog(QDialog):
    """Dialog for showing update information and options."""
    
    def __init__(self, update_info: dict, parent=None):
        """Initialize the update dialog.
        
        Args:
            update_info: Dictionary containing update information.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.update_info = update_info
        self.lang_manager = SimpleLanguageManager()
        self.setup_ui()
        self.retranslate_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        self.setWindowTitle(self.tr("Update Available"))
        self.setWindowIcon(QIcon(":/icons/update.png"))
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Update available message
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setOpenExternalLinks(True)
        
        # Changelog
        self.changelog_label = QLabel()
        self.changelog_label.setWordWrap(True)
        self.changelog_label.setOpenExternalLinks(True)
        
        # Don't ask again checkbox
        self.dont_ask_checkbox = QCheckBox()
        
        # Buttons
        self.button_box = QDialogButtonBox()
        self.update_button = QPushButton()
        self.later_button = QPushButton()
        self.skip_button = QPushButton()
        
        self.button_box.addButton(self.update_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(self.later_button, QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.addButton(self.skip_button, QDialogButtonBox.ButtonRole.DestructiveRole)
        
        # Connect signals
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.skip_button.clicked.connect(self.skip_update)
        
        # Add widgets to layout
        layout.addWidget(self.message_label)
        layout.addWidget(self.changelog_label)
        layout.addWidget(self.dont_ask_checkbox)
        layout.addWidget(self.button_box)
        
        # Set initial state
        self.update_ui()
    
    def retranslate_ui(self):
        """Update the UI text based on the current language."""
        self.setWindowTitle(self.tr("Update Available"))
        self.update_button.setText(self.tr("Update Now"))
        self.later_button.setText(self.tr("Remind Me Later"))
        self.skip_button.setText(self.tr("Skip This Version"))
        self.dont_ask_checkbox.setText(self.tr("Don't ask again for this version"))
    
    def update_ui(self):
        """Update the UI with the latest update information."""
        if not self.update_info:
            return
            
        current_version = self.update_info.get('current_version', '1.0.0')
        latest_version = self.update_info.get('latest_version', '1.0.0')
        release_notes = self.update_info.get('release_notes', '')
        download_url = self.update_info.get('download_url', '#')
        
        # Set message
        message = self.tr(
            "A new version of ClamAV GUI is available!\n\n"
            "Current version: {current_version}\n"
            "Latest version: {latest_version}\n"
            "<a href='{download_url}'>Download now</a>"
        ).format(
            current_version=current_version,
            latest_version=latest_version,
            download_url=download_url
        )
        
        self.message_label.setText(message)
        
        # Set changelog
        changelog = self.tr("<b>What's new:</b><br>")
        if release_notes:
            changelog += release_notes.replace('\n', '<br>')
        else:
            changelog += self.tr("No release notes available.")
            
        self.changelog_label.setText(changelog)
    
        """Skip this version of the update."""
        self.done(2)  # Custom return code for skip


def check_for_updates(parent=None, current_version: str = "1.0.0", force_check: bool = False):
    """Check for updates and show a dialog if an update is available.
    
    Args:
        parent: Parent window for dialogs.
        current_version: Current application version.
        force_check: If True, skip the cache and force a check.
    """
    try:
        # Create a progress dialog
        progress = QProgressDialog(
            parent.tr("Checking for updates..."),
            parent.tr("Cancel"),
            0, 0, parent
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(1000)
        progress.setValue(0)
        progress.setMaximum(0)  # Indeterminate progress
        progress.canceled.connect(progress.close)

        # Create and configure the update checker
        checker = UpdateChecker(current_version=current_version)
        
        # Connect signals
        def on_update_available(version, release_notes, download_url):
            try:
                progress.close()
                dialog = UpdatesDialog(parent, current_version)
                dialog.on_update_available(version, release_notes, download_url)
                result = dialog.exec()
                
                if result == 2:  # Skip this version
                    checker.skip_version(version)
            except Exception as e:
                logger.error(f"Error in update available handler: {e}", exc_info=True)
        
        def on_no_update_available():
            try:
                progress.close()
                if force_check:
                    QMessageBox.information(
                        parent,
                        parent.tr("No Updates"),
                        parent.tr("You are using the latest version of ClamAV GUI.")
                    )
            except Exception as e:
                logger.error(f"Error in no update handler: {e}", exc_info=True)
        
        def on_error(error_msg):
            try:
                progress.close()
                QMessageBox.warning(
                    parent,
                    parent.tr("Update Error"),
                    parent.tr(f"Error checking for updates: {error_msg}")
                )
            except Exception as e:
                logger.error(f"Error in error handler: {e}", exc_info=True)
        
        # Connect signals
        checker.update_available.connect(on_update_available)
        checker.no_update_available.connect(on_no_update_available)
        checker.error_occurred.connect(on_error)
        
        # Start the update check
        checker.start()
        
        # Show the progress dialog
        progress.show()
        
    except Exception as e:
        logger.error(f"Error checking for updates: {e}", exc_info=True)
        if force_check:
            QMessageBox.critical(
                parent,
                parent.tr("Update Error"),
                parent.tr("An error occurred while checking for updates. Please try again later.")
            )
