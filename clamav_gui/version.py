"""
Version information for ClamAV GUI.
"""

# Version as a tuple (major, minor, patch)
VERSION = (1, 2, 5)

# String version
__version__ = ".".join(map(str, VERSION))

# Detailed version information
__status__ = "stable"
__author__ = "Nsfr750"
__maintainer__ = "Nsfr750"
__organization__ = 'Tuxxle'
__copyright__ = '© 2025 Nsfr750 - All Rights Reserved'
__email__ = "nsfr750@yandex.com"
__license__ = "GPL-3.0"

# Build information
__build__ = ""
__date__ = "2025-10-24"

# Version description
__description__ = "A modern PySide6-based graphical user interface for ClamAV Antivirus on Windows with enhanced scanning, reporting, and quarantine management."

# Dependencies
__requires__ = [
    "PySide6>=6.4.0",
    "PyMuPDF>=1.21.0",
    "wand>=0.6.10",
    "PyPDF2>=3.0.0",
    "pdf2image>=1.17.0",
    "imagehash>=4.3.1",
    "python-dotenv>=0.19.0",
    "tqdm>=4.64.0",
    "clamd>=1.0.2",
    "pyclamd>=0.4.0"
]

# Version as a tuple for comparison
version_info = tuple(map(int, __version__.split('.')))

# Changelog
__changelog__ = """
## [1.2.5] - 2025-10-24
### Added
- Database Configuration Section: Added visible database path configuration in settings tab
- Enhanced Database Path Detection: Improved automatic detection of ClamAV database location
- Settings Persistence: Database path now properly saved to settings.json

### Improved
- Settings Tab UI: Fixed missing Virus Database Configuration section visibility
- Database Path Management: Better integration between settings and database detection
- Configuration Loading: Enhanced loading of database settings from config files

## [1.2.0] - 2025-10-16
### Added
- Enhanced Log Viewer: Advanced log viewing with search, filtering, color coding, and statistics
- Config Editor Tab: Separate tab for editing ClamAV configuration files
- Advanced Scanning Menu: New menu with smart scanning, ML detection, email scanning, and batch analysis
- Help Menu Positioning: Moved Help menu to the right side of the menu bar for better UX

### Improved
- Menu Organization: Reorganized menu structure for better user experience
- Log Analysis: Comprehensive log viewer with filtering and search capabilities
- Configuration Management: Dedicated tab for editing configuration files

## [1.1.1] - 2025-10-15
### Added
- Enhanced UI styling for scan progress bar (animated blue gradient)
- Improved button styling with color-coded actions (green for start, red for stop)
- Better visual feedback for scan operations

### Improved
- Enhanced progress bar visualization with animated gradients
- Color-coded action buttons for better user experience
- Improved visual consistency across scan interface

## [1.1.0] - 2025-10-12
### Added
- Machine Learning Integration: AI-powered threat detection with feature extraction and ML models
- Error Recovery: Automatic retry mechanisms for failed operations with exponential backoff
- Advanced Reporting: Comprehensive analytics, threat intelligence, and export capabilities
- Sandbox Analysis: Behavioral analysis and system monitoring for suspicious files
- Email Scanning: Complete email scanning with .eml/.msg file support and attachment analysis
- Network Drive Scanning: UNC path support with network connectivity validation
- Enhanced Quarantine Management: Full restore/delete functionality with bulk operations and metadata display
- Async Scanning: Non-blocking UI during large scans with progress cancellation
- Smart Scanning: Skip known safe files using hash databases
- Incremental Updates: Differential virus database updates for faster downloads
- Enhanced error handling for missing ClamAV installation with auto-detection and installation guidance
- Comprehensive scan report generation with HTML and text formats
- Advanced quarantine management system for infected files
- Extended configuration options including performance settings and file patterns
- Real-time scan statistics and progress tracking
- Automatic infected file quarantine during scans

### Improved
- Better user feedback and error messages throughout the application
- Enhanced scan progress visualization and reporting
- More robust handling of corrupted or incomplete metadata
- Improved file pattern filtering and performance controls

## [1.0.0] - 2025-09-25
### Added
- Initial release
"""

def get_version():
    """Return the current version as a string."""
    return __version__

def get_version_info():
    """Return the version as a tuple for comparison."""
    return VERSION

def get_version_history():
    """Return the version history."""
    return [
        {
            "version": "1.2.5",
            "date": "2025-10-24",
            "changes": [
                "Database Configuration Section: Added visible database path configuration in settings tab",
                "Enhanced Database Path Detection: Improved automatic detection of ClamAV database location",
                "Settings Persistence: Database path now properly saved to settings.json",
                "Settings Tab UI: Fixed missing Virus Database Configuration section visibility",
                "Database Path Management: Better integration between settings and database detection",
                "Configuration Loading: Enhanced loading of database settings from config files"
            ]
        },
        {
            "version": "1.2.0",
            "date": "2025-10-16",
            "changes": [
                "Enhanced Log Viewer: Advanced log viewing with search, filtering, color coding, and statistics",
                "Config Editor Tab: Separate tab for editing ClamAV configuration files",
                "Advanced Scanning Menu: New menu with smart scanning, ML detection, email scanning, and batch analysis",
                "Help Menu Positioning: Moved Help menu to the right side of the menu bar for better UX",
                "Menu Organization: Reorganized menu structure for better user experience",
                "Log Analysis: Comprehensive log viewer with filtering and search capabilities",
                "Configuration Management: Dedicated tab for editing configuration files"
            ]
        },
        {
            "version": "1.1.1",
            "date": "2025-10-15",
            "changes": [
                "Enhanced UI styling for scan progress bar (animated blue gradient)",
                "Improved button styling with color-coded actions (green for start, red for stop)",
                "Better visual feedback for scan operations",
                "Enhanced progress bar visualization with animated gradients",
                "Color-coded action buttons for better user experience",
                "Improved visual consistency across scan interface"
            ]
        },
        {
            "version": "1.1.0",
            "date": "2025-10-12",
            "changes": [
                "Enhanced error handling for missing ClamAV installation with auto-detection and installation guidance",
                "Comprehensive scan report generation with HTML and text formats",
                "Advanced quarantine management system for infected files",
                "Extended configuration options including performance settings and file patterns",
                "Real-time scan statistics and progress tracking",
                "Automatic infected file quarantine during scans",
                "Better user feedback and error messages throughout the application",
                "Enhanced scan progress visualization and reporting",
                "More robust handling of corrupted or incomplete metadata",
                "Improved file pattern filtering and performance controls"
            ]
        },
        {
            "version": "1.0.0",
            "date": "2025-09-25",
            "changes": [
                "Initial release"
            ]
        },
    ]

def get_latest_changes():
    """Get the changes in the latest version."""
    if get_version_history():
        return get_version_history()[0]['changes']
    return []

def is_development():
    """Check if this is a development version."""
    return "dev" in __version__ or "a" in __version__ or "b" in __version__

def get_codename():
    """Get the codename for this version."""
    # Simple codename based on version number
    major, minor, patch = VERSION
    codenames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
    return codenames[minor % len(codenames)]
