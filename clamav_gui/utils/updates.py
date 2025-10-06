"""
Update checking functionality for the PDF finder application.
"""
import logging
from typing import Optional, Tuple, Callable, Dict, Any
import requests
import json
from pathlib import Path
import os
from datetime import datetime, timedelta

# PySide6 imports
from PySide6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox, QDialogButtonBox,
    QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QObject

# Import language manager
from clamav_gui.lang.lang_manager import SimpleLanguageManager

# Get the application directory (project root)
APP_DIR = Path(__file__).parent.parent.parent

# Ensure config directory exists
CONFIG_DIR = APP_DIR / 'config'
CONFIG_DIR.mkdir(exist_ok=True)
UPDATES_FILE = CONFIG_DIR / 'updates.json'

# Configure logger
logger = logging.getLogger(__name__)

class UpdateWorker(QObject):
    """Worker class for running the update check in a separate thread."""
    finished = Signal()
    result = Signal(dict, bool)
    error = Signal(str)
    
    def __init__(self, checker):
        super().__init__()
        self.checker = checker
    
    def run(self):
        """Run the update check."""
        try:
            update_available, update_info = self.checker._check_for_updates()
            self.result.emit(update_info, update_available)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class UpdateChecker(QObject):
    """Handles checking for application updates."""
    
    # Signal emitted when update check is complete
    update_check_complete = Signal(dict, bool)
    
    # Signal emitted when an update is available
    update_available = Signal(dict)  # dict contains update information
    
    # Signal emitted when no update is available
    no_update_available = Signal()
    
    # Signal emitted when an error occurs during update check
    error_occurred = Signal(str)  # str contains error message
    
    def __init__(self, current_version: str, config_path: Optional[Path] = None):
        """Initialize the update checker.
        
        Args:
            current_version: The current version of the application.
            config_path: Path to the configuration file (optional).
        """
        super().__init__()
        self.current_version = current_version
        self.config_path = config_path or UPDATES_FILE
        self.config = self._load_config()
        self.update_url = "https://api.github.com/repos/Nsfr750/clamav-gui/releases/latest"
    
    def _load_config(self) -> dict:
        """Load the update configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading update config: {e}")
        return {
            'last_checked': None,
            'last_version': None,
            'dont_ask_until': None
        }
    
    def _save_config(self):
        """Save the update configuration."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving update config: {e}")
    
    def start(self, force: bool = False):
        """Start the update check in a separate thread."""
        self.thread = QThread()
        self.worker = UpdateWorker(self)
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self._handle_result)
        self.worker.error.connect(self.error_occurred.emit)
        
        # Start the thread
        self.thread.start()
    
    def _handle_result(self, update_info, update_available):
        """Handle the result of the update check."""
        self.update_check_complete.emit(update_info, update_available)
        if update_available:
            self.update_available.emit(update_info)
        else:
            self.no_update_available.emit()
    
    def _check_for_updates(self) -> Tuple[bool, Optional[dict]]:
        """Internal method to check for updates."""
        return self.check_for_updates(force=True)
    
    def check_for_updates(self, force: bool = False) -> Tuple[bool, Optional[dict]]:
        """Check for updates.
        
        Args:
            force: If True, skip the cache and force a check.
            
        Returns:
            A tuple of (update_available, update_info).
            update_available is True if an update is available.
            update_info contains information about the update if available.
        """
        now = datetime.utcnow()
        
        # Check if we should skip the update check
        if not force and self.config.get('dont_ask_until'):
            try:
                dont_ask_until = datetime.fromisoformat(self.config['dont_ask_until'])
                if now < dont_ask_until:
                    logger.info("Skipping update check: user asked not to check until %s", 
                               self.config['dont_ask_until'])
                    return False, None
            except (ValueError, KeyError) as e:
                logger.warning("Error parsing don't ask until date: %s", e)
        
        # Check if we've checked recently (within 1 day)
        if not force and self.config.get('last_checked'):
            try:
                last_checked = datetime.fromisoformat(self.config['last_checked'])
                if (now - last_checked) < timedelta(days=1):
                    logger.info("Skipping update check: checked recently at %s", 
                               self.config['last_checked'])
                    return False, None
            except (ValueError, KeyError) as e:
                logger.warning("Error parsing last checked date: %s", e)
        
        # Update last checked time
        self.config['last_checked'] = now.isoformat()
        self._save_config()
        
        try:
            # Make the API request
            logger.info("Checking for updates...")
            response = requests.get(
                self.update_url,
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )
            response.raise_for_status()
            
            release_info = response.json()
            latest_version = release_info.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                logger.warning("No version information in release data")
                return False, None
            
            # Update last known version
            self.config['last_version'] = latest_version
            self._save_config()
            
            # Check if the latest version is newer than current
            if self._is_newer_version(latest_version, self.current_version):
                logger.info("Update available: %s (current: %s)", latest_version, self.current_version)
                return True, {
                    'version': latest_version,
                    'url': release_info.get('html_url', ''),
                    'changelog': release_info.get('body', ''),
                    'prerelease': release_info.get('prerelease', False),
                    'published_at': release_info.get('published_at', '')
                }
            else:
                logger.info("No updates available (current: %s, latest: %s)", 
                           self.current_version, latest_version)
                return False, None
                
        except requests.RequestException as e:
            logger.error("Error checking for updates: %s", e)
            return False, None
        except Exception as e:
            logger.exception("Unexpected error checking for updates: %s", e)
            return False, None
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Check if version1 is newer than version2."""
        try:
            from packaging import version
            return version.parse(version1) > version.parse(version2)
        except ImportError:
            # Fallback simple comparison if packaging is not available
            return version1 > version2
    
    def show_update_dialog(self, parent=None, update_info=None):
        """Show the update dialog.
        
        Args:
            parent: Parent widget for the dialog.
            update_info: Update information from check_for_updates().
        """
        if not update_info:
            return
            
        dialog = QDialog(parent)
        dialog.setWindowTitle("Update Available")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Add update message
        message = f"<b>Version {update_info['version']} is available!</b>"
        if update_info.get('prerelease'):
            message += " (Pre-release)"
        message += "<br><br>"
        
        if update_info.get('changelog'):
            # Limit changelog length
            changelog = update_info['changelog']
            if len(changelog) > 500:
                changelog = changelog[:497] + "..."
            message += f"<b>What's new:</b><br>{changelog}"
        
        label = QLabel(message)
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)
        
        # Add "Don't ask again" checkbox
        dont_ask_checkbox = QCheckBox("Don't ask me again for this version")
        layout.addWidget(dont_ask_checkbox)
        
        # Add buttons
        buttons = QDialogButtonBox()
        download_btn = buttons.addButton("Download", QDialogButtonBox.ButtonRole.AcceptRole)
        later_btn = buttons.addButton("Remind Me Later", QDialogButtonBox.ButtonRole.RejectRole)
        
        download_btn.clicked.connect(lambda: self._on_download_clicked(dialog, update_info['url']))
        later_btn.clicked.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Handle dialog result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dont_ask_checkbox.isChecked():
                # Set don't ask until next version
                self.config['dont_ask_until'] = None
                self._save_config()
        else:
            if dont_ask_checkbox.isChecked():
                # Set don't ask until tomorrow
                tomorrow = datetime.utcnow() + timedelta(days=1)
                self.config['dont_ask_until'] = tomorrow.isoformat()
                self._save_config()
    
    def _on_download_clicked(self, dialog, url):
        """Handle download button click."""
        try:
            import webbrowser
            webbrowser.open(url)
            dialog.accept()
        except Exception as e:
            logger.error("Error opening download URL: %s", e)
            QMessageBox.critical(
                dialog,
                "Error",
                f"Could not open the download page. Please visit {url} manually."
            )


def check_for_updates(parent=None, current_version: str = "1.0.0", force_check: bool = False):
    """Check for application updates and show a dialog if an update is available.
    
    Args:
        parent: Parent window for dialogs.
        current_version: Current application version.
        force_check: If True, skip the cache and force a check.
    """
    def show_update_dialog(update_info):
        checker.show_update_dialog(parent, update_info)
    
    def show_error(message):
        QMessageBox.warning(
            parent,
            "Update Check Failed",
            message,
            QMessageBox.StandardButton.Ok
        )
    
    # Create a progress dialog
    progress = QProgressDialog(
        "Checking for updates...",
        "Cancel",
        0,
        0,
        parent
    )
    progress.setWindowTitle("Checking for Updates")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setCancelButton(None)  # No cancel button for now
    progress.setMinimumDuration(1000)  # Show after 1 second if not done
    
    # Create and start the update checker
    checker = UpdateChecker(current_version)
    
    # Use a thread to avoid freezing the UI
    class UpdateThread(QThread):
        finished_signal = pyqtSignal(tuple)
        
        def run(self):
            try:
                result = checker.check_for_updates(force_check)
                self.finished_signal.emit(result)
            except Exception as e:
                logger.exception("Error in update thread: %s", e)
                self.finished_signal.emit((False, None))
    
    def on_finished(result):
        progress.close()
        update_available, update_info = result
        
        if update_available and update_info:
            show_update_dialog(update_info)
        elif force_check:
            QMessageBox.information(
                parent,
                "No Updates",
                "You are already using the latest version.",
                QMessageBox.StandardButton.Ok
            )
    
    thread = UpdateThread()
    thread.finished_signal.connect(on_finished)
    thread.start()
    
    # Keep the progress dialog open until the thread is done
    while thread.isRunning():
        QApplication.processEvents()
    
    return thread
