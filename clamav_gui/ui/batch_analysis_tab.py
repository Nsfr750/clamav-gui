"""
Batch Analysis tab for ClamAV GUI.
Provides UI for batch scanning multiple files and directories.
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

from clamav_gui.utils.batch_analysis import BatchAnalyzer, BatchAnalysisThread

logger = logging.getLogger(__name__)


class BatchAnalysisTab(QWidget):
    """Batch Analysis tab for scanning multiple files and directories."""

    def __init__(self, parent=None):
        """Initialize the batch analysis tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.batch_analyzer = None
        self.analysis_thread = None
        self.batch_items = []
        self.analysis_results = []

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.connect_signals()

        # Initialize batch analyzer
        self.initialize_analyzer()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)

        # Top section - Item management and controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Item selection section
        items_group = QGroupBox(self.tr("Items to Analyze"))
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

        # Batch settings section
        settings_group = QGroupBox(self.tr("Batch Settings"))
        settings_layout = QVBoxLayout()

        # Basic options
        basic_layout = QHBoxLayout()

        self.recursive_scan = QCheckBox(self.tr("Recursive scan"))
        self.recursive_scan.setChecked(True)
        self.recursive_scan.setToolTip(self.tr("Scan subdirectories recursively"))
        basic_layout.addWidget(self.recursive_scan)

        self.scan_archives = QCheckBox(self.tr("Scan archives"))
        self.scan_archives.setChecked(True)
        self.scan_archives.setToolTip(self.tr("Scan inside archive files"))
        basic_layout.addWidget(self.scan_archives)

        self.heuristic_scan = QCheckBox(self.tr("Heuristic analysis"))
        self.heuristic_scan.setChecked(True)
        self.heuristic_scan.setToolTip(self.tr("Enable heuristic threat detection"))
        basic_layout.addWidget(self.heuristic_scan)

        settings_layout.addLayout(basic_layout)

        # Advanced options
        advanced_layout = QHBoxLayout()

        self.scan_pua = QCheckBox(self.tr("Scan PUA"))
        self.scan_pua.setChecked(False)
        self.scan_pua.setToolTip(self.tr("Scan for potentially unwanted applications"))
        advanced_layout.addWidget(self.scan_pua)

        self.parallel_processing = QCheckBox(self.tr("Parallel processing"))
        self.parallel_processing.setChecked(False)
        self.parallel_processing.setToolTip(self.tr("Process multiple items simultaneously (experimental)"))
        advanced_layout.addWidget(self.parallel_processing)

        settings_layout.addLayout(advanced_layout)

        # Performance settings
        perf_layout = QFormLayout()

        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(1, 1000)
        self.max_file_size.setValue(100)
        self.max_file_size.setSuffix(" MB")
        self.max_file_size.setToolTip(self.tr("Maximum file size to scan"))
        perf_layout.addRow(self.tr("Max file size:"), self.max_file_size)

        self.max_scan_time = QSpinBox()
        self.max_scan_time.setRange(60, 3600)
        self.max_scan_time.setValue(300)
        self.max_scan_time.setSuffix(" sec")
        self.max_scan_time.setToolTip(self.tr("Maximum scan time per item"))
        perf_layout.addRow(self.tr("Max scan time:"), self.max_scan_time)

        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 50)
        self.batch_size.setValue(10)
        self.batch_size.setToolTip(self.tr("Number of items to process in each batch"))
        perf_layout.addRow(self.tr("Batch size:"), self.batch_size)

        settings_layout.addLayout(perf_layout)

        # Exclude patterns
        self.exclude_patterns = QLineEdit()
        self.exclude_patterns.setPlaceholderText(self.tr("*.log,*.tmp,*.cache"))
        self.exclude_patterns.setToolTip(self.tr("Comma-separated patterns to exclude"))
        settings_layout.addWidget(QLabel(self.tr("Exclude patterns:")))
        settings_layout.addWidget(self.exclude_patterns)

        settings_group.setLayout(settings_layout)
        top_layout.addWidget(settings_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self.start_analysis_btn = QPushButton(self.tr("Start Batch Analysis"))
        self.start_analysis_btn.clicked.connect(self.start_batch_analysis)
        self.start_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)
        control_layout.addWidget(self.start_analysis_btn)

        self.stop_analysis_btn = QPushButton(self.tr("Stop Analysis"))
        self.stop_analysis_btn.setEnabled(False)
        self.stop_analysis_btn.clicked.connect(self.stop_batch_analysis)
        self.stop_analysis_btn.setStyleSheet("""
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
        control_layout.addWidget(self.stop_analysis_btn)

        self.clear_results_btn = QPushButton(self.tr("Clear Results"))
        self.clear_results_btn.clicked.connect(self.clear_results)
        control_layout.addWidget(self.clear_results_btn)

        self.export_report_btn = QPushButton(self.tr("Export Report"))
        self.export_report_btn.setEnabled(False)
        self.export_report_btn.clicked.connect(self.export_batch_report)
        control_layout.addWidget(self.export_report_btn)

        top_layout.addLayout(control_layout)

        # Progress bar
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setRange(0, 100)
        self.analysis_progress.setValue(0)
        top_layout.addWidget(self.analysis_progress)

        splitter.addWidget(top_widget)

        # Bottom section - Results display
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        # Results tabs
        self.results_tabs = QTabWidget()

        # Analysis results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)

        self.analysis_output = QTextEdit()
        self.analysis_output.setReadOnly(True)
        self.analysis_output.setFont(QFont("Courier", 9))
        results_layout.addWidget(self.analysis_output)

        self.results_tabs.addTab(results_tab, self.tr("Analysis Results"))

        # Statistics tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)

        self.stats_tree = QTreeWidget()
        self.stats_tree.setHeaderLabels([self.tr("Statistic"), self.tr("Value")])
        self.stats_tree.setAlternatingRowColors(True)
        stats_layout.addWidget(self.stats_tree)

        self.results_tabs.addTab(stats_tab, self.tr("Statistics"))

        # Items status tab
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)

        self.items_status_table = QTableWidget()
        self.items_status_table.setColumnCount(4)
        self.items_status_table.setHorizontalHeaderLabels([
            self.tr("Item"), self.tr("Status"), self.tr("Threats"), self.tr("Scan Time")
        ])
        self.items_status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        status_layout.addWidget(self.items_status_table)

        self.results_tabs.addTab(status_tab, self.tr("Items Status"))

        bottom_layout.addWidget(self.results_tabs)

        splitter.addWidget(bottom_widget)

        # Set splitter proportions
        splitter.setSizes([500, 700])

        layout.addWidget(splitter)

    def initialize_analyzer(self):
        """Initialize the batch analyzer."""
        try:
            # Get clamscan path from settings if available
            clamscan_path = getattr(self.parent, 'clamscan_path', None) if self.parent else None
            clamscan_path = clamscan_path.text() if clamscan_path else "clamscan"

            self.batch_analyzer = BatchAnalyzer(clamscan_path)
            logger.info("Batch analyzer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize batch analyzer: {e}")
            QMessageBox.critical(
                self, self.tr("Initialization Error"),
                self.tr(f"Failed to initialize batch analyzer:\n\n{str(e)}")
            )

    def browse_item(self):
        """Browse for a file or directory to add."""
        # Try to get a directory first
        item_path = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"))

        if not item_path:
            # If no directory selected, try for a file
            file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Select File"), "", self.tr("All Files (*)"))
            if file_path:
                item_path = file_path

        if item_path:
            self.item_input.setText(item_path)

    def add_item(self):
        """Add an item to the batch analysis list."""
        item_path = self.item_input.text().strip()

        if not item_path:
            QMessageBox.warning(self, self.tr("No Item"), self.tr("Please enter an item path first"))
            return

        if not os.path.exists(item_path):
            QMessageBox.warning(self, self.tr("Item Not Found"), self.tr(f"Item not found: {item_path}"))
            return

        # Check if item already in list
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            if item.data(Qt.UserRole) == item_path:
                QMessageBox.information(self, self.tr("Duplicate"), self.tr("Item already in analysis list"))
                return

        # Add to list
        item_name = os.path.basename(item_path)
        if os.path.isdir(item_path):
            item_name += "/"

        item = QListWidgetItem(item_name)
        item.setData(Qt.UserRole, item_path)  # Store full path
        item.setToolTip(item_path)
        self.items_list.addItem(item)

        # Clear the input field
        self.item_input.clear()

    def remove_selected_items(self):
        """Remove selected items from the analysis list."""
        selected_items = self.items_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select items to remove"))
            return

        for item in selected_items:
            row = self.items_list.row(item)
            self.items_list.takeItem(row)

    def clear_items(self):
        """Clear all items from the analysis list."""
        reply = QMessageBox.question(
            self, self.tr("Clear List"),
            self.tr("Are you sure you want to clear all items from the analysis list?"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.items_list.clear()
            self.batch_items = []

    def start_batch_analysis(self):
        """Start batch analysis of selected items."""
        if not self.batch_analyzer:
            QMessageBox.warning(self, self.tr("Not Ready"), self.tr("Batch analyzer not initialized"))
            return

        # Get items to analyze
        batch_items = []
        for i in range(self.items_list.count()):
            item = self.items_list.item(i)
            item_path = item.data(Qt.UserRole)
            if item_path and os.path.exists(item_path):
                batch_items.append(item_path)
            else:
                self.analysis_output.append(f"Warning: Item not found or inaccessible: {item_path}")

        if not batch_items:
            QMessageBox.warning(self, self.tr("No Items"), self.tr("No valid items to analyze"))
            return

        # Prepare analysis options
        options = {
            'recursive': self.recursive_scan.isChecked(),
            'scan_archives': self.scan_archives.isChecked(),
            'heuristic_scan': self.heuristic_scan.isChecked(),
            'scan_pua': self.scan_pua.isChecked(),
            'parallel_processing': self.parallel_processing.isChecked(),
            'max_file_size': self.max_file_size.value(),
            'max_scan_time': self.max_scan_time.value(),
            'batch_size': self.batch_size.value(),
            'exclude_patterns': self.exclude_patterns.text().strip()
        }

        # Disable controls during analysis
        self.set_controls_enabled(False)

        # Clear previous results
        self.analysis_output.clear()
        self.stats_tree.clear()
        self.items_status_table.clearContents()
        self.items_status_table.setRowCount(0)
        self.analysis_results = []

        # Create and start analysis thread
        self.analysis_thread = BatchAnalysisThread(self.batch_analyzer, batch_items, options)

        # Connect thread signals
        self.analysis_thread.update_progress.connect(self.update_progress)
        self.analysis_thread.update_output.connect(self.update_output)
        self.analysis_thread.item_finished.connect(self.on_item_finished)
        self.analysis_thread.analysis_finished.connect(self.on_analysis_finished)

        # Start the analysis
        self.analysis_thread.start()

        self.analysis_output.append(f"Starting batch analysis of {len(batch_items)} items...")

    def stop_batch_analysis(self):
        """Stop the current batch analysis."""
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.terminate()
            self.analysis_thread.wait(5000)  # Wait up to 5 seconds

            self.analysis_output.append("Batch analysis stopped by user")
            self.set_controls_enabled(True)

    def clear_results(self):
        """Clear all analysis results."""
        self.analysis_output.clear()
        self.stats_tree.clear()
        self.items_status_table.clearContents()
        self.items_status_table.setRowCount(0)
        self.analysis_results = []
        self.export_report_btn.setEnabled(False)

    def export_batch_report(self):
        """Export batch analysis results to a file."""
        if not self.analysis_results:
            QMessageBox.warning(self, self.tr("No Results"), self.tr("No analysis results to export"))
            return

        # Generate report
        stats = self.batch_analyzer.get_batch_statistics(self.analysis_results)
        report = self.batch_analyzer.generate_batch_report(self.analysis_results, stats)

        # Save to file
        file_name, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export Batch Report"), "", self.tr("Text Files (*.txt);;All Files (*)")
        )

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(report)

                QMessageBox.information(
                    self, self.tr("Export Complete"),
                    self.tr(f"Batch report exported successfully:\n{file_name}")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, self.tr("Export Failed"),
                    self.tr(f"Failed to export report:\n\n{str(e)}")
                )

    def set_controls_enabled(self, enabled: bool):
        """Enable or disable analysis controls."""
        self.start_analysis_btn.setEnabled(enabled)
        self.stop_analysis_btn.setEnabled(not enabled)
        self.item_input.setEnabled(enabled)
        self.items_list.setEnabled(enabled)
        self.recursive_scan.setEnabled(enabled)
        self.scan_archives.setEnabled(enabled)
        self.heuristic_scan.setEnabled(enabled)
        self.scan_pua.setEnabled(enabled)
        self.parallel_processing.setEnabled(enabled)
        self.max_file_size.setEnabled(enabled)
        self.max_scan_time.setEnabled(enabled)
        self.batch_size.setEnabled(enabled)
        self.exclude_patterns.setEnabled(enabled)

    def update_progress(self, value: int):
        """Update the progress bar."""
        self.analysis_progress.setValue(value)

    def update_output(self, text: str):
        """Update the analysis output."""
        self.analysis_output.append(text)

        # Auto-scroll to bottom
        cursor = self.analysis_output.textCursor()
        cursor.movePosition(cursor.End)
        self.analysis_output.setTextCursor(cursor)

    def on_item_finished(self, item_path: str, result: Dict):
        """Handle completion of individual item analysis."""
        # Update the items status table
        row_count = self.items_status_table.rowCount()
        self.items_status_table.insertRow(row_count)

        # Item name
        item_name = os.path.basename(item_path)
        if os.path.isdir(item_path):
            item_name += "/"

        self.items_status_table.setItem(row_count, 0, QTableWidgetItem(item_name))

        # Status
        status = "Success" if result['success'] else f"Failed: {result.get('error', 'Unknown')}"
        status_item = QTableWidgetItem(status)
        if result['success']:
            status_item.setBackground(Qt.green)
        else:
            status_item.setBackground(Qt.red)
        self.items_status_table.setItem(row_count, 1, status_item)

        # Threats
        threats = str(result.get('threats_found', 0))
        self.items_status_table.setItem(row_count, 2, QTableWidgetItem(threats))

        # Scan time
        scan_time = f"{result.get('scan_time', 0):.2f}s"
        self.items_status_table.setItem(row_count, 3, QTableWidgetItem(scan_time))

    def on_analysis_finished(self, success: bool, message: str, results: List[Dict]):
        """Handle batch analysis completion."""
        self.analysis_results = results
        self.set_controls_enabled(True)
        self.export_report_btn.setEnabled(True)

        # Update summary
        if success:
            self.analysis_output.append(f"\n=== Batch Analysis Complete ===")
            self.analysis_output.append(message)

            # Update statistics
            self.update_statistics(results)
        else:
            self.analysis_output.append(f"\n=== Batch Analysis Failed ===")
            self.analysis_output.append(message)

    def update_statistics(self, results: List[Dict]):
        """Update the statistics tree with analysis results."""
        self.stats_tree.clear()

        if not results:
            return

        stats = self.batch_analyzer.get_batch_statistics(results)

        # Create root item
        root_item = QTreeWidgetItem(self.stats_tree)
        root_item.setText(0, "Batch Analysis Statistics")
        root_item.setText(1, "")

        # Summary statistics
        summary_item = QTreeWidgetItem(root_item)
        summary_item.setText(0, "Summary")
        summary_item.setText(1, "")

        QTreeWidgetItem(summary_item).setText(0, "Total Items")
        QTreeWidgetItem(summary_item).setText(1, str(stats.get('total_items', 0)))

        QTreeWidgetItem(summary_item).setText(0, "Successful Scans")
        QTreeWidgetItem(summary_item).setText(1, str(stats.get('successful_scans', 0)))

        QTreeWidgetItem(summary_item).setText(0, "Failed Scans")
        QTreeWidgetItem(summary_item).setText(1, str(stats.get('failed_scans', 0)))

        QTreeWidgetItem(summary_item).setText(0, "Total Threats")
        QTreeWidgetItem(summary_item).setText(1, str(stats.get('total_threats', 0)))

        QTreeWidgetItem(summary_item).setText(0, "Total Scan Time")
        QTreeWidgetItem(summary_item).setText(1, f"{stats.get('total_scan_time', 0):.2f}s")

        QTreeWidgetItem(summary_item).setText(0, "Average Scan Time")
        QTreeWidgetItem(summary_item).setText(1, f"{stats.get('avg_scan_time', 0):.2f}s")

        # Threat types
        threat_types = stats.get('threat_types', {})
        if threat_types:
            threats_item = QTreeWidgetItem(root_item)
            threats_item.setText(0, "Threat Types")
            threats_item.setText(1, "")

            for threat_type, count in sorted(threat_types.items()):
                QTreeWidgetItem(threats_item).setText(0, threat_type)
                QTreeWidgetItem(threats_item).setText(1, str(count))

        # Errors
        errors = stats.get('errors', [])
        if errors:
            errors_item = QTreeWidgetItem(root_item)
            errors_item.setText(0, "Errors")
            errors_item.setText(1, "")

            for error in errors[:10]:  # Show first 10 errors
                error_item = QTreeWidgetItem(errors_item)
                error_item.setText(0, os.path.basename(error['path']))
                error_item.setText(1, error['error'])

            if len(errors) > 10:
                more_item = QTreeWidgetItem(errors_item)
                more_item.setText(0, "...")
                more_item.setText(1, f"{len(errors) - 10} more errors")

        # Expand all items
        root_item.setExpanded(True)
        if self.stats_tree.topLevelItemCount() > 0:
            for i in range(self.stats_tree.topLevelItemCount()):
                self.stats_tree.topLevelItem(i).setExpanded(True)

        # Resize columns
        self.stats_tree.resizeColumnToContents(0)
        self.stats_tree.resizeColumnToContents(1)

    def get_batch_options(self) -> Dict:
        """Get the current batch analysis options."""
        return {
            'recursive': self.recursive_scan.isChecked(),
            'scan_archives': self.scan_archives.isChecked(),
            'heuristic_scan': self.heuristic_scan.isChecked(),
            'scan_pua': self.scan_pua.isChecked(),
            'parallel_processing': self.parallel_processing.isChecked(),
            'max_file_size': self.max_file_size.value(),
            'max_scan_time': self.max_scan_time.value(),
            'batch_size': self.batch_size.value(),
            'exclude_patterns': self.exclude_patterns.text().strip()
        }

    def set_batch_options(self, options: Dict):
        """Set batch options from dictionary."""
        if 'recursive' in options:
            self.recursive_scan.setChecked(options['recursive'])
        if 'scan_archives' in options:
            self.scan_archives.setChecked(options['scan_archives'])
        if 'heuristic_scan' in options:
            self.heuristic_scan.setChecked(options['heuristic_scan'])
        if 'scan_pua' in options:
            self.scan_pua.setChecked(options['scan_pua'])
        if 'parallel_processing' in options:
            self.parallel_processing.setChecked(options['parallel_processing'])
        if 'max_file_size' in options:
            self.max_file_size.setValue(options['max_file_size'])
        if 'max_scan_time' in options:
            self.max_scan_time.setValue(options['max_scan_time'])
        if 'batch_size' in options:
            self.batch_size.setValue(options['batch_size'])
        if 'exclude_patterns' in options:
            self.exclude_patterns.setText(options['exclude_patterns'])
