"""
ML Detection tab for ClamAV GUI.
Provides UI for machine learning-based threat detection and analysis.
"""
import os
import logging
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QTextEdit, QProgressBar, QCheckBox, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QFormLayout,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFileDialog, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

from clamav_gui.utils.ml_threat_detector import MLThreatDetector, MLSandboxAnalyzer

logger = logging.getLogger(__name__)


class MLAnalysisThread(QThread):
    """Thread for ML analysis operations."""

    update_progress = Signal(int)
    update_output = Signal(str)
    analysis_finished = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, analyzer: MLSandboxAnalyzer, file_paths: List[str]):
        super().__init__()
        self.analyzer = analyzer
        self.file_paths = file_paths

    def run(self):
        """Run the ML analysis process."""
        try:
            self.update_output.emit(f"Starting ML analysis of {len(self.file_paths)} files...")

            # Analyze files in batches
            batch_size = 10
            total_files = len(self.file_paths)
            results = []

            for i in range(0, total_files, batch_size):
                batch = self.file_paths[i:i + batch_size]
                self.update_progress.emit(int((i / total_files) * 100))

                try:
                    batch_results = self.analyzer.batch_analyze(batch)
                    results.extend(batch_results)

                    # Update progress for each file in batch
                    for result in batch_results:
                        if 'error' not in result:
                            self.update_output.emit(f"Analyzed: {os.path.basename(result['file_path'])} - Risk: {result.get('risk_level', 'unknown')}")
                        else:
                            self.update_output.emit(f"Error analyzing {result['file_path']}: {result['error']}")

                except Exception as e:
                    self.update_output.emit(f"Error in batch {i//batch_size + 1}: {str(e)}")

            self.update_progress.emit(100)
            self.analysis_finished.emit(results)

        except Exception as e:
            self.error_occurred.emit(f"ML analysis failed: {str(e)}")


class MLDetectionTab(QWidget):
    """ML Detection tab widget."""

    def __init__(self, parent=None):
        """Initialize the ML detection tab.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.ml_detector = None
        self.sandbox_analyzer = None
        self.analysis_thread = None
        self.analysis_results = []

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.connect_signals()

        # Initialize ML components
        self.initialize_ml_components()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)

        # Top section - File selection and controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # File selection section
        file_group = QGroupBox(self.tr("File Selection"))
        file_layout = QVBoxLayout()

        # File path input
        path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText(self.tr("Enter file path or use browse button..."))
        path_layout.addWidget(self.file_path_input)

        browse_btn = QPushButton(self.tr("Browse"))
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)

        file_layout.addLayout(path_layout)

        # File list for batch analysis
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.file_list.setMaximumHeight(120)
        file_layout.addWidget(self.file_list)

        # File management buttons
        file_btn_layout = QHBoxLayout()

        add_file_btn = QPushButton(self.tr("Add File"))
        add_file_btn.clicked.connect(self.add_file)
        file_btn_layout.addWidget(add_file_btn)

        remove_file_btn = QPushButton(self.tr("Remove Selected"))
        remove_file_btn.clicked.connect(self.remove_selected_files)
        file_btn_layout.addWidget(remove_file_btn)

        clear_files_btn = QPushButton(self.tr("Clear All"))
        clear_files_btn.clicked.connect(self.clear_file_list)
        file_btn_layout.addWidget(clear_files_btn)

        file_layout.addLayout(file_btn_layout)
        file_group.setLayout(file_layout)
        top_layout.addWidget(file_group)

        # ML Settings section
        settings_group = QGroupBox(self.tr("ML Settings"))
        settings_layout = QVBoxLayout()

        # ML Model status
        model_layout = QHBoxLayout()
        self.model_status_label = QLabel(self.tr("ML Model: Not loaded"))
        model_layout.addWidget(self.model_status_label)

        refresh_model_btn = QPushButton(self.tr("Refresh Model"))
        refresh_model_btn.clicked.connect(self.refresh_model_info)
        model_layout.addWidget(refresh_model_btn)

        settings_layout.addLayout(model_layout)

        # Analysis options
        options_layout = QHBoxLayout()

        self.enable_ml_analysis = QCheckBox(self.tr("Enable ML Analysis"))
        self.enable_ml_analysis.setChecked(True)
        self.enable_ml_analysis.setToolTip(self.tr("Enable machine learning-based threat detection"))
        options_layout.addWidget(self.enable_ml_analysis)

        self.enable_detailed_features = QCheckBox(self.tr("Detailed Features"))
        self.enable_detailed_features.setChecked(False)
        self.enable_detailed_features.setToolTip(self.tr("Extract and display detailed file features"))
        options_layout.addWidget(self.enable_detailed_features)

        settings_layout.addLayout(options_layout)

        # Confidence threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel(self.tr("Confidence Threshold:")))

        self.confidence_threshold = QComboBox()
        self.confidence_threshold.addItems(["0.3", "0.5", "0.7", "0.8", "0.9"])
        self.confidence_threshold.setCurrentText("0.7")
        threshold_layout.addWidget(self.confidence_threshold)

        threshold_layout.addStretch()
        settings_layout.addLayout(threshold_layout)

        settings_group.setLayout(settings_layout)
        top_layout.addWidget(settings_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self.analyze_btn = QPushButton(self.tr("Start ML Analysis"))
        self.analyze_btn.clicked.connect(self.start_ml_analysis)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        control_layout.addWidget(self.analyze_btn)

        self.stop_btn = QPushButton(self.tr("Stop Analysis"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_ml_analysis)
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
        control_layout.addWidget(self.stop_btn)

        self.clear_results_btn = QPushButton(self.tr("Clear Results"))
        self.clear_results_btn.clicked.connect(self.clear_results)
        control_layout.addWidget(self.clear_results_btn)

        self.export_report_btn = QPushButton(self.tr("Export Report"))
        self.export_report_btn.setEnabled(False)
        self.export_report_btn.clicked.connect(self.export_ml_report)
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

        # Detailed features tab
        features_tab = QWidget()
        features_layout = QVBoxLayout(features_tab)

        self.features_tree = QTreeWidget()
        self.features_tree.setHeaderLabels([self.tr("Feature"), self.tr("Value")])
        self.features_tree.setAlternatingRowColors(True)
        features_layout.addWidget(self.features_tree)

        self.results_tabs.addTab(features_tab, self.tr("File Features"))

        bottom_layout.addWidget(self.results_tabs)

        splitter.addWidget(bottom_widget)

        # Set splitter proportions
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

    def connect_signals(self):
        """Connect UI signals."""
        pass

    def initialize_ml_components(self):
        """Initialize the ML components."""
        try:
            self.ml_detector = MLThreatDetector()
            self.sandbox_analyzer = MLSandboxAnalyzer()

            # Update model status
            self.refresh_model_info()

            logger.info("ML components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            QMessageBox.critical(
                self, self.tr("ML Initialization Error"),
                self.tr(f"Failed to initialize ML components:\n\n{str(e)}")
            )

    def refresh_model_info(self):
        """Refresh and display ML model information."""
        if not self.ml_detector:
            self.model_status_label.setText(self.tr("ML Model: Not initialized"))
            return

        try:
            model_info = self.ml_detector.get_model_info()

            if model_info.get('status') == 'trained':
                classes = model_info.get('classes', [])
                feature_count = model_info.get('feature_count', 0)
                self.model_status_label.setText(
                    self.tr(f"ML Model: Trained ({feature_count} features, {len(classes)} classes)")
                )
            else:
                self.model_status_label.setText(self.tr("ML Model: Not trained"))

        except Exception as e:
            logger.error(f"Error refreshing model info: {e}")
            self.model_status_label.setText(self.tr("ML Model: Error loading info"))

    def browse_file(self):
        """Browse for a file to analyze."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select File"), "", self.tr("All Files (*)")
        )

        if file_name:
            self.file_path_input.setText(file_name)

    def add_file(self):
        """Add a file to the analysis list."""
        file_path = self.file_path_input.text().strip()

        if not file_path:
            QMessageBox.warning(self, self.tr("No File"), self.tr("Please enter a file path first"))
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, self.tr("File Not Found"), self.tr(f"File not found: {file_path}"))
            return

        # Check if file already in list
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.UserRole) == file_path:
                QMessageBox.information(self, self.tr("Duplicate"), self.tr("File already in analysis list"))
                return

        # Add to list
        item = QListWidgetItem(os.path.basename(file_path))
        item.setData(Qt.UserRole, file_path)  # Store full path
        item.setToolTip(file_path)
        self.file_list.addItem(item)

        # Clear the input field
        self.file_path_input.clear()

    def remove_selected_files(self):
        """Remove selected files from the analysis list."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select files to remove"))
            return

        for item in selected_items:
            row = self.file_list.row(item)
            self.file_list.takeItem(row)

    def clear_file_list(self):
        """Clear all files from the analysis list."""
        reply = QMessageBox.question(
            self, self.tr("Clear List"),
            self.tr("Are you sure you want to clear all files from the analysis list?"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.file_list.clear()

    def start_ml_analysis(self):
        """Start ML analysis of selected files."""
        if not self.sandbox_analyzer:
            QMessageBox.warning(self, self.tr("Not Ready"), self.tr("ML analyzer not initialized"))
            return

        # Get files to analyze
        file_paths = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.data(Qt.UserRole)
            if file_path and os.path.exists(file_path):
                file_paths.append(file_path)
            else:
                self.analysis_output.append(f"Warning: File not found or inaccessible: {file_path}")

        if not file_paths:
            QMessageBox.warning(self, self.tr("No Files"), self.tr("No valid files to analyze"))
            return

        # Disable controls during analysis
        self.set_controls_enabled(False)

        # Clear previous results
        self.analysis_output.clear()
        self.features_tree.clear()
        self.analysis_results = []

        # Create and start analysis thread
        self.analysis_thread = MLAnalysisThread(self.sandbox_analyzer, file_paths)

        # Connect thread signals
        self.analysis_thread.update_progress.connect(self.update_progress)
        self.analysis_thread.update_output.connect(self.update_output)
        self.analysis_thread.analysis_finished.connect(self.on_analysis_finished)
        self.analysis_thread.error_occurred.connect(self.on_analysis_error)

        # Start the analysis
        self.analysis_thread.start()

        self.analysis_output.append(f"Starting ML analysis of {len(file_paths)} files...")

    def stop_ml_analysis(self):
        """Stop the current ML analysis."""
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.terminate()
            self.analysis_thread.wait(3000)  # Wait up to 3 seconds

            self.analysis_output.append("ML analysis stopped by user")
            self.set_controls_enabled(True)

    def clear_results(self):
        """Clear all analysis results."""
        self.analysis_output.clear()
        self.features_tree.clear()
        self.analysis_results = []
        self.export_report_btn.setEnabled(False)

    def export_ml_report(self):
        """Export ML analysis results to a file."""
        if not self.analysis_results:
            QMessageBox.warning(self, self.tr("No Results"), self.tr("No analysis results to export"))
            return

        # Generate report
        report = self.sandbox_analyzer.generate_ml_report(self.analysis_results)

        # Save to file
        file_name, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export ML Report"), "", self.tr("Text Files (*.txt);;All Files (*)")
        )

        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(report)

                QMessageBox.information(
                    self, self.tr("Export Complete"),
                    self.tr(f"ML report exported successfully:\n{file_name}")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, self.tr("Export Failed"),
                    self.tr(f"Failed to export report:\n\n{str(e)}")
                )

    def set_controls_enabled(self, enabled: bool):
        """Enable or disable analysis controls."""
        self.analyze_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)
        self.file_path_input.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
        self.enable_ml_analysis.setEnabled(enabled)
        self.enable_detailed_features.setEnabled(enabled)
        self.confidence_threshold.setEnabled(enabled)

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

    def on_analysis_finished(self, results: List[Dict]):
        """Handle analysis completion."""
        self.analysis_results = results
        self.set_controls_enabled(True)
        self.export_report_btn.setEnabled(True)

        # Update summary
        total_files = len(results)
        high_risk = sum(1 for r in results if r.get('risk_level') == 'high')
        medium_risk = sum(1 for r in results if r.get('risk_level') == 'medium')
        ml_detections = sum(1 for r in results if r.get('ml_confidence', 0) > 0.5)

        self.analysis_output.append("=== Analysis Complete ===")
        self.analysis_output.append(f"Total files analyzed: {total_files}")
        self.analysis_output.append(f"High risk files: {high_risk}")
        self.analysis_output.append(f"Medium risk files: {medium_risk}")
        self.analysis_output.append(f"ML detections: {ml_detections}")

        # Show results in features tree if detailed features enabled
        if self.enable_detailed_features.isChecked():
            self.update_features_tree(results)

    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.set_controls_enabled(True)
        self.analysis_output.append(f"Error: {error}")
        QMessageBox.critical(self, self.tr("Analysis Error"), error)

    def update_features_tree(self, results: List[Dict]):
        """Update the features tree with analysis results."""
        self.features_tree.clear()

        for result in results:
            if 'error' in result:
                continue

            # Create root item for file
            file_item = QTreeWidgetItem(self.features_tree)
            file_item.setText(0, os.path.basename(result['file_path']))
            file_item.setText(1, f"Risk: {result.get('risk_level', 'unknown')}")

            # Add basic info
            basic_item = QTreeWidgetItem(file_item)
            basic_item.setText(0, "Basic Information")
            basic_item.setText(1, "")

            QTreeWidgetItem(basic_item).setText(0, "ML Confidence")
            QTreeWidgetItem(basic_item).setText(1, f"{result.get('ml_confidence', 0):.3f}")

            QTreeWidgetItem(basic_item).setText(0, "ML Category")
            QTreeWidgetItem(basic_item).setText(1, result.get('ml_category', 'unknown'))

            QTreeWidgetItem(basic_item).setText(0, "File Size")
            QTreeWidgetItem(basic_item).setText(1, f"{result.get('file_size', 0):,} bytes")

            QTreeWidgetItem(basic_item).setText(0, "Entropy")
            QTreeWidgetItem(basic_item).setText(1, f"{result.get('entropy', 0):.2f}")

            # Expand the tree
            file_item.setExpanded(True)
            basic_item.setExpanded(True)

        # Resize columns
        self.features_tree.resizeColumnToContents(0)
        self.features_tree.resizeColumnToContents(1)

    def get_analysis_options(self) -> Dict:
        """Get the current analysis options."""
        return {
            'enable_ml': self.enable_ml_analysis.isChecked(),
            'detailed_features': self.enable_detailed_features.isChecked(),
            'confidence_threshold': float(self.confidence_threshold.currentText())
        }

    def set_analysis_options(self, options: Dict):
        """Set analysis options from dictionary."""
        if 'enable_ml' in options:
            self.enable_ml_analysis.setChecked(options['enable_ml'])
        if 'detailed_features' in options:
            self.enable_detailed_features.setChecked(options['detailed_features'])
        if 'confidence_threshold' in options:
            threshold = str(options['confidence_threshold'])
            index = self.confidence_threshold.findText(threshold)
            if index >= 0:
                self.confidence_threshold.setCurrentIndex(index)
