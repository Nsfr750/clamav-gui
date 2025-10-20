"""
Smart scanning functionality for ClamAV GUI.
Uses hash databases to skip files that have been previously scanned and confirmed safe.
"""
import os
import hashlib
import logging
import sqlite3
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class SmartScanner:
    """Smart scanning system using hash databases for efficiency."""

    def __init__(self, clamscan_path: str = "clamscan", db_path: str = None):
        """Initialize the smart scanner.

        Args:
            clamscan_path: Path to clamscan executable
            db_path: Path to the hash database file
        """
        self.clamscan_path = clamscan_path
        self.db_path = db_path or os.path.expanduser("~/.clamav-gui/hash_cache.db")
        self.scan_results = []
        self.hash_cache = {}

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize the hash database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_hashes (
                        hash TEXT PRIMARY KEY,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        last_modified REAL,
                        scan_result TEXT,
                        scan_date REAL,
                        is_safe BOOLEAN DEFAULT 0
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scan_sessions (
                        id INTEGER PRIMARY KEY,
                        start_time REAL,
                        end_time REAL,
                        total_files INTEGER,
                        safe_files INTEGER,
                        skipped_files INTEGER
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize hash database: {e}")

    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash string or None if failed
        """
        try:
            if not os.path.exists(file_path) or os.path.isdir(file_path):
                return None

            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None

    def is_file_unchanged(self, file_path: str, file_hash: str) -> bool:
        """Check if a file has changed since last scan.

        Args:
            file_path: Path to the file
            file_hash: Previously calculated hash

        Returns:
            True if file is unchanged, False otherwise
        """
        try:
            current_hash = self.calculate_file_hash(file_path)
            return current_hash == file_hash
        except Exception as e:
            logger.error(f"Error checking file change for {file_path}: {e}")
            return False

    def scan_file_with_clamav(self, file_path: str) -> Tuple[str, str]:
        """Scan a file using ClamAV.

        Args:
            file_path: Path to the file to scan

        Returns:
            Tuple of (scan_result, output)
        """
        try:
            result = subprocess.run(
                [self.clamscan_path, "--no-summary", "--quiet", file_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return "CLEAN", result.stdout.strip()
            else:
                return "INFECTED", result.stdout.strip() or result.stderr.strip()
        except subprocess.TimeoutExpired:
            return "TIMEOUT", "Scan timed out"
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            return "ERROR", str(e)

    def get_cached_result(self, file_hash: str) -> Optional[Tuple[str, bool]]:
        """Get cached scan result for a file hash.

        Args:
            file_hash: The file hash

        Returns:
            Tuple of (scan_result, is_safe) or None if not cached
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT scan_result, is_safe FROM file_hashes WHERE hash = ?",
                    (file_hash,)
                )
                row = cursor.fetchone()
                if row:
                    return row[0], bool(row[1])
        except sqlite3.Error as e:
            logger.error(f"Database error getting cached result: {e}")
        return None

    def cache_scan_result(self, file_hash: str, file_path: str, scan_result: str, is_safe: bool):
        """Cache a scan result.

        Args:
            file_hash: The file hash
            file_path: Path to the file
            scan_result: Result of the scan
            is_safe: Whether the file is safe
        """
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            last_modified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO file_hashes
                    (hash, file_path, file_size, last_modified, scan_result, scan_date, is_safe)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (file_hash, file_path, file_size, last_modified, scan_result, datetime.now().timestamp(), is_safe))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error caching result: {e}")
        except Exception as e:
            logger.error(f"Error caching scan result: {e}")

    def smart_scan_file(self, file_path: str) -> Tuple[str, str, bool]:
        """Perform a smart scan on a file.

        Args:
            file_path: Path to the file to scan

        Returns:
            Tuple of (scan_result, output, was_skipped)
        """
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return "ERROR", "File not found or is a directory", False

        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return "ERROR", "Could not calculate file hash", False

        # Check cache first
        cached_result = self.get_cached_result(file_hash)
        if cached_result:
            scan_result, is_safe = cached_result

            # If file is safe and unchanged, skip scanning
            if is_safe and self.is_file_unchanged(file_path, file_hash):
                return "SKIPPED", "File is safe and unchanged", True

        # Scan with ClamAV
        scan_result, output = self.scan_file_with_clamav(file_path)

        # Determine if file is safe
        is_safe = scan_result == "CLEAN"

        # Cache the result
        self.cache_scan_result(file_hash, file_path, scan_result, is_safe)

        return scan_result, output, False

    def scan_directory_smart(self, directory: str) -> Dict[str, Any]:
        """Scan a directory using smart scanning.

        Args:
            directory: Path to the directory to scan

        Returns:
            Dictionary with scan statistics
        """
        if not os.path.exists(directory) or not os.path.isdir(directory):
            return {"error": "Directory not found"}

        results = {
            "total_files": 0,
            "scanned_files": 0,
            "skipped_files": 0,
            "clean_files": 0,
            "infected_files": 0,
            "errors": 0,
            "start_time": datetime.now(),
            "end_time": None,
            "duration": None
        }

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                results["total_files"] += 1

                scan_result, output, was_skipped = self.smart_scan_file(file_path)

                if was_skipped:
                    results["skipped_files"] += 1
                else:
                    results["scanned_files"] += 1

                    if scan_result == "CLEAN":
                        results["clean_files"] += 1
                    elif scan_result == "INFECTED":
                        results["infected_files"] += 1
                    else:
                        results["errors"] += 1

        results["end_time"] = datetime.now()
        results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()

        return results

    def clear_cache(self):
        """Clear the hash cache database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM file_hashes")
                conn.commit()
            logger.info("Hash cache cleared")
        except sqlite3.Error as e:
            logger.error(f"Error clearing cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the hash cache.

        Returns:
            Dictionary with cache statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM file_hashes")
                total_entries = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM file_hashes WHERE is_safe = 1")
                safe_entries = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM scan_sessions")
                total_sessions = cursor.fetchone()[0]

                return {
                    "total_entries": total_entries,
                    "safe_entries": safe_entries,
                    "infected_entries": total_entries - safe_entries,
                    "total_sessions": total_sessions
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}


class SmartScanThread(QThread):
    """Thread for running smart scans in the background."""

    # Signals
    progress_updated = Signal(int, str)  # progress, status
    scan_finished = Signal(dict)  # results
    file_scanned = Signal(str, str, str)  # file_path, result, output

    def __init__(self, scanner: SmartScanner, paths: List[str]):
        super().__init__()
        self.scanner = scanner
        self.paths = paths

    def run(self):
        """Run the smart scan."""
        total_paths = len(self.paths)
        results = {
            "total_files": 0,
            "scanned_files": 0,
            "skipped_files": 0,
            "clean_files": 0,
            "infected_files": 0,
            "errors": 0,
            "files": []
        }

        for i, path in enumerate(self.paths):
            self.progress_updated.emit(int((i / total_paths) * 100), f"Scanning: {os.path.basename(path)}")

            if os.path.isfile(path):
                scan_result, output, was_skipped = self.scanner.smart_scan_file(path)
                results["total_files"] += 1

                if was_skipped:
                    results["skipped_files"] += 1
                else:
                    results["scanned_files"] += 1

                if scan_result == "CLEAN":
                    results["clean_files"] += 1
                elif scan_result == "INFECTED":
                    results["infected_files"] += 1
                else:
                    results["errors"] += 1

                results["files"].append({
                    "path": path,
                    "result": scan_result,
                    "output": output,
                    "skipped": was_skipped
                })

                self.file_scanned.emit(path, scan_result, output)

            elif os.path.isdir(path):
                dir_results = self.scanner.scan_directory_smart(path)
                if "error" not in dir_results:
                    for key in ["total_files", "scanned_files", "skipped_files", "clean_files", "infected_files", "errors"]:
                        results[key] += dir_results.get(key, 0)

        self.progress_updated.emit(100, "Scan completed")
        self.scan_finished.emit(results)
