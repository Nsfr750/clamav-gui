"""
ClamAV installation detection and validation utilities.
"""
import os
import subprocess
import shutil
import platform
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ClamAVValidator:
    """Utility class for validating ClamAV installation and providing installation guidance."""

    def __init__(self):
        self.system = platform.system().lower()

    def get_default_paths(self) -> Dict[str, str]:
        """Get default ClamAV executable paths for the current platform."""
        if self.system == "windows":
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')

            return {
                'clamscan': os.path.join(program_files, 'ClamAV', 'clamscan.exe'),
                'clamd': os.path.join(program_files, 'ClamAV', 'clamd.exe'),
                'freshclam': os.path.join(program_files, 'ClamAV', 'freshclam.exe'),
                'clamscan_alt': os.path.join(program_files_x86, 'ClamAV', 'clamscan.exe'),
                'clamd_alt': os.path.join(program_files_x86, 'ClamAV', 'clamd.exe'),
                'freshclam_alt': os.path.join(program_files_x86, 'ClamAV', 'freshclam.exe')
            }
        else:  # Linux/macOS
            return {
                'clamscan': '/usr/bin/clamscan',
                'clamd': '/usr/sbin/clamd',
                'freshclam': '/usr/bin/freshclam',
                'clamscan_alt': '/usr/local/bin/clamscan',
                'clamd_alt': '/usr/local/sbin/clamd',
                'freshclam_alt': '/usr/local/bin/freshclam'
            }

    def find_clamscan(self) -> Optional[str]:
        """Find the clamscan executable in common locations."""
        paths = self.get_default_paths()

        # Check primary paths first
        for key in ['clamscan', 'clamscan_alt']:
            path = paths.get(key)
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                return path

        # Check if it's in PATH
        try:
            result = shutil.which('clamscan')
            if result:
                return result
        except Exception:
            pass

        return None

    def find_freshclam(self) -> Optional[str]:
        """Find the freshclam executable in common locations."""
        paths = self.get_default_paths()

        # Check primary paths first
        for key in ['freshclam', 'freshclam_alt']:
            path = paths.get(key)
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                return path

        # Check if it's in PATH
        try:
            result = shutil.which('freshclam')
            if result:
                return result
        except Exception:
            pass

        return None

    def check_clamav_installation(self) -> Tuple[bool, str, str]:
        """Check if ClamAV is properly installed and return status information."""
        clamscan_path = self.find_clamscan()

        if not clamscan_path:
            return False, "ClamAV not found", self.get_installation_guidance()

        # Try to run clamscan --version to verify it's working
        try:
            result = subprocess.run([clamscan_path, '--version'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                version_info = result.stdout.strip()
                return True, f"ClamAV found at {clamscan_path}", version_info
            else:
                return False, f"ClamAV found but not working properly: {result.stderr.strip()}", self.get_installation_guidance()

        except subprocess.TimeoutExpired:
            return False, "ClamAV command timed out", self.get_installation_guidance()
        except FileNotFoundError:
            return False, "ClamAV executable not found", self.get_installation_guidance()
        except Exception as e:
            return False, f"Error testing ClamAV: {str(e)}", self.get_installation_guidance()

    def get_installation_guidance(self) -> str:
        """Get installation guidance for the current platform."""
        if self.system == "windows":
            return (
                "To install ClamAV on Windows:\n\n"
                "1. Visit the official ClamAV website: https://www.clamav.net/downloads\n"
                "2. Download the latest Windows installer\n"
                "3. Run the installer and follow the setup wizard\n"
                "4. Make sure to add ClamAV to your system PATH during installation\n\n"
                "Alternatively, you can install via Chocolatey:\n"
                "choco install clamav"
            )
        else:  # Linux/macOS
            return (
                "To install ClamAV on Linux:\n\n"
                "Ubuntu/Debian:\n"
                "sudo apt update && sudo apt install clamav clamav-daemon\n\n"
                "CentOS/RHEL/Fedora:\n"
                "sudo yum install clamav clamav-update  # RHEL/CentOS\n"
                "sudo dnf install clamav clamav-update  # Fedora\n\n"
                "macOS (via Homebrew):\n"
                "brew install clamav\n\n"
                "Make sure ClamAV is in your PATH after installation."
            )

    def validate_database_directory(self, db_path: str) -> Tuple[bool, str]:
        """Validate that the ClamAV database directory is accessible."""
        if not db_path:
            return False, "Database path not specified"

        if not os.path.exists(db_path):
            try:
                os.makedirs(db_path, exist_ok=True)
                return True, f"Created database directory: {db_path}"
            except Exception as e:
                return False, f"Cannot create database directory: {str(e)}"

        if not os.access(db_path, os.R_OK | os.W_OK):
            return False, f"Database directory is not accessible: {db_path}"

        return True, f"Database directory is valid: {db_path}"
