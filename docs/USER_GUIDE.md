# ClamAV GUI User Guide

Welcome to ClamAV GUI! This comprehensive guide will help you get started with using the application to scan your system for malware, manage quarantined files, and keep your Windows system secure.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Main Interface](#main-interface)
4. [Scanning Files and Directories](#scanning-files-and-directories)
5. [Quarantine Management](#quarantine-management)
6. [Updating Virus Definitions](#updating-virus-definitions)
7. [Settings and Configuration](#settings-and-configuration)
8. [Troubleshooting](#troubleshooting)
9. [Frequently Asked Questions](#frequently-asked-questions)

## Quick Start

### Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.10+** (if running from source)
- **ClamAV Antivirus** (recommended for full functionality)

### Installation

#### Method 1: From Source (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Nsfr750/clamav-gui.git
   cd clamav-gui
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python -m clamav_gui
   ```

#### Method 2: Pre-built Executable

Download the latest Windows executable from the [GitHub Releases](https://github.com/Nsfr750/clamav-gui/releases) page and run it directly.

## Main Interface

When you launch ClamAV GUI, you'll see the main window with a tabbed interface:

### Tabs Overview

- **Scan**: File and directory scanning interface
- **Update**: Virus database update management
- **Settings**: Application configuration and preferences
- **Quarantine**: Manage quarantined files
- **Config Editor**: Advanced configuration editing

### Menu Bar

- **File > Exit**: Close the application
- **Tools > Check for Updates**: Check for application updates
- **Help > Documentation**: Open this user guide
- **Help > About**: Show version and system information
- **Language**: Switch between supported languages (English, Italian)

## Scanning Files and Directories

### Basic Scanning

1. **Select Target**: Click "Browse..." to choose files or directories to scan
2. **Configure Options**:
   - **Scan subdirectories**: Include files in subfolders
   - **Enable heuristic scan**: Use advanced detection methods
   - **Auto-quarantine infected files**: Automatically isolate threats
   - **Scan archives**: Check inside ZIP, RAR, and other archives
   - **Scan potentially unwanted applications**: Detect PUA files

3. **Start Scan**: Click "Start Scan" to begin the scanning process

### Scan Progress

- **Progress Bar**: Shows scan completion percentage
- **Output Window**: Displays detailed scan results and findings
- **Status Bar**: Shows current application status

### Scan Results

- **Clean Files**: No threats detected - system is secure
- **Infected Files**: Threats found and handled according to settings
- **Scan Summary**: Total files scanned, time taken, threats found

## Quarantine Management

### Viewing Quarantined Files

The Quarantine tab shows all files that have been isolated due to virus detection:

- **File List**: Shows quarantined files with threat names and sizes
- **Statistics**: Total quarantined files and space used
- **Threat Types**: Breakdown of different malware categories

### Managing Quarantined Files

- **Restore Selected**: Move files back to original location (use caution!)
- **Delete Selected**: Permanently remove files from quarantine
- **Export List**: Save quarantine list to JSON file for analysis

**⚠️ Warning**: Only restore files if you're certain they're safe. Quarantined files were detected as threats.

## Updating Virus Definitions

### Automatic Updates

ClamAV GUI can automatically check for virus database updates:

1. **Go to Update tab**
2. **Click "Update Now"**
3. **Monitor progress** in the output window

### Manual Updates

If automatic updates fail:

1. **Check internet connection**
2. **Verify ClamAV installation**
3. **Try updating from command line**:
   ```bash
   freshclam
   ```

## Settings and Configuration

### ClamAV Paths

Configure paths to ClamAV executables:

- **ClamD Path**: Location of ClamAV daemon (clamd.exe)
- **FreshClam Path**: Location of database update tool (freshclam.exe)
- **ClamScan Path**: Location of scanner (clamscan.exe)

### Scan Options

Customize scanning behavior:

- **Scan archives**: Enable/disable archive scanning
- **Enable heuristic analysis**: Use advanced detection
- **Scan potentially unwanted applications**: Detect PUA files
- **Auto-quarantine infected files**: Automatically isolate threats

### Performance Settings

Optimize scan performance:

- **Max file size (MB)**: Skip files larger than this size
- **Max scan time (sec)**: Timeout for individual file scans
- **File patterns**: Include/exclude specific file types

### Application Settings

- **Theme**: Choose between light and dark themes
- **Language**: Select interface language
- **Auto-update checks**: Enable/disable automatic update checking

## Troubleshooting

### Common Issues

#### Application Won't Start

**Solution**:
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.10+)
- Check for conflicting antivirus software

#### ClamAV Not Found

**Solution**:
1. Install ClamAV from official sources
2. Add ClamAV to system PATH
3. Configure paths in Settings tab
4. Restart the application

#### Scan Hangs or Freezes

**Solution**:
1. Check for large files that might be causing timeouts
2. Reduce max file size in settings
3. Try scanning smaller directories first
4. Restart the application

#### GUI Display Issues

**Solution**:
1. Update PySide6: `pip install --upgrade PySide6`
2. Check display resolution settings
3. Try running with different Qt backend

### Getting Help

#### Documentation
- This user guide in the `docs/` folder
- Online documentation on GitHub

#### Community Support
- **GitHub Issues**: [Bug Reports & Feature Requests](https://github.com/Nsfr750/clamav-gui/issues)
- **GitHub Discussions**: [General Questions](https://github.com/Nsfr750/clamav-gui/discussions)

#### Direct Support
- **Email**: [nsfr750@yandex.com](mailto:nsfr750@yandex.com)
- **Response Time**: Within 48 hours

### Logs and Debugging

Application logs are stored in:
- **Windows**: `%APPDATA%\ClamAV GUI\logs\`
- **Runtime logs**: Check the console output when running from source

For detailed debugging:
```bash
# Run with debug logging
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import clamav_gui"
```

## Frequently Asked Questions

### Is ClamAV GUI safe to use?

Yes, ClamAV GUI is open source software licensed under GPLv3. It performs all scanning operations locally and doesn't transmit your files externally.

### Does it work without ClamAV installed?

Basic functionality requires ClamAV. You can install ClamAV from:
- Official ClamAV website
- Windows package managers
- Pre-configured paths in Settings

### How often should I scan my system?

- **Full system scan**: Weekly or monthly
- **Critical files**: Daily or after downloading new software
- **Removable media**: Always before opening files

### What file types are scanned?

By default, ClamAV scans all file types. You can configure include/exclude patterns in Settings for performance optimization.

### Can I schedule automatic scans?

Scheduled scans are planned for version 1.2.0. Currently, you need to run scans manually or use Windows Task Scheduler with the command line interface.

### How do I update virus definitions?

1. Go to the "Update" tab
2. Click "Update Now"
3. Monitor progress in the output window

### What should I do with quarantined files?

- **Review carefully** before restoring
- **Delete permanently** if you're sure they're malicious
- **Keep backups** of important files before scanning

### Is my data safe?

- All operations are performed locally
- No files are sent to external servers
- Settings are stored locally in your AppData folder
- Quarantine files are encrypted and stored locally

## Advanced Usage

### Command Line Interface

For automation and scripting:

```bash
# Run scan from command line
python -m clamav_gui scan --path "C:\Users\Downloads"

# Check for updates
python -m clamav_gui update

# Show version
python -m clamav_gui --version
```

### Configuration Files

Advanced users can edit configuration files directly:
- **Settings**: Stored in `%APPDATA%\ClamAV GUI\settings.json`
- **Logs**: Available in `%APPDATA%\ClamAV GUI\logs\`

### Performance Tuning

For optimal performance:

- **Use SSD storage** for virus database and temporary files
- **Close unnecessary applications** during large scans
- **Configure appropriate file size limits** in settings
- **Regular database updates** for best detection rates

## Security Best Practices

1. **Keep software updated**: Regular updates for both ClamAV GUI and virus definitions
2. **Use strong passwords**: For any accounts related to security tools
3. **Verify downloads**: Check file integrity before opening
4. **Regular backups**: Keep backups of important files
5. **Multiple security layers**: Use ClamAV GUI alongside other security tools

## Contributing

Found a bug or want to suggest a feature? See our [Contributing Guide](CONTRIBUTING.md) for details on how to help improve ClamAV GUI.

## Support the Project

If ClamAV GUI helps keep your system secure, consider supporting the development:

- **GitHub Sponsors**: Support ongoing development
- **PayPal**: [paypal.me/3dmega](https://paypal.me/3dmega)
- **Monero**: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`

---

*This user guide was last updated for ClamAV GUI version 1.1.0. For the latest version, visit the [GitHub repository](https://github.com/Nsfr750/clamav-gui).*


### Quick Reference

**Application**: ClamAV GUI v1.1.0
**License**: GPLv3
**Platform**: Windows 10/11
**Support**: [GitHub Issues](https://github.com/Nsfr750/clamav-gui/issues)
**Documentation**: [GitHub Pages](https://nsfr750.github.io/clamav-gui/)

Thank you for using ClamAV GUI! Stay secure! 🛡️

- **Quick Scan**: Scans common system directories
- **Full Scan**: Scans the entire system
- **Custom Scan**: Allows you to select specific files or directories
- **Update**: Updates the virus definitions
- **Quarantine**: Manages quarantined files
- **Settings**: Configure application preferences

## Scanning Files and Directories

### Quick Scan

1. Click on the "Quick Scan" button
2. The scan will start automatically
3. View the results in the scan results window

### Custom Scan

1. Click on "Custom Scan"
2. Select the files or directories you want to scan
3. Click "Start Scan"
4. Review the scan results

## Scheduled Scans

### Creating a Scheduled Scan

1. Go to "Settings" > "Scheduled Scans"
2. Click "Add New Schedule"
3. Configure the scan:
   - Select scan type (Quick/Full/Custom)
   - Set the frequency (Daily/Weekly/Monthly)
   - Choose the time
   - Enable/Disable email notifications
4. Click "Save"

## Quarantine Management

### Viewing Quarantined Items

1. Click on the "Quarantine" button
2. View the list of quarantined files
3. Select a file to see details and available actions

### Restoring Files

1. Select the file(s) you want to restore
2. Click "Restore"
3. Choose the restore location
4. Click "Confirm"

## Updating Virus Definitions

### Manual Update

1. Click on the "Update" button
2. Wait for the update to complete

### Automatic Updates

1. Go to "Settings" > "Updates"
2. Enable automatic updates
3. Set the update frequency

## Settings

### General Settings

- Theme selection
- Language preferences
- Start with system startup

### Scan Settings

- Scan behavior
- File size limits
- File type exclusions

### Notifications

- Enable/disable notifications
- Configure email notifications
- Sound alerts

## Troubleshooting

### Common Issues

- **Virus definitions won't update**: Check your internet connection and ensure ClamAV service is running
- **Scan is slow**: Try excluding large files or directories
- **Application crashes**: Check the log file at `~/.clamav-gui/clamav-gui.log`

### Viewing Logs

Logs are stored in `~/.clamav-gui/` directory:

- `clamav-gui.log`: Application logs
- `clamscan.log`: Scan logs

## Frequently Asked Questions

### Is ClamAV GUI free to use?

Yes, ClamAV GUI is open-source software released under the GPLv3 license.

### How often should I update the virus definitions?

It's recommended to update the virus definitions at least once a day for optimal protection.

### Can I schedule multiple scans?

Yes, you can create multiple scheduled scans with different configurations.

### How do I report a bug?

Please open an issue on our [GitHub repository](https://github.com/Nsfr750/clamav-gui/issues) with detailed information about the bug.

## Support

For additional help, please visit our [GitHub repository](https://github.com/Nsfr750/clamav-gui)
