"""
Thread for scanning files asynchronously in ClamAV GUI.
"""
import os
import logging
import subprocess
from typing import List, Optional
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class ScanThread(QThread):
    """Thread for scanning files asynchronously."""
    update_output = Signal(str)
    update_progress = Signal(int)
    update_stats = Signal(str, int, int)
    finished = Signal(int, str)
    cancelled = Signal()

    def __init__(self, cmd: List[str], enable_smart_scanning: bool = False):
        super().__init__()
        self.cmd = cmd
        self.enable_smart_scanning = enable_smart_scanning
        self.process = None
        self._is_cancelled = False

    def run(self):
        """Run the scan process."""
        try:
            # Start the clamscan process
            logger.info(f"Starting scan with command: {' '.join(self.cmd)}")

            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            files_scanned = 0
            threats_found = 0
            current_file = ""

            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if self._is_cancelled:
                    self.process.terminate()
                    self.process.wait()
                    self.cancelled.emit()
                    return

                line = line.strip()
                if not line:
                    continue

                # Update output display
                self.update_output.emit(line)

                # Try to extract progress information
                if 'Scanned file:' in line:
                    current_file = line.split('Scanned file:')[1].strip()
                    files_scanned += 1
                    # Estimate progress (this is approximate)
                    progress = min(99, files_scanned * 2)  # Assume ~50 files for 100%
                    self.update_progress.emit(progress)

                elif 'FOUND' in line:
                    threats_found += 1
                    self.update_stats.emit("Scanning", files_scanned, threats_found)

            # Wait for process to complete
            self.process.wait()
            exit_code = self.process.returncode

            # Final progress update
            self.update_progress.emit(100)

            # Determine result message based on exit code
            if exit_code == 0:
                result_msg = "Scan completed successfully - No threats found"
            elif exit_code == 1:
                result_msg = f"Scan completed - {threats_found} threats found"
            else:
                result_msg = f"Scan failed with exit code {exit_code}"

            self.finished.emit(exit_code, result_msg)

        except Exception as e:
            logger.error(f"Error in scan thread: {e}")
            self.finished.emit(-1, f"Error during scan: {str(e)}")

    def cancel(self):
        """Cancel the scan process."""
        self._is_cancelled = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
