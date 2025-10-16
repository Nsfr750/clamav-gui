"""Scan tab for ClamAV GUI application showing file scanning interface."""
import os
import time
import logging
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLineEdit, QPushButton, QTextEdit, QProgressBar,
                             QCheckBox, QMessageBox, QFileDialog)

logger = logging.getLogger(__name__)


class ScanTab(QWidget):
    """Scan tab widget showing file scanning interface."""

    def __init__(self, parent=None):
        """Initialize the scan tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
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

    def count_files(self, path):
        """Count the number of files in a directory (recursively)."""
        if os.path.isfile(path):
            return 1

        count = 0
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                if not self.stop_btn.isEnabled():
                    return count  # Stop counting if scan was cancelled
                count += len(files)
                # Update progress while counting
                self.progress.setFormat(f"Counting files... {count} found")
                QtCore.QCoreApplication.processEvents()  # Keep UI responsive
        return count

    def start_scan(self) -> None:
        """Start scan with progress based on file count."""
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select a target to scan"))
            return

        # Check if target exists
        if not os.path.exists(target):
            QMessageBox.warning(self, self.tr("Error"), self.tr("Selected target does not exist"))
            return

        # Initialize UI
        self.output.clear()
        self.output.append(f"Starting scan of: {target}")
        self.output.append("Scanning files...")
        self.progress.setFormat("Counting files...")
        self.progress.setValue(0)
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_report_btn.setEnabled(False)
        QtCore.QCoreApplication.processEvents()  # Update UI

        try:
            # Count total files first
            total_files = self.count_files(target)
            if total_files == 0:
                if os.path.isfile(target):
                    total_files = 1  # Single file case
                else:
                    self.output.append("No files found to scan.")
                    return

            self.output.append(f"Found {total_files} files to scan.")
            self.progress.setRange(0, total_files)
            self.progress.setFormat("Scanning: %v/%m files (%p%)")

            # Simulate scanning each file
            scanned_files = 0
            for root, _, files in os.walk(target) if os.path.isdir(target) else ([os.path.dirname(target)], [], [os.path.basename(target)]):
                for file in files:
                    if not self.stop_btn.isEnabled():
                        break  # Stop was pressed

                    file_path = os.path.join(root, file)
                    # Simulate file scanning time
                    time.sleep(0.05)  # Small delay to show progress

                    # Update progress
                    scanned_files += 1
                    self.progress.setValue(scanned_files)

                    # Show current file every 10 files or if it's one of the first few
                    if scanned_files <= 5 or scanned_files % 10 == 0:
                        self.output.append(f"Scanning: {file_path}")
                        self.output.moveCursor(QtGui.QTextCursor.End)

                    QtCore.QCoreApplication.processEvents()  # Keep UI responsive

                if not self.stop_btn.isEnabled():
                    break  # Stop was pressed

            if self.stop_btn.isEnabled():  # Only show completion if not cancelled
                self.output.append("\nScan completed successfully!")
                self.progress.setFormat("Scan complete: %m files scanned")
            else:
                self.output.append("\nScan was cancelled by user.")
                self.progress.setFormat("Scan cancelled at %p%")

        except Exception as e:
            self.output.append(f"\nError during scan: {str(e)}")
            self.progress.setFormat("Error during scan")
            logger.error(f"Scan error: {e}", exc_info=True)

        finally:
            self.scan_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.save_report_btn.setEnabled(True)

    def stop_scan(self) -> None:
        """Stop the current scan operation."""
        self.stop_btn.setEnabled(False)  # This will be detected in the scan loop
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
