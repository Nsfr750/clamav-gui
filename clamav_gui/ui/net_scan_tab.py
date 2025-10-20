"""
Network scanning tab for ClamAV GUI.
Provides UI for scanning network drives and UNC paths.
"""
import os
import logging
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QTextEdit, QProgressBar, QCheckBox, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QFormLayout,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

from clamav_gui.utils.network_scanner import NetworkScanner, NetworkScanThread

logger = logging.getLogger(__name__)


class NetworkScanTab(QDialog):
    """Network scanning dialog for scanning network drives and UNC paths."""

    def __init__(self, parent=None):
        """Initialize the network scan tab.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.scanner = None
        self.scan_thread = None
        self.network_drives = []

        # Set dialog properties
        self.setWindowTitle(self.tr("Network Scanning"))
        self.setModal(True)
        self.resize(900, 700)

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.connect_signals()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Network path selection
        path_group = QGroupBox(self.tr("Network Path"))
        path_layout = QVBoxLayout()

        # UNC path input
        self.network_path_input = QLineEdit()
        self.network_path_input.setPlaceholderText(self.tr("Enter UNC path (e.g., \\\\server\\share)"))
        path_layout.addWidget(self.network_path_input)

        # Network drives section (Windows only)
        drives_layout = QHBoxLayout()

        self.network_drives_list = QListWidget()
        self.network_drives_list.setMaximumHeight(100)
        drives_layout.addWidget(self.network_drives_list)

        drives_btn_layout = QVBoxLayout()
        refresh_drives_btn = QPushButton(self.tr("Refresh Drives"))
        refresh_drives_btn.clicked.connect(self.refresh_network_drives)
        drives_btn_layout.addWidget(refresh_drives_btn)

        map_drive_btn = QPushButton(self.tr("Map Drive"))
        map_drive_btn.clicked.connect(self.map_network_drive)
        drives_btn_layout.addWidget(map_drive_btn)

        unmap_drive_btn = QPushButton(self.tr("Unmap Drive"))
        unmap_drive_btn.clicked.connect(self.unmap_network_drive)
        drives_btn_layout.addWidget(unmap_drive_btn)

        drives_layout.addLayout(drives_btn_layout)
        path_layout.addLayout(drives_layout)

        path_group.setLayout(path_layout)

        # Scan options
        options_group = QGroupBox(self.tr("Scan Options"))
        options_layout = QVBoxLayout()

        # Basic options
        basic_layout = QHBoxLayout()

        self.recursive_scan = QCheckBox(self.tr("Recursive scan"))
        self.recursive_scan.setChecked(True)
        basic_layout.addWidget(self.recursive_scan)

        self.scan_archives = QCheckBox(self.tr("Scan archives"))
        self.scan_archives.setChecked(True)
        basic_layout.addWidget(self.scan_archives)

        self.heuristic_scan = QCheckBox(self.tr("Heuristic analysis"))
        self.heuristic_scan.setChecked(True)
        basic_layout.addWidget(self.heuristic_scan)

        options_layout.addLayout(basic_layout)

        # Advanced options
        advanced_layout = QHBoxLayout()

        self.scan_pua = QCheckBox(self.tr("Scan PUA"))
        self.scan_pua.setChecked(False)
        self.scan_pua.setToolTip(self.tr("Scan for potentially unwanted applications"))
        advanced_layout.addWidget(self.scan_pua)

        self.follow_symlinks = QCheckBox(self.tr("Follow symlinks"))
        self.follow_symlinks.setChecked(False)
        advanced_layout.addWidget(self.follow_symlinks)

        options_layout.addLayout(advanced_layout)

        # Performance settings
        perf_layout = QFormLayout()

        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(1, 1000)
        self.max_file_size.setValue(100)
        self.max_file_size.setSuffix(" MB")
        perf_layout.addRow(self.tr("Max file size:"), self.max_file_size)

        self.max_scan_time = QSpinBox()
        self.max_scan_time.setRange(60, 3600)
        self.max_scan_time.setValue(300)
        self.max_scan_time.setSuffix(" sec")
        perf_layout.addRow(self.tr("Max scan time:"), self.max_scan_time)

        options_layout.addLayout(perf_layout)

        # Exclude patterns
        self.exclude_patterns = QLineEdit()
        self.exclude_patterns.setPlaceholderText(self.tr("*.log,*.tmp,*.cache"))
        options_layout.addWidget(QLabel(self.tr("Exclude patterns:")))
        options_layout.addWidget(self.exclude_patterns)

        options_group.setLayout(options_layout)

        # Output area
        output_group = QGroupBox(self.tr("Scan Results"))
        output_layout = QVBoxLayout()

        self.scan_output = QTextEdit()
        self.scan_output.setReadOnly(True)
        self.scan_output.setFont(QFont("Courier", 9))
        output_layout.addWidget(self.scan_output)

        output_group.setLayout(output_layout)

        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 0)  # Indeterminate progress

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_scan_btn = QPushButton(self.tr("Start Network Scan"))
        self.start_scan_btn.clicked.connect(self.start_network_scan)
        self.start_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        button_layout.addWidget(self.start_scan_btn)

        self.stop_scan_btn = QPushButton(self.tr("Stop Scan"))
        self.stop_scan_btn.setEnabled(False)
        self.stop_scan_btn.clicked.connect(self.stop_network_scan)
        self.stop_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        button_layout.addWidget(self.stop_scan_btn)

        self.clear_output_btn = QPushButton(self.tr("Clear Results"))
        self.clear_output_btn.clicked.connect(self.clear_scan_output)
        button_layout.addWidget(self.clear_output_btn)

        self.save_report_btn = QPushButton(self.tr("Save Report"))
        self.save_report_btn.setEnabled(False)
        self.save_report_btn.clicked.connect(self.save_scan_report)
        button_layout.addWidget(self.save_report_btn)

        # Add all to main layout
        layout.addWidget(path_group)
        layout.addWidget(options_group)
        layout.addWidget(output_group)
        layout.addWidget(self.scan_progress)
        layout.addLayout(button_layout)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Initialize scanner
        self.initialize_scanner()

    def connect_signals(self):
        """Connect UI signals."""
        pass

    def accept(self):
        """Override accept to handle dialog closing."""
        # Don't close if scan is in progress
        if (hasattr(self, 'scan_thread') and self.scan_thread and
            self.scan_thread.isRunning()):
            QMessageBox.warning(
                self, self.tr("Scan in Progress"),
                self.tr("Cannot close dialog while network scan is running. Please stop the scan first.")
            )
            return
        super().accept()

    def reject(self):
        """Override reject to handle dialog closing."""
        # Don't close if scan is in progress
        if (hasattr(self, 'scan_thread') and self.scan_thread and
            self.scan_thread.isRunning()):
            reply = QMessageBox.question(
                self, self.tr("Scan in Progress"),
                self.tr("Network scan is currently running. Do you want to stop it and close the dialog?"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.stop_network_scan()
                super().reject()
        else:
            super().reject()

    def initialize_scanner(self):
        """Initialize the network scanner."""
        try:
            # Get clamscan path from settings if available
            clamscan_path = getattr(self.parent(), 'clamscan_path', None) if self.parent() else None
            clamscan_path = clamscan_path.text() if clamscan_path else "clamscan"

            self.scanner = NetworkScanner(clamscan_path)
            logger.info("Network scanner initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize network scanner: {e}")
            QMessageBox.critical(
                self, self.tr("Scanner Error"),
                self.tr(f"Failed to initialize network scanner:\n\n{str(e)}")
            )

    def refresh_network_drives(self):
        """Refresh the list of available network drives."""
        if not self.scanner:
            QMessageBox.warning(self, self.tr("Scanner Error"), self.tr("Network scanner not initialized"))
            return

        try:
            self.network_drives = self.scanner.get_network_drives()
            self.network_drives_list.clear()

            if not self.network_drives:
                self.network_drives_list.addItem(self.tr("No network drives found"))
                return

            for drive in self.network_drives:
                item_text = f"{drive['drive_letter']}: - {drive['network_path']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, drive)
                self.network_drives_list.addItem(item)

        except Exception as e:
            logger.error(f"Error refreshing network drives: {e}")
            QMessageBox.critical(
                self, self.tr("Error"),
                self.tr(f"Failed to refresh network drives:\n\n{str(e)}")
            )

    def map_network_drive(self):
        """Map a network drive."""
        if not self.scanner:
            QMessageBox.warning(self, self.tr("Scanner Error"), self.tr("Network scanner not initialized"))
            return

        network_path = self.network_path_input.text().strip()
        if not network_path:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr("Please enter a network path first"))
            return

        try:
            success, message = self.scanner.map_network_drive(network_path)

            if success:
                QMessageBox.information(self, self.tr("Success"), message)
                self.refresh_network_drives()
            else:
                QMessageBox.warning(self, self.tr("Mapping Failed"), message)

        except Exception as e:
            logger.error(f"Error mapping network drive: {e}")
            QMessageBox.critical(
                self, self.tr("Error"),
                self.tr(f"Failed to map network drive:\n\n{str(e)}")
            )

    def unmap_network_drive(self):
        """Unmap a selected network drive."""
        if not self.scanner:
            QMessageBox.warning(self, self.tr("Scanner Error"), self.tr("Network scanner not initialized"))
            return

        current_item = self.network_drives_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a drive to unmap"))
            return

        drive_info = current_item.data(Qt.UserRole)
        if not drive_info:
            return

        drive_letter = drive_info['drive_letter']

        reply = QMessageBox.question(
            self, self.tr("Unmap Drive"),
            self.tr(f"Are you sure you want to unmap drive {drive_letter}:?"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success, message = self.scanner.unmap_network_drive(drive_letter)

                if success:
                    QMessageBox.information(self, self.tr("Success"), message)
                    self.refresh_network_drives()
                else:
                    QMessageBox.warning(self, self.tr("Unmapping Failed"), message)

            except Exception as e:
                logger.error(f"Error unmapping network drive: {e}")
                QMessageBox.critical(
                    self, self.tr("Error"),
                    self.tr(f"Failed to unmap network drive:\n\n{str(e)}")
                )

    def start_network_scan(self):
        """Start the network scanning process."""
        if not self.scanner:
            QMessageBox.warning(self, self.tr("Scanner Error"), self.tr("Network scanner not initialized"))
            return

        network_path = self.network_path_input.text().strip()
        if not network_path:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr("Please enter a network path to scan"))
            return

        # Validate the network path
        is_valid, message = self.scanner.validate_network_path(network_path)
        if not is_valid:
            QMessageBox.warning(self, self.tr("Invalid Path"), message)
            return

        # Prepare scan options
        options = {
            'recursive': self.recursive_scan.isChecked(),
            'scan_archives': self.scan_archives.isChecked(),
            'heuristic_scan': self.heuristic_scan.isChecked(),
            'scan_pua': self.scan_pua.isChecked(),
            'follow_symlinks': self.follow_symlinks.isChecked(),
            'max_file_size': self.max_file_size.value(),
            'max_scan_time': self.max_scan_time.value(),
            'exclude_patterns': self.exclude_patterns.text().strip()
        }

        # Disable controls during scan
        self.set_controls_enabled(False)

        # Clear previous output
        self.scan_output.clear()

        # Create and start scan thread
        self.scan_thread = NetworkScanThread(self.scanner, network_path, options)

        # Connect thread signals
        self.scan_thread.update_progress.connect(self.update_scan_progress)
        self.scan_thread.update_output.connect(self.update_scan_output)
        self.scan_thread.finished.connect(self.on_scan_finished)

        # Start the scan
        self.scan_thread.start()

        self.scan_output.append(f"Starting network scan of: {network_path}")
        logger.info(f"Started network scan of: {network_path}")

    def stop_network_scan(self):
        """Stop the current network scan."""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.terminate()
            self.scan_thread.wait(5000)  # Wait up to 5 seconds

            self.scan_output.append("Network scan stopped by user")
            self.set_controls_enabled(True)
            logger.info("Network scan stopped by user")

    def clear_scan_output(self):
        """Clear the scan output area."""
        self.scan_output.clear()

    def save_scan_report(self):
        """Save the scan results to a file."""
        if not self.scan_output.toPlainText().strip():
            QMessageBox.warning(self, self.tr("No Content"), self.tr("No scan results to save"))
            return

        # Implementation for saving scan report
        QMessageBox.information(
            self, self.tr("Save Report"),
            self.tr("Scan report saving functionality will be implemented")
        )

    def set_controls_enabled(self, enabled: bool):
        """Enable or disable scan controls.

        Args:
            enabled: Whether controls should be enabled
        """
        self.start_scan_btn.setEnabled(enabled)
        self.stop_scan_btn.setEnabled(not enabled)
        self.network_path_input.setEnabled(enabled)
        self.recursive_scan.setEnabled(enabled)
        self.scan_archives.setEnabled(enabled)
        self.heuristic_scan.setEnabled(enabled)
        self.scan_pua.setEnabled(enabled)
        self.follow_symlinks.setEnabled(enabled)
        self.max_file_size.setEnabled(enabled)
        self.max_scan_time.setEnabled(enabled)
        self.exclude_patterns.setEnabled(enabled)

    def update_scan_progress(self, progress: int):
        """Update scan progress (placeholder for future use).

        Args:
            progress: Progress value (0-100)
        """
        pass

    def update_scan_output(self, text: str):
        """Update the scan output text area.

        Args:
            text: Text to append to output
        """
        self.scan_output.append(text)

        # Auto-scroll to bottom
        cursor = self.scan_output.textCursor()
        cursor.movePosition(cursor.End)
        self.scan_output.setTextCursor(cursor)

    def on_scan_finished(self, success: bool, message: str, threats: List[str]):
        """Handle scan completion.

        Args:
            success: Whether scan completed successfully
            message: Result message
            threats: List of detected threats
        """
        # Re-enable controls
        self.set_controls_enabled(True)

        # Update output
        self.update_scan_output(f"\nScan completed: {message}")

        if threats:
            self.update_scan_output(f"\nThreats found: {len(threats)}")
            for threat in threats[:10]:  # Show first 10 threats
                self.update_scan_output(f"  • {threat}")
            if len(threats) > 10:
                self.update_scan_output(f"  ... and {len(threats) - 10} more threats")
        else:
            self.update_scan_output("\nNo threats detected - scan completed successfully")

        # Enable save report button if there are results
        has_results = self.scan_output.toPlainText().strip()
        self.save_report_btn.setEnabled(has_results)

        # Log completion
        if success:
            logger.info(f"Network scan completed successfully: {message}")
        else:
            logger.error(f"Network scan failed: {message}")

    def get_scan_options(self) -> Dict:
        """Get the current scan options.

        Returns:
            Dictionary of scan options
        """
        return {
            'recursive': self.recursive_scan.isChecked(),
            'scan_archives': self.scan_archives.isChecked(),
            'heuristic_scan': self.heuristic_scan.isChecked(),
            'scan_pua': self.scan_pua.isChecked(),
            'follow_symlinks': self.follow_symlinks.isChecked(),
            'max_file_size': self.max_file_size.value(),
            'max_scan_time': self.max_scan_time.value(),
            'exclude_patterns': self.exclude_patterns.text().strip()
        }

    def set_scan_options(self, options: Dict):
        """Set scan options from dictionary.

        Args:
            options: Dictionary of scan options
        """
        if 'recursive' in options:
            self.recursive_scan.setChecked(options['recursive'])
        if 'scan_archives' in options:
            self.scan_archives.setChecked(options['scan_archives'])
        if 'heuristic_scan' in options:
            self.heuristic_scan.setChecked(options['heuristic_scan'])
        if 'scan_pua' in options:
            self.scan_pua.setChecked(options['scan_pua'])
        if 'follow_symlinks' in options:
            self.follow_symlinks.setChecked(options['follow_symlinks'])
        if 'max_file_size' in options:
            self.max_file_size.setValue(options['max_file_size'])
        if 'max_scan_time' in options:
            self.max_scan_time.setValue(options['max_scan_time'])
        if 'exclude_patterns' in options:
            self.exclude_patterns.setText(options['exclude_patterns'])
