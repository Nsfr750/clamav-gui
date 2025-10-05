# ClamAV GUI

A modern PySide6-based graphical user interface for ClamAV Antivirus on Windows.

## Features

- **Virus Scanning**

  - Scan files and directories
  - Real-time scan progress tracking
  - Detailed scan reports
  - Quarantine management

- **Database Management**

  - One-click virus database updates
  - Automatic update scheduling
  - Database integrity verification

- **Configuration**

  - Easy access to ClamAV configuration
  - Built-in configuration file editor
  - Custom scan options
  - Path management for ClamAV executables

- **User Interface**

  - Intuitive tab-based navigation
  - Dark/Light theme support
  - Real-time status updates
  - Comprehensive help system

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
- **Patreon**: [https://www.patreon.com/Nsfr750](https://www.patreon.com/Nsfr750)
- **Monero**: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`

---

© 2025 Nsfr750 - All rights reserved
