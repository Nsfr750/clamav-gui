"""
Enhanced virus database updater with incremental update support.
Supports differential updates for faster downloads and better reliability.
"""
import os
import json
import logging
import platform
import subprocess
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class EnhancedVirusDBUpdater:
    """Enhanced virus database updater with incremental update support."""

    def __init__(self, freshclam_path: str = None):
        """Initialize the enhanced virus database updater.

        Args:
            freshclam_path: Path to freshclam executable
        """
        self.freshclam_path = freshclam_path or "freshclam"
        self.app_data = os.getenv('APPDATA') if platform.system() == 'Windows' else os.path.expanduser('~')
        self.clamav_dir = os.path.join(self.app_data, 'ClamAV')
        self.db_dir = os.path.join(self.clamav_dir, 'database')
        self.temp_dir = os.path.join(self.clamav_dir, 'temp')
        self.metadata_file = os.path.join(self.clamav_dir, 'db_metadata.json')

        # Ensure directories exist
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        self.current_metadata = self.load_metadata()

    def load_metadata(self) -> Dict:
        """Load database metadata from file."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    'last_update': None,
                    'version': '0.0.0',
                    'file_count': 0,
                    'total_size': 0,
                    'files': {}
                }
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {
                'last_update': None,
                'version': '0.0.0',
                'file_count': 0,
                'total_size': 0,
                'files': {}
            }

    def save_metadata(self):
        """Save database metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def get_database_info(self) -> Dict:
        """Get comprehensive information about the current virus database."""
        try:
            # First get basic file information
            db_files = []
            total_size = 0

            for file_path in Path(self.db_dir).glob('*'):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    total_size += size
                    db_files.append({
                        'name': file_path.name,
                        'size': size,
                        'modified': file_path.stat().st_mtime
                    })

            base_info = {
                'directory': self.db_dir,
                'file_count': len(db_files),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files': db_files,
                'exists': os.path.exists(self.db_dir)
            }

            # Try to get detailed signature information using sigtool if available
            try:
                result = subprocess.run(['sigtool', '--info'],
                                      capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    output = result.stdout
                    # Parse sigtool output for signature information
                    for line in output.split('\n'):
                        line = line.strip()
                        if ': ' in line:
                            key, value = line.split(': ', 1)
                            key = key.lower().replace(' ', '_')
                            if key == 'signatures':
                                try:
                                    base_info['signature_count'] = int(value.replace(',', ''))
                                except ValueError:
                                    pass
                            elif key == 'version':
                                base_info['database_version'] = value
                            elif key == 'build_time':
                                base_info['build_time'] = value

            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
                # sigtool not available or failed, use basic info
                base_info['note'] = 'Detailed signature count requires sigtool (ClamAV development tools)'

                # Try to estimate signature count based on file sizes
                # This is a rough estimation based on typical ClamAV database characteristics
                if 'main.cvd' in [f['name'] for f in db_files]:
                    main_file = next(f for f in db_files if f['name'] == 'main.cvd')
                    # Rough estimation: main.cvd typically contains ~50,000-100,000 signatures per 100MB
                    estimated_main = int(main_file['size'] / 100000 * 75000)  # Conservative estimate
                    base_info['estimated_main_signatures'] = estimated_main

                if 'daily.cld' in [f['name'] for f in db_files]:
                    daily_file = next(f for f in db_files if f['name'] == 'daily.cld')
                    # Daily signatures are typically smaller and more numerous
                    estimated_daily = int(daily_file['size'] / 1000 * 100)  # Rough estimate
                    base_info['estimated_daily_signatures'] = estimated_daily

                if 'bytecode.cvd' in [f['name'] for f in db_files]:
                    bytecode_file = next(f for f in db_files if f['name'] == 'bytecode.cvd')
                    # Bytecode signatures are specialized
                    estimated_bytecode = int(bytecode_file['size'] / 10000 * 50)  # Rough estimate
                    base_info['estimated_bytecode_signatures'] = estimated_bytecode

                if 'estimated_main_signatures' in base_info or 'estimated_daily_signatures' in base_info or 'estimated_bytecode_signatures' in base_info:
                    total_estimated = sum(base_info.get(key, 0) for key in ['estimated_main_signatures', 'estimated_daily_signatures', 'estimated_bytecode_signatures'])
                    base_info['estimated_total_signatures'] = total_estimated

            return base_info

        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {
                'directory': self.db_dir,
                'file_count': 0,
                'total_size': 0,
                'total_size_mb': 0,
                'files': [],
                'exists': False,
                'error': str(e)
            }

    def check_for_updates(self) -> Tuple[bool, str, Dict]:
        """Check if database updates are available.

        Returns:
            Tuple of (update_available: bool, message: str, update_info: Dict)
        """
        try:
            # Get current database info
            current_info = self.get_database_info()

            # Run freshclam in check-only mode
            cmd = [self.freshclam_path, '--datadir', self.db_dir, '--check', '--quiet']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            if result.returncode == 0:
                # Check if updates are available
                if 'is up to date' in result.stdout.lower():
                    return False, "Database is up to date", {}
                else:
                    # Parse update information from output
                    update_info = self._parse_update_info(result.stdout)
                    return True, "Updates available", update_info
            else:
                return False, f"Check failed: {result.stderr.strip()}", {}

        except subprocess.TimeoutExpired:
            return False, "Update check timeout", {}
        except Exception as e:
            return False, f"Error checking for updates: {str(e)}", {}

    def _parse_update_info(self, output: str) -> Dict:
        """Parse update information from freshclam output."""
        update_info = {}

        try:
            lines = output.split('\n')
            for line in lines:
                if 'new version' in line.lower():
                    # Extract version info
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'version' and i + 1 < len(parts):
                            update_info['new_version'] = parts[i + 1]
                            break

        except Exception as e:
            logger.error(f"Error parsing update info: {e}")

        return update_info

    def perform_incremental_update(self) -> Tuple[bool, str]:
        """Perform an incremental database update.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check for updates first
            update_available, message, update_info = self.check_for_updates()
            if not update_available:
                return True, message

            # Create backup of current database
            backup_dir = os.path.join(self.clamav_dir, 'backup')
            os.makedirs(backup_dir, exist_ok=True)

            backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'db_backup_{backup_timestamp}')

            try:
                import shutil
                shutil.copytree(self.db_dir, backup_path)
                logger.info(f"Created database backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

            # Perform incremental update using freshclam
            cmd = [
                self.freshclam_path,
                '--datadir', self.db_dir,
                '--update-db',  # Update specific databases
                '--quiet'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout for updates
            )

            if result.returncode == 0:
                # Update metadata
                self._update_metadata_after_update(result.stdout)
                return True, f"Database updated successfully: {result.stdout.strip()}"
            else:
                # Try to restore from backup if update failed
                if os.path.exists(backup_path):
                    try:
                        shutil.rmtree(self.db_dir)
                        shutil.copytree(backup_path, self.db_dir)
                        logger.info("Restored database from backup after failed update")
                    except Exception as e:
                        logger.error(f"Failed to restore backup: {e}")

                return False, f"Update failed: {result.stderr.strip()}"

        except subprocess.TimeoutExpired:
            return False, "Database update timeout"
        except Exception as e:
            return False, f"Error during update: {str(e)}"

    def _update_metadata_after_update(self, output: str):
        """Update metadata after a successful database update."""
        try:
            # Get updated database info
            updated_info = self.get_database_info()

            # Update metadata
            self.current_metadata.update({
                'last_update': datetime.now().isoformat(),
                'file_count': updated_info['file_count'],
                'total_size': updated_info['total_size'],
                'files': {f['name']: f for f in updated_info['files']}
            })

            self.save_metadata()
            logger.info("Updated database metadata after successful update")

        except Exception as e:
            logger.error(f"Error updating metadata: {e}")

    def cleanup_old_backups(self, days_old: int = 7):
        """Clean up old database backups.

        Args:
            days_old: Remove backups older than this many days
        """
        try:
            backup_dir = os.path.join(self.clamav_dir, 'backup')
            if not os.path.exists(backup_dir):
                return

            cutoff_date = datetime.now() - timedelta(days=days_old)

            for item in Path(backup_dir).iterdir():
                if item.is_dir() and item.name.startswith('db_backup_'):
                    try:
                        # Extract timestamp from directory name
                        timestamp_str = item.name.replace('db_backup_', '')
                        backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                        if backup_date < cutoff_date:
                            import shutil
                            shutil.rmtree(item)
                            logger.info(f"Removed old backup: {item.name}")
                    except (ValueError, OSError):
                        # Remove directories that don't match expected format
                        try:
                            shutil.rmtree(item)
                        except:
                            pass

        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")

    def get_update_history(self) -> List[Dict]:
        """Get history of database updates."""
        try:
            backup_dir = os.path.join(self.clamav_dir, 'backup')
            if not os.path.exists(backup_dir):
                return []

            history = []
            for item in Path(backup_dir).iterdir():
                if item.is_dir() and item.name.startswith('db_backup_'):
                    try:
                        timestamp_str = item.name.replace('db_backup_', '')
                        backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                        history.append({
                            'timestamp': backup_date.isoformat(),
                            'backup_path': str(item),
                            'formatted_date': backup_date.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except ValueError:
                        continue

            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x['timestamp'], reverse=True)
            return history

        except Exception as e:
            logger.error(f"Error getting update history: {e}")
            return []


class EnhancedUpdateThread(QThread):
    """Enhanced thread for database updates with incremental support."""
    update_output = Signal(str)
    update_progress = Signal(int)
    finished = Signal(bool, str)

    def __init__(self, updater: EnhancedVirusDBUpdater):
        super().__init__()
        self.updater = updater

    def run(self):
        """Run the enhanced database update process."""
        try:
            self.update_output.emit("Starting enhanced database update...")

            # Perform incremental update
            success, message = self.updater.perform_incremental_update()

            if success:
                self.update_output.emit(f"Update completed: {message}")
                self.update_progress.emit(100)
            else:
                self.update_output.emit(f"Update failed: {message}")
                self.update_progress.emit(0)

            self.finished.emit(success, message)

        except Exception as e:
            self.update_output.emit(f"Update error: {str(e)}")
            self.finished.emit(False, str(e))
