"""
Batch analysis functionality for ClamAV GUI.
Supports scanning multiple files and directories in batch operations.
"""
import os
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """Batch analysis system for scanning multiple files and directories."""

    def __init__(self, clamscan_path: str = "clamscan"):
        """Initialize the batch analyzer.

        Args:
            clamscan_path: Path to clamscan executable
        """
        self.clamscan_path = clamscan_path
        self.scan_results = []

    def validate_batch_items(self, items: List[str]) -> Tuple[bool, str, List[str]]:
        """Validate a list of files/directories for batch scanning.

        Args:
            items: List of file/directory paths to validate

        Returns:
            Tuple of (is_valid: bool, message: str, valid_items: List[str])
        """
        if not items:
            return False, "No items provided for batch analysis", []

        valid_items = []
        invalid_items = []

        for item in items:
            if not item or not os.path.exists(item):
                invalid_items.append(f"Path not found: {item}")
                continue

            # Check if it's a file or directory
            if os.path.isfile(item) or os.path.isdir(item):
                valid_items.append(item)
            else:
                invalid_items.append(f"Invalid path type: {item}")

        if not valid_items:
            return False, f"All items are invalid: {'; '.join(invalid_items)}", []

        if invalid_items:
            warning_msg = f"Warning: {len(invalid_items)} items were skipped"
            return True, warning_msg, valid_items

        return True, f"All {len(valid_items)} items are valid", valid_items

    def scan_batch_items(self, items: List[str], options: Dict = None) -> Tuple[bool, str, List[Dict]]:
        """Scan multiple files and directories in batch.

        Args:
            items: List of file/directory paths to scan
            options: Scan options dictionary

        Returns:
            Tuple of (success: bool, message: str, results: List[Dict])
        """
        options = options or {}
        results = []

        try:
            # Validate items first
            is_valid, message, valid_items = self.validate_batch_items(items)
            if not is_valid:
                return False, message, results

            logger.info(f"Starting batch scan of {len(valid_items)} items")

            # Create database directory
            app_data = os.getenv('APPDATA') if platform.system() == 'Windows' else os.path.expanduser('~')
            clamav_dir = os.path.join(app_data, 'ClamAV')
            db_dir = os.path.join(clamav_dir, 'database')

            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            # Scan each item
            for item in valid_items:
                item_result = self._scan_single_item(item, options, db_dir)
                results.append(item_result)

            # Calculate overall statistics
            success_count = sum(1 for r in results if r['success'])
            threat_count = sum(r.get('threats_found', 0) for r in results)

            if success_count == len(valid_items):
                message = f"Batch scan completed successfully. Scanned {len(valid_items)} items, found {threat_count} threats."
            elif success_count > 0:
                message = f"Batch scan partially successful. {success_count}/{len(valid_items)} items scanned, {threat_count} threats found."
            else:
                message = f"Batch scan failed. No items were successfully scanned."

            return True, message, results

        except Exception as e:
            error_msg = f"Batch scan error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, results

    def _scan_single_item(self, item_path: str, options: Dict, db_dir: str) -> Dict:
        """Scan a single file or directory.

        Args:
            item_path: Path to scan
            options: Scan options
            db_dir: ClamAV database directory

        Returns:
            Dictionary with scan results for this item
        """
        result = {
            'path': item_path,
            'success': False,
            'threats_found': 0,
            'threats': [],
            'scan_time': 0,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Build clamscan command
            cmd = [self.clamscan_path, '--database', db_dir]

            # Add scan options
            if options.get('recursive', True) and os.path.isdir(item_path):
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

            # Add target and output options
            cmd.extend([item_path, "--verbose", "--stdout"])

            # Run the scan
            start_time = datetime.now()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout for large scans
                check=False
            )
            end_time = datetime.now()

            result['scan_time'] = (end_time - start_time).total_seconds()

            # Parse output for threats
            output = process.stdout + process.stderr

            threats = []
            for line in output.split('\n'):
                if 'FOUND' in line or 'infected' in line.lower():
                    threats.append(line.strip())

            result['threats'] = threats
            result['threats_found'] = len(threats)
            result['success'] = process.returncode in (0, 1)  # 0 = clean, 1 = infected (not error)

        except subprocess.TimeoutExpired:
            result['error'] = "Scan timeout"
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error scanning {item_path}: {e}")

        return result

    def get_batch_statistics(self, results: List[Dict]) -> Dict:
        """Get statistics from batch scan results.

        Args:
            results: List of scan results

        Returns:
            Dictionary with batch statistics
        """
        if not results:
            return {}

        stats = {
            'total_items': len(results),
            'successful_scans': sum(1 for r in results if r['success']),
            'failed_scans': sum(1 for r in results if not r['success']),
            'total_threats': sum(r.get('threats_found', 0) for r in results),
            'total_scan_time': sum(r.get('scan_time', 0) for r in results),
            'avg_scan_time': 0,
            'threat_types': {},
            'errors': []
        }

        # Calculate average scan time
        if stats['successful_scans'] > 0:
            stats['avg_scan_time'] = stats['total_scan_time'] / stats['successful_scans']

        # Count threat types
        for result in results:
            if result['success']:
                for threat in result.get('threats', []):
                    threat_type = threat.split(':')[0] if ':' in threat else 'Unknown'
                    stats['threat_types'][threat_type] = stats['threat_types'].get(threat_type, 0) + 1

        # Collect errors
        for result in results:
            if result.get('error'):
                stats['errors'].append({
                    'path': result['path'],
                    'error': result['error']
                })

        return stats

    def generate_batch_report(self, results: List[Dict], stats: Dict) -> str:
        """Generate a detailed batch analysis report.

        Args:
            results: List of scan results
            stats: Batch statistics

        Returns:
            Formatted report string
        """
        report = []
        report.append("Batch Analysis Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary statistics
        report.append("Summary:")
        report.append(f"  Total items analyzed: {stats.get('total_items', 0)}")
        report.append(f"  Successful scans: {stats.get('successful_scans', 0)}")
        report.append(f"  Failed scans: {stats.get('failed_scans', 0)}")
        report.append(f"  Total threats found: {stats.get('total_threats', 0)}")
        report.append(f"  Total scan time: {stats.get('total_scan_time', 0):.2f} seconds")
        report.append(f"  Average scan time: {stats.get('avg_scan_time', 0):.2f} seconds")
        report.append("")

        # Threat distribution
        threat_types = stats.get('threat_types', {})
        if threat_types:
            report.append("Threat Types:")
            for threat_type, count in sorted(threat_types.items()):
                report.append(f"  {threat_type}: {count}")
            report.append("")

        # Errors
        errors = stats.get('errors', [])
        if errors:
            report.append("Errors:")
            for error in errors[:10]:  # Show first 10 errors
                report.append(f"  {error['path']}: {error['error']}")
            if len(errors) > 10:
                report.append(f"  ... and {len(errors) - 10} more errors")
            report.append("")

        # Detailed results
        report.append("Detailed Results:")
        report.append("-" * 50)

        for result in results:
            report.append(f"Path: {result['path']}")
            report.append(f"  Success: {'Yes' if result['success'] else 'No'}")
            report.append(f"  Scan time: {result.get('scan_time', 0):.2f} seconds")
            report.append(f"  Threats found: {result.get('threats_found', 0)}")

            if result.get('threats'):
                report.append("  Threats:")
                for threat in result['threats']:
                    report.append(f"    • {threat}")

            if result.get('error'):
                report.append(f"  Error: {result['error']}")

            report.append("")

        return "\n".join(report)


class BatchAnalysisThread(QThread):
    """Thread for batch analysis operations."""

    update_progress = Signal(int)
    update_output = Signal(str)
    analysis_finished = Signal(bool, str, list)
    item_finished = Signal(str, dict)

    def __init__(self, analyzer: BatchAnalyzer, items: List[str], options: Dict = None):
        super().__init__()
        self.analyzer = analyzer
        self.items = items
        self.options = options or {}

    def run(self):
        """Run the batch analysis process."""
        try:
            self.update_output.emit(f"Starting batch analysis of {len(self.items)} items...")

            # Validate items first
            is_valid, message, valid_items = self.analyzer.validate_batch_items(self.items)

            if not is_valid:
                self.analysis_finished.emit(False, message, [])
                return

            if message.startswith("Warning"):
                self.update_output.emit(message)

            # Scan each item
            results = []
            total_items = len(valid_items)

            for i, item in enumerate(valid_items):
                self.update_progress.emit(int((i / total_items) * 100))

                try:
                    item_result = self.analyzer._scan_single_item(item, self.options, self._get_db_dir())
                    results.append(item_result)

                    # Emit individual item result
                    self.item_finished.emit(item, item_result)

                    # Update progress message
                    if item_result['success']:
                        threat_count = item_result.get('threats_found', 0)
                        status = f"threats found" if threat_count > 0 else "clean"
                        self.update_output.emit(f"Completed: {os.path.basename(item)} ({threat_count} {status})")
                    else:
                        self.update_output.emit(f"Failed: {os.path.basename(item)} - {item_result.get('error', 'Unknown error')}")

                except Exception as e:
                    error_result = {
                        'path': item,
                        'success': False,
                        'threats_found': 0,
                        'threats': [],
                        'scan_time': 0,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(error_result)
                    self.item_finished.emit(item, error_result)
                    self.update_output.emit(f"Error analyzing {os.path.basename(item)}: {str(e)}")

            self.update_progress.emit(100)

            # Generate final statistics
            stats = self.analyzer.get_batch_statistics(results)
            final_message = f"Batch analysis completed. {stats['successful_scans']}/{stats['total_items']} successful, {stats['total_threats']} threats found."

            self.analysis_finished.emit(True, final_message, results)

        except Exception as e:
            self.analysis_finished.emit(False, f"Batch analysis failed: {str(e)}", [])

    def _get_db_dir(self) -> str:
        """Get the ClamAV database directory."""
        app_data = os.getenv('APPDATA') if platform.system() == 'Windows' else os.path.expanduser('~')
        clamav_dir = os.path.join(app_data, 'ClamAV')
        return os.path.join(clamav_dir, 'database')
