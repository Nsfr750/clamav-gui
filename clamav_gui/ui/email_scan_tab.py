"""
Email scanning tab for ClamAV GUI application.
Provides interface for scanning email files (.eml, .msg) and their attachments.
"""
import os
import time
import logging
import subprocess
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit, QPushButton,
    QTextEdit, QProgressBar, QCheckBox, QMessageBox, QFileDialog,
    QListWidget, QListWidgetItem, QSplitter, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QTableWidget, QTableWidgetItem, QLabel, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal

logger = logging.getLogger(__name__)


class EmailScanWorker(QThread):
    """Worker thread for email scanning operations."""

    # Signals
    progress_updated = Signal(int, str)  # progress, current_file
    scan_result = Signal(str, str, str)  # file_path, status, details
    finished = Signal()
    error = Signal(str)

    def __init__(self, clamscan_path, email_files, scan_options):
        super().__init__()
        self.clamscan_path = clamscan_path
        self.email_files = email_files
        self.scan_options = scan_options
        self.is_cancelled = False

    def run(self):
        """Run the email scanning process."""
        try:
            total_files = len(self.email_files)

            for i, email_file in enumerate(self.email_files):
                if self.is_cancelled:
                    break

                # Update progress
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, email_file)

                # Scan the email file
                result = self.scan_email_file(email_file)
                self.scan_result.emit(email_file, result[0], result[1])

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def scan_email_file(self, email_file):
        """Scan a single email file and return (status, details)."""
        try:
            # Build clamscan command
            cmd = [self.clamscan_path]

            # Add scan options
            if self.scan_options.get('recursive', False):
                cmd.append('--recursive')
            if self.scan_options.get('archives', False):
                cmd.append('--archives')
            if self.scan_options.get('heuristics', True):
                cmd.append('--heuristic-alerts=yes')
            if self.scan_options.get('pua', False):
                cmd.append('--detect-pua=yes')

            # Add max file size if specified
            max_size = self.scan_options.get('max_file_size', 100)
            if max_size > 0:
                cmd.append(f'--max-filesize={max_size}M')

            # Add max scan time if specified
            max_time = self.scan_options.get('max_scan_time', 300)
            if max_time > 0:
                cmd.append(f'--max-scantime={max_time}')

            # Add file to scan
            cmd.append(email_file)

            # Run scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                return "CLEAN", "No threats detected"
            elif result.returncode == 1:
                return "INFECTED", result.stdout.strip()
            else:
                return "ERROR", f"Scan failed with code {result.returncode}: {result.stderr.strip()}"

        except subprocess.TimeoutExpired:
            return "ERROR", "Scan timed out"
        except Exception as e:
            return "ERROR", f"Scan error: {str(e)}"


class EmailScanTab(QWidget):
    """Email scanning tab for scanning email files and attachments."""

    def __init__(self, parent=None):
        """Initialize the email scan tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.scan_worker = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Vertical)

        # Top panel - Email file selection and options
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Email file selection
        file_group = QGroupBox(self.tr("Email Files"))
        file_layout = QVBoxLayout()

        # File selection controls
        file_select_layout = QHBoxLayout()

        self.email_path_input = QLineEdit()
        self.email_path_input.setPlaceholderText(self.tr("Select email file (.eml, .msg) or directory..."))
        file_select_layout.addWidget(self.email_path_input)

        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self.browse_email_files)
        file_select_layout.addWidget(browse_btn)

        file_layout.addLayout(file_select_layout)

        # Email file list
        self.email_files_list = QListWidget()
        self.email_files_list.setMaximumHeight(100)
        file_layout.addWidget(self.email_files_list)

        file_group.setLayout(file_layout)
        top_layout.addWidget(file_group)

        # Scan options
        options_group = QGroupBox(self.tr("Scan Options"))
        options_layout = QVBoxLayout()

        # Basic options
        basic_layout = QHBoxLayout()

        self.scan_attachments = QCheckBox(self.tr("Scan email attachments"))
        self.scan_attachments.setChecked(True)
        basic_layout.addWidget(self.scan_attachments)

        self.scan_headers = QCheckBox(self.tr("Scan email headers"))
        self.scan_headers.setChecked(True)
        basic_layout.addWidget(self.scan_headers)

        self.scan_body = QCheckBox(self.tr("Scan email body"))
        self.scan_body.setChecked(True)
        basic_layout.addWidget(self.scan_body)

        options_layout.addLayout(basic_layout)

        # Advanced options
        advanced_layout = QHBoxLayout()

        self.recursive_scan = QCheckBox(self.tr("Recursive scan"))
        self.recursive_scan.setChecked(False)
        advanced_layout.addWidget(self.recursive_scan)

        self.scan_archives = QCheckBox(self.tr("Scan archives"))
        self.scan_archives.setChecked(True)
        advanced_layout.addWidget(self.scan_archives)

        self.scan_heuristics = QCheckBox(self.tr("Heuristic analysis"))
        self.scan_heuristics.setChecked(True)
        advanced_layout.addWidget(self.scan_heuristics)

        options_layout.addLayout(advanced_layout)

        options_group.setLayout(options_layout)
        top_layout.addWidget(options_group)

        splitter.addWidget(top_widget)

        # Bottom panel - Scan results and progress
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        # Progress section
        progress_group = QGroupBox(self.tr("Scan Progress"))
        progress_layout = QVBoxLayout()

        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 100)
        self.scan_progress.setValue(0)
        self.scan_progress.setFormat("Ready - %p%")
        progress_layout.addWidget(self.scan_progress)

        # Current file label
        self.current_file_label = QLabel(self.tr("Ready to scan"))
        self.current_file_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        progress_layout.addWidget(self.current_file_label)

        progress_group.setLayout(progress_layout)
        bottom_layout.addWidget(progress_group)

        # Results section
        results_group = QGroupBox(self.tr("Scan Results"))
        results_layout = QVBoxLayout()

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels([
            self.tr("File"), self.tr("Status"), self.tr("Details")
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        results_layout.addWidget(self.results_table)

        results_group.setLayout(results_layout)
        bottom_layout.addWidget(results_group)

        # Scan output (collapsible)
        output_group = QGroupBox(self.tr("Detailed Output"))
        output_layout = QVBoxLayout()

        self.scan_output = QTextEdit()
        self.scan_output.setReadOnly(True)
        self.scan_output.setMaximumHeight(150)
        output_layout.addWidget(self.scan_output)

        output_group.setLayout(output_layout)
        bottom_layout.addWidget(output_group)

        splitter.addWidget(bottom_widget)

        # Set splitter proportions (30% top, 70% bottom)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        # Control buttons
        buttons_layout = QHBoxLayout()

        self.start_scan_btn = QPushButton(self.tr("Start Email Scan"))
        self.start_scan_btn.clicked.connect(self.start_email_scan)
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
        buttons_layout.addWidget(self.start_scan_btn)

        self.stop_scan_btn = QPushButton(self.tr("Stop Scan"))
        self.stop_scan_btn.setEnabled(False)
        self.stop_scan_btn.clicked.connect(self.stop_email_scan)
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
        buttons_layout.addWidget(self.stop_scan_btn)

        self.clear_results_btn = QPushButton(self.tr("Clear Results"))
        self.clear_results_btn.clicked.connect(self.clear_results)
        buttons_layout.addWidget(self.clear_results_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def browse_email_files(self):
        """Browse for email files or directories."""
        # Let user choose either file or directory
        dir_path = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"), "")
        if dir_path:
            self.email_path_input.setText(dir_path)
            self.load_email_files(dir_path)
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Select Email Files"),
            "", "Email Files (*.eml *.msg);;All Files (*)"
        )

        if file_paths:
            if len(file_paths) == 1:
                self.email_path_input.setText(file_paths[0])
            else:
                self.email_path_input.setText(f"{len(file_paths)} files selected")

            self.load_email_files_from_list(file_paths)

    def load_email_files(self, path):
        """Load email files from a directory."""
        if not os.path.exists(path):
            return

        email_files = []
        if os.path.isfile(path):
            if path.lower().endswith(('.eml', '.msg')):
                email_files.append(path)
        else:
            # Scan directory for email files
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(('.eml', '.msg')):
                        email_files.append(os.path.join(root, file))

        self.load_email_files_from_list(email_files)

    def load_email_files_from_list(self, file_paths):
        """Load email files from a list of paths."""
        self.email_files_list.clear()
        for file_path in file_paths:
            item = QListWidgetItem(file_path)
            item.setToolTip(file_path)
            self.email_files_list.addItem(item)

    def start_email_scan(self):
        """Start scanning email files."""
        # Get email files to scan
        email_files = []
        for i in range(self.email_files_list.count()):
            email_files.append(self.email_files_list.item(i).text())

        if not email_files:
            QMessageBox.warning(
                self, self.tr("No Files"),
                self.tr("Please select email files to scan.")
            )
            return

        # Get ClamAV executable path
        clamscan_path = self.get_clamscan_path()
        if not clamscan_path or not os.path.exists(clamscan_path):
            QMessageBox.critical(
                self, self.tr("ClamAV Not Found"),
                self.tr("ClamAV executable not found. Please check your installation.")
            )
            return

        # Prepare scan options
        scan_options = {
            'recursive': self.recursive_scan.isChecked(),
            'archives': self.scan_archives.isChecked(),
            'heuristics': self.scan_heuristics.isChecked(),
            'max_file_size': 100,  # MB
            'max_scan_time': 300,  # seconds
        }

        # Initialize UI for scanning
        self.scan_progress.setValue(0)
        self.scan_progress.setFormat("Starting scan...")
        self.current_file_label.setText(self.tr("Preparing scan..."))
        self.results_table.setRowCount(0)
        self.scan_output.clear()

        # Update button states
        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        self.clear_results_btn.setEnabled(False)

        # Start scan worker
        self.scan_worker = EmailScanWorker(clamscan_path, email_files, scan_options)
        self.scan_worker.progress_updated.connect(self.on_scan_progress)
        self.scan_worker.scan_result.connect(self.on_scan_result)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()

    def stop_email_scan(self):
        """Stop the current email scan."""
        if self.scan_worker:
            self.scan_worker.is_cancelled = True
            self.scan_worker.wait(1000)  # Wait up to 1 second
            self.stop_scan_btn.setEnabled(False)

    def on_scan_progress(self, progress, current_file):
        """Handle scan progress updates."""
        self.scan_progress.setValue(progress)
        self.scan_progress.setFormat(f"Scanning: %p%")
        self.current_file_label.setText(os.path.basename(current_file))

    def on_scan_result(self, file_path, status, details):
        """Handle individual scan results."""
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        # File name
        file_item = QTableWidgetItem(os.path.basename(file_path))
        self.results_table.setItem(row, 0, file_item)

        # Status with color coding
        status_item = QTableWidgetItem(status)
        if status == "CLEAN":
            status_item.setBackground(QtGui.QColor("#C8E6C9"))  # Light green
        elif status == "INFECTED":
            status_item.setBackground(QtGui.QColor("#FFCDD2"))  # Light red
        else:
            status_item.setBackground(QtGui.QColor("#FFF9C4"))  # Light yellow
        self.results_table.setItem(row, 1, status_item)

        # Details
        details_item = QTableWidgetItem(details[:100] + "..." if len(details) > 100 else details)
        self.results_table.setItem(row, 2, details_item)

        # Add to output
        self.scan_output.append(f"{os.path.basename(file_path)}: {status}")
        if details and status != "CLEAN":
            self.scan_output.append(f"  Details: {details}")
        self.scan_output.append("")

    def on_scan_finished(self):
        """Handle scan completion."""
        self.scan_progress.setFormat("Scan complete - %p%")
        self.current_file_label.setText(self.tr("Scan completed"))

        # Update button states
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.clear_results_btn.setEnabled(True)

        # Show completion message
        QMessageBox.information(
            self, self.tr("Scan Complete"),
            self.tr("Email scan completed successfully!")
        )

    def on_scan_error(self, error_message):
        """Handle scan errors."""
        self.scan_progress.setFormat("Error - %p%")
        self.current_file_label.setText(self.tr("Scan error"))

        # Update button states
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.clear_results_btn.setEnabled(True)

        # Show error message
        QMessageBox.critical(
            self, self.tr("Scan Error"),
            self.tr(f"Scan failed with error:\n\n{error_message}")
        )

    def clear_results(self):
        """Clear all scan results."""
        self.results_table.setRowCount(0)
        self.scan_output.clear()
        self.scan_progress.setValue(0)
        self.scan_progress.setFormat("Ready - %p%")
        self.current_file_label.setText(self.tr("Ready to scan"))

    def get_clamscan_path(self):
        """Get the path to clamscan executable."""
        # Try to get from settings first
        if hasattr(self.parent, 'settings') and self.parent.settings:
            settings = self.parent.settings.load_settings() or {}
            clamscan_path = settings.get('clamscan_path', '')
            if clamscan_path and os.path.exists(clamscan_path):
                return clamscan_path

        # Try common installation paths
        common_paths = [
            "clamscan",
            "/usr/bin/clamscan",
            "/usr/local/bin/clamscan",
            "C:\\Program Files\\ClamAV\\clamscan.exe",
            "C:\\Program Files (x86)\\ClamAV\\clamscan.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None
