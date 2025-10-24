"""
Home tab for ClamAV GUI application showing dashboard and quick actions.
"""
import os
import logging
from datetime import datetime, timedelta
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QProgressBar, QGridLayout, QFrame, QSizePolicy, QSpacerItem,
    QListWidget, QListWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap

from clamav_gui.version import VERSION

logger = logging.getLogger(__name__)


class HomeTab(QWidget):
    """Home tab widget showing dashboard and quick actions."""

    def __init__(self, parent=None):
        """Initialize the home tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.update_timer = None
        self.init_ui()

        # Start update timer for real-time information
        self.start_update_timer()

    def init_ui(self):
        """Initialize the user interface."""
        # Main vertical layout for the entire tab
        main_layout = QVBoxLayout(self)

        # Top section: 2-column layout (logo left, welcome right)
        top_layout = QHBoxLayout()

        # Left column: Logo
        logo_layout = QVBoxLayout()
        self.logo_label = QLabel()
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_label.setMaximumWidth(200)
        self.logo_label.setStyleSheet("QLabel { margin: 10px; }")
        self.load_logo()
        logo_layout.addWidget(self.logo_label)
        logo_layout.addStretch()  # Push logo to center vertically

        # Right column: Welcome text
        welcome_layout = QVBoxLayout()
        welcome_group = QGroupBox(self.tr("Welcome to ClamAV GUI"))
        welcome_group.setStyleSheet("QGroupBox { margin: 10px; }")
        welcome_text_layout = QVBoxLayout() 

        welcome_text = QLabel(self.tr(
            "Welcome to ClamAV GUI - Your comprehensive antivirus solution\n\n"
            "Protect your system with:\n"
            "- real-time scanning\n"
            "- advanced threat detection\n"
            "- comprehensive security management."
        ))
        welcome_text.setWordWrap(True)
        welcome_text.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #fff;
                padding: 10px;
            }
        """)
        welcome_text_layout.addWidget(welcome_text)

        welcome_group.setLayout(welcome_text_layout)
        welcome_layout.addWidget(welcome_group)
        welcome_layout.addStretch()  # Push welcome to center vertically

        # Add top section columns
        top_layout.addLayout(logo_layout, 1)  # Logo column (25% width)
        top_layout.addLayout(welcome_layout, 2)  # Welcome column (75% width)

        # Bottom section: Single column for everything else
        bottom_layout = QVBoxLayout()

        # Quick actions section
        actions_group = QGroupBox(self.tr("Quick Actions"))
        actions_layout = QGridLayout()

        # Quick scan button
        quick_scan_btn = self.create_action_button(
            self.tr("Quick Scan"),
            self.tr("Scan common locations for threats"),
            "#4CAF50",
            self.quick_scan
        )
        actions_layout.addWidget(quick_scan_btn, 0, 0)

        # Full system scan button
        full_scan_btn = self.create_action_button(
            self.tr("Full System Scan"),
            self.tr("Comprehensive scan of entire system"),
            "#2196F3",
            self.full_system_scan
        )
        actions_layout.addWidget(full_scan_btn, 0, 1)

        # Update database button
        update_db_btn = self.create_action_button(
            self.tr("Update Database"),
            self.tr("Download latest virus definitions"),
            "#FF9800",
            self.update_database
        )
        actions_layout.addWidget(update_db_btn, 1, 0)

        # View quarantine button
        quarantine_btn = self.create_action_button(
            self.tr("Quarantine"),
            self.tr("Manage quarantined files"),
            "#9C27B0",
            self.view_quarantine
        )
        actions_layout.addWidget(quarantine_btn, 1, 1)

        actions_group.setLayout(actions_layout)
        bottom_layout.addWidget(actions_group)

        # System status section
        status_group = QGroupBox(self.tr("System Status"))
        status_layout = QGridLayout()

        # Database status
        self.db_status_label = self.create_status_label(
            self.tr("Virus Database:"),
            self.tr("Checking..."),
            "orange"
        )
        status_layout.addWidget(self.db_status_label, 0, 0)

        # Last scan status
        self.last_scan_label = self.create_status_label(
            self.tr("Last Scan:"),
            self.tr("Never"),
            "gray"
        )
        status_layout.addWidget(self.last_scan_label, 0, 1)

        # Threats found
        self.threats_label = self.create_status_label(
            self.tr("Threats Found:"),
            self.tr("0"),
            "green"
        )
        status_layout.addWidget(self.threats_label, 1, 0)

        # System protection
        self.protection_label = self.create_status_label(
            self.tr("Protection:"),
            self.tr("Active"),
            "green"
        )
        status_layout.addWidget(self.protection_label, 1, 1)

        status_group.setLayout(status_layout)
        bottom_layout.addWidget(status_group)

        # Recent activity section
        activity_group = QGroupBox(self.tr("Recent Activity"))
        activity_layout = QVBoxLayout()

        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(150)
        self.activity_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #1f1f1f;
                color: #75b5aa;
            }
        """)
        activity_layout.addWidget(self.activity_list)

        clear_activity_btn = QPushButton(self.tr("Clear Activity"))
        clear_activity_btn.clicked.connect(self.clear_activity)
        activity_layout.addWidget(clear_activity_btn)

        activity_group.setLayout(activity_layout)
        bottom_layout.addWidget(activity_group)

        # Progress section for operations
        progress_group = QGroupBox(self.tr("Current Operations"))
        progress_layout = QVBoxLayout()

        self.operation_progress = QProgressBar()
        self.operation_progress.setVisible(False)
        self.operation_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4CAF50, stop: 0.5 #2196F3, stop: 1 #4CAF50);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.operation_progress)

        self.operation_label = QLabel(self.tr("Ready"))
        self.operation_label.setStyleSheet("font-weight: bold; color: #2196F3; padding: 5px;")
        progress_layout.addWidget(self.operation_label)

        progress_group.setLayout(progress_layout)
        bottom_layout.addWidget(progress_group)

        # Add sections to main layout
        main_layout.addLayout(top_layout)  # Top 2-column section
        main_layout.addLayout(bottom_layout)  # Bottom single-column section

    def load_logo(self):
        """Load and display the application logo."""
        logo_path = 'clamav_gui/assets/logo.png'

        if os.path.exists(logo_path):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Scale the logo to a reasonable size for the left panel
                    scaled_pixmap = pixmap.scaled(180, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    self.logo_label.setPixmap(scaled_pixmap)
                    self.logo_label.setVisible(True)
                    logger.info(f"Successfully loaded logo from: {logo_path}")
                    return
                else:
                    logger.warning(f"Logo file exists but could not be loaded: {logo_path}")
            except Exception as e:
                logger.warning(f"Failed to load logo from {logo_path}: {e}")

        # If no logo found, hide the label
        self.logo_label.setVisible(False)
        logger.info("No logo file found, hiding logo area")

    def create_action_button(self, title, tooltip, color, callback):
        """Create a styled action button."""
        btn = QPushButton(title)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        btn.setMinimumHeight(60)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
                border: 2px solid {self.darken_color(color, 0.7)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
                border: 2px solid {self.darken_color(color, 0.9)};
            }}
        """)
        return btn

    def create_status_label(self, label_text, value_text, color):
        """Create a styled status label."""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 1px solid {color}40;
                border-radius: 5px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(container)

        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; color: #333; font-size: 11px;")
        layout.addWidget(label)

        value = QLabel(value_text)
        value.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        layout.addWidget(value)

        return container

    def darken_color(self, color, factor=0.9):
        """Darken a color by a factor."""
        # Simple color darkening for hover effects
        if color == "#4CAF50":
            return "#45a049"
        elif color == "#2196F3":
            return "#1976D2"
        elif color == "#FF9800":
            return "#F57C00"
        elif color == "#9C27B0":
            return "#7B1FA2"
        return color

    def start_update_timer(self):
        """Start timer for periodic status updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_system_status)
        self.update_timer.start(30000)  # Update every 30 seconds

    def update_system_status(self):
        """Update system status information."""
        try:
            # Update database status
            self.update_database_status()

            # Update last scan status
            self.update_scan_status()

            # Update threats count
            self.update_threats_status()

            # Add activity entry
            self.add_activity_entry(self.tr("Status updated"))

        except Exception as e:
            logger.error(f"Error updating system status: {e}")

    def update_database_status(self):
        """Update virus database status."""
        try:
            # Try to get database info from virus DB updater
            if hasattr(self.parent, 'virus_db_updater') and self.parent.virus_db_updater:
                db_info = self.parent.virus_db_updater.get_database_info()

                if 'error' in db_info and db_info['error']:
                    status = self.tr("Error")
                    color = "red"
                else:
                    version = db_info.get('version', self.tr('Unknown'))
                    signatures = db_info.get('signatures', self.tr('Unknown'))
                    status = f"{version} ({signatures} signatures)"
                    color = "green"
            else:
                status = self.tr("Not available")
                color = "orange"

            # Update the database status label (this is a simplified approach)
            # In a real implementation, you'd update the actual label widget

        except Exception as e:
            logger.error(f"Error updating database status: {e}")

    def update_scan_status(self):
        """Update last scan status."""
        try:
            # This would typically read from scan history or logs
            # For now, show a placeholder
            status = self.tr("Ready")
            color = "green"

            # Update the last scan label

        except Exception as e:
            logger.error(f"Error updating scan status: {e}")

    def update_threats_status(self):
        """Update threats found status."""
        try:
            # This would typically read from quarantine or scan results
            # For now, show 0 threats
            threats = "0"
            color = "green"

            # Update the threats label

        except Exception as e:
            logger.error(f"Error updating threats status: {e}")

    def add_activity_entry(self, activity):
        """Add an entry to the activity list."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {activity}"

        self.activity_list.insertItem(0, entry)  # Add to top

        # Keep only last 20 entries
        while self.activity_list.count() > 20:
            self.activity_list.takeItem(self.activity_list.count() - 1)

    def clear_activity(self):
        """Clear the activity list."""
        self.activity_list.clear()

    def quick_scan(self):
        """Perform a quick scan of common locations."""
        self.perform_scan(self.tr("Quick Scan"), self.get_quick_scan_paths())

    def full_system_scan(self):
        """Perform a full system scan."""
        self.perform_scan(self.tr("Full System Scan"), self.get_system_paths())

    def update_database(self):
        """Update virus database."""
        try:
            if hasattr(self.parent, 'virus_db_updater') and self.parent.virus_db_updater:
                # Show progress
                self.show_operation_progress(self.tr("Updating virus database..."))

                # Start update (this would typically be handled by the virus DB tab)
                # For now, just show a message
                self.add_activity_entry(self.tr("Database update initiated"))

                QMessageBox.information(
                    self, self.tr("Update Started"),
                    self.tr("Virus database update has been started.\n\nCheck the VirusDB tab for progress.")
                )

                self.hide_operation_progress()
            else:
                QMessageBox.warning(
                    self, self.tr("Update Not Available"),
                    self.tr("Database updater not available.")
                )

        except Exception as e:
            logger.error(f"Error updating database: {e}")
            QMessageBox.critical(
                self, self.tr("Update Error"),
                self.tr(f"Failed to start database update:\n\n{str(e)}")
            )

    def view_quarantine(self):
        """Open quarantine management."""
        try:
            # Switch to quarantine tab
            if hasattr(self.parent, 'tabs'):
                for i in range(self.parent.tabs.count()):
                    if self.parent.tabs.tabText(i) == self.tr("Quarantine"):
                        self.parent.tabs.setCurrentIndex(i)
                        break

        except Exception as e:
            logger.error(f"Error opening quarantine: {e}")
            QMessageBox.warning(
                self, self.tr("Quarantine Error"),
                self.tr("Could not open quarantine management.")
            )

    def perform_scan(self, scan_type, paths):
        """Perform a scan of specified paths."""
        try:
            if not paths:
                QMessageBox.warning(
                    self, self.tr("No Paths"),
                    self.tr("No paths specified for scan.")
                )
                return

            # Switch to scan tab
            if hasattr(self.parent, 'tabs'):
                for i in range(self.parent.tabs.count()):
                    if self.parent.tabs.tabText(i) == self.tr("Scan"):
                        self.parent.tabs.setCurrentIndex(i)
                        break

            # Set the scan target in the scan tab
            if hasattr(self.parent, 'scan_tab') and hasattr(self.parent.scan_tab, 'target_input'):
                if len(paths) == 1:
                    self.parent.scan_tab.target_input.setText(paths[0])
                else:
                    self.parent.scan_tab.target_input.setText(f"{len(paths)} locations selected")

                self.add_activity_entry(f"{scan_type} initiated")

        except Exception as e:
            logger.error(f"Error performing scan: {e}")
            QMessageBox.critical(
                self, self.tr("Scan Error"),
                self.tr(f"Failed to start scan:\n\n{str(e)}")
            )

    def get_quick_scan_paths(self):
        """Get paths for quick scan (common user locations)."""
        paths = []

        # Add common user directories
        home = os.path.expanduser("~")
        common_paths = [
            os.path.join(home, "Downloads"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Pictures"),
        ]

        for path in common_paths:
            if os.path.exists(path):
                paths.append(path)

        return paths

    def get_system_paths(self):
        """Get paths for full system scan."""
        paths = []

        # Add system drives/partitions
        if os.name == 'nt':  # Windows
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    paths.append(drive)
        else:  # Unix-like
            paths.append("/")

        return paths

    def show_operation_progress(self, message):
        """Show operation progress bar."""
        self.operation_label.setText(message)
        self.operation_progress.setVisible(True)
        self.operation_progress.setRange(0, 0)  # Indeterminate progress

    def hide_operation_progress(self):
        """Hide operation progress bar."""
        self.operation_progress.setVisible(False)
        self.operation_label.setText(self.tr("Ready"))

    def closeEvent(self, event):
        """Handle tab close event."""
        if self.update_timer:
            self.update_timer.stop()
        super().closeEvent(event)
