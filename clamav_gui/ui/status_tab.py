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

        # ClamAV Information group
        info_group = QGroupBox(self.tr("ClamAV Information"))
        info_layout = QVBoxLayout()

        # Information display
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(300)
        info_layout.addWidget(self.info_text)

        # Action buttons layout (side by side)
        buttons_layout = QHBoxLayout()

        refresh_btn = QPushButton(self.tr("Refresh Status"))
        refresh_btn.clicked.connect(self.refresh_status_info)
        buttons_layout.addWidget(refresh_btn)

        update_db_btn = QPushButton(self.tr("Update Database"))
        update_db_btn.clicked.connect(self.update_database)
        buttons_layout.addWidget(update_db_btn)

        info_layout.addLayout(buttons_layout)
        info_group.setLayout(info_layout)

        # Add group to main layout
        layout.addWidget(info_group)
        layout.addStretch()

        # Schedule initial refresh after a short delay to ensure controls are initialized
        QtCore.QTimer.singleShot(100, self.refresh_status_info)

    def refresh_status_info(self):
        """Refresh and display ClamAV status information."""
        try:
            # Check if control exists before using it
            if not hasattr(self, 'info_text'):
                logger.warning("Info control not initialized yet")
                return

            # Get ClamAV version
            version_info = self._get_clamav_version()

            # Get virus database information
            db_info = self._get_database_info()

            # Get system information
            system_info = self._get_system_info()

            # Get ClamAV paths from settings
            clamav_paths = self._get_clamav_paths()

            # Format information in a clean, organized way
            info_text = f"""ClamAV Information:
==================

📋 Version Information:
   • ClamAV Version: {version_info.get('version', 'Unknown')}
   • Engine Version: {version_info.get('engine_version', 'Unknown')}
   • Platform: {version_info.get('platform', 'Unknown')}
   • Build Date: {version_info.get('build_date', 'Unknown')}

🗃️ Database Information:
   • Database Path: {db_info.get('database_path', 'Unknown')}
   • Total Signatures: {db_info.get('total_signatures', 'Unknown')}
   • Database Version: {db_info.get('database_version', 'Unknown')}
   • Last Update: {db_info.get('last_update', 'Unknown')}

💻 System Information:
   • Operating System: {system_info.get('os_version', 'Unknown')}
   • Python Version: {system_info.get('python_version', 'Unknown')}
   • App Version: {system_info.get('app_version', 'Unknown')}

🔧 ClamAV Paths:
   • ClamScan Path: {clamav_paths.get('clamscan_path', 'Not configured')}
   • FreshClam Path: {clamav_paths.get('freshclam_path', 'Not configured')}
   • ClamD Path: {clamav_paths.get('clamd_path', 'Not configured')}

🔄 Status: {'✅ Up to date' if db_info.get('total_signatures', '0').isdigit() and int(db_info['total_signatures']) > 0 else '⚠️ Database may need update'}
"""

            self.info_text.setPlainText(info_text.strip())

        except Exception as e:
            error_msg = f"❌ Error retrieving ClamAV status: {str(e)}"
            if hasattr(self, 'info_text'):
                self.info_text.setPlainText(error_msg)
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

    def _get_system_info(self):
        """Get system information including OS, Python, and app version."""
        info = {
            'app_version': 'Unknown',
            'os_version': 'Unknown',
            'python_version': 'Unknown'            
        }

        try:
            # Get OS version
            try:
                import platform
                info['os_version'] = platform.platform()
            except Exception:
                pass

            # Get Python version
            try:
                import sys
                info['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            except Exception:
                pass

            # Get app version
            try:
                from clamav_gui import __version__
                info['app_version'] = __version__
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error getting system info: {e}")

        return info

    def _get_clamav_paths(self):
        """Get ClamAV executable paths from settings."""
        paths = {
            'clamscan_path': 'Not configured',
            'freshclam_path': 'Not configured',
            'clamd_path': 'Not configured'
        }

        try:
            # Get paths from parent settings if available
            if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
                settings = self.parent.current_settings
                paths['clamscan_path'] = settings.get('clamscan_path', 'Not configured')
                paths['freshclam_path'] = settings.get('freshclam_path', 'Not configured')
                paths['clamd_path'] = settings.get('clamd_path', 'Not configured')
            elif hasattr(self.parent, 'settings') and self.parent.settings:
                # Fallback to load settings
                settings = self.parent.settings.load_settings() or {}
                paths['clamscan_path'] = settings.get('clamscan_path', 'Not configured')
                paths['freshclam_path'] = settings.get('freshclam_path', 'Not configured')
                paths['clamd_path'] = settings.get('clamd_path', 'Not configured')

        except Exception as e:
            logger.error(f"Error getting ClamAV paths: {e}")

        return paths

    def update_database(self):
        """Update the ClamAV virus database."""
        try:
            # Check if parent has the update_database method
            if not hasattr(self.parent, 'update_database'):
                error_msg = (
                    "❌ Update Database Not Available\n\n"
                    "The 'Update Database' functionality requires the full ClamAV GUI application.\n\n"
                    "Possible solutions:\n"
                    "• Use the 'Virus DB' tab instead (if available)\n"
                    "• Run 'freshclam' manually from command line\n"
                    "• Check if ClamAV is properly installed and configured\n"
                    "• Use the main ClamAV GUI application instead of this simplified version"
                )
                QMessageBox.warning(self, self.tr("Update Database Unavailable"), error_msg)
                return

            # Check if virus database updater is available
            if not hasattr(self.parent, 'virus_db_updater') or not self.parent.virus_db_updater:
                error_msg = (
                    "❌ Database Updater Not Initialized\n\n"
                    "The virus database updater is not properly initialized.\n\n"
                    "Please check that ClamAV is installed and configured correctly."
                )
                QMessageBox.warning(self, self.tr("Updater Not Ready"), error_msg)
                return

            # Show progress dialog
            self.progress_dialog = QMessageBox(self)
            self.progress_dialog.setWindowTitle(self.tr("Database Update"))
            self.progress_dialog.setText(self.tr("Starting database update..."))
            self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
            self.progress_dialog.setModal(True)

            # Create update output widget
            self.update_output_widget = QTextEdit()
            self.update_output_widget.setMaximumHeight(200)
            self.update_output_widget.setReadOnly(True)

            # Custom layout for progress dialog
            layout = QVBoxLayout()
            layout.addWidget(self.update_output_widget)
            layout.setContentsMargins(10, 10, 10, 10)

            # Create a container widget for the layout
            container = QWidget()
            container.setLayout(layout)

            # Add container to the message box layout
            main_layout = self.progress_dialog.layout()
            if main_layout:
                main_layout.addWidget(container, 1, 0)  # Add to second row, first column

            self.progress_dialog.show()

            # Connect to parent's update signals if they exist
            if hasattr(self.parent, 'update_update_output'):
                self.parent.update_update_output = self.update_update_output

            # Call parent's update method
            self.parent.update_database()

        except Exception as e:
            error_msg = f"❌ Update Failed\n\nError starting database update: {str(e)}\n\nPlease check the logs for more details."
            QMessageBox.critical(self, self.tr("Update Error"), error_msg)
            logger.error(f"Error in StatusTab.update_database: {e}")

    def update_update_output(self, text):
        """Update the progress dialog with new text."""
        if hasattr(self, 'update_output_widget') and self.update_output_widget:
            self.update_output_widget.append(text)
            # Scroll to bottom
            scrollbar = self.update_output_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # Update progress dialog text
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                # Extract status from text for better user feedback
                if "completed" in text.lower() or "success" in text.lower():
                    self.progress_dialog.setText(self.tr("Update completed successfully!"))
                elif "failed" in text.lower() or "error" in text.lower():
                    self.progress_dialog.setText(self.tr("Update failed. Check output below."))
                else:
                    self.progress_dialog.setText(self.tr("Updating database..."))

            # Process events to keep UI responsive
            QtWidgets.QApplication.processEvents()

    def closeEvent(self, event):
        """Handle close event to clean up resources."""
        # Clean up any running update threads
        if hasattr(self.parent, 'update_thread') and self.parent.update_thread:
            if self.parent.update_thread.isRunning():
                self.parent.update_thread.terminate()
                self.parent.update_thread.wait(3000)  # Wait up to 3 seconds

        event.accept()
