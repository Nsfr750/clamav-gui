"""
Home tab for ClamAV GUI application showing dashboard and quick actions.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QProgressBar, QGridLayout, QFrame, QSizePolicy, QSpacerItem,
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox
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

        # Initial status update
        QTimer.singleShot(1000, self.update_system_status)  # Update after 1 second

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
        welcome_group.setStyleSheet("QGroupBox { margin: 10px; font-size: 18px; font-weight: bold; }")
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

        # Load current settings
        self.load_settings()

        # Check and reinitialize quarantine manager if needed
        self._check_quarantine_manager()

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
                color: #75b5aa;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
                width: 1px;
                margin: 0px;
            }
        """)
        # Disable any animations
        self.operation_progress.setProperty("animated", False)
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
        candidates = []
        try:
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                base = Path(sys._MEIPASS)
                candidates.extend([
                    base / 'clamav_gui' / 'assets' / 'logo.png',
                    base / 'assets' / 'logo.png',
                ])
        except Exception:
            pass

        try:
            here = Path(__file__).resolve()
            pkg_root = here.parent.parent
            candidates.extend([
                pkg_root / 'assets' / 'logo.png',
                Path.cwd() / 'clamav_gui' / 'assets' / 'logo.png',
                Path.cwd() / 'assets' / 'logo.png',
            ])
        except Exception:
            pass

        for path in candidates:
            try:
                if path and path.exists():
                    pixmap = QPixmap(str(path))
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(180, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                        self.logo_label.setPixmap(scaled_pixmap)
                        self.logo_label.setVisible(True)
                        logger.info(f"Successfully loaded logo from: {path}")
                        return
            except Exception:
                continue

        self.logo_label.setVisible(False)
        logger.info("No logo file found, hiding logo area")

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
        label.setStyleSheet("font-weight: bold; color: #00ffff; font-size: 11px;")
        layout.addWidget(label)

        value = QLabel(value_text)
        value.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        layout.addWidget(value)

        return container

    def update_status_label(self, container, label_text, value_text, color):
        """Update a status label container with new values."""
        try:
            # Find the value label within the container using findChildren
            value_labels = container.findChildren(QLabel)

            # Find the value label (the one that doesn't contain the label text)
            value_label = None
            for label in value_labels:
                if label_text not in label.text():  # This should be the value label
                    value_label = label
                    break

            if value_label:
                # Update the value text
                value_label.setText(value_text)

                # Update the color based on status
                color_map = {
                    "green": "#4CAF50",
                    "red": "#F44336",
                    "orange": "#FF9800",
                    "gray": "#9E9E9E"
                }

                hex_color = color_map.get(color, "#4CAF50")
                value_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {hex_color};")

                # Update container background color too
                container.setStyleSheet(f"""
                    QFrame {{
                        background-color: #1f1f1f;
                        border: 1px solid gray;
                        border-radius: 5px;
                        padding: 8px;
                    }}
                """)

        except Exception as e:
            logger.error(f"Error updating status label: {e}")

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

            # Update protection status (overall system state)
            self.update_protection_status()

            # Add activity entry
            self.add_activity_entry(self.tr("Status updated"))

        except Exception as e:
            logger.error(f"Error updating system status: {e}")

    def update_database_status(self):
        """Update virus database status."""
        try:
            # First try to get database info from status tab (which we know works)
            if hasattr(self.parent, 'status_tab'):
                # Get fresh database info from status tab
                db_info = self.parent.status_tab._get_database_info()

                if db_info and db_info.get('total_signatures') not in ['Database not accessible', 'Unknown', 'Error accessing database:']:
                    # Database is accessible
                    signatures = db_info.get('total_signatures', 'Unknown')
                    version = db_info.get('database_version', 'Unknown')
                    last_update = db_info.get('last_update', 'Unknown')

                    if signatures and signatures != 'Unknown':
                        status = f"{version} ({signatures} signatures)"
                        color = "green"
                    else:
                        status = self.tr("Checking...")
                        color = "orange"
                else:
                    status = self.tr("Not available")
                    color = "orange"
            else:
                # Fallback: try virus DB updater
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

            # Update the database status label
            self.update_status_label(self.db_status_label, self.tr("Virus Database:"), status, color)

        except Exception as e:
            logger.error(f"Error updating database status: {e}")
            self.update_status_label(self.db_status_label, self.tr("Virus Database:"), self.tr("Error"), "red")

    def update_scan_status(self):
        """Update last scan status."""
        try:
            # Try to get information from advanced reporting or scan history
            if hasattr(self.parent, 'advanced_reporting'):
                try:
                    # Get recent scan statistics
                    analytics = self.parent.advanced_reporting.generate_analytics_report(7)  # Last 7 days

                    if 'error' not in analytics and analytics.get('total_scans', 0) > 0:
                        last_scan_date = analytics.get('last_scan_date', self.tr('Unknown'))
                        total_scans = analytics.get('total_scans', 0)

                        if last_scan_date != 'Unknown':
                            status = f"{total_scans} scans (last: {last_scan_date})"
                        else:
                            status = f"{total_scans} scans"
                        color = "green"
                    else:
                        status = self.tr("Ready")
                        color = "green"
                except Exception as e:
                    logger.warning(f"Error getting scan analytics: {e}")
                    status = self.tr("Ready")
                    color = "green"
            else:
                status = self.tr("Ready")
                color = "green"

            # Update the last scan label
            self.update_status_label(self.last_scan_label, self.tr("Last Scan:"), status, color)

        except Exception as e:
            logger.error(f"Error updating scan status: {e}")
            self.update_status_label(self.last_scan_label, self.tr("Last Scan:"), self.tr("Error"), "red")

    def update_threats_status(self):
        """Update threats found status."""
        try:
            # Get real information from quarantine manager
            if hasattr(self.parent, 'quarantine_manager') and self.parent.quarantine_manager:
                try:
                    stats = self.parent.quarantine_manager.get_quarantine_stats()
                    if stats and isinstance(stats, dict):
                        threats = str(stats.get('total_quarantined', 0))
                        color = "orange" if int(threats) > 0 else "green"
                    else:
                        threats = "0"
                        color = "green"
                except Exception as e:
                    logger.warning(f"Error getting quarantine stats: {e}")
                    threats = "0"
                    color = "green"
            else:
                logger.debug("Quarantine manager not available or not initialized")
                # Try to create a minimal fallback quarantine manager
                try:
                    from clamav_gui.utils.quarantine_manager import QuarantineManager
                    # Try to create with app directory fallback
                    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    fallback_dir = os.path.join(app_dir, 'quarantine')
                    self.parent.quarantine_manager = QuarantineManager(fallback_dir)
                    logger.info(f"Created fallback quarantine manager: {fallback_dir}")
                    # Now try to get stats
                    stats = self.parent.quarantine_manager.get_quarantine_stats()
                    if stats and isinstance(stats, dict):
                        threats = str(stats.get('total_quarantined', 0))
                        color = "orange" if int(threats) > 0 else "green"
                    else:
                        threats = "0"
                        color = "green"
                except Exception as e2:
                    logger.warning(f"Could not create fallback quarantine manager: {e2}")
                    threats = "0"
                    color = "green"

            # Update the threats label
            self.update_status_label(self.threats_label, self.tr("Threats Found:"), threats, color)

        except Exception as e:
            logger.error(f"Error updating threats status: {e}")
            self.update_status_label(self.threats_label, self.tr("Threats Found:"), self.tr("Error"), "red")

    def update_protection_status(self):
        """Update overall system protection status."""
        try:
            # Evaluate overall protection state
            protection_level = self.evaluate_protection_level()

            # Update the protection label
            self.update_status_label(self.protection_label, self.tr("Protection:"), protection_level['status'], protection_level['color'])

        except Exception as e:
            logger.error(f"Error updating protection status: {e}")
            self.update_status_label(self.protection_label, self.tr("Protection:"), self.tr("Error"), "red")

    def evaluate_protection_level(self):
        """Evaluate the overall system protection level."""
        try:
            # Check database status
            db_ok = False
            if hasattr(self.parent, 'status_tab'):
                db_info = self.parent.status_tab._get_database_info()
                if db_info and db_info.get('total_signatures') not in ['Database not accessible', 'Unknown', 'Error accessing database:']:
                    db_ok = True

            # Check threats
            threats_count = 0
            if hasattr(self.parent, 'quarantine_manager') and self.parent.quarantine_manager:
                try:
                    stats = self.parent.quarantine_manager.get_quarantine_stats()
                    if stats and isinstance(stats, dict):
                        threats_count = stats.get('total_quarantined', 0)
                except Exception as e:
                    logger.debug(f"Could not get quarantine stats for protection evaluation: {e}")
                    threats_count = 0
            else:
                logger.debug("Quarantine manager not available for protection evaluation")
                # Try to create a fallback quarantine manager
                try:
                    from clamav_gui.utils.quarantine_manager import QuarantineManager
                    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    fallback_dir = os.path.join(app_dir, 'quarantine')
                    self.parent.quarantine_manager = QuarantineManager(fallback_dir)
                    logger.info(f"Created fallback quarantine manager for protection evaluation: {fallback_dir}")
                    stats = self.parent.quarantine_manager.get_quarantine_stats()
                    if stats and isinstance(stats, dict):
                        threats_count = stats.get('total_quarantined', 0)
                except Exception as e2:
                    logger.debug(f"Could not create fallback quarantine manager for protection: {e2}")
                    threats_count = 0

            # Check scan history
            recent_scans = False
            if hasattr(self.parent, 'advanced_reporting'):
                try:
                    analytics = self.parent.advanced_reporting.generate_analytics_report(7)
                    if 'error' not in analytics and analytics.get('total_scans', 0) > 0:
                        recent_scans = True
                except:
                    pass

            # Evaluate overall protection
            if not db_ok:
                return {
                    'status': self.tr("Database Error"),
                    'color': "red"
                }
            elif threats_count > 5:
                return {
                    'status': self.tr("Multiple Threats"),
                    'color': "red"
                }
            elif threats_count > 0:
                return {
                    'status': self.tr("Threats Detected"),
                    'color': "orange"
                }
            elif recent_scans:
                return {
                    'status': self.tr("Protected"),
                    'color': "green"
                }
            else:
                return {
                    'status': self.tr("Ready"),
                    'color': "green"
                }

        except Exception as e:
            logger.error(f"Error evaluating protection level: {e}")
            return {
                'status': self.tr("Unknown"),
                'color': "orange"
            }

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

    def load_settings(self):
        """Load settings for the home tab."""
        try:
            if hasattr(self.parent, 'settings') and self.parent.settings:
                settings = self.parent.settings.load_settings() or {}

                # Update database path display if custom path is saved
                if hasattr(self, 'db_path_display') and 'db_path' in settings and settings['db_path']:
                    self.db_path_display.setText(settings['db_path'])
                elif hasattr(self, 'db_path_display'):
                    # Show detected database path
                    self.db_path_display.setText(self.get_database_path())

        except Exception as e:
            logger.error(f"Error loading settings in home tab: {e}")

    def _check_quarantine_manager(self):
        """Check and reinitialize quarantine manager if needed."""
        if not hasattr(self.parent, 'quarantine_manager') or not self.parent.quarantine_manager:
            logger.info("Attempting to reinitialize quarantine manager from home tab...")
            if hasattr(self.parent, 'reinitialize_quarantine_manager'):
                if self.parent.reinitialize_quarantine_manager():
                    logger.info("Quarantine manager successfully reinitialized")
                else:
                    logger.warning("Failed to reinitialize quarantine manager")

    def closeEvent(self, event):
        """Handle tab close event."""
        if self.update_timer:
            self.update_timer.stop()
        super().closeEvent(event)
