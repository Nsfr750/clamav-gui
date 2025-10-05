"""
Log Viewer for PDF Duplicate Finder

This module provides a graphical interface to view and filter log messages.
"""

import os
import re
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QComboBox, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QApplication, QLineEdit, QStyle)
from PySide6.QtCore import Qt, QRegularExpression, Slot
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QSyntaxHighlighter, QFont

# Import language manager
from ..lang.lang_manager import SimpleLanguageManager

class LogHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for log messages."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Format for different log levels with improved contrast and accessibility
        
        # CRITICAL - High contrast red background with white text
        critical_format = QTextCharFormat()
        critical_format.setForeground(QColor(255, 255, 255))  # White text
        critical_format.setBackground(QColor(178, 34, 34))    # Firebrick red background
        critical_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((QRegularExpression(r'CRITICAL.*'), critical_format))
        
        # ERROR - Bright red
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(220, 50, 47))  # Bright red
        error_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((QRegularExpression(r'ERROR.*'), error_format))
        
        # WARNING - Orange/brown
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(203, 75, 22))  # Chocolate orange
        warning_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((QRegularExpression(r'WARNING.*'), warning_format))
        
        # INFO - Navy blue
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(42, 101, 153))  # Darker blue
        info_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((QRegularExpression(r'INFO.*'), info_format))
        
        # DEBUG - Dark gray
        debug_format = QTextCharFormat()
        debug_format.setForeground(QColor(88, 110, 117))  # Dark gray-blue
        debug_format.setFontItalic(True)  # Italic to distinguish debug messages
        self.highlighting_rules.append((QRegularExpression(r'DEBUG.*'), debug_format))
        
        # Timestamp - Teal
        time_format = QTextCharFormat()
        time_format.setForeground(QColor(7, 102, 120))  # Dark teal
        time_format.setFontWeight(QFont.Weight.Medium)
        self.highlighting_rules.append((QRegularExpression(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}'), time_format))
        
        # Tracebacks - Dark red with subtle background
        traceback_format = QTextCharFormat()
        traceback_format.setForeground(QColor(178, 34, 34))  # Firebrick red
        traceback_format.setBackground(QColor(255, 245, 245))  # Very light red background
        self.highlighting_rules.append((QRegularExpression(r'Traceback \(most recent call last\):'), traceback_format))
        self.highlighting_rules.append((QRegularExpression(r'File ".*", line \d+.*'), traceback_format))
        
        # Module/function names - Purple
        module_format = QTextCharFormat()
        module_format.setForeground(QColor(108, 113, 196))  # Soft purple
        module_format.setFontWeight(QFont.Weight.Medium)
        self.highlighting_rules.append((QRegularExpression(r'\b[a-zA-Z_][a-zA-Z0-9_]*\.py:\d+'), module_format))
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class LogViewer(QDialog):
    """Log viewer dialog for displaying and filtering log messages."""
    
    def __init__(self, log_file, parent=None):
        super().__init__(parent)
        self.language_manager = SimpleLanguageManager()
        self.log_file = os.path.abspath(log_file)
        self.log_dir = os.path.dirname(self.log_file)
        self.log_content = []
        self.filtered_content = []
        self.current_level = "ALL"
        
        # Set window size and title
        self.resize(800, 600)
        self.setWindowTitle(self.tr("Log Viewer"))
        
        # Initialize UI
        self.init_ui()
        self.retranslate_ui()
        
        # Populate log files and load the initial log
        self.populate_log_files()
        self.load_log_file()
        
        # Connect language change signal
        self.language_manager.language_changed.connect(self.retranslate_ui)
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Top toolbar (file selection and actions)
        top_toolbar = QHBoxLayout()
        
        # Log file selection
        self.log_file_label = QLabel()
        top_toolbar.addWidget(self.log_file_label)
        
        self.log_file_combo = QComboBox()
        self.log_file_combo.setMinimumWidth(300)
        self.log_file_combo.currentTextChanged.connect(self.on_log_file_changed)
        top_toolbar.addWidget(self.log_file_combo, 1)  # Add stretch
        
        # Delete log button
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_TrashIcon))
        self.delete_btn.setToolTip(self.tr("Delete selected log file"))
        self.delete_btn.clicked.connect(self.delete_log_file)
        top_toolbar.addWidget(self.delete_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_btn.setToolTip(self.tr("Refresh log files list"))
        self.refresh_btn.clicked.connect(self.populate_log_files)
        top_toolbar.addWidget(self.refresh_btn)
        
        layout.addLayout(top_toolbar)
        
        # Filter toolbar
        filter_toolbar = QHBoxLayout()
        
        # Log level filter
        self.level_label = QLabel()
        filter_toolbar.addWidget(self.level_label)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        filter_toolbar.addWidget(self.level_combo)
        
        # Search box
        self.search_label = QLabel()
        filter_toolbar.addWidget(self.search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.tr("Search in logs..."))
        self.search_edit.textChanged.connect(self.filter_logs)
        filter_toolbar.addWidget(self.search_edit, 1)  # Add stretch
        
        # Clear search button
        self.clear_search_btn = QPushButton()
        self.clear_search_btn.setIcon(QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogCloseButton))
        self.clear_search_btn.setToolTip(self.tr("Clear search"))
        self.clear_search_btn.clicked.connect(self.clear_search)
        filter_toolbar.addWidget(self.clear_search_btn)
        
        # Buttons
        self.clear_btn = QPushButton()
        self.clear_btn.setIcon(QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogResetButton))
        self.clear_btn.setToolTip(self.tr("Clear log content"))
        self.clear_btn.clicked.connect(self.clear_logs)
        filter_toolbar.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton()
        self.save_btn.setIcon(QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_btn.setToolTip(self.tr("Save logs to file..."))
        self.save_btn.clicked.connect(self.save_logs)
        filter_toolbar.addWidget(self.save_btn)
        
        layout.addLayout(filter_toolbar)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier New", 10))
        self.highlighter = LogHighlighter(self.log_document())
        
        layout.addWidget(self.log_display, 1)  # Add stretch factor to make it expandable
        
        # Status bar and close button
        bottom_layout = QHBoxLayout()
        
        # Status bar
        self.status_bar = QLabel()
        bottom_layout.addWidget(self.status_bar, 1)  # Add stretch to push close button to right
        
        # Close button
        self.close_btn = QPushButton(self.tr("Close"))
        self.close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_btn)
        
        layout.addLayout(bottom_layout)
    
    def retranslate_ui(self):
        """Update the UI when the language changes."""
        self.setWindowTitle(self.tr("Log Viewer"))
        self.log_file_label.setText(self.tr("Log File:"))
        self.level_label.setText(self.tr("Level:"))
        self.search_label.setText(self.tr("Search:"))
        self.search_edit.setPlaceholderText(self.tr("Search in logs..."))
        self.clear_btn.setText(self.tr("Clear"))
        self.save_btn.setText(self.tr("Save"))
        
        # Update tooltips
        self.delete_btn.setToolTip(self.tr("Delete selected log file"))
        self.refresh_btn.setToolTip(self.tr("Refresh log files list"))
        self.clear_search_btn.setToolTip(self.tr("Clear search"))
        self.clear_btn.setToolTip(self.tr("Clear log content"))
        self.save_btn.setToolTip(self.tr("Save logs to file..."))
        
        # Update status bar if we have content
        if hasattr(self, 'log_content'):
            self.update_status_bar()
    
    def log_document(self):
        """Return the document associated with the log display."""
        return self.log_display.document()
    
    def populate_log_files(self):
        """Populate the log files dropdown with available log files."""
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"),
                                   self.tr("Failed to create logs directory: {}").format(str(e)))
                return
        
        # Store current selection
        current_file = self.log_file_combo.currentText()
        
        # Clear and repopulate the combo box
        self.log_file_combo.blockSignals(True)
        self.log_file_combo.clear()
        
        # Add all .log files from the logs directory
        try:
            log_files = sorted([f for f in os.listdir(self.log_dir) 
                              if f.endswith('.log')], 
                             key=lambda x: os.path.getmtime(os.path.join(self.log_dir, x)), 
                             reverse=True)
            
            for log_file in log_files:
                self.log_file_combo.addItem(log_file, os.path.join(self.log_dir, log_file))
            
            # Try to restore the previous selection or select the main log file
            if current_file and os.path.exists(current_file):
                index = self.log_file_combo.findData(current_file)
                if index >= 0:
                    self.log_file_combo.setCurrentIndex(index)
            elif self.log_file_combo.count() > 0:
                # Select the main log file if available
                main_log_index = self.log_file_combo.findText(os.path.basename(self.log_file))
                if main_log_index >= 0:
                    self.log_file_combo.setCurrentIndex(main_log_index)
                else:
                    self.log_file_combo.setCurrentIndex(0)
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr("Failed to list log files: {}").format(str(e)))
        
        self.log_file_combo.blockSignals(False)
    
    def on_log_file_changed(self, text):
        """Handle log file selection change."""
        if not text:
            return
            
        index = self.log_file_combo.currentIndex()
        if index >= 0:
            self.log_file = self.log_file_combo.currentData()
            self.load_log_file()
    
    def load_log_file(self):
        """Load the log file content."""
        if not self.log_file or not os.path.exists(self.log_file):
            self.log_display.setPlainText(self.tr("Log file not found: {path}").format(path=self.log_file))
            self.log_content = []
            self.filtered_content = []
            self.update_status_bar()
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                self.log_content = f.readlines()
            
            self.filter_logs()
            self.update_status_bar()
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr("Failed to load log file: {}").format(str(e)))
    
    def update_status_bar(self):
        """Update the status bar with current log file info."""
        if not hasattr(self, 'log_content'):
            return
            
        if not self.log_file or not os.path.exists(self.log_file):
            self.status_bar.setText(self.tr("No log file selected"))
            return
            
        file_size = os.path.getsize(self.log_file)
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB
        
        if file_size_mb > 1:
            size_str = f"{file_size_mb:.1f} MB"
        else:
            size_str = f"{file_size / 1024:.1f} KB"
            
        self.status_bar.setText(
            self.tr("File: {file} | Entries: {entries} | Size: {size}").format(
                file=os.path.basename(self.log_file),
                entries=len(self.log_content),
                size=size_str
            )
        )
    
    def clear_search(self):
        """Clear the search box and reset filters."""
        self.search_edit.clear()
        self.level_combo.setCurrentText("ALL")
        self.filter_logs()
    
    def delete_log_file(self):
        """Delete the currently selected log file after confirmation."""
        if not self.log_file or not os.path.exists(self.log_file):
            return
            
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Delete"),
            self.tr("Are you sure you want to delete the log file?\n"
                   "This will permanently delete: {}\n"
                   "This action cannot be undone.").format(os.path.basename(self.log_file)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.log_file)
                # Remove from combo box
                index = self.log_file_combo.findData(self.log_file)
                if index >= 0:
                    self.log_file_combo.removeItem(index)
                
                # Select the first available log file or clear the display
                if self.log_file_combo.count() > 0:
                    self.log_file = self.log_file_combo.currentData()
                    self.load_log_file()
                else:
                    self.log_file = None
                    self.log_content = []
                    self.filtered_content = []
                    self.log_display.clear()
                    self.update_status_bar()
                
                QMessageBox.information(
                    self,
                    self.tr("Success"),
                    self.tr("Log file has been deleted.")
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.tr("Error"),
                    self.tr("Failed to delete log file: {}").format(str(e))
                )
    
    def filter_logs(self):
        """Filter logs based on selected level and search text."""
        try:
            level = self.level_combo.currentText()
            search_text = self.search_edit.text().lower()
            
            if not hasattr(self, 'log_content') or not self.log_content:
                self.log_display.clear()
                return
            
            self.filtered_content = []
            current_entry = []
            
            # Process each line in the log file
            for line in self.log_content:
                line = line.rstrip('\n')
                
                # Check if line starts with a timestamp (new log entry)
                is_new_entry = bool(re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line))
                
                if is_new_entry and current_entry:
                    # Process the previous entry
                    entry_text = '\n'.join(current_entry)
                    if self._should_include_entry(entry_text, level, search_text):
                        self.filtered_content.append(entry_text)
                    current_entry = [line]
                else:
                    if current_entry or line.strip():
                        current_entry.append(line)
            
            # Process the last entry
            if current_entry:
                entry_text = '\n'.join(current_entry)
                if self._should_include_entry(entry_text, level, search_text):
                    self.filtered_content.append(entry_text)
            
            # Update the display
            self.log_display.setPlainText('\n\n'.join(self.filtered_content))
            
            # Scroll to the bottom
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
            
            # Update status bar with filtered count
            if hasattr(self, 'status_bar'):
                self.status_bar.setText(
                    self.tr("Showing {filtered} of {total} entries").format(
                        filtered=len(self.filtered_content),
                        total=len(self.log_content)
                    )
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Failed to filter logs: {}").format(str(e))
            )
    
    def _should_include_entry(self, entry_text, level, search_text):
        """Check if a log entry should be included based on filters."""
        # Check level filter
        if level != "ALL":
            # Match the actual log format: "YYYY-MM-DD HH:MM:SS.SSS - PID - ThreadName - APPNAME - LEVEL - "
            level_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} - \d+ - \w+ - [^-]+ - ' + re.escape(level) + r' - '
            level_match = re.search(level_pattern, entry_text)
            if not level_match:
                # For multi-line entries (like tracebacks), check the first line
                first_line = entry_text.split('\n')[0]
                level_match = re.search(level_pattern, first_line)
                if not level_match:
                    return False
        
        # Check search text
        if search_text and search_text.lower() not in entry_text.lower():
            return False
            
        return True
    
    def clear_logs(self):
        """Clear the log file after confirmation."""
        try:
            reply = QMessageBox.question(
                self,
                self.tr("Confirm Clear"),
                self.tr("Are you sure you want to clear all logs? This cannot be undone."),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write("")
                self.load_log_file()
                
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr("Failed to clear logs: {error}").format(error=str(e)))
    
    def save_logs(self):
        """Save the filtered logs to a file."""
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Save Log File"),
                "",
                self.tr("Log Files (*.log);;All Files (*)")
            )
            
            if file_name:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.writelines(self.filtered_content)
                
                QMessageBox.information(
                    self,
                    self.tr("Save Successful"),
                    self.tr("Logs saved successfully to: {path}").format(path=file_name)
                )
                
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr("Failed to save logs: {error}").format(error=str(e)))


def show_log_viewer(log_file, parent=None):
    """
    Show the log viewer dialog.
    
    Args:
        log_file (str): Path to the log file
        parent: Parent widget
    """
    # Ensure logs directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Create an empty log file
            with open(log_file, 'w') as f:
                f.write('Log file created.\n')
        except Exception as e:
            QMessageBox.critical(
                parent,
                parent.tr("Error") if parent else "Error",
                parent.tr("Failed to create logs directory: {error}").format(error=str(e)) if parent 
                else f"Failed to create logs directory: {str(e)}"
            )
            return
    
    if not os.path.exists(log_file):
        try:
            # Create an empty log file
            with open(log_file, 'w') as f:
                f.write('Log file created.\n')
        except Exception as e:
            QMessageBox.critical(
                parent,
                parent.tr("Error") if parent else "Error",
                parent.tr("Failed to create log file: {error}").format(error=str(e)) if parent
                else f"Failed to create log file: {str(e)}"
            )
            return
    
    viewer = LogViewer(log_file, parent)
    viewer.exec()


if __name__ == "__main__":
    import sys
    
    # For testing
    app = QApplication(sys.argv)
    
    # Create a test log file if it doesn't exist
    log_file = "test.log"
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write("2023-01-01 12:00:00,000 - Test - INFO - This is an info message\n")
            f.write("2023-01-01 12:00:01,000 - Test - WARNING - This is a warning\n")
            f.write("2023-01-01 12:00:02,000 - Test - ERROR - This is an error\n")
    
    # Show the log viewer
    viewer = LogViewer(log_file)
    viewer.show()
    
    sys.exit(app.exec())
