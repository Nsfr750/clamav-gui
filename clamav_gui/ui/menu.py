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
        self._initialized = False
        self.lang_manager = None
        self.settings = None
        self.current_settings = {}
        self.UpdatesDialog = None
        
        # Initialize menu references
        self.file_menu = None
        self.tools_menu = None
        self.help_menu = None
        self.language_menu = None
        
        # Setup the UI
        self.setup_ui()
        self._initialized = True
    
    def setup_ui(self):
        """Set up the menu bar UI components."""
        # Store references to menus as instance variables
        self.file_menu = self.addMenu(self.tr("&File"))
        
        # Add menu items
        self.exit_action = QAction(self.tr("E&xit"), self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.parent().close)  # Close the parent window
        self.file_menu.addAction(self.exit_action)
        
        # Tools menu
        self.tools_menu = self.addMenu(self.tr("&Tools"))
        
        # Check for updates action
        self.check_updates_action = QAction(self.tr("Check for &Updates..."), self)
        self.check_updates_action.triggered.connect(self.check_for_updates)
        self.tools_menu.addAction(self.check_updates_action)
        
        # Create language menu (will be populated later)
        self.language_menu = QMenu(self.tr("&Language"), self)
        
        # Help menu
        self.help_menu = self.addMenu(self.tr("&Help"))
        
        # Help action
        self.help_action = QAction(self.tr("&Help"), self)
        self.help_action.setShortcut("F1")
        self.help_action.triggered.connect(self.show_help_dialog)
        self.help_menu.addAction(self.help_action)
        
        self.help_menu.addSeparator()
        
        # About action
        self.about_action = QAction(self.tr("&About"), self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.help_menu.addAction(self.about_action)
        
        # Sponsor action
        self.sponsor_action = QAction(self.tr("&Sponsor"), self)
        self.sponsor_action.triggered.connect(self.show_sponsor_dialog)
        self.help_menu.addAction(self.sponsor_action)
        
        # View Logs action
        self.view_logs_action = QAction(self.tr("View &Logs"), self)
        self.view_logs_action.triggered.connect(self.show_logs_dialog)
        self.help_menu.addAction(self.view_logs_action)

        # Wiki action
        self.wiki_action = QAction(self.tr("&Wiki"), self)
        self.wiki_action.triggered.connect(self.open_wiki)
        self.help_menu.addAction(self.wiki_action)
        
        # Add language menu to menu bar after it's fully initialized
        self.addMenu(self.language_menu)
        
        # Import here to avoid circular imports
        try:
            from .updates_ui import UpdatesDialog
            self.UpdatesDialog = UpdatesDialog
        except ImportError as e:
            logger.warning(f"Could not import UpdatesDialog: {e}")
    
    def open_wiki(self):
        """Open the ClamAV GUI wiki in the default web browser."""
        wiki_url = QUrl("https://github.com/Nsfr750/clamav-gui/wiki")
        QDesktopServices.openUrl(wiki_url)
    
    @Slot()
    def check_for_updates(self):
        """Check for application updates."""
        if self.UpdatesDialog:
            dialog = self.UpdatesDialog(self)
            dialog.exec_()
    
    def set_language_manager(self, lang_manager):
        """Set the language manager for the menu bar."""
        # Disconnect from previous language manager if it exists
        if hasattr(self, 'lang_manager') and self.lang_manager is not None:
            try:
                if (hasattr(self.lang_manager, 'language_changed') and 
                    hasattr(self.lang_manager.language_changed, 'disconnect')):
                    try:
                        self.lang_manager.language_changed.disconnect(self.retranslate_ui)
                    except (TypeError, RuntimeError, AttributeError) as e:
                        # Signal was not connected or other error occurred
                        logger.debug(f"Could not disconnect signal: {e}")
            except Exception as e:
                logger.warning(f"Error disconnecting from previous language manager: {e}")
        
        # Set the new language manager
        self.lang_manager = lang_manager
        
        # Connect to the language change signal if manager is valid
        if (self.lang_manager is not None and 
            hasattr(self.lang_manager, 'language_changed') and 
            hasattr(self.lang_manager.language_changed, 'connect')):
            try:
                self.lang_manager.language_changed.connect(self.retranslate_ui)
                logger.debug("Connected to language change signal")
                
                # Setup the language menu after setting the language manager
                self.setup_language_menu()
                
                # Connect the language menu's triggered signal
                if hasattr(self, 'language_menu') and self.language_menu:
                    try:
                        # Disconnect only if we connected before, and disconnect the specific slot
                        if getattr(self, '_lang_menu_signal_connected', False):
                            try:
                                self.language_menu.triggered.disconnect(self.on_language_selected)
                            except Exception:
                                pass
                        # Connect the signal
                        self.language_menu.triggered.connect(self.on_language_selected)
                        self._lang_menu_signal_connected = True
                        logger.debug("Connected language menu triggered signal")
                    except Exception as e:
                        logger.error(f"Failed to connect language menu signal: {e}")
                
            except Exception as e:
                logger.error(f"Failed to connect to language change signal: {e}", exc_info=True)
        else:
            logger.warning("Language manager does not have a connectable 'language_changed' signal")
            
    def is_widget_valid(self, widget):
        """Check if a widget is still valid (not deleted)."""
        try:
            # Try to access a property to see if the object is still valid
            return (widget is not None and 
                   hasattr(widget, 'isWidgetType') and 
                   widget.isWidgetType())
        except RuntimeError:
            return False
            
    def retranslate_ui(self, language_code=None):
        """Retranslate the UI when the language changes.
        
        Args:
            language_code: The new language code (optional, will use current language if not provided)
        """
        # Skip if the widget is being destroyed or not visible
        if (not hasattr(self, '_initialized') or not self._initialized or 
                not hasattr(self, 'lang_manager') or self.lang_manager is None or
                not hasattr(self, 'isVisible') or not self.isVisible()):
            return
            
        # Don't proceed if the widget is being destroyed
        if not self.is_widget_valid(self):
            logger.debug("Skipping retranslate - widget is being destroyed")
            return
            
        try:
            logger.debug(f"Retranslating UI to language: {language_code or getattr(self.lang_manager, 'current_lang', 'unknown')}")
            
            # Helper function to safely set text on an action
            def safe_set_text(action, text):
                try:
                    if action is not None and hasattr(action, 'setText') and text is not None:
                        action.setText(text)
                        return True
                except RuntimeError:
                    logger.warning("Failed to set text on action - object may have been deleted")
                return False
            
            # Update menu titles with safe defaults
            if hasattr(self, 'file_menu') and self.is_widget_valid(self.file_menu):
                self.file_menu.setTitle(getattr(self.lang_manager, 'tr', lambda x: x)("menu.file") or "&File")
            if hasattr(self, 'tools_menu') and self.is_widget_valid(self.tools_menu):
                self.tools_menu.setTitle(getattr(self.lang_manager, 'tr', lambda x: x)("menu.tools") or "&Tools")
            if hasattr(self, 'help_menu') and self.is_widget_valid(self.help_menu):
                self.help_menu.setTitle(getattr(self.lang_manager, 'tr', lambda x: x)("menu.help") or "&Help")
            if hasattr(self, 'language_menu') and self.is_widget_valid(self.language_menu):
                self.language_menu.setTitle(getattr(self.lang_manager, 'tr', lambda x: x)("menu.language") or "&Language")
            
            # Update menu actions
            safe_set_text(getattr(self, 'exit_action', None), self.lang_manager.tr("E&xit") or "E&xit")
            safe_set_text(getattr(self, 'check_updates_action', None), self.lang_manager.tr("Check for &Updates...") or "Check for &Updates...")
            safe_set_text(getattr(self, 'help_action', None), self.lang_manager.tr("&Help") or "&Help")
            safe_set_text(getattr(self, 'about_action', None), self.lang_manager.tr("&About") or "&About")
            safe_set_text(getattr(self, 'sponsor_action', None), self.lang_manager.tr("&Sponsor") or "&Sponsor")
            safe_set_text(getattr(self, 'wiki_action', None), self.lang_manager.tr("&Wiki") or "&Wiki")
                
            # Update language menu items
            if (hasattr(self, 'language_menu') and 
                self.is_widget_valid(self.language_menu) and 
                hasattr(self.lang_manager, 'available_languages')):
                try:
                    # Store current language before clearing
                    current_lang = getattr(self.lang_manager, 'current_lang', 'en')
                    
                    # Clear existing actions
                    self.language_menu.clear()
                    
                    # Get available languages safely
                    languages = getattr(self.lang_manager, 'available_languages', {})
                    if callable(languages):
                        try:
                            languages = languages() or {}
                        except:
                            languages = {}
                    
                    # Add language actions
                    for lang_code, lang_name in languages.items():
                        try:
                            action = self.language_menu.addAction(str(lang_name))
                            if action:  # Ensure action was created
                                action.setCheckable(True)
                                action.setChecked(str(lang_code) == str(current_lang))
                                action.setData(str(lang_code))
                                # Store language code as an attribute for easier access
                                action.language_code = str(lang_code)
                        except Exception as e:
                            logger.error(f"Error adding language {lang_code}: {e}")
                    
                    # If no languages were added, add a default English option
                    if not self.language_menu.actions():
                        try:
                            action = self.language_menu.addAction("English")
                            action.setCheckable(True)
                            action.setChecked(True)
                            action.setData('en')
                            action.language_code = 'en'
                        except Exception as e:
                            logger.error(f"Error adding default language: {e}")
                            
                except Exception as e:
                    logger.error(f"Error updating language menu: {e}", exc_info=True)
            
            # Force update the menu if it's still valid
            if self.is_widget_valid(self):
                self.update()
            
            # Notify parent widget if it's still valid
            parent = self.parent()
            if (parent is not None and hasattr(parent, 'isWidgetType') and parent.isWidgetType() and 
                hasattr(parent, 'retranslate_ui')):
                try:
                    parent.retranslate_ui(language_code)
                except Exception as e:
                    logger.error(f"Error notifying parent of language change: {e}", exc_info=True)
                
            logger.debug("UI retranslation completed successfully")
            
        except Exception as e:
            logger.error(f"Error in retranslate_ui: {e}", exc_info=True)
        
    def show_about_dialog(self):
        """Show the About dialog."""
        try:
            if not hasattr(self, 'lang_manager') or self.lang_manager is None:
                QMessageBox.warning(self, "Error", "Language manager not initialized")
                return
                
            from .about import AboutDialog
            dialog = AboutDialog(self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to show about dialog: {str(e)}")
            
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
        
    def show_logs_dialog(self):
        """Show the Logs viewer dialog."""
        try:
            from .view_log import LogViewerDialog
            dialog = LogViewerDialog(self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing logs dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open logs viewer: {str(e)}")

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
        if (not self._initialized or 
                not hasattr(self, 'lang_manager') or 
                not self.lang_manager):
            logger.warning("Cannot setup language menu: Not initialized or language manager not set")
            return
            
        try:
            # Initialize language menu if it doesn't exist
            if not hasattr(self, 'language_menu') or not self.language_menu:
                self.language_menu = QMenu(self.tr("&Language"), self)
            
            # Block signals while updating the menu
            if hasattr(self.language_menu, 'blockSignals'):
                self.language_menu.blockSignals(True)
            
            # Clear existing actions and disconnect signals
            for action_item in self.language_menu.actions():
                try:
                    action_item.triggered.disconnect()
                except (TypeError, RuntimeError):
                    pass
            self.language_menu.clear()
            
            # Get available languages
            available_langs = getattr(self.lang_manager, 'available_languages', {})
            if not available_langs:
                logger.warning("No available languages found in language manager")
                return
            
            current_lang = getattr(self.lang_manager, 'current_lang', '')
            logger.debug(f"Setting up language menu. Current: {current_lang}, Available: {list(available_langs.items())}")
            
            # Add available languages
            for lang_code, lang_name in available_langs.items():
                try:
                    # Skip if language is not available
                    if hasattr(self.lang_manager, 'is_language_available') and \
                       not self.lang_manager.is_language_available(lang_code):
                        continue
                    
                    # Get translated language name if possible
                    display_name = getattr(self.lang_manager, 'tr', lambda x: x)(lang_name)
                    
                    # Create and configure action
                    action = self.language_menu.addAction(display_name)
                    action.setCheckable(True)
                    action.setData(lang_code)
                    action.setChecked(lang_code == current_lang)
                    action.triggered.connect(lambda checked, code=lang_code: self.on_language_selected(checked))
                    
                except Exception as e:
                    logger.error(f"Error adding language {lang_code}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error in setup_language_menu: {e}", exc_info=True)
            
        finally:
            # Always unblock signals when done
            if hasattr(self, 'language_menu') and hasattr(self.language_menu, 'blockSignals'):
                self.language_menu.blockSignals(False)
    
    @Slot()
    def on_language_selected(self, checked):
        """Handle language selection from the language menu.
        
        Args:
            checked (bool): Whether the action is checked.
        """
        if not checked:
            return
        
        # Initialize action to None to ensure it's always defined
        action = None
        lang_code = None
        
        try:
            # Safely get the sender action
            try:
                action = self.sender()
                if not action or not hasattr(action, 'isCheckable'):
                    logger.warning("Invalid action in language selection")
                    return
            except RuntimeError as e:
                logger.error(f"Failed to get sender action: {e}")
                return
            
            # Get the language code from the action
            try:
                # First try to get from our custom attribute
                if hasattr(action, 'language_code'):
                    lang_code = str(getattr(action, 'language_code', '')).strip()
                
                # Then try the data() method if we still don't have a code
                if not lang_code and hasattr(action, 'data') and callable(action.data):
                    try:
                        data = action.data()
                        if data:
                            if hasattr(data, 'isValid') and data.isValid() and hasattr(data, 'toString'):
                                lang_code = str(data.toString()).strip()
                            else:
                                lang_code = str(data).strip()
                    except Exception as e:
                        logger.debug(f"Could not get data from action: {e}")
                
                # Try direct data attribute as last resort
                if not lang_code and hasattr(action, 'data'):
                    lang_code = str(getattr(action, 'data', '')).strip()
                
                # If we still don't have a code, try to get from action text
                if not lang_code and hasattr(action, 'text'):
                    try:
                        lang_text = str(action.text()).strip().lower()
                        if lang_text:
                            # If we have a language manager, try to map text to code
                            if (hasattr(self, 'lang_manager') and 
                                hasattr(self.lang_manager, 'get_available_languages')):
                                try:
                                    languages = self.lang_manager.get_available_languages()
                                    if callable(languages):
                                        languages = languages() or {}
                                    
                                    for code, name in languages.items():
                                        if str(name).lower() == lang_text:
                                            lang_code = str(code)
                                            break
                                except Exception as e:
                                    logger.error(f"Error getting available languages: {e}")
                            
                            # If no match found, use text as code
                            if not lang_code:
                                lang_code = lang_text
                    except Exception as e:
                        logger.error(f"Error getting text from action: {e}")
                
                if not lang_code:
                    logger.warning("Could not determine language code from action")
                    return
                    
                logger.info(f"Attempting to change language to: {lang_code}")
                
                # Update the language using the language manager
                if hasattr(self, 'lang_manager') and hasattr(self.lang_manager, 'set_language'):
                    # Set the new language
                    success = self.lang_manager.set_language(lang_code)
                    if not success:
                        logger.error(f"Failed to set language to {lang_code}")
                        return
                    
                    logger.info(f"Language successfully changed to: {lang_code}")
                    
                    # Save the language preference if settings are available
                    if hasattr(self, 'settings') and hasattr(self.settings, 'setValue'):
                        try:
                            self.settings.setValue("language", lang_code)
                            logger.debug(f"Saved language preference: {lang_code}")
                        except Exception as e:
                            logger.error(f"Failed to save language preference: {e}", exc_info=True)
                    
                    # Emit the language changed signal if available
                    if hasattr(self, 'language_changed') and callable(self.language_changed):
                        try:
                            self.language_changed.emit(lang_code)
                        except Exception as e:
                            logger.error(f"Error emitting language_changed signal: {e}", exc_info=True)
                    
                    # Update the UI
                    self.retranslate_ui()
                    
                    # Update the checked state of all language actions
                    if hasattr(self, 'language_menu') and hasattr(self.language_menu, 'actions'):
                        for act in self.language_menu.actions():
                            if hasattr(act, 'isCheckable') and act.isCheckable():
                                if hasattr(act, 'data') and callable(act.data):
                                    act.setChecked(act.data() == lang_code)
                                elif hasattr(act, 'data'):
                                    act.setChecked(str(act.data) == lang_code)
                    
                    # Update menu actions
                    if hasattr(self, 'exit_action'):
                        self.exit_action.setText(self.tr("E&xit"))
                    if hasattr(self, 'check_updates_action'):
                        self.check_updates_action.setText(self.tr("Check for &Updates..."))
                    if hasattr(self, 'help_action'):
                        self.help_action.setText(self.tr("&Help"))
                    if hasattr(self, 'about_action'):
                        self.about_action.setText(self.tr("&About"))
                    if hasattr(self, 'sponsor_action'):
                        self.sponsor_action.setText(self.tr("&Support the Project"))
                    
                    # Update tab names if they exist
                    if hasattr(self, 'tabs') and hasattr(self.tabs, 'setTabText'):
                        try:
                            self.tabs.setTabText(0, self.tr("Scan"))
                            self.tabs.setTabText(1, self.tr("Update"))
                            self.tabs.setTabText(2, self.tr("Settings"))
                            self.tabs.setTabText(3, self.tr("Config Editor"))
                        except Exception as e:
                            logger.error(f"Error updating tab names: {e}")
                    
                    # Update status bar if it exists
                    if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'showMessage'):
                        try:
                            self.status_bar.showMessage(self.tr("Ready"))
                        except Exception as e:
                            logger.error(f"Error updating status bar: {e}")
                else:
                    logger.warning("Language manager not available or doesn't support set_language")
                    
            except Exception as e:
                logger.error(f"Error processing language change: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Unexpected error in on_language_selected: {e}", exc_info=True)

    def __del__(self):
        """Cleanup resources when the object is being destroyed."""
        # Disconnect all signals to prevent memory leaks
        if hasattr(self, 'language_menu') and hasattr(self.language_menu, 'blockSignals'):
            try:
                self.language_menu.blockSignals(True)
            except RuntimeError:
                pass
