# ClamAV GUI

![Version](https://img.shields.io/badge/Version-1.2.0-blue)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)
![GUI](https://img.shields.io/badge/GUI-PyQt6.6-blue)
![License](https://img.shields.io/badge/License-GPLv3-blue)
[![Issues](https://img.shields.io/github/issues/Nsfr750/clamav-gui)](https://github.com/Nsfr750/clamav-gui/issues)

![ss](clamav_gui/ui/img/ss.png)

A modern PySide6-based graphical user interface for ClamAV Antivirus on Windows.

## Features

- **Virus Scanning**

  - Scan files and directories with advanced options
  - Real-time scan progress tracking with detailed statistics
  - Comprehensive scan reports in HTML and text formats
  - Advanced file pattern filtering (include/exclude patterns)
  - Performance controls (max file size, scan time limits)
  - Automatic quarantine of infected files
  - Support for archives, heuristics, and PUA detection
  - Email scanning (.eml, .msg files) with attachment analysis
  - Network drive scanning (UNC paths) with connectivity validation
  - Smart scanning (skip known safe files using hash databases)
  - Async scanning (non-blocking UI during large scans)

- **Machine Learning Integration**

  - AI-powered threat detection with feature extraction
  - ML model training and inference for advanced threat analysis
  - Behavioral analysis and anomaly detection
  - Risk assessment based on ML confidence and file characteristics

- **Advanced Reporting**

  - Comprehensive analytics and threat intelligence reports
  - Historical scan data analysis with trend detection
  - Multiple export formats (HTML, JSON, CSV, text)
  - Threat categorization and severity assessment
  - Real-time statistics during scanning operations

- **Sandbox Analysis**

  - Behavioral analysis of suspicious files in isolated environment
  - System activity monitoring (network, processes, file I/O)
  - Execution behavior analysis with timeout protection
  - Risk level assessment based on behavioral indicators
  - Safe file execution testing

- **Error Recovery**

  - Automatic retry mechanisms for failed operations
  - Exponential backoff strategies for different error types
  - Robust handling of network timeouts and system failures
  - Comprehensive error logging and recovery tracking

- **Quarantine Management**

  - Automatic isolation of infected files during scans
  - Complete quarantine management interface
  - File restoration and permanent deletion options
  - Quarantine statistics and metadata tracking
  - Export quarantine lists for analysis
  - Bulk operations (restore/delete multiple files)

- **Database Management**

  - One-click virus database updates with incremental support
  - Automatic update scheduling with error recovery
  - Database integrity verification and backup/restore
  - Support for custom ClamAV paths and configurations

- **Configuration**

  - Easy access to ClamAV configuration
  - Built-in configuration file editor
  - Custom scan options and profiles
  - Path management for ClamAV executables
  - Advanced performance and filtering settings

- **User Interface**

  - Intuitive tab-based navigation
  - Dark/Light theme support
  - Real-time status updates and notifications
  - Comprehensive help system and error handling
  - Multi-language support (English, Italian)

## Installation

### Prerequisites

- Python 3.8 or higher
- ClamAV installed on your system
- Git (for cloning the repository)

### Quick Start

1. Clone the repository:

   ```bash
   git clone https://github.com/Nsfr750/clamav-gui.git
   cd clamav-gui
   ```

2. Set up a virtual environment (recommended):

   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Install in development mode:

   ```bash
   pip install -e .
   ```

## Usage

### Starting the Application

Run using the launcher:

```bash
clamav-gui
```

Or directly with Python:

```bash
python -m clamav_gui
```

### First-Time Setup

1. **Update Virus Definitions**
   - Navigate to the "Update" tab
   - Click "Update Now" to download the latest virus definitions
   - Enable automatic updates if desired

2. **Configure Paths**
   - Go to "Settings" tab
   - Verify or update paths to ClamAV executables
   - Save your settings

3. **Start Scanning**
   - Select the "Scan" tab
   - Choose a target directory
   - Configure scan options
   - Click "Start Scan"

## Documentation

For detailed documentation, please visit our [Wiki](https://github.com/Nsfr750/clamav-gui/wiki).

- **ClamD Path**: Path to clamd.exe
- **FreshClam Path**: Path to freshclam.exe
- **ClamScan Path**: Path to clamscan.exe

### Command Line Options

You can also run the application with command line arguments:

```text
usage: clamav-gui [-h] [--clamd CLAMD] [--freshclam FRESHCLAM] [--clamscan CLAMSCAN]

optional arguments:
  -h, --help            show this help message and exit
  --clamd CLAMD         Path to clamd executable
  --freshclam FRESHCLAM  Path to freshclam executable
  --clamscan CLAMSCAN   Path to clamscan executable
```

## Building from Source

To create a standalone executable:

1. Install PyInstaller:

   ```bash
   pip install pyinstaller
   ```

2. Build the executable:

   ```bash
   pyinstaller --onefile --windowed --name ClamAV-GUI --icon=assets/icon.ico clamav_gui/__main__.py
   ```

The executable will be in the `dist` directory.

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, please open an issue on GitHub or contact me: [Nsfr750](mailto:nsfr750@yandex.com)

## Donate

If you find this project useful, consider supporting its development:

- **PayPal**: [https://paypal.me/3dmega](https://paypal.me/3dmega)
- **Monero**: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`

---

© 2025 Nsfr750 - All rights reserved
