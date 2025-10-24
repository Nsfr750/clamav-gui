"""
Help Dialog Module

This module provides a help dialog for the ClamAV GUI application.
It includes support for multiple languages and a clean, modern interface.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QPushButton, QWidget, QFrame, QLabel, QTabWidget,
    QApplication, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, Signal, QSize
from PySide6.QtGui import QDesktopServices, QFont, QTextCursor

import os
import sys
import logging

# Handle imports for both direct execution and module import
try:
    # When running as part of the package
    from ..utils.version import (
        get_version, get_version_info, get_version_history,
        get_latest_changes, is_development, get_codename
    )
    from ..lang.lang_manager import SimpleLanguageManager
except ImportError:
    # When running directly, add parent directory to path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from clamav_gui.utils.version import (
        get_version, get_version_info, get_version_history,
        get_latest_changes, is_development, get_codename
    )
    from clamav_gui.lang.lang_manager import SimpleLanguageManager

logger = logging.getLogger('ClamAV-GUI')

def _tr(key, default_text):
    """Helper function to translate text using the language manager."""
    return SimpleLanguageManager().tr(key, default_text)

class HelpDialog(QDialog):
    """Help dialog for the ClamAV GUI application."""
    
    # Signal to notify language change
    language_changed = Signal(str)
    
    def __init__(self, parent=None, current_lang='en'):
        """
        Initialize the help dialog.
        
        Args:
            parent: Parent widget
            current_lang (str): Current language code (default: 'en')
        """
        super().__init__(parent)
        self.current_lang = current_lang
        self.language_manager = SimpleLanguageManager()
        self.resize(500, 400)
        self.setWindowTitle(self.tr("help.window_title", "ClamAV GUI Help"))
        
        # Set window icon if available
        try:
            from .. import resources  # Assuming resources are in a resources module
            self.setWindowIcon(QIcon(':/icons/help-circle'))
        except (ImportError, AttributeError):
            pass
            
        # Set window flags
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        try:
            # Set up UI
            self.init_ui()
            self.retranslate_ui()
            logger.debug(self.tr(
                "help.init_success",
                "Help dialog initialized successfully"
            ))
        except Exception as e:
            logger.error(self.tr(
                "help.init_error",
                "Error initializing help dialog: {error}"
            ).format(error=str(e)))
            raise

    def tr(self, key, default_text):
        """Translate text using the language manager."""
        return self.language_manager.tr(key, default_text)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
            
        # Create a frame for language buttons
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                border-radius: 4px;
                padding: 20px;
                background-color: #dbd3ae;
            }
        """)
        
        # Create a vertical layout for the two rows
        button_layout = QVBoxLayout(button_frame)
        button_layout.setContentsMargins(15, 15, 15, 15)
        button_layout.setSpacing(15)  # More space between rows
        
        # Create two horizontal layouts for the two rows
        first_row_layout = QHBoxLayout()
        first_row_layout.setSpacing(5)  # More space between buttons
        
        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(5)  # More space between buttons
        
        # Style for language buttons
        button_style = """
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:checked {
                background-color: #106ebe;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """
        
        # Language data with flag emojis - only English and Italian
        languages = [
            ('English', 'en', '🇬🇧'),
            ('Italiano', 'it', '🇮🇹')
        ]
        
        # Create language buttons
        self.lang_buttons = {}
        for i, (name, code, flag) in enumerate(languages):
            button = QPushButton(f"{flag} {name}")
            button.setCheckable(True)
            button.setStyleSheet(button_style)
            button.clicked.connect(lambda checked, c=code: self.on_language_changed(c))
            self.lang_buttons[code] = button
            
            # Add all buttons to the first row
            first_row_layout.addWidget(button)
        
        # Add stretch to center the buttons in each row
        first_row_layout.addStretch()
        second_row_layout.addStretch()
            
        # Add the button row to the main button layout
        button_layout.addLayout(first_row_layout)
        
        # Set current language
        for code, button in self.lang_buttons.items():
            button.setChecked(code == self.current_lang)
        
        # Add language buttons to layout
        main_layout.addWidget(button_frame)
        
        # Create and add help text browser
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        main_layout.addWidget(self.text_browser)
        
        # Close button
        button_box = QHBoxLayout()
        button_box.addStretch()
        
        self.close_btn = QPushButton(self.tr("common.close", "Close"))
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setMinimumWidth(120)
        
        # Style the close button with red background and white text
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        
        button_box.addWidget(self.close_btn)
        main_layout.addLayout(button_box)
        
        # Set initial help content
        self.retranslate_ui()
            
    def retranslate_ui(self):
        """Update the UI with the current language."""
        # Set window title
        self.setWindowTitle(self.tr("help.window_title", "ClamAV GUI Help"))
        
        # Update close button text
        self.close_btn.setText(self.tr("common.close", "Close"))
        
        # Update help content based on current language
        self.update_help_content()
            
    def update_help_content(self):
        """
        Update the help content based on the current language.
        
        This method loads the appropriate help text based on the current language
        and updates the help content accordingly.
        """
        try:
            # Get help text based on current language
            help_text = self._get_help_text(self.current_lang)
            
            self.text_browser.setHtml(help_text)
            logger.debug(self.tr(
                "help.language_changed",
                "UI retranslated to {language}"
            ).format(language=self.current_lang))
            
        except Exception as e:
            logger.error(self.tr(
                "help.translation_error",
                "Error retranslating UI: {error}"
            ).format(error=str(e)))
            # Fallback to English if translation fails
            try:
                fallback_text = self._get_help_text('en')
                self.text_browser.setHtml(fallback_text)
            except Exception as fallback_error:
                logger.error(f"Fallback to English also failed: {fallback_error}")
                self.text_browser.setHtml("<h1>Error</h1><p>Could not load help content.</p>")
    
    def show_dialog(self):
        """Show the help dialog."""
        self.show()
        return self.exec_()
    
    def _get_help_text(self, lang_code):
        """
        Get help text for the specified language.
        
        Args:
            lang_code (str): Language code ('en' or 'it')
            
        Returns:
            str: HTML help text for the specified language
        """
        help_methods = {
            'en': self._get_english_help,
            'it': self._get_italian_help,
        }
        
        # Default to English if language not found
        method = help_methods.get(lang_code, self._get_english_help)
        return method()
    
    def _get_italian_help(self):
        """Return Italian help text."""
        return self.tr(
            "help.content.it",
            """
            <h1>Guida GUI ClamAV</h1>

            <h2>Guida introduttiva</h2>
            <p>Benvenuto in ClamAV GUI, un'interfaccia intuitiva per il motore antivirus ClamAV.</p>

            <h3>Scansione rapida</h3>
            <p>Esegui una scansione rapida delle posizioni comuni alla ricerca di malware.</p>
            <ul>
                <li>Fare clic sul pulsante <b>Scansione rapida</b> per avviare una scansione rapida del sistema.</li>
                <li>Questa scansione controlla le posizioni critiche del sistema in cui è più frequente trovare malware.</li>
            </ul>

            <h3>Scansione completa</h3>
            <p>Esegue una scansione approfondita dell'intero sistema.</p>
            <ul>
                <li>Fare clic sul pulsante <b>Scansione completa</b> per eseguire la scansione di tutti i file presenti nel sistema.</li>
                <li>L'operazione potrebbe richiedere del tempo a seconda delle dimensioni del sistema.</li>
            </ul>

            <h3>Scansione personalizzata</h3>
            <p>Eseguire la scansione di file o directory specifici a scelta.</p>
            <ul>
                <li>Fare clic su <b>Scansione personalizzata</b> e selezionare i file o le cartelle che si desidera scansionare.</li>
                <li>Utilizzare il browser dei file per navigare fino alla posizione desiderata.</li>
            </ul>

            <h2>Funzionalità avanzate (Versione 1.2.5)</h2>

            <h3>Visualizzatore log avanzato</h3>
            <p>Visualizza e analizza i log dell'applicazione con funzionalità avanzate.</p>
            <ul>
                <li>Accedi tramite <b>Aiuto → Visualizza log</b> o la scheda Visualizzatore log dedicata.</li>
                <li><b>Funzione di ricerca</b>: Cerca nei log con evidenziazione in tempo reale.</li>
                <li><b>Filtri</b>: Filtra i log per livello (ERROR, WARNING, INFO, DEBUG) o mostra tutte le voci.</li>
                <li><b>Codifica colori</b>: Diversi colori per diversi livelli di log per una facile identificazione.</li>
                <li><b>Statistiche</b>: Visualizza le statistiche dei log incluse conteggi errori e informazioni sui file.</li>
                <li><b>Esporta</b>: Esporta i log filtrati per analisi esterne.</li>
            </ul>

            <h3>Editor di configurazione</h3>
            <p>Modifica i file di configurazione di ClamAV direttamente nell'applicazione.</p>
            <ul>
                <li>Accedi tramite la scheda <b>Editor configurazione</b>.</li>
                <li>Modifica <b>clamd.conf</b>, <b>freshclam.conf</b> e altri file di configurazione.</li>
                <li>Evidenziazione sintassi e validazione per i file di configurazione.</li>
                <li>Modifica sicura con funzionalità di backup e ripristino.</li>
            </ul>

            <h3>Menu scansione avanzata</h3>
            <p>Accedi alle funzionalità di scansione avanzate tramite il sistema di menu migliorato.</p>
            <ul>
                <li><b>Scansione intelligente</b>: Utilizza database hash per saltare file sicuri scansionati in precedenza.</li>
                <li><b>Rilevamento minacce ML</b>: Analisi basata su IA per il rilevamento avanzato di minacce.</li>
                <li><b>Scansione email</b>: Scansione dedicata per file email (formati .eml, .msg).</li>
                <li><b>Analisi batch</b>: Elabora più file simultaneamente.</li>
                <li><b>Scansione rete</b>: Scansiona unità di rete e posizioni remote.</li>
            </ul>

            <h2>Aggiornamenti del database dei virus</h2>
            <p>Mantenere aggiornate le definizioni dei virus per una protezione ottimale.</p>
            <ul>
                <li>Fai clic su <b>Aggiorna</b> per scaricare le definizioni dei virus più recenti.</li>
                <li>Abilita gli aggiornamenti automatici in Impostazioni per una protezione continua.</li>
            </ul>

            <h2>Quarantena</h2>
            <p>Gestisci i file che sono stati identificati come potenziali minacce.</p>
            <ul>
                <li>Visualizza i file in quarantena nella sezione <b>Quarantena</b>.</li>
                <li>Ripristina i falsi positivi o elimina le minacce confermate.</li>
            </ul>

            <h2>Impostazioni</h2>
            <p>Personalizza l'interfaccia grafica di ClamAV in base alle tue esigenze.</p>
            <ul>
                <li>Configura le opzioni di scansione e le esclusioni.</li>
                <li>Imposta le scansioni pianificate.</li>
                <li>Modifica le impostazioni di aggiornamento.</li>
            </ul>

            <h2>Hai bisogno di ulteriore assistenza?</h2>
            <p>Visita il <a href="https://www.clamav.net/">sito web di ClamAV</a> per ulteriori informazioni e documentazione.</p>

            """
        )
    
    def _get_english_help(self):
        """Return English help text."""
        return self.tr(
            "help.content.en",
            """
            <h1>ClamAV GUI Help</h1>

            <h2>Getting Started</h2>
            <p>Welcome to ClamAV GUI, a user-friendly interface for the ClamAV antivirus engine.</p>

            <h3>Quick Scan</h3>
            <p>Quickly scan common locations for malware.</p>
            <ul>
                <li>Click the <b>Quick Scan</b> button to start a quick system scan.</li>
                <li>This scan checks critical system locations where malware is commonly found.</li>
            </ul>

            <h3>Full Scan</h3>
            <p>Perform a thorough scan of your entire system.</p>
            <ul>
                <li>Click the <b>Full Scan</b> button to scan all files on your system.</li>
                <li>This may take a while depending on your system size.</li>
            </ul>

            <h3>Custom Scan</h3>
            <p>Scan specific files or directories of your choice.</p>
            <ul>
                <li>Click <b>Custom Scan</b> and select the files or folders you want to scan.</li>
                <li>Use the file browser to navigate to your desired location.</li>
            </ul>

            <h2>Advanced Features (Version 1.2.5)</h2>

            <h3>Enhanced Log Viewer</h3>
            <p>View and analyze application logs with advanced features.</p>
            <ul>
                <li>Access via <b>Help → View Logs</b> or the dedicated Log Viewer tab.</li>
                <li><b>Search Functionality</b>: Search through logs with real-time highlighting.</li>
                <li><b>Filtering</b>: Filter logs by level (ERROR, WARNING, INFO, DEBUG) or show all entries.</li>
                <li><b>Color Coding</b>: Different colors for different log levels for easy identification.</li>
                <li><b>Statistics</b>: View log statistics including error counts and file information.</li>
                <li><b>Export</b>: Export filtered logs for external analysis.</li>
            </ul>

            <h3>Configuration Editor</h3>
            <p>Edit ClamAV configuration files directly within the application.</p>
            <ul>
                <li>Access via the <b>Config Editor</b> tab.</li>
                <li>Edit <b>clamd.conf</b>, <b>freshclam.conf</b>, and other configuration files.</li>
                <li>Syntax highlighting and validation for configuration files.</li>
                <li>Safe editing with backup and restore capabilities.</li>
            </ul>

            <h3>Advanced Scanning Menu</h3>
            <p>Access advanced scanning features through the enhanced menu system.</p>
            <ul>
                <li><b>Smart Scanning</b>: Uses hash databases to skip previously scanned safe files.</li>
                <li><b>ML Threat Detection</b>: AI-powered analysis for advanced threat detection.</li>
                <li><b>Email Scanning</b>: Dedicated scanning for email files (.eml, .msg formats).</li>
                <li><b>Batch Analysis</b>: Process multiple files simultaneously.</li>
                <li><b>Network Scanning</b>: Scan network drives and remote locations.</li>
            </ul>

            <h2>Virus Database Updates</h2>
            <p>Keep your virus definitions up to date for optimal protection.</p>
            <ul>
                <li>Click <b>Update</b> to download the latest virus definitions.</li>
                <li>Enable automatic updates in Settings for continuous protection.</li>
            </ul>

            <h2>Quarantine</h2>
            <p>Manage files that have been identified as potential threats.</p>
            <ul>
                <li>View quarantined files in the <b>Quarantine</b> section.</li>
                <li>Restore false positives or delete confirmed threats.</li>
            </ul>

            <h2>Settings</h2>
            <p>Customize ClamAV GUI to suit your needs.</p>
            <ul>
                <li>Configure scan options and exclusions.</li>
                <li>Set up scheduled scans.</li>
                <li>Adjust update settings.</li>
            </ul>

            <h2>Need More Help?</h2>
            <p>Visit the <a href="https://www.clamav.net/">ClamAV website</a> for more information and documentation.</p>
            """
        )
    
    def on_language_changed(self, lang_code):
        """
        Handle language change event.
        
        Args:
            lang_code (str): New language code
        """
        try:
            if lang_code != self.current_lang:
                self.current_lang = lang_code
                self.retranslate_ui()
                self.language_changed.emit(lang_code)
                
                # Update button states
                for code, button in self.lang_buttons.items():
                    if code == lang_code:
                        button.setChecked(True)
                    else:
                        button.setChecked(False)
                    
                logger.debug(self.tr(
                    "help.language_switched",
                    "Language switched to {language}"
                ).format(language=lang_code))
                
        except Exception as e:
            logger.error(self.tr(
                "help.language_switch_error",
                "Error switching language: {error}"
            ).format(error=str(e)))
    
    def open_link(self, url):
        """
        Open a link in the default web browser.
        
        Args:
            url: QUrl of the link to open
        """
        try:
            QDesktopServices.openUrl(url)
        except Exception as e:
            logger.error(self.tr(
                "help.link_open_error",
                "Error opening link {url}: {error}"
            ).format(url=url.toString(), error=str(e)))
