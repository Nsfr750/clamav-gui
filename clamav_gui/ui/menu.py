"""
Menu bar for the ClamAV GUI application.
"""
import logging
from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox
from PySide6.QtCore import Signal, QUrl, Slot
from PySide6.QtGui import QDesktopServices, QAction

# Setup logger
logger = logging.getLogger(__name__)

class ClamAVMenuBar(QMenuBar):
    """Main menu bar for the ClamAV GUI application."""
    
    # Signals
    help_requested = Signal()
    about_requested = Signal()
    sponsor_requested = Signal()
    update_check_requested = Signal()
    language_changed = Signal(str)  # Signal emitted when language changes
    
    def __init__(self, parent=None):
        """Initialize the menu bar."""
        super().__init__(parent)
        self.lang_manager = None
        self.settings = None
        self.current_settings = {}
        self.UpdatesDialog = None
        self.language_menu = QMenu(self.tr("&Language"), self)  # Initialize language menu
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the menu bar UI components."""
        
        # File menu
        file_menu = self.addMenu(self.tr("&File"))
        
        # Add menu items
        exit_action = QAction(self.tr("E&xit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.parent().close)  # Close the parent window
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = self.addMenu(self.tr("&Tools"))
        
        # Check for updates action
        check_updates_action = QAction(self.tr("Check for &Updates..."), self)
        check_updates_action.triggered.connect(self.check_for_updates)
        tools_menu.addAction(check_updates_action)
        
        # Add language menu to menu bar
        self.addMenu(self.language_menu)

        # Help menu
        help_menu = self.addMenu(self.tr("&Help"))
        
        # Help action
        help_action = QAction(self.tr("&Help"), self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction(self.tr("&About"), self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        # Sponsor action
        sponsor_action = QAction(self.tr("&Sponsor"), self)
        sponsor_action.triggered.connect(self.show_sponsor_dialog)
        help_menu.addAction(sponsor_action)
        
        # Wiki action
        wiki_action = QAction(self.tr("&Wiki"), self)
        wiki_action.triggered.connect(self.open_wiki)
        help_menu.addAction(wiki_action)
        
        # Import here to avoid circular imports
        try:
            from .updates_ui import UpdatesDialog
            self.UpdatesDialog = UpdatesDialog
        except ImportError as e:
            logger.warning(f"Could not import UpdatesDialog: {e}")
    
    @Slot()
    def open_wiki(self):
        """Open the ClamAV GUI wiki in the default web browser."""
        wiki_url = QUrl("https://github.com/Nsfr750/clamav-gui/wiki")
        QDesktopServices.openUrl(wiki_url)
    
    @Slot()    
    def check_for_updates(self):
        """Open the updates dialog to check for new versions."""
        if self.UpdatesDialog:
            dialog = self.UpdatesDialog(self)
            dialog.exec_()
    
    def set_language_manager(self, lang_manager):
        """Set the language manager and initialize language menu."""
        self.lang_manager = lang_manager
        self.setup_language_menu()
        
    def show_about_dialog(self):
        """Show the About dialog."""
        if not hasattr(self, 'lang_manager') or self.lang_manager is None:
            QMessageBox.warning(self, "Error", "Language manager not initialized")
            return
            
        from .about import AboutDialog
        dialog = AboutDialog(self, self.lang_manager)
        dialog.exec_()
        
    def show_help_dialog(self):
        """Show the Help dialog."""
        try:
            if not hasattr(self, 'lang_manager') or self.lang_manager is None:
                QMessageBox.warning(self, "Error", "Language manager not initialized")
                return
                
            from .help import HelpDialog
            dialog = HelpDialog(self)  # HelpDialog only expects parent parameter
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing help dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open help: {str(e)}")
        from .help import HelpDialog
        dialog.exec_()
        
    def show_sponsor_dialog(self):
        """Show the sponsor dialog."""
        try:
            if not hasattr(self, 'lang_manager') or not self.lang_manager:
                logger.error("Language manager not initialized")
                return

            from .sponsor import SponsorDialog
            dialog = SponsorDialog(parent=self, language_manager=self.lang_manager)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing sponsor dialog: {e}")
            QMessageBox.critical(
                self,
                self.tr("Error") if hasattr(self, 'tr') else "Error",
                self.tr("Failed to open sponsor dialog: {}").format(str(e)) if hasattr(self, 'tr') else f"Failed to open sponsor dialog: {e}"
            )
    
    def set_settings(self, settings):
        """Set the settings instance."""
        self.settings = settings
        if hasattr(settings, 'load_settings'):
            self.current_settings = settings.load_settings() or {}
    
    def setup_language_menu(self):
        """Set up the language selection menu with only available languages."""
        if not self.lang_manager or not hasattr(self.lang_manager, 'available_languages'):
            logger.warning("Language manager not set or invalid")
            return
            
        # Clear existing actions
        self.language_menu.clear()
        
        # Make the menu exclusive (like a radio button group)
        self.language_menu.setToolTipsVisible(True)
        
        # Add only available languages that have translations
        for lang_code, lang_name in self.lang_manager.available_languages.items():
            # Only add languages that have actual translations
            if hasattr(self.lang_manager, 'is_language_available') and \
               not self.lang_manager.is_language_available(lang_code):
                continue
                
            action = self.language_menu.addAction(lang_name, self.change_language)
            action.setCheckable(True)
            action.setData(lang_code)
            
            # Check current language
            if hasattr(self.lang_manager, 'current_lang') and \
               lang_code == self.lang_manager.current_lang:
                action.setChecked(True)
    
    @Slot()
    def change_language(self):
        """Change the application language."""
        action = self.sender()
        if not action or not hasattr(self, 'lang_manager') or not self.lang_manager:
            return
            
        lang_code = action.data()
        if not lang_code:
            return
            
        # Set the language
        if hasattr(self.lang_manager, 'set_language'):
            if self.lang_manager.set_language(lang_code):
                logger.info(f"Language changed to {lang_code}")
                self.language_changed.emit(lang_code)
                
                # Save language preference
                self.current_settings['language'] = lang_code
                if self.settings and hasattr(self.settings, 'save_settings'):
                    self.settings.save_settings(self.current_settings)
            
            # Save language preference
            if not hasattr(self, 'current_settings'):
                self.current_settings = {}
            self.current_settings['language'] = lang_code
            self.settings.save_settings(self.current_settings)
    
    def retranslate_ui(self):
        """Retranslate the UI when language changes."""
        if not hasattr(self, 'lang_manager') or not self.lang_manager:
            return
            
        try:
            # Update window title
            self.setWindowTitle(self.tr("ClamAV GUI"))
            
            # Update menu bar
            self.file_menu.setTitle(self.tr("&File"))
            self.tools_menu.setTitle(self.tr("&Tools"))
            self.help_menu.setTitle(self.tr("&Help"))
            self.language_menu.setTitle(self.tr("&Language"))
            
            # Update menu actions
            self.exit_action.setText(self.tr("E&xit"))
            self.check_updates_action.setText(self.tr("Check for &Updates..."))
            self.help_action.setText(self.tr("&Help"))
            self.about_action.setText(self.tr("&About"))
            self.sponsor_action.setText(self.tr("&Support the Project"))
            
            # Update tab names
            if hasattr(self, 'tabs'):
                self.tabs.setTabText(0, self.tr("Scan"))
                self.tabs.setTabText(1, self.tr("Update"))
                self.tabs.setTabText(2, self.tr("Settings"))
                self.tabs.setTabText(3, self.tr("Config Editor"))
            
            # Update status bar
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(self.tr("Ready"))
            
        except Exception as e:
            logger.error(f"Error retranslating UI: {e}")
