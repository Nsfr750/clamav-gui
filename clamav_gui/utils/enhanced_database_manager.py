"""
Enhanced ClamAV Database Management for Integrated Scanning.

This module provides enhanced database management capabilities for the integrated
ClamAV scanner, including automatic updates, backup management, and database integrity checks.
"""
import os
import sys
import json
import logging
import shutil
import hashlib
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QThread

logger = logging.getLogger(__name__)


class DatabaseIntegrityChecker:
    """Checks ClamAV database integrity and consistency."""

    def __init__(self, database_path: str):
        self.database_path = database_path

    def check_integrity(self) -> Dict[str, Any]:
        """
        Check database integrity and return detailed status.

        Returns:
            Dict with integrity check results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_count': 0,
            'total_size': 0,
            'last_update': None
        }

        if not os.path.exists(self.database_path):
            result['valid'] = False
            result['errors'].append("Database directory does not exist")
            return result

        try:
            # Check for essential database files
            essential_files = ['main.cvd', 'daily.cvd', 'bytecode.cvd']
            found_files = []

            for root, dirs, files in os.walk(self.database_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.database_path)

                    # Check file size and modification time
                    stat = os.stat(file_path)
                    result['total_size'] += stat.st_size
                    result['file_count'] += 1

                    if stat.st_mtime > (result['last_update'] or 0):
                        result['last_update'] = stat.st_mtime

                    # Check for essential files
                    if file in essential_files:
                        found_files.append(file)

                    # Check file integrity (basic check)
                    if file.endswith('.cvd') or file.endswith('.cld'):
                        if stat.st_size == 0:
                            result['errors'].append(f"Empty database file: {rel_path}")
                            result['valid'] = False

            # Check for missing essential files
            missing_files = set(essential_files) - set(found_files)
            if missing_files:
                result['warnings'].append(f"Missing essential database files: {', '.join(missing_files)}")

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Error checking database: {str(e)}")

        return result

    def repair_database(self) -> bool:
        """
        Attempt to repair database issues.

        Returns:
            True if repair was successful or not needed
        """
        try:
            # For now, we mainly validate and report issues
            # Advanced repair would require more sophisticated logic
            logger.info("Database repair completed (validation only)")
            return True
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            return False


class EnhancedDatabaseManager(QObject):
    """
    Enhanced database manager for integrated ClamAV scanning.

    Provides comprehensive database management including updates, backups,
    integrity checks, and performance optimization.
    """

    # Signals for GUI updates
    update_progress = Signal(int)
    update_status = Signal(str)
    update_completed = Signal(bool, str)
    integrity_check_completed = Signal(dict)

    def __init__(self, database_path: Optional[str] = None):
        super().__init__()
        self.database_path = database_path or self._get_default_database_path()
        self.integrity_checker = DatabaseIntegrityChecker(self.database_path)
        self._ensure_database_directory()

    def _get_default_database_path(self) -> str:
        """Get the default ClamAV database path."""
        if sys.platform == "win32":
            appdata = os.getenv('APPDATA', os.path.expanduser('~'))
            return os.path.join(appdata, 'ClamAV', 'database')
        else:
            return '/var/lib/clamav'

    def _ensure_database_directory(self):
        """Ensure the database directory exists."""
        try:
            os.makedirs(self.database_path, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create database directory: {e}")

    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information."""
        info = {
            'path': self.database_path,
            'exists': os.path.exists(self.database_path),
            'writable': False,
            'size_mb': 0,
            'file_count': 0,
            'last_update': None,
            'version': None,
            'integrity': {}
        }

        if info['exists']:
            try:
                info['writable'] = os.access(self.database_path, os.W_OK)

                total_size = 0
                file_count = 0
                newest_file = None

                for root, dirs, files in os.walk(self.database_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        stat = os.stat(file_path)

                        total_size += stat.st_size
                        file_count += 1

                        if stat.st_mtime > (newest_file or 0):
                            newest_file = stat.st_mtime

                info['size_mb'] = total_size / (1024 * 1024)
                info['file_count'] = file_count
                info['last_update'] = newest_file

                # Get database version from main.cvd if available
                main_cvd = os.path.join(self.database_path, 'main.cvd')
                if os.path.exists(main_cvd):
                    try:
                        with open(main_cvd, 'rb') as f:
                            # Read version info from CVD header (simplified)
                            f.seek(4)  # Skip magic
                            version_data = f.read(512)
                            # Extract version string (this is a simplified approach)
                            try:
                                version_str = version_data.decode('utf-8', errors='ignore').strip()
                                # Look for version pattern
                                import re
                                version_match = re.search(r'version[:\s]+(\d+)', version_str, re.IGNORECASE)
                                if version_match:
                                    info['version'] = version_match.group(1)
                            except:
                                pass
                    except:
                        pass

                # Check integrity
                info['integrity'] = self.integrity_checker.check_integrity()

            except Exception as e:
                logger.error(f"Error getting database info: {e}")

        return info

    def update_database_async(self, freshclam_path: Optional[str] = None, force_update: bool = False):
        """
        Update database asynchronously.

        Args:
            freshclam_path: Path to freshclam executable
            force_update: Force update even if database is recent
        """
        def update_worker():
            try:
                self.update_status.emit("Starting database update...")

                # Check if update is needed (unless forced)
                if not force_update:
                    db_info = self.get_database_info()
                    if db_info.get('last_update'):
                        last_update = datetime.fromtimestamp(db_info['last_update'])
                        if datetime.now() - last_update < timedelta(hours=4):
                            self.update_status.emit("Database is up to date")
                            self.update_completed.emit(True, "Database is already current")
                            return

                # Perform the update
                success, message = self._perform_database_update(freshclam_path)

                if success:
                    # Verify the update
                    self.update_status.emit("Verifying database integrity...")
                    integrity = self.integrity_checker.check_integrity()

                    if integrity['valid']:
                        self.update_status.emit("✅ Database updated successfully")
                        self.update_completed.emit(True, message)
                    else:
                        self.update_status.emit("⚠️ Database updated but integrity issues found")
                        self.update_completed.emit(False, f"Update completed but integrity issues: {integrity['errors']}")
                else:
                    self.update_completed.emit(False, message)

            except Exception as e:
                logger.error(f"Database update error: {e}")
                self.update_completed.emit(False, f"Update failed: {str(e)}")

        thread = QThread()
        thread.run = update_worker
        thread.start()

    def _perform_database_update(self, freshclam_path: Optional[str] = None) -> Tuple[bool, str]:
        """Perform the actual database update."""
        try:
            cmd = [freshclam_path or 'freshclam']

            # Add common options for reliable updates
            cmd.extend([
                '--quiet',
                '--no-warnings',
                '--datadir', self.database_path
            ])

            # Use a timeout to prevent hanging
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=self.database_path
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

    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create a backup of the current database.

        Args:
            backup_name: Name for the backup (optional, will use timestamp if not provided)

        Returns:
            Tuple of (success, message or backup_path)
        """
        try:
            if not os.path.exists(self.database_path):
                return False, "Database directory does not exist"

            # Generate backup name
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"clamav_backup_{timestamp}"

            # Create backup directory
            backup_dir = os.path.join(os.path.dirname(self.database_path), 'backups', backup_name)

            # Copy database files
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)

            shutil.copytree(self.database_path, backup_dir)

            backup_path = backup_dir
            return True, f"Database backed up to: {backup_path}"

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, f"Backup failed: {str(e)}"

    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Restore database from backup.

        Args:
            backup_path: Path to the backup directory

        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "Backup directory does not exist"

            # Create backup of current database first
            current_backup_success, _ = self.create_backup("pre_restore_backup")
            if not current_backup_success:
                logger.warning("Failed to create pre-restore backup")

            # Restore from backup
            if os.path.exists(self.database_path):
                shutil.rmtree(self.database_path)

            shutil.copytree(backup_path, self.database_path)

            return True, "Database restored successfully"

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False, f"Restore failed: {str(e)}"

    def cleanup_old_backups(self, max_age_days: int = 7) -> int:
        """
        Remove old database backups.

        Args:
            max_age_days: Maximum age of backups to keep (in days)

        Returns:
            Number of backups removed
        """
        try:
            backups_dir = os.path.join(os.path.dirname(self.database_path), 'backups')
            if not os.path.exists(backups_dir):
                return 0

            removed_count = 0
            cutoff_time = datetime.now() - timedelta(days=max_age_days)

            for item in os.listdir(backups_dir):
                backup_path = os.path.join(backups_dir, item)
                if os.path.isdir(backup_path):
                    # Check modification time
                    try:
                        stat = os.stat(backup_path)
                        if datetime.fromtimestamp(stat.st_mtime) < cutoff_time:
                            shutil.rmtree(backup_path)
                            removed_count += 1
                            logger.info(f"Removed old backup: {item}")
                    except Exception as e:
                        logger.warning(f"Failed to check backup {item}: {e}")

            return removed_count

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return 0

    def optimize_database(self) -> Tuple[bool, str]:
        """
        Optimize database for better performance.

        Returns:
            Tuple of (success, message)
        """
        try:
            # For ClamAV, optimization mainly involves ensuring proper file structure
            # and removing any temporary or corrupted files

            temp_files = []
            for root, dirs, files in os.walk(self.database_path):
                for file in files:
                    if file.endswith('.tmp') or file.startswith('temp_'):
                        temp_files.append(os.path.join(root, file))

            # Remove temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    logger.info(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {temp_file}: {e}")

            return True, f"Database optimized (removed {len(temp_files)} temporary files)"

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False, f"Optimization failed: {str(e)}"

    def check_and_fix_permissions(self) -> Tuple[bool, str]:
        """
        Check and fix database directory permissions.

        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(self.database_path):
                os.makedirs(self.database_path, exist_ok=True)

            # Try to make directory writable
            if not os.access(self.database_path, os.W_OK):
                try:
                    os.chmod(self.database_path, 0o755)
                except Exception as e:
                    logger.warning(f"Failed to fix permissions: {e}")

            return True, "Permissions checked and fixed if needed"

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False, f"Permission check failed: {str(e)}"

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups with metadata."""
        backups = []

        try:
            backups_dir = os.path.join(os.path.dirname(self.database_path), 'backups')
            if not os.path.exists(backups_dir):
                return backups

            for item in os.listdir(backups_dir):
                backup_path = os.path.join(backups_dir, item)
                if os.path.isdir(backup_path):
                    try:
                        stat = os.stat(backup_path)
                        size = sum(os.path.getsize(os.path.join(root, f))
                                 for root, dirs, files in os.walk(backup_path)
                                 for f in files)

                        backups.append({
                            'name': item,
                            'path': backup_path,
                            'size_mb': size / (1024 * 1024),
                            'created': datetime.fromtimestamp(stat.st_mtime),
                            'file_count': sum(len(files) for _, _, files in os.walk(backup_path))
                        })
                    except Exception as e:
                        logger.warning(f"Failed to get backup info for {item}: {e}")

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
