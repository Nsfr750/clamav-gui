"""
Virus database update functionality for ClamAV GUI.
"""
import os
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QProcess

logger = logging.getLogger(__name__)

class UpdateSignals(QObject):
    """Signals for database update operations."""
    output = Signal(str)
    finished = Signal(int, int)  # exit_code, status
    
    def disconnect_all(self):
        """Safely disconnect all slots from all signals."""
        # Disconnect all slots from the output signal
        try:
            if hasattr(self.output, 'receivers') and self.output.receivers() > 0:
                self.output.disconnect()
        except (RuntimeError, TypeError, AttributeError):
            # Signal was not connected or already disconnected
            pass
            
        # Disconnect all slots from the finished signal
        try:
            if hasattr(self.finished, 'receivers') and self.finished.receivers() > 0:
                self.finished.disconnect()
        except (RuntimeError, TypeError, AttributeError):
            # Signal was not connected or already disconnected
            pass

class VirusDBUpdater:
    """Handles virus database update operations."""
    
    def __init__(self):
        """Initialize the virus database updater."""
        self.signals = UpdateSignals()
        self.process = None
        self._is_running = False
    
    def get_clamav_user_dir(self):
        """
        Get the path to the ClamAV user directory.
        Creates the directory if it doesn't exist.

        Returns:
            str: Path to the ClamAV user directory
        """
        app_data = os.getenv('APPDATA')
        clamav_dir = os.path.join(app_data, 'ClamAV')
        os.makedirs(clamav_dir, exist_ok=True)
        return clamav_dir
        
    def get_database_dir(self):
        """
        Get the path to the virus database directory.

        Returns:
            str: Path to the database directory
        """
        db_dir = os.path.join(self.get_clamav_user_dir(), 'database')
        os.makedirs(db_dir, exist_ok=True)
        return db_dir
    
    def ensure_database_dir(self):
        """
        Ensure the database directory exists.
        
        Returns:
            tuple: (success, error_message) - success is True if directory exists or was created
        """
        try:
            db_dir = self.get_database_dir()
            os.makedirs(db_dir, exist_ok=True)
            return True, None
        except Exception as e:
            error_msg = f"Failed to create database directory: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def start_update(self, freshclam_path=None):
        """
        Start the virus database update process.

        Args:
            freshclam_path: Optional path to freshclam executable. If None, uses system path.

        Returns:
            bool: True if the update process was started successfully, False otherwise
        """
        success, error = self.ensure_database_dir()
        if not success:
            self.signals.output.emit(f"Error: {error}")
            self.signals.finished.emit(1, 1)
            return False

        db_dir = self.get_database_dir()
        log_dir = self.get_clamav_user_dir()
        log_file = os.path.join(log_dir, 'freshclam.log')
        
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
            
        cmd = [
            freshclam_path if freshclam_path else "freshclam",
            "--verbose",
            f"--datadir={db_dir}",
            f"--log={log_file}",
            "--stdout"  # Ensure we still get output in our UI
        ]
        
        try:
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self._handle_stdout)
            self.process.readyReadStandardError.connect(self._handle_stderr)
            self.process.finished.connect(self._on_finished)
            
            self._is_running = True
            self.signals.output.emit("Updating virus definitions... This may take a few minutes.")
            self.process.start(cmd[0], cmd[1:])
            return True
            
        except Exception as e:
            error_msg = f"Failed to start update process: {e}"
            logger.error(error_msg)
            self.signals.output.emit(f"Error: {error_msg}")
            self.signals.finished.emit(1, 1)
            return False
    
    def stop_update(self):
        """Stop the running update process if any."""
        if self.process and self._is_running:
            self.process.terminate()
            self.process.waitForFinished()
    
    def _handle_stdout(self):
        """Handle standard output from the update process."""
        if self.process:
            output = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            if output:
                self.signals.output.emit(output.strip())
    
    def _handle_stderr(self):
        """Handle error output from the update process."""
        if self.process:
            error = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
            if error:
                self.signals.output.emit(f"Error: {error.strip()}")
    
    def _on_finished(self, exit_code, exit_status):
        """Handle process completion."""
        self._is_running = False
        self.signals.finished.emit(exit_code, exit_status)
        
        if exit_code == 0:
            self.signals.output.emit("Virus database update completed successfully.")
        else:
            self.signals.output.emit("Virus database update failed.")

    def get_database_info(self):
        """
        Get information about the ClamAV virus database.

        Returns:
            dict: Dictionary containing database information including:
                - version: Database version
                - signatures: Number of virus signatures (or signature_count)
                - build_time: When the database was built
                - error: Error message if operation failed
        """
        try:
            # First try to get database directory
            db_dir = self.get_database_dir()
            if not db_dir or not os.path.exists(db_dir):
                return {
                    'error': 'Database directory not found or not accessible',
                    'version': 'Unknown',
                    'signatures': 'Unknown',
                    'build_time': 'Unknown'
                }

            # Check for database files
            db_files = [f for f in os.listdir(db_dir) if f.endswith('.cvd') or f.endswith('.cld')]
            if not db_files:
                return {
                    'error': 'No database files found in database directory',
                    'version': 'No files',
                    'signatures': '0',
                    'build_time': 'Unknown'
                }

            # Try to find sigtool and get detailed info
            try:
                result = subprocess.run(['sigtool', '--info'],
                                      capture_output=True, text=True, timeout=10, cwd=db_dir)
            except FileNotFoundError:
                # If sigtool not in PATH, try to find it in common locations
                sigtool_path = self._find_sigtool_executable()
                if sigtool_path:
                    result = subprocess.run([sigtool_path, '--info'],
                                          capture_output=True, text=True, timeout=10, cwd=db_dir)
                else:
                    # Fallback: try to get info from database files directly
                    return self._get_database_info_from_files(db_dir, db_files)

            if result.returncode == 0:
                output = result.stdout

                # Parse the sigtool output - improved parsing
                info = {}
                for line in output.split('\n'):
                    line = line.strip()
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        # Clean up key for consistent naming
                        clean_key = key.lower().replace(' ', '_').replace('(', '').replace(')', '')
                        info[clean_key] = value.strip()

                # Extract and format the information
                result_info = {
                    'error': None,
                    'version': 'Unknown',
                    'signatures': 'Unknown',
                    'build_time': 'Unknown'
                }

                # Get version
                if 'version' in info:
                    result_info['version'] = info['version']
                elif 'clamav-vdb' in info:
                    result_info['version'] = info['clamav-vdb']

                # Get signature count
                if 'signatures' in info:
                    result_info['signatures'] = info['signatures']
                elif 'total_signatures' in info:
                    result_info['signatures'] = info['total_signatures']

                # Get build time
                if 'build_time' in info:
                    result_info['build_time'] = info['build_time']
                elif 'built' in info:
                    result_info['build_time'] = info['built']

                # If we have at least some info, return it
                if result_info['version'] != 'Unknown' or result_info['signatures'] != 'Unknown':
                    return result_info

            # Fallback: try to get info from database files directly
            return self._get_database_info_from_files(db_dir, db_files)

        except subprocess.TimeoutExpired:
            return {
                'error': 'sigtool timed out',
                'version': 'Timeout',
                'signatures': 'Unknown',
                'build_time': 'Unknown'
            }
        except Exception as e:
            return {
                'error': f'Error getting database info: {str(e)}',
                'version': 'Error',
                'signatures': 'Unknown',
                'build_time': 'Unknown'
            }

    def _find_sigtool_executable(self):
        """Find sigtool executable in common locations."""
        common_paths = [
            r'C:\Program Files\ClamAV\sigtool.exe',
            r'C:\Program Files (x86)\ClamAV\sigtool.exe',
            r'C:\ClamAV\sigtool.exe',
            '/usr/bin/sigtool',
            '/usr/local/bin/sigtool',
            '/opt/clamav/bin/sigtool'
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        # Check if sigtool is in PATH
        try:
            subprocess.run(['sigtool', '--version'],
                         capture_output=True, timeout=5)
            return 'sigtool'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def _get_database_info_from_files(self, db_dir, db_files):
        """Get database information by examining the database files directly."""
        try:
            info = {
                'error': None,
                'version': 'Unknown',
                'signatures': 'Unknown',
                'build_time': 'Unknown'
            }

            # Get the most recent database file
            latest_file = None
            latest_time = 0

            for db_file in db_files:
                db_path = os.path.join(db_dir, db_file)
                try:
                    mod_time = os.path.getmtime(db_path)
                    if mod_time > latest_time:
                        latest_time = mod_time
                        latest_file = db_path
                except (OSError, IOError):
                    continue

            if latest_file:
                # Set build time from file modification time
                build_time = datetime.fromtimestamp(latest_time)
                info['build_time'] = build_time.strftime('%Y-%m-%d %H:%M:%S')

                # Try to extract version from CVD file header
                if latest_file.endswith('.cvd'):
                    try:
                        with open(latest_file, 'rb') as f:
                            # Read CVD header (first 512 bytes typically contain metadata)
                            header = f.read(512)
                            header_str = header.decode('latin-1', errors='ignore')

                            # Look for version information in header
                            if 'ClamAV-VDB:' in header_str:
                                version_start = header_str.find('ClamAV-VDB:') + 11
                                version_end = header_str.find('\0', version_start)
                                if version_end > version_start:
                                    version = header_str[version_start:version_end].strip()
                                    info['version'] = version

                    except (IOError, OSError):
                        pass

                # Estimate signature count based on file count and typical sizes
                total_files = len(db_files)
                if total_files > 0:
                    # Rough estimate: each CVD file typically contains ~1M signatures
                    estimated_signatures = total_files * 1000000
                    info['signatures'] = str(estimated_signatures)

                # If no version found, use filename
                if info['version'] == 'Unknown':
                    filename = os.path.basename(latest_file)
                    if '.cvd' in filename:
                        info['version'] = filename.replace('.cvd', '')

            return info

        except Exception as e:
            return {
                'error': f'Error reading database files: {str(e)}',
                'version': 'Error',
                'signatures': 'Unknown',
                'build_time': 'Unknown'
            }
