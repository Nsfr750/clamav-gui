"""
Quarantine management tab for ClamAV GUI application.
Provides interface for viewing and managing quarantined files.
"""
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class QuarantineTab(QWidget):
    """Quarantine management tab widget."""

    def __init__(self, parent=None):
        """Initialize the quarantine tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.quarantine_manager = None  # Will be set by parent

        # Initialize UI
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Quarantine statistics section
        stats_group = QGroupBox(self.tr("Quarantine Statistics"))
        stats_layout = QVBoxLayout()

        self.quarantine_stats_text = QTextEdit()
        self.quarantine_stats_text.setReadOnly(True)
        self.quarantine_stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.quarantine_stats_text)

        refresh_btn = QPushButton(self.tr("Refresh Stats"))
        refresh_btn.clicked.connect(self.refresh_quarantine_stats)
        stats_layout.addWidget(refresh_btn)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Quarantine file list section
        files_group = QGroupBox(self.tr("Quarantined Files"))
        files_layout = QVBoxLayout()

        self.quarantine_files_list = QListWidget()
        self.quarantine_files_list.setSelectionMode(QListWidget.MultiSelection)
        files_layout.addWidget(self.quarantine_files_list)

        # File management buttons
        file_btn_layout = QHBoxLayout()

        restore_btn = QPushButton(self.tr("Restore Selected"))
        restore_btn.clicked.connect(self.restore_selected_files)
        file_btn_layout.addWidget(restore_btn)

        delete_btn = QPushButton(self.tr("Delete Selected"))
        delete_btn.clicked.connect(self.delete_selected_files)
        file_btn_layout.addWidget(delete_btn)

        # Bulk operations
        bulk_btn_layout = QHBoxLayout()

        restore_all_btn = QPushButton(self.tr("Restore All"))
        restore_all_btn.clicked.connect(self.restore_all_files)
        bulk_btn_layout.addWidget(restore_all_btn)

        delete_all_btn = QPushButton(self.tr("Delete All"))
        delete_all_btn.clicked.connect(self.delete_all_files)
        bulk_btn_layout.addWidget(delete_all_btn)

        cleanup_btn = QPushButton(self.tr("Cleanup (30+ days)"))
        cleanup_btn.clicked.connect(self.cleanup_old_files)
        bulk_btn_layout.addWidget(cleanup_btn)

        files_layout.addLayout(file_btn_layout)
        files_layout.addLayout(bulk_btn_layout)

        export_btn = QPushButton(self.tr("Export List"))
        export_btn.clicked.connect(self.export_quarantine_list)
        file_btn_layout.addWidget(export_btn)

        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        # Initialize quarantine manager reference
        if hasattr(self.parent, 'quarantine_manager'):
            self.quarantine_manager = self.parent.quarantine_manager

        # Initial refresh
        self.refresh_quarantine_stats()
        self.refresh_quarantine_files()

    def refresh_quarantine_stats(self):
        """Refresh the quarantine statistics display."""
        try:
            if not self.quarantine_manager:
                self.quarantine_stats_text.setPlainText("Quarantine manager not initialized")
                return

            stats = self.quarantine_manager.get_quarantine_stats()

            stats_text = f"""
Quarantine Statistics:
====================

Total quarantined files: {stats.get('total_quarantined', 0)}
Total size: {stats.get('total_size_mb', 0):.2f} MB

Threat types found:
{chr(10).join(f"  • {threat}" for threat in stats.get('threat_types', [])) if stats.get('threat_types') else "  None"}

Last activity:
  Newest file: {stats.get('newest_file') or 'N/A'}
  Oldest file: {stats.get('oldest_file') or 'N/A'}
"""
            self.quarantine_stats_text.setPlainText(stats_text.strip())

        except Exception as e:
            error_msg = f"Error loading quarantine statistics: {str(e)}"
            logger.error(error_msg)
            self.quarantine_stats_text.setPlainText(error_msg)

    def refresh_quarantine_files(self):
        """Refresh the list of quarantined files."""
        try:
            if not self.quarantine_manager:
                self.quarantine_files_list.clear()
                self.quarantine_files_list.addItem("Quarantine manager not initialized")
                return

            self.quarantine_files_list.clear()
            quarantined_files = self.quarantine_manager.list_quarantined_files()

            if not quarantined_files:
                self.quarantine_files_list.addItem(self.tr("No quarantined files"))
                return

            for file_info in quarantined_files:
                filename = file_info.get('original_filename', 'Unknown')
                threat = file_info.get('threat_name', 'Unknown')
                size = file_info.get('file_size', 0)
                item_text = f"{filename} - {threat} ({size} bytes)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, file_info)
                self.quarantine_files_list.addItem(item)

        except Exception as e:
            self.quarantine_files_list.clear()
            self.quarantine_files_list.addItem(f"Error loading quarantined files: {str(e)}")

    def restore_selected_files(self):
        """Restore selected quarantined files."""
        selected_items = self.quarantine_files_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select files to restore"))
            return

        if len(selected_items) == 1:
            # Single file
            self._restore_single_file(selected_items[0])
        else:
            # Multiple files
            self._restore_multiple_files(selected_items)

    def _restore_single_file(self, item):
        """Restore a single quarantined file."""
        file_info = item.data(Qt.UserRole)
        if not file_info:
            return

        filename = file_info.get('original_filename', 'Unknown')

        reply = QMessageBox.question(
            self, self.tr("Restore File"),
            self.tr(f"Are you sure you want to restore '{filename}'?\n\n"
                   "Warning: This file was detected as infected and may be dangerous."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            file_id = self._get_file_id_from_info(file_info)
            if not file_id:
                QMessageBox.critical(
                    self, self.tr("Restore Failed"),
                    self.tr("Could not determine file ID for restoration. The file may be corrupted.")
                )
                return

            success, message = self.quarantine_manager.restore_file(file_id)

            if success:
                QMessageBox.information(
                    self, self.tr("Restore Successful"),
                    self.tr(f"File '{filename}' has been successfully restored.\n\n{message}")
                )
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(
                    self, self.tr("Restore Failed"),
                    self.tr(f"Failed to restore file '{filename}':\n\n{message}")
                )

    def _restore_multiple_files(self, items):
        """Restore multiple selected quarantined files."""
        file_list = []
        for item in items:
            file_info = item.data(Qt.UserRole)
            if file_info:
                filename = file_info.get('original_filename', 'Unknown')
                file_list.append(filename)

        reply = QMessageBox.question(
            self, self.tr("Restore Multiple Files"),
            self.tr(f"Are you sure you want to restore {len(items)} files?\n\n"
                   "Files to restore:\n" + "\n".join(f"• {name}" for name in file_list[:5]) +
                   (f"\n... and {len(file_list) - 5} more" if len(file_list) > 5 else "") +
                   "\n\nWarning: These files were detected as infected and may be dangerous."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []

            for item in items:
                file_info = item.data(Qt.UserRole)
                if not file_info:
                    continue

                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue

                success, message = self.quarantine_manager.restore_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")

            # Show results
            result_msg = f"Restored {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to restore {error_count} files:"
                result_msg += "\n" + "\n".join(errors[:3])
                if error_count > 3:
                    result_msg += f"\n... and {error_count - 3} more errors"

            if success_count > 0:
                QMessageBox.information(self, self.tr("Restore Complete"), result_msg)
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(self, self.tr("Restore Failed"), result_msg)

    def delete_selected_files(self):
        """Delete selected quarantined files."""
        selected_items = self.quarantine_files_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select files to delete"))
            return

        if len(selected_items) == 1:
            # Single file
            self._delete_single_file(selected_items[0])
        else:
            # Multiple files
            self._delete_multiple_files(selected_items)

    def _delete_single_file(self, item):
        """Delete a single quarantined file."""
        file_info = item.data(Qt.UserRole)
        if not file_info:
            return

        filename = file_info.get('original_filename', 'Unknown')

        reply = QMessageBox.question(
            self, self.tr("Delete File"),
            self.tr(f"Are you sure you want to permanently delete '{filename}'?\n\n"
                   "This action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            file_id = self._get_file_id_from_info(file_info)
            if not file_id:
                QMessageBox.critical(
                    self, self.tr("Delete Failed"),
                    self.tr("Could not determine file ID for deletion. The file may be corrupted.")
                )
                return

            success, message = self.quarantine_manager.delete_quarantined_file(file_id)

            if success:
                QMessageBox.information(
                    self, self.tr("Delete Successful"),
                    self.tr(f"File '{filename}' has been permanently deleted.\n\n{message}")
                )
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(
                    self, self.tr("Delete Failed"),
                    self.tr(f"Failed to delete file '{filename}':\n\n{message}")
                )

    def _delete_multiple_files(self, items):
        """Delete multiple selected quarantined files."""
        file_list = []
        for item in items:
            file_info = item.data(Qt.UserRole)
            if file_info:
                filename = file_info.get('original_filename', 'Unknown')
                file_list.append(filename)

        reply = QMessageBox.question(
            self, self.tr("Delete Multiple Files"),
            self.tr(f"Are you sure you want to permanently delete {len(items)} files?\n\n"
                   "Files to delete:\n" + "\n".join(f"• {name}" for name in file_list[:5]) +
                   (f"\n... and {len(file_list) - 5} more" if len(file_list) > 5 else "") +
                   "\n\nThis action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []

            for item in items:
                file_info = item.data(Qt.UserRole)
                if not file_info:
                    continue

                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue

                success, message = self.quarantine_manager.delete_quarantined_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")

            # Show results
            result_msg = f"Deleted {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to delete {error_count} files:"
                result_msg += "\n" + "\n".join(errors[:3])
                if error_count > 3:
                    result_msg += f"\n... and {error_count - 3} more errors"

            if success_count > 0:
                QMessageBox.information(self, self.tr("Delete Complete"), result_msg)
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(self, self.tr("Delete Failed"), result_msg)

    def restore_all_files(self):
        """Restore all quarantined files."""
        if not self.quarantine_manager:
            QMessageBox.warning(self, self.tr("No Manager"), self.tr("Quarantine manager not available"))
            return

        quarantined_files = self.quarantine_manager.list_quarantined_files()
        if not quarantined_files:
            QMessageBox.information(self, self.tr("No Files"), self.tr("No files in quarantine to restore"))
            return

        reply = QMessageBox.question(
            self, self.tr("Restore All Files"),
            self.tr(f"Are you sure you want to restore all {len(quarantined_files)} quarantined files?\n\n"
                   "Warning: These files were detected as infected and may be dangerous."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []

            for file_info in quarantined_files:
                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue

                success, message = self.quarantine_manager.restore_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")

            # Show results
            result_msg = f"Restored {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to restore {error_count} files."

            QMessageBox.information(self, self.tr("Restore Complete"), result_msg)
            self.refresh_quarantine_stats()
            self.refresh_quarantine_files()

    def delete_all_files(self):
        """Delete all quarantined files."""
        if not self.quarantine_manager:
            QMessageBox.warning(self, self.tr("No Manager"), self.tr("Quarantine manager not available"))
            return

        quarantined_files = self.quarantine_manager.list_quarantined_files()
        if not quarantined_files:
            QMessageBox.information(self, self.tr("No Files"), self.tr("No files in quarantine to delete"))
            return

        reply = QMessageBox.question(
            self, self.tr("Delete All Files"),
            self.tr(f"Are you sure you want to permanently delete all {len(quarantined_files)} quarantined files?\n\n"
                   "This action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []

            for file_info in quarantined_files:
                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue

                success, message = self.quarantine_manager.delete_quarantined_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")

            # Show results
            result_msg = f"Deleted {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to delete {error_count} files."

            QMessageBox.information(self, self.tr("Delete Complete"), result_msg)
            self.refresh_quarantine_stats()
            self.refresh_quarantine_files()

    def cleanup_old_files(self):
        """Clean up quarantined files older than 30 days."""
        if not self.quarantine_manager:
            QMessageBox.warning(self, self.tr("No Manager"), self.tr("Quarantine manager not available"))
            return

        reply = QMessageBox.question(
            self, self.tr("Cleanup Old Files"),
            self.tr("This will permanently delete all quarantined files older than 30 days.\n\n"
                   "Do you want to continue?"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count, message = self.quarantine_manager.cleanup_old_files(30)

            QMessageBox.information(
                self, self.tr("Cleanup Complete"),
                self.tr(f"Cleanup completed.\n\n{message}")
            )

            self.refresh_quarantine_stats()
            self.refresh_quarantine_files()

    def export_quarantine_list(self):
        """Export the quarantine list to a file."""
        if not self.quarantine_manager:
            QMessageBox.warning(self, self.tr("No Manager"), self.tr("Quarantine manager not available"))
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Quarantine List"),
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_name:
            return

        if not file_name.lower().endswith('.json'):
            file_name += '.json'

        success = self.quarantine_manager.export_quarantine_list(file_name)

        if success:
            QMessageBox.information(
                self, self.tr("Export Complete"),
                self.tr(f"Quarantine list exported successfully:\n{file_name}")
            )
        else:
            QMessageBox.critical(
                self, self.tr("Export Failed"),
                self.tr("Failed to export quarantine list")
            )

    def _get_file_id_from_info(self, file_info):
        """Extract file ID from file info dictionary."""
        # Try multiple methods to get file ID
        for key, value in file_info.items():
            if key.startswith('file_hash') or (isinstance(key, str) and len(key) > 10 and key.replace('_', '').isalnum()):
                return key

        if 'quarantined_path' in file_info:
            # Fallback: try to extract file ID from quarantined path
            quarantined_path = file_info['quarantined_path']
            basename = os.path.basename(quarantined_path)
            # Extract timestamp_hash_filename format
            parts = basename.split('_', 2)
            if len(parts) >= 2:
                return f"{parts[1]}_{parts[0]}"  # hash_timestamp format

        return None

    def set_quarantine_manager(self, manager):
        """Set the quarantine manager reference."""
        self.quarantine_manager = manager
        # Refresh data when manager is set
        self.refresh_quarantine_stats()
        self.refresh_quarantine_files()

    def tr(self, key, default=None):
        """Translate text using the parent window's language manager."""
        if self.parent and hasattr(self.parent, 'tr'):
            return self.parent.tr(key, default or key)
        return default or key
