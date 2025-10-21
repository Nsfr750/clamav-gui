"""
ClamAV Integration Utility for ClamAV GUI.

This module provides a high-level interface for integrating ClamAV functionality
directly into the application, with automatic fallback to subprocess methods.
"""
import os
import logging
import threading
from typing import List, Dict, Optional, Tuple, Any, Callable
from PySide6.QtCore import QObject, Signal

from clamav_gui.utils.integrated_clamav_scanner import IntegratedClamAVScanner, ScanFileResult, ScanResult

logger = logging.getLogger(__name__)


class ClamAVIntegration(QObject):
    """
    High-level ClamAV integration utility for the GUI application.

    This class provides a Qt-friendly interface for ClamAV scanning with
    progress updates and error handling.
    """

    # Signals for GUI updates
    scan_progress = Signal(int)  # Progress percentage (0-100)
    scan_output = Signal(str)   # Scan output text
    scan_stats = Signal(str, int, int)  # Status, files_scanned, threats_found
    scan_finished = Signal(bool, str)  # Success, message
    file_scanned = Signal(str, object)  # File path, ScanFileResult

    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize ClamAV integration.

        Args:
            database_path: Path to ClamAV database directory (optional)
        """
        super().__init__()
        self.scanner = IntegratedClamAVScanner(database_path)
        self._scan_thread = None
        self._is_scanning = False

        logger.info(f"ClamAV integration initialized - Direct integration: {self.scanner.is_direct_integration_available()}")

    def is_available(self) -> bool:
        """Check if ClamAV is available for scanning."""
        return self.scanner.get_version() is not None

    def is_direct_integration(self) -> bool:
        """Check if direct integration is available."""
        return self.scanner.is_direct_integration_available()

    def get_version(self) -> Optional[str]:
        """Get ClamAV version."""
        return self.scanner.get_version()

    def get_database_info(self) -> Dict[str, Any]:
        """Get virus database information."""
        return self.scanner.get_database_info()

    def scan_file(self, file_path: str) -> ScanFileResult:
        """
        Scan a single file synchronously.

        Args:
            file_path: Path to file to scan

        Returns:
            ScanFileResult with scan results
        """
        try:
            result = self.scanner.scan_file(file_path)

            # Emit signals for GUI updates
            self.scan_output.emit(f"Scanning: {os.path.basename(file_path)}")
            self.file_scanned.emit(file_path, result)

            if result.result == ScanResult.INFECTED:
                self.scan_output.emit(f"⚠️  THREAT FOUND: {result.threat_name}")
            elif result.result == ScanResult.ERROR:
                self.scan_output.emit(f"❌ ERROR: {result.error_message}")

            return result

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            error_result = ScanFileResult(
                file_path=file_path,
                result=ScanResult.ERROR,
                error_message=str(e)
            )
            self.file_scanned.emit(file_path, error_result)
            return error_result

    def scan_files_async(self, file_paths: List[str], callback: Optional[Callable] = None):
        """
        Scan multiple files asynchronously.

        Args:
            file_paths: List of file paths to scan
            callback: Optional callback function called when scan completes
        """
        if self._is_scanning:
            logger.warning("Scan already in progress")
            return

        self._is_scanning = True
        self._scan_thread = threading.Thread(target=self._scan_files_worker, args=(file_paths, callback))
        self._scan_thread.daemon = True
        self._scan_thread.start()

    def _scan_files_worker(self, file_paths: List[str], callback: Optional[Callable]):
        """Worker thread for scanning multiple files."""
        try:
            total_files = len(file_paths)
            files_scanned = 0
            threats_found = 0

            self.scan_progress.emit(0)
            self.scan_stats.emit("Starting scan...", 0, 0)

            for file_path in file_paths:
                if not self._is_scanning:
                    break

                result = self.scanner.scan_file(file_path)

                files_scanned += 1
                if result.result == ScanResult.INFECTED:
                    threats_found += 1

                # Update progress
                progress = int((files_scanned / total_files) * 100) if total_files > 0 else 0
                self.scan_progress.emit(progress)
                self.scan_stats.emit(f"Scanning... ({files_scanned}/{total_files})", files_scanned, threats_found)

                # Emit file result
                self.file_scanned.emit(file_path, result)

            # Scan completed
            success = files_scanned == total_files
            message = f"Scanned {files_scanned} files, {threats_found} threats found"
            self.scan_finished.emit(success, message)
            self.scan_progress.emit(100)

            if callback:
                callback(success, message, files_scanned, threats_found)

        except Exception as e:
            logger.error(f"Error in scan worker: {e}")
            self.scan_finished.emit(False, f"Scan failed: {str(e)}")
        finally:
            self._is_scanning = False

    def scan_directory_async(self, directory_path: str, recursive: bool = True, callback: Optional[Callable] = None):
        """
        Scan directory asynchronously.

        Args:
            directory_path: Directory to scan
            recursive: Whether to scan subdirectories
            callback: Optional callback function
        """
        if self._is_scanning:
            logger.warning("Scan already in progress")
            return

        self._is_scanning = True
        self._scan_thread = threading.Thread(target=self._scan_directory_worker, args=(directory_path, recursive, callback))
        self._scan_thread.daemon = True
        self._scan_thread.start()

    def _scan_directory_worker(self, directory_path: str, recursive: bool, callback: Optional[Callable]):
        """Worker thread for scanning directory."""
        try:
            # First, collect all files to scan
            all_files = []
            pattern = "**/*" if recursive else "*"

            for file_path in Path(directory_path).glob(pattern):
                if file_path.is_file():
                    all_files.append(str(file_path))

            if not all_files:
                self.scan_finished.emit(True, "No files found to scan")
                self._is_scanning = False
                return

            # Now scan the files
            self._scan_files_worker(all_files, callback)

        except Exception as e:
            logger.error(f"Error in directory scan worker: {e}")
            self.scan_finished.emit(False, f"Directory scan failed: {str(e)}")
            self._is_scanning = False

    def stop_scan(self):
        """Stop the current scan operation."""
        if self._is_scanning and self._scan_thread:
            self._is_scanning = False
            # Note: In a real implementation, you'd need a way to signal the thread to stop
            logger.info("Scan stop requested")

    def update_database_async(self, callback: Optional[Callable] = None):
        """
        Update virus database asynchronously.

        Args:
            callback: Optional callback function called when update completes
        """
        def update_worker():
            try:
                self.scan_output.emit("Starting database update...")
                success, message = self.scanner.update_database()

                if success:
                    self.scan_output.emit("✅ Database updated successfully")
                    self.scan_finished.emit(True, message)
                else:
                    self.scan_output.emit(f"❌ Database update failed: {message}")
                    self.scan_finished.emit(False, message)

                if callback:
                    callback(success, message)

            except Exception as e:
                error_msg = f"Database update error: {str(e)}"
                logger.error(error_msg)
                self.scan_output.emit(f"❌ {error_msg}")
                self.scan_finished.emit(False, error_msg)
                if callback:
                    callback(False, error_msg)

        thread = threading.Thread(target=update_worker)
        thread.daemon = True
        thread.start()

    def get_scan_statistics(self, results: List[ScanFileResult]) -> Dict[str, Any]:
        """Generate statistics from scan results."""
        stats = {
            'total_files': len(results),
            'clean_files': 0,
            'infected_files': 0,
            'error_files': 0,
            'unsupported_files': 0,
            'threats': {},
            'total_scan_time': 0.0
        }

        for result in results:
            stats['total_scan_time'] += result.scan_time

            if result.result == ScanResult.CLEAN:
                stats['clean_files'] += 1
            elif result.result == ScanResult.INFECTED:
                stats['infected_files'] += 1
                threat_name = result.threat_name or "Unknown threat"
                stats['threats'][threat_name] = stats['threats'].get(threat_name, 0) + 1
            elif result.result == ScanResult.ERROR:
                stats['error_files'] += 1
            elif result.result == ScanResult.UNSUPPORTED:
                stats['unsupported_files'] += 1

        return stats

    def export_scan_results(self, results: List[ScanFileResult], format_type: str = 'txt') -> str:
        """
        Export scan results to a formatted string.

        Args:
            results: List of scan results
            format_type: Export format ('txt', 'json', 'csv')

        Returns:
            Formatted export string
        """
        import json
        from datetime import datetime

        if format_type == 'json':
            # Convert results to JSON-serializable format
            json_data = {
                'scan_timestamp': datetime.now().isoformat(),
                'total_files': len(results),
                'results': []
            }

            for result in results:
                json_result = {
                    'file_path': result.file_path,
                    'result': result.result.value,
                    'scan_time': result.scan_time
                }

                if result.threat_name:
                    json_result['threat_name'] = result.threat_name
                if result.error_message:
                    json_result['error_message'] = result.error_message

                json_data['results'].append(json_result)

            return json.dumps(json_data, indent=2)

        elif format_type == 'csv':
            lines = []
            lines.append("File Path,Result,Threat Name,Scan Time,Error Message")
            lines.append("")

            for result in results:
                threat_name = result.threat_name or ""
                error_message = result.error_message or ""
                lines.append(f'"{result.file_path}","{result.result.value}","{threat_name}",{result.scan_time},"{error_message}"')

            return "\n".join(lines)

        else:  # Default to text format
            lines = []
            lines.append("ClamAV Scan Results")
            lines.append("=" * 50)
            lines.append(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Total Files: {len(results)}")
            lines.append("")

            stats = self.get_scan_statistics(results)
            lines.append("Summary:")
            lines.append(f"  Clean files: {stats['clean_files']}")
            lines.append(f"  Infected files: {stats['infected_files']}")
            lines.append(f"  Error files: {stats['error_files']}")
            lines.append(f"  Unsupported files: {stats['unsupported_files']}")
            lines.append(f"  Total scan time: {stats['total_scan_time']:.2f}s")
            lines.append("")

            if stats['threats']:
                lines.append("Threats Found:")
                for threat, count in sorted(stats['threats'].items()):
                    lines.append(f"  {threat}: {count}")
                lines.append("")

            lines.append("Detailed Results:")
            lines.append("-" * 30)

            for result in results:
                if result.result == ScanResult.INFECTED:
                    lines.append(f"⚠️  {result.file_path} - INFECTED: {result.threat_name}")
                elif result.result == ScanResult.ERROR:
                    lines.append(f"❌ {result.file_path} - ERROR: {result.error_message}")
                elif result.result == ScanResult.UNSUPPORTED:
                    lines.append(f"⭕ {result.file_path} - UNSUPPORTED")
                else:
                    lines.append(f"✅ {result.file_path} - CLEAN")

            return "\n".join(lines)


class ClamAVManager:
    """
    Manager class for ClamAV integration with configuration and error handling.
    """

    def __init__(self):
        """Initialize ClamAV manager."""
        self.integration = None
        self._initialize_integration()

    def _initialize_integration(self):
        """Initialize ClamAV integration with error handling."""
        try:
            # Try to initialize with default database path
            self.integration = ClamAVIntegration()

            if not self.integration.is_available():
                logger.warning("ClamAV not available - some features will be disabled")
            else:
                logger.info(f"ClamAV integration ready - Version: {self.integration.get_version()}")

        except Exception as e:
            logger.error(f"Failed to initialize ClamAV integration: {e}")
            self.integration = None

    def get_integration(self) -> Optional[ClamAVIntegration]:
        """Get the ClamAV integration instance."""
        return self.integration

    def is_available(self) -> bool:
        """Check if ClamAV integration is available."""
        return self.integration is not None and self.integration.is_available()

    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        status = {
            'available': self.is_available(),
            'direct_integration': False,
            'version': None,
            'database_info': {},
            'error': None
        }

        if self.integration:
            status['direct_integration'] = self.integration.is_direct_integration()
            status['version'] = self.integration.get_version()
            status['database_info'] = self.integration.get_database_info()
        else:
            status['error'] = "ClamAV integration not initialized"

        return status
