"""
Quarantine management for infected files in ClamAV GUI.
"""
import os
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class QuarantineManager:
    """Manages quarantined files from ClamAV scans."""

    def __init__(self, quarantine_dir: str = None):
        """Initialize the quarantine manager.

        Args:
            quarantine_dir: Directory to store quarantined files (default: user's Documents/ClamAV_Quarantine)
        """
        if quarantine_dir is None:
            home_dir = os.path.expanduser("~")
            self.quarantine_dir = os.path.join(home_dir, "Documents", "ClamAV_Quarantine")
        else:
            self.quarantine_dir = quarantine_dir

        self.metadata_file = os.path.join(self.quarantine_dir, "quarantine_metadata.json")
        self._ensure_quarantine_dir()

    def _ensure_quarantine_dir(self):
        """Ensure the quarantine directory exists."""
        try:
            os.makedirs(self.quarantine_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create quarantine directory: {e}")
            raise

    def _load_metadata(self) -> Dict:
        """Load quarantine metadata from file."""
        if not os.path.exists(self.metadata_file):
            return {"quarantined_files": {}, "total_quarantined": 0}

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load quarantine metadata: {e}")
            return {"quarantined_files": {}, "total_quarantined": 0}

    def _save_metadata(self, metadata: Dict):
        """Save quarantine metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save quarantine metadata: {e}")

    def quarantine_file(self, file_path: str, threat_name: str, scan_time: str = None) -> Tuple[bool, str]:
        """Quarantine an infected file.

        Args:
            file_path: Path to the infected file
            threat_name: Name of the threat detected
            scan_time: When the file was scanned (ISO format)

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"

        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"

        try:
            # Generate unique filename for quarantined file
            original_filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = self._calculate_file_hash(file_path)
            quarantined_filename = f"{timestamp}_{file_hash}_{original_filename}"
            quarantined_path = os.path.join(self.quarantine_dir, quarantined_filename)

            # Move file to quarantine
            shutil.move(file_path, quarantined_path)

            # Update metadata
            metadata = self._load_metadata()
            file_id = f"{file_hash}_{timestamp}"

            metadata["quarantined_files"][file_id] = {
                "original_path": file_path,
                "quarantined_path": quarantined_path,
                "original_filename": original_filename,
                "threat_name": threat_name,
                "scan_time": scan_time or datetime.now().isoformat(),
                "quarantine_time": datetime.now().isoformat(),
                "file_size": os.path.getsize(quarantined_path),
                "file_hash": file_hash
            }
            metadata["total_quarantined"] = len(metadata["quarantined_files"])

            self._save_metadata(metadata)

            logger.info(f"Quarantined file: {file_path} -> {quarantined_path}")
            return True, f"File quarantined successfully: {quarantined_filename}"

        except Exception as e:
            logger.error(f"Failed to quarantine file {file_path}: {e}")
            return False, f"Failed to quarantine file: {str(e)}"

    def restore_file(self, file_id: str) -> Tuple[bool, str]:
        """Restore a quarantined file.

        Args:
            file_id: ID of the quarantined file

        Returns:
            Tuple of (success: bool, message: str)
        """
        metadata = self._load_metadata()

        if file_id not in metadata["quarantined_files"]:
            return False, f"File not found in quarantine: {file_id}"

        file_info = metadata["quarantined_files"][file_id]
        quarantined_path = file_info["quarantined_path"]
        original_path = file_info["original_path"]

        try:
            # Ensure the original directory exists
            original_dir = os.path.dirname(original_path)
            if original_dir and not os.path.exists(original_dir):
                os.makedirs(original_dir, exist_ok=True)

            # Check if file already exists at original location
            if os.path.exists(original_path):
                # Create a restore directory if file exists
                restore_dir = os.path.join(original_dir, "restored_from_quarantine")
                os.makedirs(restore_dir, exist_ok=True)
                restored_path = os.path.join(restore_dir, file_info["original_filename"])

                # Add timestamp if there's a name conflict
                counter = 1
                while os.path.exists(restored_path):
                    name, ext = os.path.splitext(file_info["original_filename"])
                    restored_path = os.path.join(restore_dir, f"{name}_restored_{counter}{ext}")
                    counter += 1

                original_path = restored_path

            # Move file back
            shutil.move(quarantined_path, original_path)

            # Remove from metadata
            del metadata["quarantined_files"][file_id]
            metadata["total_quarantined"] = len(metadata["quarantined_files"])
            self._save_metadata(metadata)

            logger.info(f"Restored file: {quarantined_path} -> {original_path}")
            return True, f"File restored successfully: {original_path}"

        except Exception as e:
            logger.error(f"Failed to restore file {file_id}: {e}")
            return False, f"Failed to restore file: {str(e)}"

    def delete_quarantined_file(self, file_id: str) -> Tuple[bool, str]:
        """Permanently delete a quarantined file.

        Args:
            file_id: ID of the quarantined file

        Returns:
            Tuple of (success: bool, message: str)
        """
        metadata = self._load_metadata()

        if file_id not in metadata["quarantined_files"]:
            return False, f"File not found in quarantine: {file_id}"

        file_info = metadata["quarantined_files"][file_id]
        quarantined_path = file_info["quarantined_path"]

        try:
            # Delete the file
            if os.path.exists(quarantined_path):
                os.remove(quarantined_path)

            # Remove from metadata
            del metadata["quarantined_files"][file_id]
            metadata["total_quarantined"] = len(metadata["quarantined_files"])
            self._save_metadata(metadata)

            logger.info(f"Deleted quarantined file: {quarantined_path}")
            return True, f"File deleted successfully: {file_info['original_filename']}"

        except Exception as e:
            logger.error(f"Failed to delete quarantined file {file_id}: {e}")
            return False, f"Failed to delete file: {str(e)}"

    def list_quarantined_files(self) -> List[Dict]:
        """List all quarantined files with their metadata.

        Returns:
            List of dictionaries containing file information
        """
        metadata = self._load_metadata()
        return list(metadata["quarantined_files"].values())

    def get_quarantine_stats(self) -> Dict:
        """Get statistics about quarantined files.

        Returns:
            Dictionary with quarantine statistics
        """
        metadata = self._load_metadata()
        quarantined_files = metadata["quarantined_files"]

        if not quarantined_files:
            return {
                "total_quarantined": 0,
                "total_size": 0,
                "oldest_file": None,
                "newest_file": None,
                "threat_types": []
            }

        # Calculate total size - handle files that might not have file_size field
        total_size = 0
        for file_info in quarantined_files.values():
            file_size = file_info.get("file_size", 0)
            # If file_size is not available, try to get it from the actual file if it exists
            if file_size == 0:
                quarantined_path = file_info.get("quarantined_path", "")
                if quarantined_path and os.path.exists(quarantined_path):
                    try:
                        file_size = os.path.getsize(quarantined_path)
                    except (OSError, IOError):
                        file_size = 0
            total_size += file_size

        # Find oldest and newest files - handle files that might not have quarantine_time field
        quarantine_times = []
        for file_info in quarantined_files.values():
            quarantine_time_str = file_info.get("quarantine_time")
            if quarantine_time_str:
                try:
                    quarantine_times.append(quarantine_time_str)
                except (ValueError, TypeError):
                    pass  # Skip invalid timestamps
        oldest_time = min(quarantine_times) if quarantine_times else None
        newest_time = max(quarantine_times) if quarantine_times else None

        # Get unique threat types - handle files that might not have threat_name field
        threat_types = []
        for file_info in quarantined_files.values():
            threat_name = file_info.get("threat_name", "Unknown")
            if threat_name not in threat_types:
                threat_types.append(threat_name)

        return {
            "total_quarantined": len(quarantined_files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file": oldest_time,
            "newest_file": newest_time,
            "threat_types": sorted(threat_types)
        }

    def cleanup_old_files(self, days_old: int = 30) -> Tuple[int, str]:
        """Clean up quarantined files older than specified days.

        Args:
            days_old: Number of days after which files should be deleted

        Returns:
            Tuple of (files_deleted: int, message: str)
        """
        metadata = self._load_metadata()
        quarantined_files = metadata["quarantined_files"]

        if not quarantined_files:
            return 0, "No quarantined files to clean up"

        cutoff_date = datetime.now()
        files_to_delete = []
        files_deleted = 0

        for file_id, file_info in quarantined_files.items():
            quarantine_time = datetime.fromisoformat(file_info["quarantine_time"])

            if (cutoff_date - quarantine_time).days >= days_old:
                files_to_delete.append(file_id)

        # Delete the files
        for file_id in files_to_delete:
            success, _ = self.delete_quarantined_file(file_id)
            if success:
                files_deleted += 1

        return files_deleted, f"Cleaned up {files_deleted} quarantined files older than {days_old} days"

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            hash_obj = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()[:16]  # Use first 16 characters for shorter ID
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return "unknown"

    def export_quarantine_list(self, export_path: str) -> bool:
        """Export the list of quarantined files to a file.

        Args:
            export_path: Path to save the export file

        Returns:
            True if successful, False otherwise
        """
        try:
            quarantined_files = self.list_quarantined_files()

            export_data = {
                "export_time": datetime.now().isoformat(),
                "quarantine_stats": self.get_quarantine_stats(),
                "files": quarantined_files
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Failed to export quarantine list: {e}")
            return False
