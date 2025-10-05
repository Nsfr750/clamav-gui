"""
Menu bar for the ClamAV GUI application.
"""
from PySide6.QtWidgets import QMenuBar, QMenu, QAction
from PySide6.QtCore import Signal, QUrl
from PySide6.QtGui import QDesktopServices

class ClamAVMenuBar(QMenuBar):
    """Main menu bar for the ClamAV GUI application."""
    
    # Signals
    help_requested = Signal()
    about_requested = Signal()
    sponsor_requested = Signal()
    update_check_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize the menu bar."""
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the menu bar UI."""
        # Create Help menu
        help_menu = self.addMenu('&Help')
        
        # Add actions
        help_action = help_menu.addAction('&Documentation')
        help_action.triggered.connect(self.help_requested.emit)
        
        # Add Wiki action that opens in default browser
        wiki_action = help_menu.addAction('&Wiki')
        wiki_action.triggered.connect(self.open_wiki)
        
        help_menu.addSeparator()
        
        about_action = help_menu.addAction('&About')
        about_action.triggered.connect(self.about_requested.emit)
        
        sponsor_action = help_menu.addAction('&Sponsor')
        sponsor_action.triggered.connect(self.sponsor_requested.emit)
        
        help_menu.addSeparator()
        
        # Add check for updates action
        update_action = help_menu.addAction('&Check for Updates...')
        update_action.triggered.connect(self.check_for_updates)
        
        # Import here to avoid circular imports
        from .updates_ui import UpdatesDialog
        self.UpdatesDialog = UpdatesDialog
    
    def open_wiki(self):
        """Open the ClamAV GUI wiki in the default web browser."""
        wiki_url = QUrl("https://github.com/Nsfr750/clamav-gui/wiki")
        QDesktopServices.openUrl(wiki_url)
        
    def check_for_updates(self):
        """Open the updates dialog to check for new versions."""
        dialog = self.UpdatesDialog(self)
        dialog.exec_()
