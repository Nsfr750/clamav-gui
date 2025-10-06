"""
Version information for ClamAV GUI.
"""

# Version as a tuple (major, minor, patch)
VERSION = (1, 0, 0)

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
__date__ = "2025-09-25"

# Version description
__description__ = "A tool to find and manage duplicate PDF files on your computer."

# Dependencies
__requires__ = [
    "PySide6>=6.4.0",
    "PyMuPDF>=1.21.0",
    "wand>=0.6.10",
    "PyPDF2>=3.0.0",
    "pdf2image>=1.17.0",
    "imagehash>=4.3.1",
    "python-dotenv>=0.19.0",
    "tqdm>=4.64.0"
]

# Version as a tuple for comparison
version_info = tuple(map(int, __version__.split('.')))

# Changelog
__changelog__ = """
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
