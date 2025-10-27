"""
Virus Database Tab for ClamAV GUI.
Displays comprehensive information about the ClamAV virus database.
"""
import os
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

import logging
logger = logging.getLogger(__name__)

class VirusDBTab(QWidget):
    """Tab for displaying and managing ClamAV virus database information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.db_info = {}
        self.refresh_timer = None

        # Initialize UI
        self.setup_ui()
        self.refresh_database_info()

        # Set up auto-refresh timer (every 30 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_database_info)
        self.refresh_timer.start(30000)  # 30 seconds

    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)

        # Database Information Section
        info_group = QGroupBox("Virus Database Information")
        info_layout = QVBoxLayout(info_group)

        # Database status display
        self.db_info_text = QTextEdit()
        self.db_info_text.setReadOnly(True)
        self.db_info_text.setMaximumHeight(200)
        info_layout.addWidget(self.db_info_text)

        # Database files table
        files_group = QGroupBox("Database Files")
        files_layout = QVBoxLayout(files_group)

        self.files_table = QTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels([
            "File Name", "Size (KB)", "Version", "Signatures", "Last Modified"
        ])
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_table)

        main_layout.addWidget(info_group)
        main_layout.addWidget(files_group)

        # Control buttons
        buttons_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh Information")
        self.refresh_btn.clicked.connect(self.refresh_database_info)
        # Style the Refresh Information button with gray background and dark text
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #333333;
                border: 1px solid #CCCCCC;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                color: #999999;
            }
        """)
        buttons_layout.addWidget(self.refresh_btn)
        self.update_btn = QPushButton("Update Database")
        self.update_btn.clicked.connect(self.update_database)
        # Style the Update Database button with blue background and white text
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #B0BEC5;
                color: #78909C;
            }
        """)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # Progress bar for updates
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 25px;
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
        self.progress_bar.setProperty("animated", False)
        main_layout.addWidget(self.progress_bar)

    def refresh_database_info(self):
        """Refresh and display virus database information."""
        try:
            # Get database information
            self.db_info = self._get_database_info()

            # Update the display
            self._update_info_display()

            # Update files table
            self._update_files_table()

            logger.info("Virus database information refreshed successfully")

        except Exception as e:
            error_msg = f"Error refreshing database information: {str(e)}"
            self.db_info_text.setPlainText(error_msg)
            logger.error(error_msg)

    def _get_database_info(self):
        """Get comprehensive database information."""
        info = {
            'database_path': 'Database not accessible',
            'total_signatures': 'Unknown',
            'database_version': 'Unknown',
            'last_update': 'Unknown',
            'total_files': 0,
            'total_size': 0,
            'files': []
        }

        try:
            # Find database directory
            db_dir = self._find_database_directory()

            if db_dir and os.path.exists(db_dir):
                info['database_path'] = db_dir

                # Get database files
                db_files = [f for f in os.listdir(db_dir) if f.endswith('.cvd') or f.endswith('.cld')]

                if db_files:
                    info['total_files'] = len(db_files)

                    # Calculate total size
                    total_size = 0
                    files_info = []

                    for db_file in db_files:
                        db_path = os.path.join(db_dir, db_file)
                        try:
                            file_size = os.path.getsize(db_path)
                            total_size += file_size

                            # Get file modification time
                            mod_time = os.path.getmtime(db_path)

                            # Get file info
                            file_info = {
                                'name': db_file,
                                'size': file_size,
                                'mod_time': datetime.fromtimestamp(mod_time),
                                'version': self._get_file_version(db_path, db_file),
                                'signatures': self._get_file_signature_count(db_path, db_file)
                            }
                            files_info.append(file_info)

                        except (OSError, IOError) as e:
                            logger.warning(f"Error reading file {db_file}: {e}")

                    info['total_size'] = total_size
                    info['files'] = files_info

                    # Get signature counts and versions
                    total_signatures = 0
                    versions = []

                    for file_info in files_info:
                        sig_count = file_info.get('signatures', 0)
                        if isinstance(sig_count, int):
                            total_signatures += sig_count

                        version = file_info.get('version', '')
                        if version and version not in versions:
                            versions.append(version)

                    if total_signatures > 0:
                        info['total_signatures'] = str(total_signatures)

                    if versions:
                        info['database_version'] = ', '.join(versions)

                    # Get last update time (most recent file)
                    if files_info:
                        latest_file = max(files_info, key=lambda x: x['mod_time'])
                        info['last_update'] = latest_file['mod_time'].strftime('%Y-%m-%d %H:%M:%S')

                else:
                    info['total_signatures'] = 'No database files found'
                    info['database_version'] = 'No database files found'
                    info['last_update'] = 'No database files found'

            else:
                info['total_signatures'] = 'Database directory not found - Check ClamAV installation'
                info['database_version'] = 'Database directory not found - Check ClamAV installation'
                info['last_update'] = 'Database directory not found - Check ClamAV installation'

        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            info['total_signatures'] = f'Error accessing database: {str(e)}'
            info['database_version'] = f'Error accessing database: {str(e)}'
            info['last_update'] = f'Error accessing database: {str(e)}'

        return info

    def _find_database_directory(self):
        """Find the ClamAV database directory using multiple methods."""
        # Method 1: Check common Windows installation paths
        common_paths = [
            r'C:\Program Files\ClamAV\database',
            r'C:\Program Files (x86)\ClamAV\database',
            r'C:\ClamAV\database',
            r'C:\ProgramData\ClamAV\db',
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        # Method 2: Check APPDATA if it exists (for user-specific installations)
        try:
            app_data = os.getenv('APPDATA')
            if app_data:
                user_paths = [
                    os.path.join(app_data, 'ClamAV', 'database'),
                    os.path.join(app_data, '.clamav', 'database'),
                    os.path.join(app_data, 'clamav', 'database'),
                ]
                for path in user_paths:
                    if os.path.exists(path):
                        return path
        except Exception:
            pass

        # Method 3: Check ProgramData (system-wide app data)
        try:
            program_data = os.getenv('PROGRAMDATA')
            if program_data:
                system_paths = [
                    os.path.join(program_data, 'ClamAV', 'db'),
                    os.path.join(program_data, 'clamav', 'db'),
                ]
                for path in system_paths:
                    if os.path.exists(path):
                        return path
        except Exception:
            pass

        # Method 4: Try to detect from clamscan location if available
        try:
            # Get clamscan path from parent settings
            if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
                clamscan_path = self.parent.current_settings.get('clamscan_path', 'clamscan')
            elif hasattr(self.parent, 'settings') and self.parent.settings:
                settings = self.parent.settings.load_settings() or {}
                clamscan_path = settings.get('clamscan_path', 'clamscan')
            else:
                clamscan_path = 'clamscan'

            if clamscan_path and clamscan_path != 'clamscan':
                clamscan_dir = os.path.dirname(clamscan_path)
                if clamscan_dir and clamscan_dir != '.':
                    # Assume database is in same directory or subdirectory
                    possible_db_paths = [
                        os.path.join(clamscan_dir, 'database'),
                        os.path.join(os.path.dirname(clamscan_dir), 'database'),
                        os.path.join(clamscan_dir, '..', 'database'),
                        os.path.join(clamscan_dir, 'db'),
                    ]
                    for path in possible_db_paths:
                        if os.path.exists(path):
                            return path
        except Exception:
            pass

        # Method 5: Check common Linux/Unix paths (if running on non-Windows)
        if os.name != 'nt':
            unix_paths = [
                '/var/lib/clamav',
                '/usr/share/clamav',
                '/usr/local/share/clamav',
                '/opt/clamav/share/clamav',
            ]
            for path in unix_paths:
                if os.path.exists(path):
                    return path

        return None

    def _get_file_version(self, file_path, file_name):
        """Get version information from a database file."""
        try:
            if file_name.endswith('.cvd'):
                with open(file_path, 'rb') as f:
                    # CVD format has version info in header
                    header = f.read(512)
                    header_str = header.decode('latin-1', errors='ignore')
                    if 'ClamAV-VDB:' in header_str:
                        version_start = header_str.find('ClamAV-VDB:') + 11
                        version_end = header_str.find('\0', version_start)
                        if version_end > version_start:
                            version = header_str[version_start:version_end].strip()
                            return version
        except Exception:
            pass

        # Fallback: extract from filename
        if '.cvd' in file_name or '.cld' in file_name:
            name_part = file_name.replace('.cvd', '').replace('.cld', '')
            if name_part and not name_part.isdigit():
                return name_part

        return 'Unknown'

    def _get_file_signature_count(self, file_path, file_name):
        """Get signature count from a database file."""
        try:
            with open(file_path, 'rb') as f:
                # Try different offsets for signature count
                for offset in [512, 516, 520, 524]:
                    f.seek(offset, 0)
                    count_data = f.read(4)
                    if len(count_data) == 4:
                        count = int.from_bytes(count_data, byteorder='little', signed=False)
                        if 100000 <= count <= 10000000:  # Reasonable range
                            return count
        except Exception:
            pass

        return 0

    def _update_info_display(self):
        """Update the database information display."""
        info = self.db_info

        info_text = f"""📊 Virus Database Information
{'=' * 40}

📁 Database Path: {info.get('database_path', 'Unknown')}
🔢 Total Signatures: {info.get('total_signatures', 'Unknown')}
📋 Database Version: {info.get('database_version', 'Unknown')}
🕒 Last Update: {info.get('last_update', 'Unknown')}
📁 Total Files: {info.get('total_files', 0)}
💾 Total Size: {info.get('total_size', 0) / (1024*1024):.2f} MB

🔄 Status: {'✅ Database ready' if info.get('total_files', 0) > 0 else '⚠️ Database not found'}
"""

        self.db_info_text.setPlainText(info_text.strip())

    def _update_files_table(self):
        """Update the database files table."""
        files_info = self.db_info.get('files', [])

        self.files_table.setRowCount(len(files_info))

        for i, file_info in enumerate(files_info):
            # File name
            self.files_table.setItem(i, 0, QTableWidgetItem(file_info['name']))

            # Size
            size_kb = file_info['size'] / 1024
            self.files_table.setItem(i, 1, QTableWidgetItem(f"{size_kb:.1f}"))

            # Version
            self.files_table.setItem(i, 2, QTableWidgetItem(file_info.get('version', 'Unknown')))

            # Signatures
            sig_count = file_info.get('signatures', 0)
            if isinstance(sig_count, int):
                self.files_table.setItem(i, 3, QTableWidgetItem(f"{sig_count:,}"))
            else:
                self.files_table.setItem(i, 3, QTableWidgetItem(str(sig_count)))

            # Last modified
            mod_time_str = file_info['mod_time'].strftime('%Y-%m-%d %H:%M:%S')
            self.files_table.setItem(i, 4, QTableWidgetItem(mod_time_str))

        self.files_table.resizeColumnsToContents()

    def update_database(self):
        """Update the ClamAV virus database."""
        try:
            # Check if freshclam is available
            if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
                freshclam_path = self.parent.current_settings.get('freshclam_path', 'freshclam')
            elif hasattr(self.parent, 'settings') and self.parent.settings:
                settings = self.parent.settings.load_settings() or {}
                freshclam_path = settings.get('freshclam_path', 'freshclam')
            else:
                freshclam_path = 'freshclam'

            if not freshclam_path or freshclam_path == 'freshclam':
                # Try to find freshclam in PATH
                try:
                    subprocess.run(['freshclam', '--version'], capture_output=True, timeout=5)
                    freshclam_path = 'freshclam'
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    freshclam_path = None

            if not freshclam_path:
                QMessageBox.warning(
                    self, "Update Not Available",
                    "FreshClam (database updater) is not available.\n\n"
                    "Please ensure ClamAV is properly installed and configured."
                )
                return

            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)  # Determinate progress
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Starting database update...")
            self.update_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)

            # Start update in a separate thread
            self.update_thread = DatabaseUpdateThread(freshclam_path)
            self.update_thread.update_output.connect(self._handle_update_output)
            self.update_thread.finished.connect(self._handle_update_finished)
            self.update_thread.start()

        except Exception as e:
            QMessageBox.critical(
                self, "Update Error",
                f"Failed to start database update: {str(e)}"
            )
            self._reset_update_ui()

    def _handle_update_output(self, text):
        """Handle update output."""
        # Update progress text and simulate progress
        if "Downloading" in text or "Testing" in text:
            self.progress_bar.setFormat(f"Updating... {text.strip()}")
            self.progress_bar.setValue(50)  # Midway through update
        elif "Updated" in text or "updated" in text.lower():
            self.progress_bar.setFormat("Update completed successfully!")
            self.progress_bar.setValue(100)
        elif "Error" in text or "ERROR" in text:
            self.progress_bar.setFormat(f"Error: {text.strip()}")
            self.progress_bar.setValue(0)

    def _handle_update_finished(self, success, message):
        """Handle update completion."""
        self._reset_update_ui()

        if success:
            QMessageBox.information(
                self, "Update Successful",
                f"Virus database updated successfully!\n\n{message}"
            )
            # Refresh information after successful update
            QTimer.singleShot(1000, self.refresh_database_info)
        else:
            QMessageBox.warning(
                self, "Update Failed",
                f"Virus database update failed.\n\nError: {message}"
            )

    def _reset_update_ui(self):
        """Reset the update UI controls."""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")
        self.update_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)

    def closeEvent(self, event):
        """Handle close event."""
        if self.refresh_timer:
            self.refresh_timer.stop()
        event.accept()

class DatabaseUpdateThread(QThread):
    """Thread for updating ClamAV database."""
    update_output = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, freshclam_path):
        super().__init__()
        self.freshclam_path = freshclam_path

    def run(self):
        """Run the database update."""
        try:
            # First, check what options are supported by this freshclam version
            supported_options = self._get_supported_freshclam_options()

            # Build command with only supported options
            cmd = [self.freshclam_path]

            # Add verbose if supported
            if '--verbose' in supported_options or '-v' in supported_options:
                cmd.append('--verbose')

            print(f"VirusDB DEBUG: Running freshclam command: {' '.join(cmd)}")
            print(f"VirusDB DEBUG: Supported options: {supported_options}")

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            print(f"VirusDB DEBUG: Freshclam return code: {process.returncode}")
            print(f"VirusDB DEBUG: Freshclam stdout: {process.stdout}")
            print(f"VirusDB DEBUG: Freshclam stderr: {process.stderr}")

            if process.returncode == 0:
                self.finished.emit(True, process.stdout.strip())
            else:
                error_msg = process.stderr.strip() or process.stdout.strip()
                self.finished.emit(False, error_msg)

        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Database update timed out after 5 minutes")
        except Exception as e:
            self.finished.emit(False, str(e))

    def _get_supported_freshclam_options(self):
        """Get list of supported options for the installed freshclam version."""
        try:
            # Try to get help output
            process = subprocess.run(
                [self.freshclam_path, '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if process.returncode == 0:
                help_text = process.stdout.lower()
                supported = []

                # Check for common options
                option_map = {
                    '--verbose': ['--verbose', '-v'],
                    '--user-agent': ['--user-agent'],
                    '--config': ['--config', '-c'],
                    '--daemon': ['--daemon', '-d'],
                    '--no-daemon': ['--no-daemon'],
                    '--checks': ['--checks'],
                    '--datadir': ['--datadir'],
                    '--log': ['--log', '-l'],
                }

                for option, variants in option_map.items():
                    for variant in variants:
                        if variant in help_text:
                            supported.append(option)
                            break

                return supported

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Fallback: return basic options that are almost always supported
        return ['--verbose']
