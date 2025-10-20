"""
Dialog classes for advanced ClamAV GUI features.
"""
import os
import logging
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QListWidget, QListWidgetItem, QTextEdit,
                             QProgressBar, QGroupBox, QCheckBox, QSpinBox, QComboBox,
                             QMessageBox, QFileDialog, QSplitter, QTreeWidget,
                             QTreeWidgetItem, QHeaderView, QInputDialog)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)


class NetworkPathDialog(QDialog):
    """Dialog for selecting network paths for scanning."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_path = None
        self.network_scanner = None
        self.init_ui()

    def init_ui(self):
        """Initialize the network path selection dialog."""
        self.setWindowTitle(self.tr("Network Path Selection"))
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(self.tr(
            "Select a network path to scan:\n\n"
            "Examples:\n"
            "• \\\\server\\share\n"
            "• \\\\192.168.1.100\\shared_folder\n"
            "• /mnt/network_share (Unix/Linux)"
        ))
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Path input
        path_layout = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(self.tr("Enter network path (e.g., \\\\server\\share)"))
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self.browse_network)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        # Network discovery section
        discovery_group = QGroupBox(self.tr("Network Discovery"))
        discovery_layout = QVBoxLayout()

        self.discovery_list = QListWidget()
        self.discovery_list.setMaximumHeight(150)
        discovery_layout.addWidget(self.discovery_list)

        discover_btn = QPushButton(self.tr("Discover Network Shares"))
        discover_btn.clicked.connect(self.discover_network_shares)
        discovery_layout.addWidget(discover_btn)

        discovery_group.setLayout(discovery_layout)
        layout.addWidget(discovery_group)

        # Buttons
        button_layout = QHBoxLayout()

        ok_btn = QPushButton(self.tr("OK"))
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton(self.tr("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def browse_network(self):
        """Browse for network paths."""
        # For now, just show a simple input dialog for UNC paths
        path, ok = QInputDialog.getText(
            self,
            self.tr("Network Path"),
            self.tr("Enter network path:"),
            QLineEdit.Normal,
            self.path_input.text()
        )

        if ok and path.strip():
            self.path_input.setText(path.strip())

    def discover_network_shares(self):
        """Discover available network shares."""
        try:
            # This would require network scanning functionality
            # For now, show a placeholder
            self.discovery_list.clear()
            self.discovery_list.addItem(self.tr("Network discovery not yet implemented"))
            self.discovery_list.addItem(self.tr("Please enter UNC path manually"))

        except Exception as e:
            logger.error(f"Error discovering network shares: {e}")
            QMessageBox.critical(self, self.tr("Discovery Error"),
                               self.tr(f"Failed to discover network shares: {str(e)}"))

    def get_selected_path(self):
        """Get the selected network path."""
        return self.path_input.text().strip()

    def accept(self):
        """Handle dialog acceptance."""
        path = self.get_selected_path()
        if path:
            self.selected_path = path
            super().accept()
        else:
            QMessageBox.warning(self, self.tr("No Path Selected"),
                              self.tr("Please enter a network path"))


class MLDetectionDialog(QDialog):
    """Dialog for Machine Learning threat detection."""

    def __init__(self, ml_detector, parent=None):
        super().__init__(parent)
        self.ml_detector = ml_detector
        self.analysis_result = None
        self.init_ui()

    def init_ui(self):
        """Initialize the ML detection dialog."""
        self.setWindowTitle(self.tr("ML Threat Detection"))
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox(self.tr("File Selection"))
        file_layout = QVBoxLayout()

        file_btn_layout = QHBoxLayout()

        self.file_path_label = QLabel(self.tr("No file selected"))
        file_btn_layout.addWidget(self.file_path_label)

        select_btn = QPushButton(self.tr("Select File"))
        select_btn.clicked.connect(self.select_file)
        file_btn_layout.addWidget(select_btn)

        file_layout.addLayout(file_btn_layout)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Analysis options
        options_group = QGroupBox(self.tr("Analysis Options"))
        options_layout = QVBoxLayout()

        self.deep_analysis = QCheckBox(self.tr("Deep Analysis (slower but more accurate)"))
        self.deep_analysis.setChecked(False)
        options_layout.addWidget(self.deep_analysis)

        self.sandbox_analysis = QCheckBox(self.tr("Sandbox Analysis (check behavior)"))
        self.sandbox_analysis.setChecked(True)
        options_layout.addWidget(self.sandbox_analysis)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Analysis results
        results_group = QGroupBox(self.tr("Analysis Results"))
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Progress
        progress_layout = QHBoxLayout()

        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        progress_layout.addWidget(self.analysis_progress)

        self.status_label = QLabel(self.tr("Ready"))
        progress_layout.addWidget(self.status_label)

        layout.addLayout(progress_layout)

        # Buttons
        button_layout = QHBoxLayout()

        analyze_btn = QPushButton(self.tr("Analyze"))
        analyze_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(analyze_btn)

        export_btn = QPushButton(self.tr("Export Results"))
        export_btn.clicked.connect(self.export_results)
        export_btn.setEnabled(False)
        button_layout.addWidget(export_btn)

        close_btn = QPushButton(self.tr("Close"))
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Store reference to export button for enabling/disabling
        self.export_btn = export_btn

    def select_file(self):
        """Select a file for ML analysis."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select File for ML Analysis"),
            "",
            "All Files (*)"
        )

        if file_name:
            self.file_path_label.setText(file_name)
            self.analysis_result = None
            self.results_text.clear()
            self.export_btn.setEnabled(False)

    def start_analysis(self):
        """Start ML analysis of the selected file."""
        file_path = self.file_path_label.text()

        if not file_path or file_path == self.tr("No file selected"):
            QMessageBox.warning(self, self.tr("No File"), self.tr("Please select a file to analyze"))
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, self.tr("File Not Found"), self.tr("Selected file does not exist"))
            return

        try:
            # Show progress
            self.analysis_progress.setVisible(True)
            self.analysis_progress.setRange(0, 0)  # Indeterminate
            self.status_label.setText(self.tr("Analyzing file..."))
            self.analyze_btn.setEnabled(False)

            # Perform analysis in a separate thread
            self.analysis_thread = MLAnalysisThread(self.ml_detector, file_path,
                                                  self.deep_analysis.isChecked(),
                                                  self.sandbox_analysis.isChecked())
            self.analysis_thread.analysis_complete.connect(self.on_analysis_complete)
            self.analysis_thread.start()

        except Exception as e:
            logger.error(f"Error starting ML analysis: {e}")
            QMessageBox.critical(self, self.tr("Analysis Error"),
                               self.tr(f"Failed to start analysis: {str(e)}"))

    def on_analysis_complete(self, result):
        """Handle analysis completion."""
        try:
            # Hide progress
            self.analysis_progress.setVisible(False)
            self.analyze_btn.setEnabled(True)

            if 'error' in result:
                self.status_label.setText(self.tr("Analysis failed"))
                self.results_text.setPlainText(f"Error: {result['error']}")
                return

            # Display results
            self.analysis_result = result
            self.status_label.setText(self.tr("Analysis complete"))
            self.export_btn.setEnabled(True)

            result_text = f"""
ML Threat Detection Results
{'=' * 40}

File: {result.get('file_path', 'Unknown')}
Risk Level: {result.get('risk_level', 'Unknown').upper()}
ML Confidence: {result.get('ml_confidence', 0):.3f}
Category: {result.get('ml_category', 'Unknown')}

Detection Details:
{result.get('details', 'No additional details available')}

Analysis Time: {result.get('analysis_timestamp', 'Unknown')}
"""
            self.results_text.setPlainText(result_text.strip())

        except Exception as e:
            logger.error(f"Error handling analysis completion: {e}")
            QMessageBox.critical(self, self.tr("Display Error"),
                               self.tr(f"Failed to display results: {str(e)}"))

    def export_results(self):
        """Export analysis results to a file."""
        if not self.analysis_result:
            QMessageBox.warning(self, self.tr("No Results"), self.tr("No analysis results to export"))
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export ML Analysis Results"),
            "",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )

        if not file_name:
            return

        try:
            if file_name.lower().endswith('.json'):
                import json
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.analysis_result, f, indent=2, ensure_ascii=False)
            else:
                # Text format
                if not file_name.lower().endswith('.txt'):
                    file_name += '.txt'

                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())

            QMessageBox.information(self, self.tr("Export Complete"),
                                  self.tr(f"Results exported successfully:\n{file_name}"))

        except Exception as e:
            QMessageBox.critical(self, self.tr("Export Error"),
                               self.tr(f"Failed to export results: {str(e)}"))


class MLAnalysisThread(QThread):
    """Thread for performing ML analysis."""

    analysis_complete = Signal(dict)

    def __init__(self, ml_detector, file_path, deep_analysis=False, sandbox_analysis=True):
        super().__init__()
        self.ml_detector = ml_detector
        self.file_path = file_path
        self.deep_analysis = deep_analysis
        self.sandbox_analysis = sandbox_analysis

    def run(self):
        """Perform ML analysis."""
        try:
            if not self.ml_detector:
                self.analysis_complete.emit({'error': 'ML detector not available'})
                return

            # Perform the analysis
            result = self.ml_detector.analyze_file(self.file_path)

            if 'error' not in result:
                # Add additional details
                result['details'] = self._get_analysis_details(result)
                result['analysis_timestamp'] = str(datetime.now())

            self.analysis_complete.emit(result)

        except Exception as e:
            logger.error(f"Error in ML analysis thread: {e}")
            self.analysis_complete.emit({'error': str(e)})

    def _get_analysis_details(self, result):
        """Get detailed analysis information."""
        details = []

        if result.get('is_executable'):
            details.append("• File is executable - higher risk")
        else:
            details.append("• File is not executable - lower risk")

        if result.get('entropy', 0) > 7.0:
            details.append("• High entropy detected - possible packed/encrypted content")
        else:
            details.append("• Normal entropy level")

        risk_level = result.get('risk_level', 'unknown')
        if risk_level == 'high':
            details.append("• High risk level - immediate attention recommended")
        elif risk_level == 'medium':
            details.append("• Medium risk level - monitor closely")
        else:
            details.append("• Low risk level - appears safe")

        return "\n".join(details)


class SmartScanningDialog(QDialog):
    """Dialog for configuring smart scanning settings."""

    def __init__(self, hash_database, parent=None):
        super().__init__(parent)
        self.hash_database = hash_database
        self.settings_changed = False
        self.init_ui()

    def init_ui(self):
        """Initialize the smart scanning configuration dialog."""
        self.setWindowTitle(self.tr("Smart Scanning Configuration"))
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Database status
        status_group = QGroupBox(self.tr("Hash Database Status"))
        status_layout = QVBoxLayout()

        self.db_status_label = QLabel(self.tr("Checking database status..."))
        status_layout.addWidget(self.db_status_label)

        refresh_btn = QPushButton(self.tr("Refresh Status"))
        refresh_btn.clicked.connect(self.refresh_database_status)
        status_layout.addWidget(refresh_btn)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Smart scanning options
        options_group = QGroupBox(self.tr("Smart Scanning Options"))
        options_layout = QVBoxLayout()

        self.enable_hash_check = QCheckBox(self.tr("Enable hash-based file skipping"))
        self.enable_hash_check.setChecked(True)
        self.enable_hash_check.setToolTip(self.tr("Skip files that have been previously scanned and confirmed safe"))
        options_layout.addWidget(self.enable_hash_check)

        self.auto_add_clean_files = QCheckBox(self.tr("Automatically add clean files to hash database"))
        self.auto_add_clean_files.setChecked(True)
        self.auto_add_clean_files.setToolTip(self.tr("Add successfully scanned clean files to the hash database"))
        options_layout.addWidget(self.auto_add_clean_files)

        # Hash database size limit
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel(self.tr("Maximum database size (entries):")))

        self.db_size_limit = QSpinBox()
        self.db_size_limit.setRange(1000, 1000000)
        self.db_size_limit.setValue(50000)
        self.db_size_limit.setSingleStep(1000)
        size_layout.addWidget(self.db_size_limit)

        options_layout.addLayout(size_layout)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Database management
        management_group = QGroupBox(self.tr("Database Management"))
        management_layout = QVBoxLayout()

        mgmt_btn_layout = QHBoxLayout()

        export_btn = QPushButton(self.tr("Export Database"))
        export_btn.clicked.connect(self.export_database)
        mgmt_btn_layout.addWidget(export_btn)

        import_btn = QPushButton(self.tr("Import Database"))
        import_btn.clicked.connect(self.import_database)
        mgmt_btn_layout.addWidget(import_btn)

        clear_btn = QPushButton(self.tr("Clear Database"))
        clear_btn.clicked.connect(self.clear_database)
        mgmt_btn_layout.addWidget(clear_btn)

        management_layout.addLayout(mgmt_btn_layout)
        management_group.setLayout(management_layout)
        layout.addWidget(management_group)

        # Buttons
        button_layout = QHBoxLayout()

        apply_btn = QPushButton(self.tr("Apply"))
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)

        cancel_btn = QPushButton(self.tr("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Load current settings
        self.load_current_settings()

    def load_current_settings(self):
        """Load current smart scanning settings."""
        try:
            if self.hash_database:
                # Get database statistics
                stats = self.hash_database.get_database_stats()

                total_entries = stats.get('total_entries', 0)
                db_size_mb = stats.get('database_size_mb', 0)

                self.db_status_label.setText(
                    self.tr(f"Database contains {total_entries:,} entries ({db_size_mb:.1f} MB)")
                )

                # Load settings if available
                if hasattr(self.hash_database, 'get_settings'):
                    settings = self.hash_database.get_settings()
                    self.enable_hash_check.setChecked(settings.get('enable_hash_check', True))
                    self.auto_add_clean_files.setChecked(settings.get('auto_add_clean_files', True))
                    self.db_size_limit.setValue(settings.get('max_entries', 50000))

        except Exception as e:
            logger.error(f"Error loading smart scanning settings: {e}")
            self.db_status_label.setText(self.tr("Error loading database status"))

    def refresh_database_status(self):
        """Refresh database status display."""
        self.load_current_settings()

    def apply_settings(self):
        """Apply the smart scanning settings."""
        try:
            if not self.hash_database:
                QMessageBox.warning(self, self.tr("No Database"),
                                  self.tr("Hash database not available"))
                return

            # Apply settings
            settings = {
                'enable_hash_check': self.enable_hash_check.isChecked(),
                'auto_add_clean_files': self.auto_add_clean_files.isChecked(),
                'max_entries': self.db_size_limit.value()
            }

            if hasattr(self.hash_database, 'update_settings'):
                self.hash_database.update_settings(settings)
                self.settings_changed = True

            QMessageBox.information(self, self.tr("Settings Applied"),
                                  self.tr("Smart scanning settings have been applied successfully"))

            self.accept()

        except Exception as e:
            logger.error(f"Error applying smart scanning settings: {e}")
            QMessageBox.critical(self, self.tr("Settings Error"),
                               self.tr(f"Failed to apply settings: {str(e)}"))

    def export_database(self):
        """Export the hash database."""
        try:
            if not self.hash_database:
                QMessageBox.warning(self, self.tr("No Database"),
                                  self.tr("Hash database not available"))
                return

            file_name, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Export Hash Database"),
                "",
                "JSON Files (*.json);;All Files (*)"
            )

            if not file_name:
                return

            if not file_name.lower().endswith('.json'):
                file_name += '.json'

            success = self.hash_database.export_database(file_name)

            if success:
                QMessageBox.information(self, self.tr("Export Complete"),
                                      self.tr(f"Hash database exported successfully:\n{file_name}"))
            else:
                QMessageBox.critical(self, self.tr("Export Failed"),
                                   self.tr("Failed to export hash database"))

        except Exception as e:
            QMessageBox.critical(self, self.tr("Export Error"),
                               self.tr(f"Failed to export database: {str(e)}"))

    def import_database(self):
        """Import a hash database."""
        try:
            if not self.hash_database:
                QMessageBox.warning(self, self.tr("No Database"),
                                  self.tr("Hash database not available"))
                return

            file_name, _ = QFileDialog.getOpenFileName(
                self,
                self.tr("Import Hash Database"),
                "",
                "JSON Files (*.json);;All Files (*)"
            )

            if not file_name:
                return

            reply = QMessageBox.question(
                self,
                self.tr("Import Database"),
                self.tr(f"Are you sure you want to import the hash database from:\n{file_name}\n\n"
                       "This will replace the current database. Make sure to backup first."),
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                success = self.hash_database.import_database(file_name)

                if success:
                    QMessageBox.information(self, self.tr("Import Complete"),
                                          self.tr("Hash database imported successfully"))
                    self.refresh_database_status()
                else:
                    QMessageBox.critical(self, self.tr("Import Failed"),
                                       self.tr("Failed to import hash database"))

        except Exception as e:
            QMessageBox.critical(self, self.tr("Import Error"),
                               self.tr(f"Failed to import database: {str(e)}"))

    def clear_database(self):
        """Clear the hash database."""
        try:
            if not self.hash_database:
                QMessageBox.warning(self, self.tr("No Database"),
                                  self.tr("Hash database not available"))
                return

            reply = QMessageBox.question(
                self,
                self.tr("Clear Database"),
                self.tr("Are you sure you want to clear the entire hash database?\n\n"
                       "This action cannot be undone."),
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                success = self.hash_database.clear_database()

                if success:
                    QMessageBox.information(self, self.tr("Clear Complete"),
                                          self.tr("Hash database cleared successfully"))
                    self.refresh_database_status()
                else:
                    QMessageBox.critical(self, self.tr("Clear Failed"),
                                       self.tr("Failed to clear hash database"))

        except Exception as e:
            QMessageBox.critical(self, self.tr("Clear Error"),
                               self.tr(f"Failed to clear database: {str(e)}"))
