"""
Hash database for smart scanning functionality.
Stores file hashes to skip known safe files during scans.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HashDatabase:
    """Manages a database of file hashes for smart scanning."""

    def __init__(self, db_path: str = None):
        """Initialize the hash database.

        Args:
            db_path: Path to the hash database file (default: user's AppData/ClamAV/hash_db.json)
        """
        if db_path is None:
            app_data = os.getenv('APPDATA') if os.name == 'nt' else os.path.expanduser('~')
            clamav_dir = os.path.join(app_data, 'ClamAV')
            os.makedirs(clamav_dir, exist_ok=True)
            self.db_path = os.path.join(clamav_dir, 'hash_db.json')
        else:
            self.db_path = db_path

        self.hash_cache: Dict[str, Dict] = {}
        self.load_database()

    def load_database(self):
        """Load the hash database from file."""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.hash_cache = json.load(f)
                    logger.info(f"Loaded hash database with {len(self.hash_cache)} entries")
            else:
                self.hash_cache = {}
                logger.info("Created new hash database")
        except Exception as e:
            logger.error(f"Error loading hash database: {e}")
            self.hash_cache = {}

    def save_database(self):
        """Save the hash database to file."""
        try:
            # Create backup before saving
            backup_path = self.db_path + '.backup'
            if os.path.exists(self.db_path):
                os.rename(self.db_path, backup_path)

            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.hash_cache, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved hash database with {len(self.hash_cache)} entries")

            # Clean up backup if save was successful
            if os.path.exists(backup_path):
                os.unlink(backup_path)

        except Exception as e:
            logger.error(f"Error saving hash database: {e}")
            # Restore backup if save failed
            if os.path.exists(backup_path):
                os.rename(backup_path, self.db_path)

    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash as hex string
        """
        try:
            hash_obj = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def is_known_safe(self, file_hash: str) -> bool:
        """Check if a file hash is known to be safe.

        Args:
            file_hash: SHA-256 hash of the file

        Returns:
            True if the file is known safe, False otherwise
        """
        if not file_hash:
            return False

        # Check if hash exists in database
        if file_hash in self.hash_cache:
            entry = self.hash_cache[file_hash]

            # Check if the entry is still valid (not expired)
            if self._is_entry_valid(entry):
                return entry.get('status') == 'safe'

        return False

    def mark_file_safe(self, file_path: str, scan_result: str = "clean"):
        """Mark a file as safe in the database.

        Args:
            file_path: Path to the file
            scan_result: Scan result from ClamAV
        """
        try:
            file_hash = self.get_file_hash(file_path)
            if not file_hash:
                return

            # Only mark as safe if scan result indicates clean
            if scan_result.lower() in ['clean', 'ok', 'no threats found']:
                self.hash_cache[file_hash] = {
                    'file_path': file_path,
                    'status': 'safe',
                    'first_seen': datetime.now().isoformat(),
                    'last_verified': datetime.now().isoformat(),
                    'scan_result': scan_result
                }

                logger.debug(f"Marked file as safe: {file_path} ({file_hash[:16]}...)")

        except Exception as e:
            logger.error(f"Error marking file as safe: {e}")

    def mark_file_infected(self, file_path: str, threat_name: str):
        """Mark a file as infected in the database.

        Args:
            file_path: Path to the file
            threat_name: Name of the detected threat
        """
        try:
            file_hash = self.get_file_hash(file_path)
            if not file_hash:
                return

            # Mark as infected and remove from safe list if present
            if file_hash in self.hash_cache:
                del self.hash_cache[file_hash]

            logger.debug(f"Marked file as infected and removed from safe list: {file_path}")

        except Exception as e:
            logger.error(f"Error marking file as infected: {e}")

    def cleanup_old_entries(self, days_old: int = 30):
        """Remove old entries from the hash database.

        Args:
            days_old: Remove entries older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0

        for file_hash, entry in list(self.hash_cache.items()):
            try:
                last_verified = datetime.fromisoformat(entry.get('last_verified', ''))
                if last_verified < cutoff_date:
                    del self.hash_cache[file_hash]
                    removed_count += 1
            except (ValueError, TypeError):
                # Remove entries with invalid dates
                del self.hash_cache[file_hash]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old hash database entries")
            self.save_database()

    def get_database_stats(self) -> Dict:
        """Get statistics about the hash database.

        Returns:
            Dictionary with database statistics
        """
        safe_count = 0
        total_size = 0

        for entry in self.hash_cache.values():
            if entry.get('status') == 'safe':
                safe_count += 1

        # Estimate database size in memory
        try:
            total_size = len(json.dumps(self.hash_cache).encode('utf-8'))
        except:
            pass

        return {
            'total_entries': len(self.hash_cache),
            'safe_entries': safe_count,
            'database_size_bytes': total_size,
            'database_size_mb': round(total_size / (1024 * 1024), 2)
        }

    def _is_entry_valid(self, entry: Dict) -> bool:
        """Check if a database entry is still valid.

        Args:
            entry: Database entry dictionary

        Returns:
            True if entry is valid, False if expired
        """
        try:
            # Check if entry has required fields
            if not all(key in entry for key in ['status', 'last_verified']):
                return False

            # Check if entry is not too old (30 days max)
            last_verified = datetime.fromisoformat(entry['last_verified'])
            max_age = timedelta(days=30)

            if datetime.now() - last_verified > max_age:
                return False

            return True

        except (ValueError, TypeError, KeyError):
            return False

    def clear_database(self):
        """Clear all entries from the hash database."""
        self.hash_cache.clear()
        self.save_database()
        logger.info("Cleared hash database")

    def export_database(self, export_path: str) -> bool:
        """Export the hash database to a file.

        Args:
            export_path: Path to save the exported database

        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'database_stats': self.get_database_stats(),
                'hash_entries': self.hash_cache
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Error exporting hash database: {e}")
            return False

    def import_database(self, import_path: str, merge: bool = False) -> bool:
        """Import hash database from a file.

        Args:
            import_path: Path to the file to import
            merge: If True, merge with existing database; if False, replace

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if not merge:
                self.hash_cache.clear()

            # Import hash entries
            hash_entries = import_data.get('hash_entries', import_data)
            if isinstance(hash_entries, dict):
                self.hash_cache.update(hash_entries)

            self.save_database()
            logger.info(f"Imported hash database with {len(hash_entries)} entries")
            return True

        except Exception as e:
            logger.error(f"Error importing hash database: {e}")
            return False
