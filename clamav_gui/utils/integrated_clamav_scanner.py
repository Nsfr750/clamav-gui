"""
Integrated ClamAV Scanner for ClamAV GUI.

This module provides a direct integration with ClamAV using Python bindings,
with fallback to subprocess calls when direct integration is not available.
"""
import os
import sys
import logging
import subprocess
import threading
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ScanResult(Enum):
    """Scan result enumeration."""
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    UNSUPPORTED = "unsupported"


@dataclass
class ScanFileResult:
    """Result of scanning a single file."""
    file_path: str
    result: ScanResult
    threat_name: Optional[str] = None
    error_message: Optional[str] = None
    scan_time: float = 0.0


class IntegratedClamAVScanner:
    """
    Integrated ClamAV scanner that uses direct library integration when possible.

    This scanner provides better performance and tighter integration compared to
    subprocess calls, while maintaining compatibility with existing installations.
    """

    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize the integrated ClamAV scanner.

        Args:
            database_path: Path to ClamAV database directory (optional)
        """
        self.database_path = database_path or self._get_default_database_path()
        self._clamav_handle = None
        self._engine_loaded = False
        self._use_direct_integration = False

        # Try to initialize direct integration
        self._init_direct_integration()

    def _get_default_database_path(self) -> str:
        """Get the default ClamAV database path."""
        if sys.platform == "win32":
            # Windows: Use AppData directory
            appdata = os.getenv('APPDATA', os.path.expanduser('~'))
            return os.path.join(appdata, 'ClamAV', 'database')
        else:
            # Unix-like systems
            return '/var/lib/clamav'

    def _init_direct_integration(self) -> bool:
        """Initialize direct ClamAV integration using pyclamav."""
        try:
            # Try to import pyclamav (direct C bindings)
            try:
                import clamav
                logger.info("Using pyclamav for direct ClamAV integration")
                self._clamav_handle = clamav
                self._use_direct_integration = True
                return True

            except ImportError:
                # Try alternative bindings
                try:
                    from clamav import libclamav
                    logger.info("Using libclamav for direct ClamAV integration")
                    self._clamav_handle = libclamav
                    self._use_direct_integration = True
                    return True

                except ImportError:
                    logger.info("Direct ClamAV integration not available, using subprocess fallback")
                    return False

        except Exception as e:
            logger.warning(f"Failed to initialize direct ClamAV integration: {e}")
            return False

    def is_direct_integration_available(self) -> bool:
        """Check if direct integration is available."""
        return self._use_direct_integration and self._clamav_handle is not None

    def scan_file(self, file_path: str) -> ScanFileResult:
        """
        Scan a single file for threats.

        Args:
            file_path: Path to the file to scan

        Returns:
            ScanFileResult with scan results
        """
        if not os.path.exists(file_path):
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message="File does not exist"
            )

        if not os.path.isfile(file_path):
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.UNSUPPORTED,
                error_message="Path is not a file"
            )

        # Use direct integration if available
        if self._use_direct_integration:
            return self._scan_file_direct(file_path)

        # Fallback to subprocess approach
        return self._scan_file_subprocess(file_path)

    def _scan_file_direct(self, file_path: str) -> ScanFileResult:
        """Scan file using direct ClamAV integration."""
        import time
        start_time = time.time()

        try:
            # Use pyclamav to scan the file
            if hasattr(self._clamav_handle, 'scan_file'):
                # Newer pyclamav API
                result = self._clamav_handle.scan_file(file_path)
                scan_time = time.time() - start_time

                if result is None or result == 0:
                    return ScanFileResult(
                        file_path=file_path,
                        result=ScanResult.CLEAN,
                        scan_time=scan_time
                    )
                else:
                    # Extract threat information
                    threat_name = self._get_threat_name(result)
                    return ScanFileResult(
                        file_path=file_path,
                        result=ScanResult.INFECTED,
                        threat_name=threat_name,
                        scan_time=scan_time
                    )

            elif hasattr(self._clamav_handle, 'cl_scanfile'):
                # Direct libclamav API
                result = self._clamav_handle.cl_scanfile(
                    file_path.encode('utf-8'),
                    self.database_path.encode('utf-8') if self.database_path else None
                )
                scan_time = time.time() - start_time

                if result is None or result[0] == 0:
                    return ScanFileResult(
                        file_path=file_path,
                        result=ScanResult.CLEAN,
                        scan_time=scan_time
                    )
                else:
                    threat_name = result[1].decode('utf-8') if result[1] else "Unknown threat"
                    return ScanFileResult(
                        file_path=file_path,
                        result=ScanResult.INFECTED,
                        threat_name=threat_name,
                        scan_time=scan_time
                    )

        except Exception as e:
            logger.error(f"Direct scan failed for {file_path}: {e}")
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message=str(e),
                scan_time=time.time() - start_time
            )

        # If we get here, direct integration is not properly implemented
        logger.warning("Direct integration detected but not properly implemented")
        return self._scan_file_subprocess(file_path)

    def _scan_file_subprocess(self, file_path: str) -> ScanFileResult:
        """Scan file using subprocess fallback."""
        import time
        start_time = time.time()

        try:
            # Use clamscan via subprocess
            cmd = ['clamscan', '--no-summary', '--stdout', file_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.path.dirname(file_path)
            )

            scan_time = time.time() - start_time

            if result.returncode == 0:
                # No threats found
                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.CLEAN,
                    scan_time=scan_time
                )
            elif result.returncode == 1:
                # Threats found
                threat_name = self._extract_threat_from_output(result.stdout)
                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.INFECTED,
                    threat_name=threat_name or "Threat detected",
                    scan_time=scan_time
                )
            else:
                # Error occurred
                return ScanFileResult(
                    file_path=file_path,
                    result=ScanResult.ERROR,
                    error_message=result.stderr or f"Exit code: {result.returncode}",
                    scan_time=scan_time
                )

        except subprocess.TimeoutExpired:
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message="Scan timeout",
                scan_time=time.time() - start_time
            )
        except Exception as e:
            return ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message=str(e),
                scan_time=time.time() - start_time
            )

    def _get_threat_name(self, result: Any) -> Optional[str]:
        """Extract threat name from scan result."""
        try:
            if isinstance(result, str):
                return result
            elif isinstance(result, (list, tuple)) and len(result) > 1:
                return str(result[1])
            elif hasattr(result, 'decode'):
                return result.decode('utf-8')
            else:
                return "Unknown threat"
        except:
            return "Unknown threat"

    def _extract_threat_from_output(self, output: str) -> Optional[str]:
        """Extract threat name from clamscan output."""
        lines = output.strip().split('\n')
        for line in lines:
            if 'FOUND' in line:
                # Extract threat name after "FOUND"
                parts = line.split('FOUND')
                if len(parts) > 1:
                    threat_part = parts[1].strip()
                    if ':' in threat_part:
                        return threat_part.split(':', 1)[0].strip()
                    else:
                        return threat_part
        return None

    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[ScanFileResult]:
        """
        Scan all files in a directory.

        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of ScanFileResult objects
        """
        if not os.path.exists(directory_path):
            return [ScanFileResult(
                file_path=directory_path,
                result=ScanResult.ERROR,
                error_message="Directory does not exist"
            )]

        if not os.path.isdir(directory_path):
            return [ScanFileResult(
                file_path=directory_path,
                result=ScanResult.UNSUPPORTED,
                error_message="Path is not a directory"
            )]

        results = []
        pattern = "**/*" if recursive else "*"

        try:
            for file_path in Path(directory_path).glob(pattern):
                if file_path.is_file():
                    result = self.scan_file(str(file_path))
                    results.append(result)

                    # Yield control periodically for UI responsiveness
                    if len(results) % 10 == 0:
                        import time
                        time.sleep(0.001)

        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {e}")
            results.append(ScanFileResult(
                file_path=directory_path,
                result=ScanResult.ERROR,
                error_message=str(e)
            ))

        return results

    def update_database(self, freshclam_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Update ClamAV virus database.

        Args:
            freshclam_path: Path to freshclam executable (optional)

        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = [freshclam_path or 'freshclam', '--quiet', '--no-warnings']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for updates
            )

            if result.returncode == 0:
                return True, "Database updated successfully"
            else:
                return False, result.stderr or f"Update failed with exit code {result.returncode}"

        except subprocess.TimeoutExpired:
            return False, "Database update timed out"
        except FileNotFoundError:
            return False, "freshclam not found - please install ClamAV"
        except Exception as e:
            return False, f"Database update failed: {str(e)}"

    def get_version(self) -> Optional[str]:
        """Get ClamAV version information."""
        if self._use_direct_integration and hasattr(self._clamav_handle, 'cl_init'):
            try:
                # Try to get version from direct integration
                if hasattr(self._clamav_handle, 'cl_retver'):
                    return self._clamav_handle.cl_retver()
            except:
                pass

        # Fallback to subprocess
        try:
            result = subprocess.run(['clamscan', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the virus database."""
        info = {
            'database_path': self.database_path,
            'exists': os.path.exists(self.database_path),
            'size': 0,
            'file_count': 0,
            'last_update': None
        }

        if info['exists']:
            try:
                total_size = 0
                file_count = 0

                for root, dirs, files in os.walk(self.database_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1

                        # Check for timestamp files
                        if file.endswith('.cld') or file.endswith('.cvd'):
                            stat = os.stat(file_path)
                            if info['last_update'] is None or stat.st_mtime > info['last_update']:
                                info['last_update'] = stat.st_mtime

                info['size'] = total_size
                info['file_count'] = file_count

            except Exception as e:
                logger.warning(f"Error getting database info: {e}")

        return info
