"""
Scan tab for ClamAV GUI application showing file scanning interface.
"""
import os
import time
import logging
import subprocess
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLineEdit, QPushButton, QTextEdit, QProgressBar,
                             QCheckBox, QMessageBox, QFileDialog)
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Worker thread for file scanning operations."""

    # Signals
    progress_updated = Signal(int, str)  # progress, current_file
    scan_result = Signal(str, str, str)  # file_path, status, details
    finished = Signal()
    error = Signal(str)

    def __init__(self, clamscan_path, target_path, scan_options):
        super().__init__()
        self.clamscan_path = clamscan_path
        self.target_path = target_path
        self.scan_options = scan_options
        self.is_cancelled = False

    def run(self):
        """Run the scanning process."""
        try:
            # Get list of files to scan
            files_to_scan = self.get_files_to_scan()

            if not files_to_scan:
                self.error.emit("No files found to scan")
                return

            total_files = len(files_to_scan)

            for i, file_path in enumerate(files_to_scan):
                if self.is_cancelled:
                    break

                # Update progress
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, file_path)

                # Scan the file
                result = self.scan_file(file_path)
                self.scan_result.emit(file_path, result[0], result[1])

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def get_files_to_scan(self):
        """Get list of files to scan based on target path and options."""
        files_to_scan = []

        if os.path.isfile(self.target_path):
            files_to_scan.append(self.target_path)
        else:
            # Walk directory tree
            for root, dirs, files in os.walk(self.target_path):
                # Skip directories if not recursive
                if not self.scan_options.get('recursive', True) and root != self.target_path:
                    dirs.clear()
                    continue

                for file in files:
                    file_path = os.path.join(root, file)

                    # Apply file size filter if specified
                    max_size = self.scan_options.get('max_file_size', 100)  # MB
                    if max_size > 0:
                        try:
                            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                            if file_size_mb > max_size:
                                continue
                        except (OSError, IOError):
                            continue

                    files_to_scan.append(file_path)

        return files_to_scan

    def scan_file(self, file_path):
        """Scan a single file and return (status, details)."""
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
            if self.scan_options.get('smart_scan', False):
                cmd.append('--skip-hashes')

            # Add max file size if specified
            max_size = self.scan_options.get('max_file_size', 100)
            if max_size > 0:
                cmd.append(f'--max-filesize={max_size}M')

            # Add max scan time if specified
            max_time = self.scan_options.get('max_scan_time', 300)
            if max_time > 0:
                cmd.append(f'--max-scantime={max_time}')

            # Add file to scan
            cmd.append(file_path)

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


class ScanTab(QWidget):
    """Scan tab widget showing file scanning interface."""

    def __init__(self, parent=None):
        """Initialize the scan tab.

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

        # Target selection
        target_group = QGroupBox(self.tr("Scan Target"))
        target_layout = QHBoxLayout()

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText(self.tr("Select a file or directory to scan..."))
        target_layout.addWidget(self.target_input)

        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self.browse_target)
        target_layout.addWidget(browse_btn)

        target_group.setLayout(target_layout)

        # Scan options
        options_group = QGroupBox(self.tr("Scan Options"))
        options_layout = QVBoxLayout()

        self.recursive_scan = QCheckBox(self.tr("Scan subdirectories"))
        self.recursive_scan.setChecked(True)
        options_layout.addWidget(self.recursive_scan)

        self.heuristic_scan = QCheckBox(self.tr("Enable heuristic scan"))
        self.heuristic_scan.setChecked(True)
        options_layout.addWidget(self.heuristic_scan)

        self.enable_smart_scanning = QCheckBox(self.tr("Enable smart scanning (skip known safe files)"))
        self.enable_smart_scanning.setChecked(False)
        self.enable_smart_scanning.setToolTip(self.tr("Use hash database to skip files that have been previously scanned and confirmed safe"))
        options_layout.addWidget(self.enable_smart_scanning)

        # Advanced scan options
        self.scan_archives = QCheckBox(self.tr("Scan archives (zip, rar, etc.)"))
        self.scan_archives.setChecked(True)
        options_layout.addWidget(self.scan_archives)

        self.scan_pua = QCheckBox(self.tr("Scan potentially unwanted applications (PUA)"))
        self.scan_pua.setChecked(False)
        self.scan_pua.setToolTip(self.tr("Enable scanning for potentially unwanted applications"))
        options_layout.addWidget(self.scan_pua)

        options_group.setLayout(options_layout)

        # Output
        output_group = QGroupBox(self.tr("Output"))
        output_layout = QVBoxLayout()

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        output_layout.addWidget(self.output)

        output_group.setLayout(output_layout)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)  # 0-100% range
        self.progress.setValue(0)  # Start at 0%
        self.progress.setFormat("Idle - %p%")
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4CAF50, stop: 0.5 #2196F3, stop: 1 #4CAF50);
                border-radius: 3px;
                width: 10px;  /* Width of each chunk */
            }
        """)

        # Buttons
        button_layout = QHBoxLayout()

        self.scan_btn = QPushButton(self.tr("Start Scan"))
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setStyleSheet("""
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
        button_layout.addWidget(self.scan_btn)

        self.stop_btn = QPushButton(self.tr("Stop"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setStyleSheet("""
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
        button_layout.addWidget(self.stop_btn)

        # Report buttons
        self.save_report_btn = QPushButton(self.tr("Save Report"))
        self.save_report_btn.setEnabled(False)
        self.save_report_btn.clicked.connect(self.save_scan_report)
        button_layout.addWidget(self.save_report_btn)

        self.view_quarantine_btn = QPushButton(self.tr("View Quarantine"))
        self.view_quarantine_btn.clicked.connect(self.show_quarantine_dialog)
        button_layout.addWidget(self.view_quarantine_btn)

        # Add all to main layout
        layout.addWidget(target_group)
        layout.addWidget(options_group)
        layout.addWidget(output_group)
        layout.addWidget(self.progress)
        layout.addLayout(button_layout)
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Target selection
        target_group = QGroupBox(self.tr("Scan Target"))
        target_layout = QHBoxLayout()

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText(self.tr("Select a file or directory to scan..."))
        target_layout.addWidget(self.target_input)

        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self.browse_target)
        target_layout.addWidget(browse_btn)

        target_group.setLayout(target_layout)

        # Scan options
        options_group = QGroupBox(self.tr("Scan Options"))
        options_layout = QVBoxLayout()

        self.recursive_scan = QCheckBox(self.tr("Scan subdirectories"))
        self.recursive_scan.setChecked(True)
        options_layout.addWidget(self.recursive_scan)

        self.heuristic_scan = QCheckBox(self.tr("Enable heuristic scan"))
        self.heuristic_scan.setChecked(True)
        options_layout.addWidget(self.heuristic_scan)

        self.enable_smart_scanning = QCheckBox(self.tr("Enable smart scanning (skip known safe files)"))
        self.enable_smart_scanning.setChecked(False)
        self.enable_smart_scanning.setToolTip(self.tr("Use hash database to skip files that have been previously scanned and confirmed safe"))
        options_layout.addWidget(self.enable_smart_scanning)

        # Advanced scan options
        self.scan_archives = QCheckBox(self.tr("Scan archives (zip, rar, etc.)"))
        self.scan_archives.setChecked(True)
        options_layout.addWidget(self.scan_archives)

        self.scan_pua = QCheckBox(self.tr("Scan potentially unwanted applications (PUA)"))
        self.scan_pua.setChecked(False)
        self.scan_pua.setToolTip(self.tr("Enable scanning for potentially unwanted applications"))
        options_layout.addWidget(self.scan_pua)

        options_group.setLayout(options_layout)

        # Output
        output_group = QGroupBox(self.tr("Output"))
        output_layout = QVBoxLayout()

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        output_layout.addWidget(self.output)

        output_group.setLayout(output_layout)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)  # 0-100% range
        self.progress.setValue(0)  # Start at 0%
        self.progress.setFormat("Idle - %p%")
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4CAF50, stop: 0.5 #2196F3, stop: 1 #4CAF50);
                border-radius: 3px;
                width: 10px;  /* Width of each chunk */
            }
        """)

        # Buttons
        button_layout = QHBoxLayout()

        self.scan_btn = QPushButton(self.tr("Start Scan"))
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setStyleSheet("""
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
        button_layout.addWidget(self.scan_btn)

        self.stop_btn = QPushButton(self.tr("Stop"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setStyleSheet("""
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
        button_layout.addWidget(self.stop_btn)

        # Report buttons
        self.save_report_btn = QPushButton(self.tr("Save Report"))
        self.save_report_btn.setEnabled(False)
        self.save_report_btn.clicked.connect(self.save_scan_report)
        button_layout.addWidget(self.save_report_btn)

        self.view_quarantine_btn = QPushButton(self.tr("View Quarantine"))
        self.view_quarantine_btn.clicked.connect(self.show_quarantine_dialog)
        button_layout.addWidget(self.view_quarantine_btn)

        # Add all to main layout
        layout.addWidget(target_group)
        layout.addWidget(options_group)
        layout.addWidget(output_group)
        layout.addWidget(self.progress)
        layout.addLayout(button_layout)

        return

    def browse_target(self) -> None:
        """Browse for scan target."""
        # Let user choose either file or directory; prefer dir first
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan", "")
        if dir_path:
            self.target_input.setText(dir_path)
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Scan", "", "All Files (*.*)")
        if file_path:
            self.target_input.setText(file_path)

    def start_scan(self) -> None:
        """Start scan with actual ClamAV scanning."""
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select a target to scan"))
            return

        # Check if target exists
        if not os.path.exists(target):
            QMessageBox.warning(self, self.tr("Error"), self.tr("Selected target does not exist"))
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
            'heuristics': self.heuristic_scan.isChecked(),
            'pua': self.scan_pua.isChecked(),
            'smart_scan': self.enable_smart_scanning.isChecked(),
            'max_file_size': 100,  # MB
            'max_scan_time': 300,  # seconds
        }

        # Initialize UI
        self.output.clear()
        self.output.append(f"Starting ClamAV scan of: {target}")
        self.output.append("Initializing scan...")
        self.progress.setFormat("Preparing scan...")
        self.progress.setValue(0)
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_report_btn.setEnabled(False)
        QtCore.QCoreApplication.processEvents()  # Update UI

        # Start scan worker
        self.scan_worker = ScanWorker(clamscan_path, target, scan_options)
        self.scan_worker.progress_updated.connect(self.on_scan_progress)
        self.scan_worker.scan_result.connect(self.on_scan_result)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()

    def on_scan_progress(self, progress, current_file):
        """Handle scan progress updates."""
        self.progress.setValue(progress)
        self.progress.setFormat(f"Scanning: {os.path.basename(current_file)} - %p%")

    def on_scan_result(self, file_path, status, details):
        """Handle individual scan results."""
        # Add to output with color coding
        if status == "CLEAN":
            self.output.append(f"✓ {os.path.basename(file_path)}: CLEAN")
        elif status == "INFECTED":
            self.output.append(f"✗ {os.path.basename(file_path)}: INFECTED")
            if details:
                self.output.append(f"  Threat: {details}")
        else:
            self.output.append(f"⚠ {os.path.basename(file_path)}: {status}")
            if details:
                self.output.append(f"  Details: {details}")
        self.output.append("")

    def on_scan_finished(self):
        """Handle scan completion."""
        self.progress.setFormat("Scan complete - %p%")
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_report_btn.setEnabled(True)

        # Show completion message
        QMessageBox.information(
            self, self.tr("Scan Complete"),
            self.tr("ClamAV scan completed successfully!")
        )

    def on_scan_error(self, error_message):
        """Handle scan errors."""
        self.progress.setFormat("Error - %p%")
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_report_btn.setEnabled(True)

        # Show error message
        QMessageBox.critical(
            self, self.tr("Scan Error"),
            self.tr(f"Scan failed with error:\n\n{error_message}")
        )

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

    def stop_scan(self) -> None:
        """Stop the current scan operation."""
        if self.scan_worker:
            self.scan_worker.is_cancelled = True
            self.scan_worker.wait(1000)  # Wait up to 1 second
        self.stop_btn.setEnabled(False)
        self.output.append("Stopping scan...")
        self.progress.setFormat("Stopping...")
        QtCore.QCoreApplication.processEvents()  # Update UI immediately

    def save_scan_report(self) -> None:
        """Save scan report (simplified version for scan_tab.py)."""
        text = self.output.toPlainText()
        if not text:
            QMessageBox.information(self, self.tr("Info"), self.tr("No scan output to save"))
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save Scan Report"), "scan_report.txt", "Text Files (*.txt);;All Files (*)"
        )

        if file_name:
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write("ClamAV GUI Scan Report (Scan Tab)\n")
                    f.write("=" * 40 + "\n\n")
                    f.write(f"Scan Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Target: {self.target_input.text()}\n")
                    f.write(f"Options: Recursive={self.recursive_scan.isChecked()}, ")
                    f.write(f"Heuristics={self.heuristic_scan.isChecked()}, ")
                    f.write(f"Archives={self.scan_archives.isChecked()}, ")
                    f.write(f"PUA={self.scan_pua.isChecked()}\n\n")
                    f.write("Scan Output:\n")
                    f.write("-" * 20 + "\n")
                    f.write(text)

                QMessageBox.information(
                    self, self.tr("Report Saved"),
                    self.tr(f"Scan report saved successfully:\n{file_name}")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, self.tr("Error"),
                    self.tr(f"Failed to save scan report:\n{e}")
                )
    
    def show_quarantine_dialog(self) -> None:
        """Show quarantine dialog (simplified version for scan_tab.py)."""
        QMessageBox.information(
            self, self.tr("Quarantine Management"),
            self.tr(
                "Quarantine management is available in the full ClamAV GUI application.\n\n"
                "This simplified version shows basic status information only.\n\n"
                "For full quarantine functionality, use the main ClamAV GUI application."
            )
        )
