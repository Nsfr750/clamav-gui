"""
Smart Scanning tab for ClamAV GUI.
Provides UI for smart scanning using hash databases for efficiency.
"""
import os
import logging
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QTextEdit, QProgressBar, QCheckBox, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QFormLayout,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFileDialog, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QScrollArea, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

from clamav_gui.utils.smart_scanning import SmartScanner, SmartScanThread

logger = logging.getLogger(__name__)


class SmartScanningTab(QWidget):
    """Smart Scanning tab widget."""

    def __init__(self, parent=None):
        """Initialize the smart scanning tab.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.smart_scanner = None
        self.scan_thread = None
        self.scan_items = []
        self.scan_results = []

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.connect_signals()

        # Initialize smart scanner
        self.initialize_scanner()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)

        # Top section - Item management and controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Item selection section
        items_group = QGroupBox(self.tr("Items to Scan"))
        items_layout = QVBoxLayout()

        # Directory/file input
        input_layout = QHBoxLayout()
        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText(self.tr("Enter file/directory path or use browse button..."))
        input_layout.addWidget(self.item_input)

        browse_btn = QPushButton(self.tr("Browse"))
        browse_btn.clicked.connect(self.browse_item)
        input_layout.addWidget(browse_btn)

        items_layout.addLayout(input_layout)

        # Items list
        self.items_list = QListWidget()
        self.items_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.items_list.setMaximumHeight(150)
        items_layout.addWidget(self.items_list)

        # Item management buttons
        item_btn_layout = QHBoxLayout()

        add_item_btn = QPushButton(self.tr("Add Item"))
        add_item_btn.clicked.connect(self.add_item)
        item_btn_layout.addWidget(add_item_btn)

        remove_item_btn = QPushButton(self.tr("Remove Selected"))
        remove_item_btn.clicked.connect(self.remove_selected_items)
        item_btn_layout.addWidget(remove_item_btn)

        clear_items_btn = QPushButton(self.tr("Clear All"))
        clear_items_btn.clicked.connect(self.clear_items)
        item_btn_layout.addWidget(clear_items_btn)

        items_layout.addLayout(item_btn_layout)
        items_group.setLayout(items_layout)
        top_layout.addWidget(items_group)

        # Scan controls
        controls_group = QGroupBox(self.tr("Scan Controls"))
        controls_layout = QVBoxLayout()

        # Scan buttons
        scan_btn_layout = QHBoxLayout()

        self.start_scan_btn = QPushButton(self.tr("Start Smart Scan"))
        self.start_scan_btn.clicked.connect(self.start_scan)
        self.start_scan_btn.setStyleSheet("QPushButton { font-weight: bold; color: green; }")
        scan_btn_layout.addWidget(self.start_scan_btn)

        self.stop_scan_btn = QPushButton(self.tr("Stop Scan"))
        self.stop_scan_btn.clicked.connect(self.stop_scan)
        self.stop_scan_btn.setEnabled(False)
        self.stop_scan_btn.setStyleSheet("QPushButton { font-weight: bold; color: red; }")
        scan_btn_layout.addWidget(self.stop_scan_btn)

        controls_layout.addLayout(scan_btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        controls_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel(self.tr("Ready"))
        self.status_label.setStyleSheet("QLabel { font-weight: bold; }")
        controls_layout.addWidget(self.status_label)

        controls_group.setLayout(controls_layout)
        top_layout.addWidget(controls_group)

        splitter.addWidget(top_widget)

        # Bottom section - Results
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        # Results section
        results_group = QGroupBox(self.tr("Scan Results"))
        results_layout = QVBoxLayout()

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            self.tr("File"), self.tr("Result"), self.tr("Output"), self.tr("Skipped")
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        results_layout.addWidget(self.results_table)

        # Results summary
        summary_layout = QHBoxLayout()

        self.summary_label = QLabel(self.tr("No scans performed yet"))
        summary_layout.addWidget(self.summary_label)

        summary_layout.addStretch()

        clear_results_btn = QPushButton(self.tr("Clear Results"))
        clear_results_btn.clicked.connect(self.clear_results)
        summary_layout.addWidget(clear_results_btn)

        results_layout.addLayout(summary_layout)

        results_group.setLayout(results_layout)
        bottom_layout.addWidget(results_group)

        splitter.addWidget(bottom_widget)

        # Set splitter proportions
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

    def connect_signals(self):
        """Connect widget signals."""
        pass

    def initialize_scanner(self):
        """Initialize the smart scanner."""
        try:
            self.smart_scanner = SmartScanner()
            logger.info("Smart scanner initialized")
        except Exception as e:
            logger.error(f"Failed to initialize smart scanner: {e}")
            QMessageBox.critical(self, self.tr("Error"), f"Failed to initialize smart scanner: {str(e)}")

    def browse_item(self):
        """Browse for a file or directory to add."""
        path = QFileDialog.getExistingDirectory(self, self.tr("Select Directory")) or QFileDialog.getOpenFileName(self, self.tr("Select File"))[0]
        if path:
            self.item_input.setText(path)

    def add_item(self):
        """Add an item to the scan list."""
        item_path = self.item_input.text().strip()
        if not item_path:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Please enter a file or directory path."))
            return

        if not os.path.exists(item_path):
            QMessageBox.warning(self, self.tr("Warning"), self.tr("The specified path does not exist."))
            return

        if item_path not in self.scan_items:
            self.scan_items.append(item_path)
            self.items_list.addItem(item_path)
            self.item_input.clear()
        else:
            QMessageBox.information(self, self.tr("Information"), self.tr("Item already in the list."))

    def remove_selected_items(self):
        """Remove selected items from the scan list."""
        selected_items = self.items_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Please select items to remove."))
            return

        for item in selected_items:
            row = self.items_list.row(item)
            self.items_list.takeItem(row)
            if row < len(self.scan_items):
                del self.scan_items[row]

    def clear_items(self):
        """Clear all items from the scan list."""
        self.scan_items.clear()
        self.items_list.clear()

    def start_scan(self):
        """Start the smart scan."""
        if not self.scan_items:
            QMessageBox.warning(self, self.tr("Warning"), self.tr("Please add items to scan first."))
            return

        if self.scan_thread and self.scan_thread.isRunning():
            QMessageBox.information(self, self.tr("Information"), self.tr("A scan is already in progress."))
            return

        # Clear previous results
        self.clear_results()

        # Update UI
        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(self.tr("Starting scan..."))

        # Start scan thread
        self.scan_thread = SmartScanThread(self.smart_scanner, self.scan_items)
        self.scan_thread.progress_updated.connect(self.update_progress)
        self.scan_thread.scan_finished.connect(self.scan_finished)
        self.scan_thread.file_scanned.connect(self.file_scanned)
        self.scan_thread.start()

    def stop_scan(self):
        """Stop the current scan."""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.terminate()
            self.scan_thread.wait()

        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(self.tr("Scan stopped"))

    def update_progress(self, progress, status):
        """Update the progress bar and status."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)

    def file_scanned(self, file_path, result, output):
        """Handle a scanned file."""
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        self.results_table.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
        self.results_table.setItem(row, 1, QTableWidgetItem(result))
        self.results_table.setItem(row, 2, QTableWidgetItem(output))
        self.results_table.setItem(row, 3, QTableWidgetItem("Yes" if "SKIPPED" in result else "No"))

        # Scroll to bottom
        self.results_table.scrollToBottom()

    def scan_finished(self, results):
        """Handle scan completion."""
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # Update summary
        summary = (
            f"Total: {results['total_files']}, "
            f"Scanned: {results['scanned_files']}, "
            f"Skipped: {results['skipped_files']}, "
            f"Clean: {results['clean_files']}, "
            f"Infected: {results['infected_files']}, "
            f"Errors: {results['errors']}"
        )
        self.summary_label.setText(summary)

        self.status_label.setText(self.tr("Scan completed"))

        # Show completion message
        QMessageBox.information(
            self,
            self.tr("Scan Completed"),
            f"Smart scan completed!\n\n{summary}"
        )

    def clear_results(self):
        """Clear scan results."""
        self.results_table.setRowCount(0)
        self.summary_label.setText(self.tr("No scans performed yet"))
        self.scan_results.clear()

    def tr(self, text):
        """Translate text (placeholder for translation system)."""
        return text
