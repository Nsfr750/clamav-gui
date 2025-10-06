# Project Structure

```text
clamav-gui/
├── assets/                     # Static assets (icons, images, etc.)
├── clamav_gui/                 # Main application package
│   ├── __init__.py             # Package initialization
│   ├── __main__.py             # Entry point when run as a module
│   ├── main_window.py          # Main window implementation
│   ├── version.py              # Version information
│   ├── lang/                   # Internationalization
│   │   ├── __init__.py         # Package initialization
│   │   ├── en_US.py            # English (US) translations
│   │   ├── it_IT.py            # Italian translations
│   │   └── lang_manager.py     # Language management
│   ├── ui/                     # UI components and windows
│   │   ├── __init__.py         # Package initialization
│   │   ├── UI.py               # Main UI components
│   │   ├── about.py            # About dialog
│   │   ├── help.py             # Help window
│   │   ├── menu.py             # Application menu
│   │   ├── settings.py         # Settings window
│   │   ├── sponsor.py          # Sponsor information
│   │   ├── updates_dialog.py   # Update dialog
│   │   └── updates_ui.py       # Update UI components
│   └── utils/                  # Utility modules
│       ├── __init__.py         # Package initialization
│       ├── updates.py          # Update checking functionality
│       └── virus_db.py         # Virus database management
│       └── version.py          # Version management
├── config/                     # Configuration files
├── docs/                       # Documentation
│   ├── CODE_OF_CONDUCT.md      # Community guidelines
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   ├── ROADMAP.md              # Project roadmap
│   ├── STRUCT.md               # Project structure (this file)
│   ├── USER_GUIDE.md           # User documentation
│   └── SECURITY.md             # Security policy
├── logs/                       # Application logs
├── .gitignore                  # Git ignore file
├── CHANGELOG.md                # Version history
├── LICENSE                     # GPLv3 License
├── README.md                   # Project documentation
├── TO_DO.md                    # Development tasks and ideas
├── build.py                    # Build script
├── clean_pycache.py            # Cleanup script
├── requirements.txt            # Python dependencies
├── setup.py                    # Installation script
└── version_info.txt            # Version metadata
```

## Key Components

### Core Application

- `__main__.py`: Entry point when running as a module
- `main_window.py`: Main application window and core functionality
- `version.py`: Version information and management

### User Interface

- `ui/UI.py`: Main UI components and layout
- `ui/about.py`: About dialog with version and author information
- `ui/help.py`: Help documentation viewer
- `ui/menu.py`: Application menu implementation
- `ui/settings.py`: Settings and preferences dialog
- `ui/sponsor.py`: Sponsor information and donation options
- `ui/updates_*.py`: Update checking and installation UI

### Internationalization

- `lang/`: Language files for internationalization
  - `en_US.py`: English (United States) translations
  - `it_IT.py`: Italian translations
  - `lang_manager.py`: Language management and switching

### Utilities

- `utils/updates.py`: Handles application and database updates
- `utils/virus_db.py`: Manages ClamAV virus database operations
- `utils/version.py`: Version checking and comparison utilities

### Build and Installation

- `setup.py`: Package installation and distribution
- `build.py`: Build script for creating distributions
- `clean_pycache.py`: Utility for cleaning Python cache files

## Dependencies

### Core Dependencies

- `PySide6`: Qt-based GUI framework
- `python-dotenv`: Environment variable management
- `pywin32`: Windows-specific functionality (Windows only)

### Development Dependencies

- `black`: Code formatter
- `pytest`: Testing framework
- `PyInstaller`: Application packaging

## Build and Run

### Installation

```bash
pip install -r requirements.txt
python -m clamav_gui
```

### Building

```bash
python build.py
```

## Documentation

- `docs/`: Contains all project documentation
  - `USER_GUIDE.md`: Comprehensive user manual
  - `CONTRIBUTING.md`: Guidelines for contributors
  - `ROADMAP.md`: Development roadmap and future plans
  - `CODE_OF_CONDUCT.md`: Community guidelines
  - `SECURITY.md`: Security policy and reporting guidelines
