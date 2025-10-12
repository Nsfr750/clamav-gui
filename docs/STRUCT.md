# ClamAV GUI Project Structure

This document describes the current structure of the ClamAV GUI project as of version 1.1.0.

## Directory Structure

```
clamav-gui/
├── .github/                    # GitHub-specific files
│   └── workflows/
│       └── test.yml           # CI/CD pipeline configuration
├── assets/                     # Static assets (icons, images, etc.)
├── build/                      # Build artifacts and temporary files
├── clamav_gui/                 # Main application package
│   ├── __init__.py             # Package initialization
│   ├── __main__.py             # Entry point when run as a module
│   ├── main_window.py          # Main window implementation
│   ├── version.py              # Version information and management
│   ├── lang/                   # Internationalization system
│   │   ├── __init__.py         # Language package initialization
│   │   ├── en_US.py            # English (US) translations
│   │   ├── it_IT.py            # Italian translations
│   │   └── lang_manager.py     # Language management and switching
│   ├── ui/                     # User interface components
│   │   ├── __init__.py         # UI package initialization
│   │   ├── about.py            # About dialog implementation
│   │   ├── help.py             # Help documentation viewer
│   │   ├── menu.py             # Application menu bar
│   │   ├── settings.py         # Settings and preferences dialog
│   │   ├── sponsor.py          # Sponsor information dialog
│   │   └── updates_dialog.py   # Update notification dialog
│   └── utils/                  # Utility modules and helpers
│       ├── __init__.py         # Utils package initialization
│       ├── clamav_validator.py # ClamAV installation validation
│       ├── quarantine_manager.py # Quarantine file management
│       ├── scan_report.py      # Scan result reporting
│       ├── updates.py          # Application update checking
│       └── virus_db.py         # Virus database management
├── config/                     # Configuration templates
├── dist/                       # Distribution packages
├── docs/                       # Documentation files
│   ├── CODE_OF_CONDUCT.md      # Community guidelines
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   ├── REQUIREMENTS.md         # System requirements and setup
│   ├── ROADMAP.md              # Development roadmap
│   ├── SECURITY.md             # Security policy
│   ├── STRUCT.md               # Project structure (this file)
│   └── USER_GUIDE.md           # User documentation
├── logs/                       # Application runtime logs
├── tests/                      # Test suite
│   ├── __init__.py             # Test package initialization
│   ├── conftest.py             # Test fixtures and configuration
│   ├── test_clamav_isolation.py # ClamAV interaction testing
│   ├── test_gui_integration.py # GUI component testing
│   ├── test_lang_manager.py    # Language management testing
│   ├── test_main.py            # Main application testing
│   ├── test_performance.py     # Performance and benchmark testing
│   ├── test_quarantine_manager.py # Quarantine management testing
│   └── test_version.py         # Version module testing
├── .coveragerc                 # Coverage configuration
├── .gitignore                  # Git ignore patterns
├── .pytest.ini                 # Pytest configuration
├── CHANGELOG.md                # Version history and changes
├── LICENSE                     # GPLv3 License
├── Makefile                    # Build and test automation
├── README.md                   # Project overview and setup
├── TO_DO.md                    # Development tasks and ideas
├── build.py                    # Build script for executables
├── clean_pycache.py            # Python cache cleanup utility
├── nuitka_compiler.py          # Nuitka compilation script
├── pytest.ini                 # Pytest configuration (alternative)
├── requirements.txt            # Runtime dependencies
├── run_tests.py               # Test runner script
├── setup.py                    # Package installation script
└── version_info.txt            # Version metadata
```

## Core Components

### Application Entry Points

- **`__main__.py`**: Main entry point when running as `python -m clamav_gui`
- **`main_window.py`**: Primary application window with tabbed interface
- **`version.py`**: Version information, comparison, and management utilities

### User Interface System

- **`ui/` Package**: Complete UI component architecture
  - **`menu.py`**: Application menu bar with File, Tools, Help menus
  - **`about.py`**: About dialog with version and system information
  - **`help.py`**: Help documentation browser
  - **`settings.py`**: Configuration and preferences management
  - **`sponsor.py`**: Support and donation information
  - **`updates_dialog.py`**: Update notification and installation

### Internationalization

- **`lang/` Package**: Multi-language support system
  - **`lang_manager.py`**: Dynamic language loading and switching
  - **`en_US.py`**: Complete English translations
  - **`it_IT.py`**: Complete Italian translations

### Utility Modules

- **`utils/` Package**: Core functionality modules
  - **`clamav_validator.py`**: ClamAV installation detection and validation
  - **`quarantine_manager.py`**: Infected file isolation and management
  - **`scan_report.py`**: Scan result formatting and HTML report generation
  - **`updates.py`**: Application and virus database update checking
  - **`virus_db.py`**: Virus database download and integrity verification

## Testing Infrastructure

### Test Organization

- **`tests/` Directory**: Comprehensive test suite
  - **Unit Tests**: Individual component testing (`test_*.py`)
  - **Integration Tests**: Component interaction testing
  - **GUI Tests**: PySide6 interface testing with pytest-qt
  - **Performance Tests**: Benchmarking and performance regression testing
  - **Isolation Tests**: ClamAV interaction mocking and isolation

### Test Configuration

- **`conftest.py`**: Test fixtures, mocking, and shared test utilities
- **`pytest.ini`**: Pytest configuration with coverage and markers
- **`.coveragerc`**: Coverage reporting configuration
- **`run_tests.py`**: Enhanced test runner with multiple execution modes

## Build and Distribution

### Build System

- **`setup.py`**: Standard Python package installation
- **`build.py`**: Windows executable creation script
- **`nuitka_compiler.py`**: Advanced compilation for optimized binaries
- **`Makefile`**: Cross-platform build and test automation

### Distribution Artifacts

- **`dist/`**: Built distribution packages (wheels, executables)
- **`.github/workflows/`**: Automated CI/CD pipeline configuration

## Documentation

### User-Facing Documentation

- **`README.md`**: Project overview, installation, and quick start
- **`USER_GUIDE.md`**: Comprehensive user manual and troubleshooting
- **`REQUIREMENTS.md`**: System requirements and detailed setup instructions

### Developer Documentation

- **`CONTRIBUTING.md`**: Development guidelines and contribution process
- **`ROADMAP.md`**: Feature roadmap and development priorities
- **`SECURITY.md`**: Security policy and vulnerability reporting
- **`STRUCT.md`**: Project structure and component overview

## Configuration and Data

### Configuration Files

- **`config/`**: Template configuration files
- **`.env.example`**: Environment variable template (if needed)
- **`version_info.txt`**: Version metadata for build processes

### Runtime Data

- **`logs/`**: Application runtime logs and debugging information
- **Application settings**: Stored in Windows AppData directory
- **Quarantine data**: Stored locally in encrypted format

## Key Architecture Decisions

### Technology Stack

- **GUI Framework**: PySide6 (Qt for Python) for cross-platform compatibility
- **Testing**: pytest with comprehensive coverage and multiple test types
- **Internationalization**: Custom translation system with runtime language switching
- **Build System**: Multi-stage build process supporting development and distribution

### Design Principles

- **Modular Architecture**: Clear separation of concerns between UI, utilities, and core logic
- **Comprehensive Testing**: Multiple test types ensuring reliability and performance
- **Security-First**: Local processing, minimal permissions, secure update mechanisms
- **User-Centric**: Intuitive interface with comprehensive user guidance

### Development Philosophy

- **Open Source**: GPLv3 license encouraging community contributions
- **Quality Assurance**: Extensive testing and code review processes
- **Documentation-Driven**: Comprehensive documentation for users and developers
- **Continuous Improvement**: Regular updates with backward compatibility

## File Sizes and Complexity

### Code Metrics (Approximate)

- **Total Lines of Code**: ~15,000+ lines across all Python files
- **Main Application**: ~5,000 lines in core modules
- **UI Components**: ~3,000 lines across dialog and window implementations
- **Utilities**: ~2,000 lines in helper modules and managers
- **Tests**: ~3,000 lines across comprehensive test suite
- **Documentation**: ~2,000+ lines across all documentation files

### Build Artifacts

- **Source Distribution**: ~50 MB (including all dependencies)
- **Windows Executable**: ~100-200 MB (standalone executable)
- **Test Coverage**: >90% across core application modules

## Extension Points

### Plugin Architecture

The codebase is designed with extension points for:

- **Custom Scan Modules**: Additional scanning capabilities beyond standard ClamAV
- **UI Themes**: Custom visual themes and styling
- **Report Formats**: Additional report generation formats
- **Integration APIs**: External tool integration capabilities

### Configuration Extensibility

- **Settings System**: Extensible configuration management
- **Plugin Registry**: Dynamic loading of optional components
- **Theme System**: Customizable visual appearance

---

*This structure document reflects the ClamAV GUI project as of version 1.1.0 and is updated as the project evolves.*
