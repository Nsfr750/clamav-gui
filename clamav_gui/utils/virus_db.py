"""
Virus database update functionality for ClamAV GUI.
"""
import os
import logging
from pathlib import Path
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
            self.output.disconnect()
        except (RuntimeError, TypeError):
            # Signal was not connected or already disconnected
            pass
            
        # Disconnect all slots from the finished signal
        try:
            self.finished.disconnect()
        except (RuntimeError, TypeError):
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
