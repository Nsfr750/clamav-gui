# Project Structure

```text
clamav-gui/
├── assets/                  # Static assets (icons, images, etc.)
├── clamav_gui/              # Main application package
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Application entry point
│   ├── main_window.py       # Main window implementation
│   ├── settings.py          # Application settings
│   ├── utils/               # Utility modules
│   │   ├── __init__.py
│   │   ├── updates.py       # Update checking functionality
│   │   └── virus_db.py      # Virus database management
│   ├── lang/                # Language files
│   │   ├── __init__.py
│   │   ├── en.py            # English translations
│   │   ├── it.py            # Italian translations
│   │   └── lang_manager.py  # Language management
│   └── ui/                  # UI components
│       ├── __init__.py
│       └── dialogs/         # Custom dialogs
├── tests/                   # Test files
│   ├── __init__.py
│   └── test_*.py
├── .gitignore               # Git ignore file
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # License information
├── README.md                # Project documentation
├── REQUIREMENTS.md          # Dependencies list
└── SECURITY.md              # Security policy
└── setup.py                 # Installation script
```

## Key Components

### Main Application

- `main.py`: Entry point that initializes and runs the application
- `main_window.py`: Implements the main window and core functionality

### Core Functionality

- `settings.py`: Manages application settings and preferences
- `utils/updates.py`: Handles update checking and downloading
- `utils/virus_db.py`: Manages virus database operations

### Internationalization

- `lang/`: Contains language files and translation logic
- `lang_manager.py`: Handles language loading and switching

### User Interface

- `ui/`: Contains custom UI components and dialogs
- `assets/`: Contains images, icons, and other static files

### Testing

- `tests/`: Contains unit and integration tests

## Dependencies

- PySide6: For the GUI
- ClamAV: For virus scanning
- Other dependencies listed in requirements.txt
