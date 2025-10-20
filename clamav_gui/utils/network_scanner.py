"""
Network drive scanning functionality for ClamAV GUI.
Supports UNC paths and network-attached storage scanning.
"""
import os
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class NetworkScanner:
    """Scans network drives and UNC paths for malware."""

    def __init__(self, clamscan_path: str = "clamscan"):
        """Initialize the network scanner.

        Args:
            clamscan_path: Path to clamscan executable
        """
        self.clamscan_path = clamscan_path

    def validate_network_path(self, path: str) -> Tuple[bool, str]:
        """Validate if a network path is accessible.

        Args:
            path: Network path to validate (UNC format like \\\\server\\share)

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        if not path:
            return False, "Empty path provided"

        # Check UNC path format
        if not path.startswith('\\\\'):
            return False, f"Invalid UNC path format. Expected: \\\\server\\share, got: {path}"

        # Basic path validation
        if len(path) < 5:  # Minimum \\\\x\\y format
            return False, "UNC path too short"

        try:
            # Check if path exists and is accessible
            if not os.path.exists(path):
                return False, f"Network path not accessible: {path}"

            # Check if it's a directory
            if not os.path.isdir(path):
                return False, f"Path is not a directory: {path}"

            # Try to list directory contents (basic access test)
            try:
                os.listdir(path)
                return True, f"Network path accessible: {path}"
            except PermissionError:
                return False, f"Permission denied accessing: {path}"
            except Exception as e:
                return False, f"Error accessing network path: {str(e)}"

        except Exception as e:
            return False, f"Error validating network path: {str(e)}"

    def scan_network_drive(self, network_path: str, options: Dict = None) -> Tuple[bool, str, List[str]]:
        """Scan a network drive or UNC path.

        Args:
            network_path: UNC path to scan (e.g., \\\\server\\share)
            options: Scan options dictionary

        Returns:
            Tuple of (success: bool, result: str, threats: List[str])
        """
        # Validate the path first
        is_valid, message = self.validate_network_path(network_path)
        if not is_valid:
            return False, message, []

        options = options or {}
        threats = []

        try:
            # Build clamscan command
            cmd = [self.clamscan_path]

            # Add database directory (use local database)
            app_data = os.getenv('APPDATA') if platform.system() == 'Windows' else os.path.expanduser('~')
            clamav_dir = os.path.join(app_data, 'ClamAV')
            db_dir = os.path.join(clamav_dir, 'database')

            if os.path.exists(db_dir):
                cmd.extend(['--database', db_dir])

            # Add scan options
            if options.get('recursive', True):
                cmd.append("-r")

            if options.get('scan_archives', True):
                cmd.append("-a")

            if options.get('heuristic_scan', True):
                cmd.append("--heuristic-alerts")

            if options.get('scan_pua', False):
                cmd.append("--detect-pua")

            # Add performance settings
            max_file_size = options.get('max_file_size', 100)
            if max_file_size > 0:
                cmd.extend(['--max-filesize', f'{max_file_size}M'])

            max_scan_time = options.get('max_scan_time', 300)
            if max_scan_time > 0:
                cmd.extend(['--max-scantime', str(max_scan_time)])

            # Add exclude patterns
            exclude_patterns = options.get('exclude_patterns', '')
            if exclude_patterns:
                for pattern in exclude_patterns.split(','):
                    pattern = pattern.strip()
                    if pattern:
                        cmd.extend(['--exclude', pattern])

            # Add target path and output options
            cmd.extend([network_path, "--verbose", "--stdout"])

            # Run the scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout for network scans
                check=False
            )

            # Parse output for threats
            output = result.stdout + result.stderr

            for line in output.split('\n'):
                if 'FOUND' in line or 'infected' in line.lower():
                    threats.append(line.strip())

            # Determine success
            success = result.returncode in (0, 1)  # 0 = clean, 1 = infected (not error)
            result_message = "Clean" if success and not threats else f"Threats found: {len(threats)}"

            return success, result_message, threats

        except subprocess.TimeoutExpired:
            return False, "Network scan timeout", ["Scan timeout"]
        except Exception as e:
            return False, f"Network scan error: {str(e)}", [str(e)]

    def get_network_drives(self) -> List[Dict]:
        """Get list of available network drives (Windows only).

        Returns:
            List of dictionaries with network drive information
        """
        drives = []

        if platform.system() != 'Windows':
            return drives

        try:
            # Use net use command to get mapped drives
            result = subprocess.run(['net', 'use'], capture_output=True, text=True)

            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('Status') and 'OK' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        drive_letter = parts[1].rstrip(':')
                        network_path = parts[2] if len(parts) > 2 else 'Unknown'

                        drives.append({
                            'drive_letter': drive_letter,
                            'network_path': network_path,
                            'status': parts[0] if len(parts) > 0 else 'Unknown',
                            'type': 'mapped_drive'
                        })

        except Exception as e:
            logger.error(f"Error getting network drives: {e}")

        return drives

    def map_network_drive(self, network_path: str, drive_letter: str = None) -> Tuple[bool, str]:
        """Map a network drive (Windows only).

        Args:
            network_path: UNC path to map (e.g., \\\\server\\share)
            drive_letter: Drive letter to use (optional, will auto-assign if None)

        Returns:
            Tuple of (success: bool, message: str)
        """
        if platform.system() != 'Windows':
            return False, "Network drive mapping only supported on Windows"

        try:
            if not drive_letter:
                # Auto-assign a drive letter (Z, Y, X, etc.)
                for letter in 'ZYXWVUTSRQPONMLKJIHGFEDCBA':
                    if not os.path.exists(f'{letter}:'):
                        drive_letter = letter
                        break

                if not drive_letter:
                    return False, "No available drive letters"

            # Map the drive
            cmd = ['net', 'use', f'{drive_letter}:', network_path]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True, f"Successfully mapped {network_path} to {drive_letter}:"
            else:
                return False, f"Failed to map drive: {result.stderr.strip()}"

        except Exception as e:
            return False, f"Error mapping network drive: {str(e)}"

    def unmap_network_drive(self, drive_letter: str) -> Tuple[bool, str]:
        """Unmap a network drive (Windows only).

        Args:
            drive_letter: Drive letter to unmap (e.g., 'Z')

        Returns:
            Tuple of (success: bool, message: str)
        """
        if platform.system() != 'Windows':
            return False, "Network drive unmapping only supported on Windows"

        try:
            cmd = ['net', 'use', f'{drive_letter}:', '/delete']

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True, f"Successfully unmapped drive {drive_letter}:"
            else:
                return False, f"Failed to unmap drive: {result.stderr.strip()}"

        except Exception as e:
            return False, f"Error unmapping network drive: {str(e)}"


class NetworkScanThread(QThread):
    """Thread for scanning network drives asynchronously."""
    update_progress = Signal(int)
    update_output = Signal(str)
    finished = Signal(bool, str, list)

    def __init__(self, scanner: NetworkScanner, network_path: str, options: Dict = None):
        super().__init__()
        self.scanner = scanner
        self.network_path = network_path
        self.options = options or {}

    def run(self):
        """Run the network scanning process."""
        try:
            self.update_output.emit(f"Starting network scan of: {self.network_path}")

            success, result, threats = self.scanner.scan_network_drive(
                self.network_path,
                self.options
            )

            if success:
                self.update_output.emit(f"Network scan completed: {result}")
            else:
                self.update_output.emit(f"Network scan failed: {result}")

            self.finished.emit(success, result, threats)

        except Exception as e:
            self.update_output.emit(f"Network scan error: {str(e)}")
            self.finished.emit(False, str(e), [])
