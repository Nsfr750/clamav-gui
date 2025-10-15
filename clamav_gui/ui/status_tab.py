"""Status tab for ClamAV GUI application showing system and database information."""
import os
import subprocess
import logging
from datetime import datetime
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QTextEdit, QPushButton, QMessageBox)

logger = logging.getLogger(__name__)


class StatusTab(QWidget):
    """Status tab widget showing ClamAV system and database information."""

    def __init__(self, parent=None):
        """Initialize the status tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Status information group
        status_group = QGroupBox(self.tr("ClamAV Status"))
        status_layout = QVBoxLayout()

        # Status information display
        self.status_info_text = QTextEdit()
        self.status_info_text.setReadOnly(True)
        self.status_info_text.setMaximumHeight(200)
        status_layout.addWidget(self.status_info_text)

        # Refresh button
        refresh_btn = QPushButton(self.tr("Refresh Status"))
        refresh_btn.clicked.connect(self.refresh_status_info)
        status_layout.addWidget(refresh_btn)

        status_group.setLayout(status_layout)

        # Virus database information group
        db_group = QGroupBox(self.tr("Virus Database"))
        db_layout = QVBoxLayout()

        # Database information display
        self.db_info_text = QTextEdit()
        self.db_info_text.setReadOnly(True)
        self.db_info_text.setMaximumHeight(150)
        db_layout.addWidget(self.db_info_text)

        # Update database button
        update_db_btn = QPushButton(self.tr("Update Database"))
        update_db_btn.clicked.connect(self.update_database)
        db_layout.addWidget(update_db_btn)

        db_group.setLayout(db_layout)

        # Add groups to main layout
        layout.addWidget(status_group)
        layout.addWidget(db_group)
        layout.addStretch()

        # Schedule initial refresh after a short delay to ensure controls are initialized
        QtCore.QTimer.singleShot(100, self.refresh_status_info)

    def refresh_status_info(self):
        """Refresh and display ClamAV status information."""
        try:
            # Check if controls exist before using them
            if not hasattr(self, 'status_info_text') or not hasattr(self, 'db_info_text'):
                logger.warning("Status controls not initialized yet")
                return

            # Get ClamAV version
            version_info = self._get_clamav_version()

            # Get virus database information
            db_info = self._get_database_info()

            # Format status information
            status_text = f"""
ClamAV System Status:
===================

Version Information:
  ClamAV Version: {version_info.get('version', 'Unknown')}
  Engine Version: {version_info.get('engine_version', 'Unknown')}

Database Information:
  Database Path: {db_info.get('database_path', 'Unknown')}
  Total Signatures: {db_info.get('total_signatures', 'Unknown')}
  Database Version: {db_info.get('database_version', 'Unknown')}
  Last Update: {db_info.get('last_update', 'Unknown')}

System Information:
  Platform: {version_info.get('platform', 'Unknown')}
  Build Date: {version_info.get('build_date', 'Unknown')}
"""
            self.status_info_text.setPlainText(status_text.strip())

            # Update database information separately
            self._update_database_info_display()

        except Exception as e:
            error_msg = f"Error retrieving ClamAV status: {str(e)}"
            if hasattr(self, 'status_info_text'):
                self.status_info_text.setPlainText(error_msg)
            logger.error(error_msg)

    def _get_clamav_version(self):
        """Get ClamAV version information."""
        info = {
            'version': 'ClamAV not found - Please install ClamAV',
            'engine_version': 'Not available',
            'platform': 'Not available',
            'build_date': 'Not available'
        }

        try:
            # Get clamscan path from parent (main window)
            clamscan_path = self.parent.clamscan_path.text().strip() if hasattr(self.parent, 'clamscan_path') else 'clamscan'
            if not clamscan_path:
                clamscan_path = 'clamscan'

            # Check if clamscan exists
            if not os.path.exists(clamscan_path) and clamscan_path != 'clamscan':
                info['version'] = f"ClamAV executable not found at: {clamscan_path}"
                return info

            # Run clamscan --version
            process = subprocess.run([clamscan_path, '--version'],
                                   capture_output=True, text=True, timeout=10)

            if process.returncode == 0:
                output = process.stdout
                # Parse version information from output
                lines = output.strip().split('\n')
                if lines:
                    # First line usually contains version info
                    first_line = lines[0]
                    if 'ClamAV' in first_line:
                        parts = first_line.split()
                        for i, part in enumerate(parts):
                            if part.startswith('/') and 'ClamAV' in ' '.join(parts[i:i+2]):
                                info['version'] = parts[i+1] if i+1 < len(parts) else 'Unknown'
                                break

                    # Look for engine version
                    for line in lines:
                        if 'ClamAV' in line and '/' in line:
                            # Extract version from something like "ClamAV 0.103.8/26887/Mon"
                            version_part = line.split('/')[-2] if '/' in line else 'Unknown'
                            if version_part and version_part.replace('.', '').isdigit():
                                info['engine_version'] = version_part

                if info['version'] == 'ClamAV not found - Please install ClamAV':
                    info['version'] = f"ClamAV found: {clamscan_path}"
            else:
                info['version'] = f"Error running clamscan: {process.stderr.strip()}"

        except FileNotFoundError:
            info['version'] = f"ClamAV not found - Please install ClamAV or check the path in Settings"
        except subprocess.TimeoutExpired:
            info['version'] = "ClamAV command timed out - Please check installation"
        except subprocess.CalledProcessError as e:
            info['version'] = f"Error running ClamAV: {e}"
        except Exception as e:
            logger.error(f"Error getting ClamAV version: {e}")
            info['version'] = f"Unexpected error: {str(e)}"

        return info

    def _get_database_info(self):
        """Get virus database information including signature count."""
        info = {
            'database_path': 'Database not accessible',
            'total_signatures': 'Database not accessible',
            'database_version': 'Database not accessible',
            'last_update': 'Database not accessible'
        }

        try:
            # Get database directory path
            app_data = os.getenv('APPDATA')
            if app_data:
                clamav_dir = os.path.join(app_data, 'ClamAV')
                db_dir = os.path.join(clamav_dir, 'database')
                info['database_path'] = db_dir

                # Check for database files
                if os.path.exists(db_dir):
                    db_files = [f for f in os.listdir(db_dir) if f.endswith('.cvd') or f.endswith('.cld')]
                    if db_files:
                        # Try to get signature count using sigtool if available
                        try:
                            sigtool_path = self._find_sigtool()
                            if sigtool_path:
                                # Use sigtool to get database info
                                process = subprocess.run([sigtool_path, '--info'],
                                                       capture_output=True, text=True, timeout=10,
                                                       cwd=db_dir)

                                if process.returncode == 0:
                                    output = process.stdout
                                    # Parse signature count from sigtool output
                                    for line in output.split('\n'):
                                        if 'signatures' in line.lower():
                                            # Extract number from something like "Total signatures: 8500000"
                                            parts = line.split(':')
                                            if len(parts) > 1:
                                                sig_count = parts[1].strip().split()[0]
                                                if sig_count.isdigit():
                                                    info['total_signatures'] = sig_count

                        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                            pass

                        # Fallback: count signatures using clamscan
                        if info['total_signatures'] == 'Database not accessible':
                            try:
                                clamscan_path = self.parent.clamscan_path.text().strip() if hasattr(self.parent, 'clamscan_path') else 'clamscan'
                                if not clamscan_path:
                                    clamscan_path = 'clamscan'

                                # Count signatures using grep
                                process = subprocess.run([clamscan_path, '--list-sigs'],
                                                       capture_output=True, text=True, timeout=30,
                                                       cwd=db_dir)

                                if process.returncode == 0:
                                    sig_count = len([line for line in process.stdout.split('\n') if line.strip()])
                                    if sig_count > 0:
                                        info['total_signatures'] = str(sig_count)

                            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                                pass

                        # Get database version from file names or info
                        try:
                            # Try to read CVD header for version info
                            for db_file in db_files:
                                if db_file.endswith('.cvd'):
                                    db_path = os.path.join(db_dir, db_file)
                                    try:
                                        with open(db_path, 'rb') as f:
                                            # CVD format has version info in header
                                            header = f.read(512)
                                            # Look for version string in header
                                            header_str = header.decode('latin-1', errors='ignore')
                                            if 'ClamAV-VDB:' in header_str:
                                                # Extract version from CVD header
                                                version_start = header_str.find('ClamAV-VDB:') + 11
                                                version_end = header_str.find('\0', version_start)
                                                if version_end > version_start:
                                                    version = header_str[version_start:version_end].strip()
                                                    info['database_version'] = version
                                                    break
                                    except:
                                        pass

                            # Fallback: use file modification time as last update
                            if db_files:
                                db_path = os.path.join(db_dir, db_files[0])
                                last_update = datetime.fromtimestamp(os.path.getmtime(db_path))
                                info['last_update'] = last_update.strftime('%Y-%m-%d %H:%M:%S')

                        except Exception as e:
                            logger.warning(f"Could not read database version: {e}")

                    else:
                        info['total_signatures'] = 'No database files found'
                        info['database_version'] = 'No database files found'
                        info['last_update'] = 'No database files found'
                else:
                    info['total_signatures'] = 'Database directory not found'
                    info['database_version'] = 'Database directory not found'
                    info['last_update'] = 'Database directory not found'
            else:
                info['database_path'] = 'APPDATA environment variable not set'
                info['total_signatures'] = 'Cannot determine database location'
                info['database_version'] = 'Cannot determine database location'
                info['last_update'] = 'Cannot determine database location'

        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            info['total_signatures'] = f'Error accessing database: {str(e)}'
            info['database_version'] = f'Error accessing database: {str(e)}'
            info['last_update'] = f'Error accessing database: {str(e)}'

        return info

    def _find_sigtool(self):
        """Find the sigtool executable."""
        possible_paths = [
            self.parent.clamscan_path.text().strip().replace('clamscan', 'sigtool') if hasattr(self.parent, 'clamscan_path') else 'sigtool',
            'sigtool'
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path

        return None

    def _update_database_info_display(self):
        """Update the database information display with current data."""
        try:
            # Check if control exists before using it
            if not hasattr(self, 'db_info_text'):
                logger.warning("Database info control not initialized yet")
                return

            db_info = self._get_database_info()

            db_text = f"""
Virus Database Information:
========================

Total Signatures: {db_info.get('total_signatures', 'Unknown')}
Database Version: {db_info.get('database_version', 'Unknown')}
Database Path: {db_info.get('database_path', 'Unknown')}
Last Update: {db_info.get('last_update', 'Unknown')}

Status: {'Up to date' if db_info.get('total_signatures', '0').isdigit() and int(db_info['total_signatures']) > 0 else 'Database may need update'}
"""
            self.db_info_text.setPlainText(db_text.strip())

        except Exception as e:
            if hasattr(self, 'db_info_text'):
                self.db_info_text.setPlainText(f"Error updating database information: {str(e)}")
            logger.error(f"Error in _update_database_info_display: {e}")

    def update_database(self):
        """Update the ClamAV virus database."""
        if hasattr(self.parent, 'update_database'):
            self.parent.update_database()
        else:
            QMessageBox.warning(self, self.tr("Error"),
                              self.tr("Update database method not available in main window"))
