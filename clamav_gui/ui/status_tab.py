"""Status tab for ClamAV GUI application showing system and database information."""
import os
import subprocess
import logging
import re
from datetime import datetime
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QTextEdit, QPushButton, QMessageBox)

logger = logging.getLogger(__name__)

class StatusTab(QWidget):
    """Status tab widget showing ClamAV system and database information."""

    def __init__(self, parent=None):
        """Initialize the status tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # ClamAV Information group
        info_group = QGroupBox(self.tr("ClamAV Information"))
        info_layout = QVBoxLayout()

        # Information display
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(300)
        info_layout.addWidget(self.info_text)

        # Action buttons layout (side by side)
        buttons_layout = QHBoxLayout()

        refresh_btn = QPushButton(self.tr("Refresh Status"))
        refresh_btn.clicked.connect(self.refresh_status_info)
        buttons_layout.addWidget(refresh_btn)

        update_db_btn = QPushButton(self.tr("Update Database"))
        update_db_btn.clicked.connect(self.update_database)
        buttons_layout.addWidget(update_db_btn)

        info_layout.addLayout(buttons_layout)
        info_group.setLayout(info_layout)

        # Add group to main layout
        layout.addWidget(info_group)
        layout.addStretch()

        # Schedule initial refresh after a short delay to ensure controls are initialized
        QtCore.QTimer.singleShot(100, self.refresh_status_info)

    def refresh_status_info(self):
        """Refresh and display ClamAV status information."""
        try:
            # Check if control exists before using it
            if not hasattr(self, 'info_text'):
                logger.warning("Info control not initialized yet")
                return

            # Get ClamAV version
            version_info = self._get_clamav_version()

            # Get virus database information
            db_info = self._get_database_info()

            # Get system information
            system_info = self._get_system_info()

            # Get ClamAV paths from settings
            clamav_paths = self._get_clamav_paths()

            # Check if ClamAV is available
            clamav_available = version_info.get('version', '').startswith('ClamAV')

            # Debug: Print what we got
            print(f"StatusTab DEBUG: Version info - {version_info}")
            print(f"StatusTab DEBUG: Database info - {db_info}")
            print(f"StatusTab DEBUG: System info - {system_info}")
            print(f"StatusTab DEBUG: ClamAV paths - {clamav_paths}")
            print(f"StatusTab DEBUG: ClamAV available - {clamav_available}")

            # Format information in a clean, organized way
            info_text = f"""Information:
==================

📋 Version Information:
   • ClamAV Version: {version_info.get('version', 'Unknown')}
   • Engine Version: {version_info.get('engine_version', 'Not available')}
   • Platform: {version_info.get('platform', 'Not available')}
   • Build Date: {version_info.get('build_date', 'Not available')}

🗃️ Database Information:
   • Database Path: {db_info.get('database_path', 'Unknown')}
   • Total Signatures: {db_info.get('total_signatures', 'Unknown')}
   • Database Version: {db_info.get('database_version', 'Unknown')}
   • Last Update: {db_info.get('last_update', 'Unknown')}

💻 System Information:
   • Operating System: {system_info.get('os_version', 'Unknown')}
   • Python Version: {system_info.get('python_version', 'Unknown')}
   • App Version: {system_info.get('app_version', 'Unknown')}

🔧 ClamAV Paths:
   • ClamScan Path: {clamav_paths.get('clamscan_path', 'Not configured')}
   • FreshClam Path: {clamav_paths.get('freshclam_path', 'Not configured')}
   • ClamD Path: {clamav_paths.get('clamd_path', 'Not configured')}

🔄 Status: {'✅ ClamAV detected and ready' if clamav_available else '⚠️ ClamAV not found - Please install ClamAV or check paths in Settings'}
"""

            self.info_text.setPlainText(info_text.strip())

        except Exception as e:
            error_msg = f"❌ Error retrieving ClamAV status: {str(e)}"
            if hasattr(self, 'info_text'):
                self.info_text.setPlainText(error_msg)
            logger.error(error_msg)

    def _get_clamav_version(self):
        """Get ClamAV version information."""
        info = {
            'version': 'ClamAV not found - Please install ClamAV',
            'engine_version': 'Not available',
            'platform': 'Not available',
            'build_date': 'Not available'
        }

        try:
            # Get clamscan path from parent settings
            if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
                clamscan_path = self.parent.current_settings.get('clamscan_path', 'clamscan')
                print(f"StatusTab DEBUG: Using current_settings: {clamscan_path}")
            elif hasattr(self.parent, 'settings') and self.parent.settings:
                settings = self.parent.settings.load_settings() or {}
                clamscan_path = settings.get('clamscan_path', 'clamscan')
                print(f"StatusTab DEBUG: Using settings.load_settings(): {clamscan_path}")
            else:
                # Try to get from SettingsTab if it exists
                if hasattr(self.parent, 'settings_tab') and self.parent.settings_tab:
                    settings = self.parent.settings_tab.get_settings()
                    clamscan_path = settings.get('clamscan_path', 'clamscan')
                    print(f"StatusTab DEBUG: Using settings_tab.get_settings(): {clamscan_path}")
                else:
                    clamscan_path = 'clamscan'
                    print(f"StatusTab DEBUG: Using default 'clamscan'")

            if not clamscan_path:
                clamscan_path = 'clamscan'
                print(f"StatusTab DEBUG: clamscan_path was empty, using default")

            print(f"StatusTab DEBUG: Final clamscan_path: '{clamscan_path}'")

            # Check if clamscan exists
            if not os.path.exists(clamscan_path) and clamscan_path != 'clamscan':
                info['version'] = f"ClamAV executable not found at: {clamscan_path}"
                info['engine_version'] = 'Configure ClamAV path in Settings'
                info['platform'] = 'Configure ClamAV path in Settings'
                info['build_date'] = 'Configure ClamAV path in Settings'
                return info

            # Run clamscan --version
            process = subprocess.run([clamscan_path, '--version'],
                                   capture_output=True, text=True, timeout=10)

            if process.returncode == 0:
                output = process.stdout.strip()
                lines = output.split('\n')

                # Debug: Print actual ClamAV output
                print(f"StatusTab DEBUG: ClamAV version output: '{output}'")
                print(f"StatusTab DEBUG: ClamAV version lines: {lines}")

                if lines:
                    # Parse the version output - typical format:
                    # "ClamAV 1.3.0/26987/Mon Jan 15 08:30:00 2024"

                    # First line contains main version info
                    first_line = lines[0].strip()
                    print(f"StatusTab DEBUG: First line: '{first_line}'")

                    if 'ClamAV' in first_line:
                        # Extract main version - improved parsing
                        parts = first_line.split()
                        print(f"StatusTab DEBUG: Split parts: {parts}")
                        for i, part in enumerate(parts):
                            if 'ClamAV' in part and i + 1 < len(parts):
                                # Version is typically the next part after "ClamAV"
                                version_part = parts[i + 1]
                                print(f"StatusTab DEBUG: Version part: '{version_part}'")

                                # Handle different version formats
                                if '/' in version_part:
                                    # Format: "1.3.0/26987/Mon Jan 15 08:30:00 2024"
                                    version_components = version_part.split('/')
                                    print(f"StatusTab DEBUG: Version components: {version_components}")
                                    if len(version_components) >= 1:
                                        info['engine_version'] = version_components[0]  # "1.3.0"
                                        if len(version_components) >= 2:
                                            # Build number (signature count)
                                            build_num = version_components[1]
                                            if build_num.isdigit():
                                                info['version'] = f"ClamAV {version_components[0]} (Build {build_num})"
                                            else:
                                                info['version'] = f"ClamAV {version_components[0]}"
                                        if len(version_components) >= 3:
                                            # Build date
                                            info['build_date'] = version_components[2]
                                            if len(version_components) >= 4:
                                                # Additional date parts
                                                info['build_date'] += f" {version_components[3]} {version_components[4]}"
                                    else:
                                        info['version'] = f"ClamAV {version_part}"
                                else:
                                    # Format: "1.5.0-rc" or "1.5.0"
                                    info['version'] = f"ClamAV {version_part}"
                                    info['engine_version'] = version_part
                                    print(f"StatusTab DEBUG: Simple version format detected: {version_part}")
                                break

                    # Look for platform information in all lines (improved detection)
                    for line in lines:
                        line_lower = line.strip().lower()
                        print(f"StatusTab DEBUG: Checking line for platform: '{line_lower}'")
                        if any(keyword in line_lower for keyword in ['platform', 'compiled', 'built', 'target']):
                            # Extract platform info
                            if 'windows' in line_lower or 'mingw' in line_lower or 'msvc' in line_lower:
                                info['platform'] = 'Windows'
                                print(f"StatusTab DEBUG: Detected Windows platform")
                                break
                            elif 'linux' in line_lower:
                                info['platform'] = 'Linux'
                                print(f"StatusTab DEBUG: Detected Linux platform")
                                break
                            elif 'darwin' in line_lower or 'macos' in line_lower or 'apple' in line_lower:
                                info['platform'] = 'macOS'
                                print(f"StatusTab DEBUG: Detected macOS platform")
                                break
                            elif 'freebsd' in line_lower:
                                info['platform'] = 'FreeBSD'
                                print(f"StatusTab DEBUG: Detected FreeBSD platform")
                                break
                            elif 'solaris' in line_lower or 'sun' in line_lower:
                                info['platform'] = 'Solaris'
                                print(f"StatusTab DEBUG: Detected Solaris platform")
                                break

                        # Also check for build date in any line
                        if any(month in line_lower for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                                               'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            # This line might contain build date
                            date_parts = line.split()
                            for part in date_parts:
                                if any(month in part.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                                                         'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                                    if not info['build_date'] or info['build_date'] == 'Not available':
                                        info['build_date'] = part
                                        print(f"StatusTab DEBUG: Found build date: '{part}'")
                                    break

                if info['version'] == 'ClamAV not found - Please install ClamAV':
                    info['version'] = f"ClamAV found: {clamscan_path}"

                # If platform is still not detected, try to determine from system
                if info['platform'] == 'Not available':
                    try:
                        import platform
                        system = platform.system().lower()
                        if 'windows' in system:
                            info['platform'] = 'Windows'
                        elif 'linux' in system:
                            info['platform'] = 'Linux'
                        elif 'darwin' in system:
                            info['platform'] = 'macOS'
                        elif 'freebsd' in system:
                            info['platform'] = 'FreeBSD'
                        print(f"StatusTab DEBUG: Fallback platform detection: {info['platform']}")
                    except Exception:
                        pass

            else:
                print(f"StatusTab DEBUG: ClamAV command failed with return code {process.returncode}")
                print(f"StatusTab DEBUG: stderr: '{process.stderr.strip()}'")
                info['version'] = f"Error running clamscan: {process.stderr.strip()}"
                info['engine_version'] = 'Check ClamAV installation'
                info['platform'] = 'Check ClamAV installation'
                info['build_date'] = 'Check ClamAV installation'

        except FileNotFoundError:
            info['version'] = f"ClamAV not found - Please install ClamAV or check the path in Settings"
            info['engine_version'] = 'Install ClamAV'
            info['platform'] = 'Install ClamAV'
            info['build_date'] = 'Install ClamAV'
        except subprocess.TimeoutExpired:
            info['version'] = "ClamAV command timed out - Please check installation"
            info['engine_version'] = 'Check ClamAV installation'
            info['platform'] = 'Check ClamAV installation'
            info['build_date'] = 'Check ClamAV installation'
        except subprocess.CalledProcessError as e:
            info['version'] = f"Error running ClamAV: {e}"
            info['engine_version'] = 'Check ClamAV installation'
            info['platform'] = 'Check ClamAV installation'
            info['build_date'] = 'Check ClamAV installation'
        except Exception as e:
            logger.error(f"Error getting ClamAV version: {e}")
            info['version'] = f"Unexpected error: {str(e)}"
            info['engine_version'] = 'Check system configuration'
            info['platform'] = 'Check system configuration'
            info['build_date'] = 'Check system configuration'

        return info

    def _get_database_info(self):
        """Get virus database information including signature count."""
        info = {
            'database_path': 'Database not accessible',
            'total_signatures': 'Database not accessible',
            'database_version': 'Database not accessible',
            'last_update': 'Database not accessible'
        }

        try:
            # Try multiple methods to find ClamAV database directory
            db_dir = self._find_database_directory()

            print(f"StatusTab DEBUG: Database directory found: '{db_dir}'")

            if db_dir and os.path.exists(db_dir):
                info['database_path'] = db_dir

                # Check for database files
                db_files = [f for f in os.listdir(db_dir) if f.endswith('.cvd') or f.endswith('.cld')]
                print(f"StatusTab DEBUG: Database files found: {db_files}")

                if db_files:
                    # Try to get signature count using multiple methods
                    sig_count = self._get_signature_count(db_dir, db_files)
                    if sig_count:
                        info['total_signatures'] = str(sig_count)
                        print(f"StatusTab DEBUG: Signature count: {sig_count}")
                    else:
                        print(f"StatusTab DEBUG: Signature count could not be determined")

                    # Get database version from file names or info
                    db_version = self._get_database_version(db_dir, db_files)
                    if db_version:
                        info['database_version'] = db_version
                        print(f"StatusTab DEBUG: Database version: {db_version}")
                    else:
                        print(f"StatusTab DEBUG: Database version could not be determined")

                    # Get last update time
                    last_update = self._get_last_update_time(db_dir, db_files)
                    if last_update:
                        info['last_update'] = last_update.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"StatusTab DEBUG: Last update: {info['last_update']}")
                    else:
                        print(f"StatusTab DEBUG: Last update could not be determined")

                    # Try to get more accurate signature count using freshclam info
                    accurate_count = self._get_accurate_signature_count(db_dir)
                    if accurate_count:
                        info['total_signatures'] = str(accurate_count)
                        print(f"StatusTab DEBUG: Using accurate signature count: {accurate_count}")
                    elif sig_count:
                        # Keep the original count if no accurate count found
                        info['total_signatures'] = str(sig_count)
                        print(f"StatusTab DEBUG: Using estimated signature count: {sig_count}")
                    else:
                        info['total_signatures'] = 'Unknown'
                        print(f"StatusTab DEBUG: Signature count unknown")

                else:
                    info['total_signatures'] = 'No database files found'
                    info['database_version'] = 'No database files found'
                    info['last_update'] = 'No database files found'
                    print(f"StatusTab DEBUG: No database files found in directory")
            else:
                info['database_path'] = 'Database directory not found - Check ClamAV installation'
                info['total_signatures'] = 'Configure ClamAV paths in Settings'
                info['database_version'] = 'Configure ClamAV paths in Settings'
                info['last_update'] = 'Configure ClamAV paths in Settings'
                print(f"StatusTab DEBUG: Database directory not found")

        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            info['total_signatures'] = f'Error accessing database: {str(e)}'
            info['database_version'] = f'Error accessing database: {str(e)}'
            info['last_update'] = f'Error accessing database: {str(e)}'
            print(f"StatusTab DEBUG: Error getting database info: {e}")

        return info

    def _find_database_directory(self):
        """Find the ClamAV database directory using multiple methods."""
        # Method 1: Check common Windows installation paths
        common_paths = [
            r'C:\ProgramData\ClamAV\db',
            r'C:\Program Files\ClamAV\db',
            r'C:\ClamAV\db',
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        # Method 2: Check APPDATA if it exists (for user-specific installations)
        try:
            app_data = os.getenv('APPDATA')
            if app_data:
                user_paths = [
                    os.path.join(app_data, 'ClamAV', 'database'),
                    os.path.join(app_data, '.clamav', 'database'),
                    os.path.join(app_data, 'clamav', 'database'),
                ]
                for path in user_paths:
                    if os.path.exists(path):
                        return path
        except Exception:
            pass

        # Method 3: Check ProgramData (system-wide app data)
        try:
            program_data = os.getenv('PROGRAMDATA')
            if program_data:
                system_paths = [
                    os.path.join(program_data, 'ClamAV', 'database'),
                    os.path.join(program_data, 'clamav', 'database'),
                ]
                for path in system_paths:
                    if os.path.exists(path):
                        return path
        except Exception:
            pass

        # Method 4: Try to detect from clamscan location if available
        try:
            # Get clamscan path from parent settings
            if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
                clamscan_path = self.parent.current_settings.get('clamscan_path', 'clamscan')
            elif hasattr(self.parent, 'settings') and self.parent.settings:
                settings = self.parent.settings.load_settings() or {}
                clamscan_path = settings.get('clamscan_path', 'clamscan')
            else:
                clamscan_path = 'clamscan'

            if clamscan_path and clamscan_path != 'clamscan':
                clamscan_dir = os.path.dirname(clamscan_path)
                if clamscan_dir and clamscan_dir != '.':
                    # Assume database is in same directory or subdirectory
                    possible_db_paths = [
                        os.path.join(clamscan_dir, 'database'),
                        os.path.join(os.path.dirname(clamscan_dir), 'database'),
                        os.path.join(clamscan_dir, '..', 'database'),
                        os.path.join(clamscan_dir, 'share', 'clamav'),
                    ]
                    for path in possible_db_paths:
                        if os.path.exists(path):
                            return path
        except Exception:
            pass

        # Method 5: Check common Linux/Unix paths (if running on non-Windows)
        if os.name != 'nt':
            unix_paths = [
                '/var/lib/clamav',
                '/usr/share/clamav',
                '/usr/local/share/clamav',
                '/opt/clamav/share/clamav',
            ]
            for path in unix_paths:
                if os.path.exists(path):
                    return path

        return None

    def _get_signature_count(self, db_dir, db_files):
        """Get signature count using multiple methods."""
        # Method 1: Try sigtool --info
        try:
            sigtool_path = self._find_sigtool()
            if sigtool_path:
                process = subprocess.run([sigtool_path, '--info', db_dir],
                                       capture_output=True, text=True, timeout=10,
                                       cwd=db_dir)
                if process.returncode == 0:
                    for line in process.stdout.split('\n'):
                        if 'signatures' in line.lower():
                            parts = line.split(':')
                            if len(parts) > 1:
                                sig_count = parts[1].strip().split()[0]
                                if sig_count.isdigit():
                                    return int(sig_count)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Method 2: Try sigtool --info (more reliable for signature count)
        try:
            # Get sigtool path
            sigtool_path = self._find_sigtool()

            if sigtool_path:
                print(f"StatusTab DEBUG: Running sigtool --info with path: {sigtool_path}")
                process = subprocess.run([sigtool_path, '--info', db_dir],
                                       capture_output=True, text=True, timeout=30,
                                       cwd=db_dir)
                if process.returncode == 0:
                    output = process.stdout.strip()
                    print(f"StatusTab DEBUG: sigtool --info output: '{output}'")
                    # Extract the number from output (sigtool --info typically outputs signature info)
                    numbers = re.findall(r'\d+', output)
                    if numbers:
                        sig_count = int(numbers[0])
                        if sig_count > 100000:  # Reasonable signature count
                            print(f"StatusTab DEBUG: sigtool --info returned {sig_count} signatures")
                            return sig_count
                else:
                    print(f"StatusTab DEBUG: sigtool --info failed with return code {process.returncode}")
                    print(f"StatusTab DEBUG: stderr: {process.stderr.strip()}")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"StatusTab DEBUG: Error running sigtool --info: {e}")
            pass

        # Method 3: Try to get signature count from CVD file headers (more accurate)
        print(f"StatusTab DEBUG: Trying to get signature count from CVD headers")
        for db_file in db_files:
            if db_file.endswith('.cvd'):
                db_path = os.path.join(db_dir, db_file)
                try:
                    with open(db_path, 'rb') as f:
                        # CVD format: signature count is typically at offset 512-516 (4 bytes, little endian)
                        f.seek(512, 0)
                        header_data = f.read(16)
                        # Look for 4-byte signature count (little endian)
                        for i in range(len(header_data) - 3):
                            if all(32 <= header_data[j] <= 126 or header_data[j] == 0 for j in range(4)):  # Printable ASCII or null
                                count_bytes = header_data[i:i+4]
                                if len(count_bytes) == 4:
                                    # Try to decode as little-endian integer
                                    count = int.from_bytes(count_bytes, byteorder='little', signed=False)
                                    if 1000000 <= count <= 20000000:  # Reasonable range for signature count
                                        print(f"StatusTab DEBUG: Found signature count in {db_file}: {count}")
                                        return count
                except Exception as e:
                    print(f"StatusTab DEBUG: Error reading {db_file}: {e}")
                    continue

        # Method 4: Count files as rough estimate (improved)
        total_files = len([f for f in db_files if f.endswith('.cvd') or f.endswith('.cld')])
        if total_files > 0:
            # More accurate estimate based on file types
            cvd_count = len([f for f in db_files if f.endswith('.cvd')])
            cld_count = len([f for f in db_files if f.endswith('.cld')])

            # CVD files typically contain ~2-4M signatures each
            # CLD files typically contain ~100K-500K signatures each
            # Daily database usually has the most signatures
            estimated_sigs = (cvd_count * 3000000) + (cld_count * 200000)

            print(f"StatusTab DEBUG: Estimated signature count: {estimated_sigs} (CVD: {cvd_count}, CLD: {cld_count})")
            if estimated_sigs > 0:
                return estimated_sigs

        return None

    def _get_database_version(self, db_dir, db_files):
        """Get database version from CVD files."""
        versions = []

        # First try to get version from main.cvd (most important)
        main_cvd = os.path.join(db_dir, 'main.cvd')
        if os.path.exists(main_cvd):
            try:
                with open(main_cvd, 'rb') as f:
                    # CVD format has version info in header
                    header = f.read(512)
                    header_str = header.decode('latin-1', errors='ignore')
                    if 'ClamAV-VDB:' in header_str:
                        version_start = header_str.find('ClamAV-VDB:') + 11
                        version_end = header_str.find('\0', version_start)
                        if version_end > version_start:
                            version = header_str[version_start:version_end].strip()
                            if version:
                                versions.append(f"main: {version}")
                                print(f"StatusTab DEBUG: Found main database version: {version}")
            except (IOError, OSError) as e:
                print(f"StatusTab DEBUG: Error reading main.cvd: {e}")

        # Then try daily.cvd
        daily_cvd = os.path.join(db_dir, 'daily.cvd')
        if os.path.exists(daily_cvd):
            try:
                with open(daily_cvd, 'rb') as f:
                    header = f.read(512)
                    header_str = header.decode('latin-1', errors='ignore')
                    if 'ClamAV-VDB:' in header_str:
                        version_start = header_str.find('ClamAV-VDB:') + 11
                        version_end = header_str.find('\0', version_start)
                        if version_end > version_start:
                            version = header_str[version_start:version_end].strip()
                            if version:
                                versions.append(f"daily: {version}")
                                print(f"StatusTab DEBUG: Found daily database version: {version}")
            except (IOError, OSError) as e:
                print(f"StatusTab DEBUG: Error reading daily.cvd: {e}")

        # Fallback: extract version from filename
        for db_file in db_files:
            if '.cvd' in db_file or '.cld' in db_file:
                # Extract version from filename like "daily.cvd" or "main.cvd"
                name_part = db_file.replace('.cvd', '').replace('.cld', '')
                if name_part and not name_part.isdigit():
                    if name_part not in [v.split(': ')[0] for v in versions]:
                        versions.append(name_part)
                        print(f"StatusTab DEBUG: Using filename for version: {name_part}")

        if versions:
            return ', '.join(versions)
        else:
            return 'Unknown'

    def _get_accurate_signature_count(self, db_dir):
        """Get accurate signature count using sigtool --info or similar."""
        try:
            # Try to get sigtool path from settings
            if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
                sigtool_path = self.parent.current_settings.get('sigtool_path', 'sigtool')
            elif hasattr(self.parent, 'settings') and self.parent.settings:
                settings = self.parent.settings.load_settings() or {}
                sigtool_path = settings.get('sigtool_path', 'sigtool')
            else:
                sigtool_path = 'sigtool'

            if not sigtool_path or sigtool_path == 'sigtool':
                # Try to find sigtool in PATH
                sigtool_path = self._find_sigtool_executable()

            if sigtool_path and os.path.exists(sigtool_path):
                print(f"StatusTab DEBUG: Running sigtool to get signature info: {sigtool_path}")
                # Try sigtool --info with database directory as argument
                process = subprocess.run([sigtool_path, '--info', db_dir],
                                       capture_output=True, text=True, timeout=30)
                if process.returncode == 0:
                    output = process.stdout.strip()
                    print(f"StatusTab DEBUG: sigtool --info output: {output}")
                    # Look for signature count in output
                    for line in output.split('\n'):
                        line_lower = line.lower()
                        if 'signatures' in line_lower or 'total' in line_lower:
                            # Try to extract number
                            numbers = re.findall(r'\d+', line)
                            if numbers:
                                count = int(numbers[0])
                                if count > 1000000:  # Reasonable signature count
                                    print(f"StatusTab DEBUG: Found signature count in sigtool output: {count}")
                                    return count
                else:
                    print(f"StatusTab DEBUG: sigtool --info failed with return code {process.returncode}")
                    if process.stderr:
                        print(f"StatusTab DEBUG: stderr: {process.stderr.strip()}")

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"StatusTab DEBUG: Error running sigtool: {e}")

        # Alternative: try to read the total signature count from all CVD files
        try:
            total_count = 0
            for db_file in os.listdir(db_dir):
                if db_file.endswith('.cvd'):
                    db_path = os.path.join(db_dir, db_file)
                    try:
                        with open(db_path, 'rb') as f:
                            # Try different offsets for signature count
                            for offset in [512, 516, 520, 524]:
                                f.seek(offset, 0)
                                count_data = f.read(4)
                                if len(count_data) == 4:
                                    count = int.from_bytes(count_data, byteorder='little', signed=False)
                                    if 100000 <= count <= 10000000:  # Reasonable range
                                        total_count += count
                                        print(f"StatusTab DEBUG: Found {count} signatures in {db_file}")
                                        break
                    except Exception:
                        continue

            if total_count > 0:
                print(f"StatusTab DEBUG: Total signature count from CVD files: {total_count}")
                return total_count

        except Exception as e:
            print(f"StatusTab DEBUG: Error reading CVD files: {e}")

        return None

    def _find_freshclam_executable(self):
        """Find freshclam executable in common locations or PATH."""
        # Check if it's in PATH
        try:
            subprocess.run(['freshclam', '--version'],
                         capture_output=True, timeout=5)
            return 'freshclam'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check common installation paths
        common_paths = [
            r'C:\Program Files\ClamAV\freshclam.exe',
            r'C:\Program Files (x86)\ClamAV\freshclam.exe',
            r'C:\ClamAV\freshclam.exe',
            'freshclam'  # Check PATH again
        ]

        for path in common_paths:
            if path == 'freshclam':
                try:
                    subprocess.run([path, '--version'],
                                 capture_output=True, timeout=5)
                    return path
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            elif os.path.exists(path):
                return path

        return None

    def _get_last_update_time(self, db_dir, db_files):
        """Get the last update time from the most recently modified database file."""
        if not db_files:
            return None

        latest_time = 0
        latest_file = None

        for db_file in db_files:
            db_path = os.path.join(db_dir, db_file)
            try:
                mod_time = os.path.getmtime(db_path)
                if mod_time > latest_time:
                    latest_time = mod_time
                    latest_file = db_path
            except (OSError, IOError):
                continue

        if latest_file:
            return datetime.fromtimestamp(latest_time)

        return None

    def _find_clamscan_executable(self):
        """Find clamscan executable in common locations or PATH."""
        # Check if it's in PATH
        try:
            subprocess.run(['clamscan', '--version'],
                         capture_output=True, timeout=5)
            return 'clamscan'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check common installation paths
        common_paths = [
            r'C:\Program Files\ClamAV\clamscan.exe',
            r'C:\Program Files (x86)\ClamAV\clamscan.exe',
            r'C:\ClamAV\clamscan.exe',
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def _find_sigtool(self):
        """Find the sigtool executable."""
        # First try to derive from clamscan path if available
        if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
            clamscan_path = self.parent.current_settings.get('clamscan_path', 'clamscan')
        elif hasattr(self.parent, 'settings') and self.parent.settings:
            settings = self.parent.settings.load_settings() or {}
            clamscan_path = settings.get('clamscan_path', 'clamscan')
        else:
            clamscan_path = 'clamscan'

        if clamscan_path and clamscan_path != 'clamscan':
            sigtool_path = clamscan_path.replace('clamscan', 'sigtool')
            if os.path.exists(sigtool_path):
                return sigtool_path

        # Check common installation paths
        common_paths = [
            r'C:\Program Files\ClamAV\sigtool.exe',
            r'C:\Program Files (x86)\ClamAV\sigtool.exe',
            r'C:\ClamAV\sigtool.exe',
            'sigtool'  # Check PATH
        ]

        for path in common_paths:
            if path == 'sigtool':
                # Check if in PATH
                try:
                    subprocess.run([path, '--version'],
                                 capture_output=True, timeout=5)
                    return path
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            elif os.path.exists(path):
                return path

        # Last resort: use the dedicated finder method
        return self._find_sigtool_executable()

    def _find_sigtool_executable(self):
        """Find sigtool executable in common locations or PATH."""
        # Check if it's in PATH
        try:
            subprocess.run(['sigtool', '--version'],
                         capture_output=True, timeout=5)
            return 'sigtool'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check common installation paths
        common_paths = [
            r'C:\Program Files\ClamAV\sigtool.exe',
            r'C:\Program Files (x86)\ClamAV\sigtool.exe',
            r'C:\ClamAV\sigtool.exe',
            'sigtool'  # Check PATH again
        ]

        for path in common_paths:
            if path == 'sigtool':
                try:
                    subprocess.run([path, '--version'],
                                 capture_output=True, timeout=5)
                    return path
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            elif os.path.exists(path):
                return path

        return None

    def _get_system_info(self):
        """Get system information including OS, Python, and app version."""
        info = {
            'app_version': 'Unknown',
            'os_version': 'Unknown',
            'python_version': 'Unknown'
        }

        try:
            # Get OS version
            try:
                import platform
                system = platform.system()
                release = platform.release()
                machine = platform.machine()

                # Create more detailed OS description
                if system == 'Windows':
                    info['os_version'] = f"Windows {release} ({machine})"
                elif system == 'Linux':
                    # Try to get distribution info
                    try:
                        import distro
                        dist = distro.name()
                        version = distro.version()
                        info['os_version'] = f"{dist} {version} ({machine})"
                    except ImportError:
                        info['os_version'] = f"Linux {release} ({machine})"
                elif system == 'Darwin':
                    info['os_version'] = f"macOS {release} ({machine})"
                else:
                    info['os_version'] = f"{system} {release} ({machine})"

                print(f"StatusTab DEBUG: OS detected: {info['os_version']}")
            except Exception as e:
                print(f"StatusTab DEBUG: Error getting OS info: {e}")

            # Get Python version
            try:
                import sys
                info['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                print(f"StatusTab DEBUG: Python version: {info['python_version']}")
            except Exception as e:
                print(f"StatusTab DEBUG: Error getting Python version: {e}")

            # Get app version
            try:
                from clamav_gui.utils.version import __version__
                info['app_version'] = __version__
                print(f"StatusTab DEBUG: App version: {info['app_version']}")
            except Exception as e:
                print(f"StatusTab DEBUG: Error getting app version: {e}")
                try:
                    # Try alternative import path
                    import clamav_gui
                    if hasattr(clamav_gui, '__version__'):
                        info['app_version'] = clamav_gui.__version__
                        print(f"StatusTab DEBUG: App version (alternative): {info['app_version']}")
                except Exception as e2:
                    print(f"StatusTab DEBUG: Error getting app version (alternative): {e2}")

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            print(f"StatusTab DEBUG: Error in system info: {e}")

        return info

    def _get_clamav_paths(self):
        """Get ClamAV executable paths from settings."""
        paths = {
            'clamscan_path': 'Not configured',
            'freshclam_path': 'Not configured',
            'clamd_path': 'Not configured'
        }

        try:
            # Get paths from parent settings
            if hasattr(self.parent, 'current_settings') and self.parent.current_settings:
                settings = self.parent.current_settings
                paths['clamscan_path'] = settings.get('clamscan_path', 'Not configured')
                paths['freshclam_path'] = settings.get('freshclam_path', 'Not configured')
                paths['clamd_path'] = settings.get('clamd_path', 'Not configured')
            elif hasattr(self.parent, 'settings') and self.parent.settings:
                # Fallback to load settings
                settings = self.parent.settings.load_settings() or {}
                paths['clamscan_path'] = settings.get('clamscan_path', 'Not configured')
                paths['freshclam_path'] = settings.get('freshclam_path', 'Not configured')
                paths['clamd_path'] = settings.get('clamd_path', 'Not configured')
            else:
                # Try to get from SettingsTab if it exists
                if hasattr(self.parent, 'settings_tab') and self.parent.settings_tab:
                    settings = self.parent.settings_tab.get_settings()
                    paths['clamscan_path'] = settings.get('clamscan_path', 'Not configured')
                    paths['freshclam_path'] = settings.get('freshclam_path', 'Not configured')
                    paths['clamd_path'] = settings.get('clamd_path', 'Not configured')
                else:
                    # Last resort: check if settings are available through other means
                    print(f"StatusTab DEBUG: No settings access method available")

        except Exception as e:
            logger.error(f"Error getting ClamAV paths: {e}")
            print(f"StatusTab DEBUG: Error getting paths: {e}")

        return paths

    def update_database(self):
        """Update the ClamAV virus database."""
        try:
            # Check if parent has the update_database method
            if not hasattr(self.parent, 'update_database'):
                error_msg = (
                    "❌ Update Database Not Available\n\n"
                    "The 'Update Database' functionality requires the full ClamAV GUI application.\n\n"
                    "Possible solutions:\n"
                    "• Use the 'Virus DB' tab instead (if available)\n"
                    "• Run 'freshclam' manually from command line\n"
                    "• Check if ClamAV is properly installed and configured\n"
                    "• Use the main ClamAV GUI application instead of this simplified version"
                )
                QMessageBox.warning(self, self.tr("Update Database Unavailable"), error_msg)
                return

            # Check if virus database updater is available
            if not hasattr(self.parent, 'virus_db_updater') or not self.parent.virus_db_updater:
                error_msg = (
                    "❌ Database Updater Not Initialized\n\n"
                    "The virus database updater is not properly initialized.\n\n"
                    "Please check that ClamAV is installed and configured correctly."
                )
                QMessageBox.warning(self, self.tr("Updater Not Ready"), error_msg)
                return

            # Show progress dialog
            self.progress_dialog = QMessageBox(self)
            self.progress_dialog.setWindowTitle(self.tr("Database Update"))
            self.progress_dialog.setText(self.tr("Starting database update..."))
            self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
            self.progress_dialog.setModal(True)

            # Create update output widget
            self.update_output_widget = QTextEdit()
            self.update_output_widget.setMaximumHeight(200)
            self.update_output_widget.setReadOnly(True)

            # Custom layout for progress dialog
            layout = QVBoxLayout()
            layout.addWidget(self.update_output_widget)
            layout.setContentsMargins(10, 10, 10, 10)

            # Create a container widget for the layout
            container = QWidget()
            container.setLayout(layout)

            # Add container to the message box layout
            main_layout = self.progress_dialog.layout()
            if main_layout:
                main_layout.addWidget(container, 1, 0)  # Add to second row, first column

            self.progress_dialog.show()

            # Connect to parent's update signals if they exist
            if hasattr(self.parent, 'update_update_output'):
                self.parent.update_update_output = self.update_update_output

            # Call parent's update method
            self.parent.update_database()

        except Exception as e:
            error_msg = f"❌ Update Failed\n\nError starting database update: {str(e)}\n\nPlease check the logs for more details."
            QMessageBox.critical(self, self.tr("Update Error"), error_msg)
            logger.error(f"Error in StatusTab.update_database: {e}")

    def update_update_output(self, text):
        """Update the progress dialog with new text."""
        if hasattr(self, 'update_output_widget') and self.update_output_widget:
            self.update_output_widget.append(text)
            # Scroll to bottom
            scrollbar = self.update_output_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # Update progress dialog text
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                # Extract status from text for better user feedback
                if "completed" in text.lower() or "success" in text.lower():
                    self.progress_dialog.setText(self.tr("Update completed successfully!"))
                elif "failed" in text.lower() or "error" in text.lower():
                    self.progress_dialog.setText(self.tr("Update failed. Check output below."))
                else:
                    self.progress_dialog.setText(self.tr("Updating database..."))

            # Process events to keep UI responsive
            QtWidgets.QApplication.processEvents()

    def closeEvent(self, event):
        """Handle close event to clean up resources."""
        # Clean up any running update threads
        if hasattr(self.parent, 'update_thread') and self.parent.update_thread:
            if self.parent.update_thread.isRunning():
                self.parent.update_thread.terminate()
                self.parent.update_thread.wait(3000)  # Wait up to 3 seconds

        event.accept()
