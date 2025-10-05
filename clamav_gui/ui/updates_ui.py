"""
Update UI for ClamAV GUI.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox, 
    QDialogButtonBox, QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QIcon

from ..utils.updates import UpdateChecker
from ..lang.lang_manager import SimpleLanguageManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

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
    
    def skip_update(self):
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
        # Create and configure the update checker
        checker = UpdateChecker(current_version=current_version)
        
        # Check for updates
        update_available, update_info = checker.check_for_updates(force=force_check)
        
        if not update_available:
            if force_check:
                QMessageBox.information(
                    parent,
                    parent.tr("No Updates"),
                    parent.tr("You are running the latest version of ClamAV GUI.")
                )
            return
        
        # Show update dialog
        dialog = UpdateDialog(update_info, parent)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # User wants to update
            pass  # Update logic will be handled by the main application
        elif result == 2:  # Skip this version
            checker.skip_version(update_info.get('latest_version'))
        
    except Exception as e:
        logger.error(f"Error checking for updates: {e}", exc_info=True)
        if force_check:
            QMessageBox.critical(
                parent,
                parent.tr("Update Error"),
                parent.tr("An error occurred while checking for updates. Please try again later.")
            )
