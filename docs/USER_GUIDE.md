# ClamAV GUI User Guide

Welcome to the ClamAV GUI! This guide will help you get started with using the application to scan your system for malware and keep it secure.

## Table of Contents
1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Scanning Files and Directories](#scanning-files-and-directories)
4. [Scheduled Scans](#scheduled-scans)
5. [Quarantine Management](#quarantine-management)
6. [Updating Virus Definitions](#updating-virus-definitions)
7. [Settings](#settings)
8. [Troubleshooting](#troubleshooting)
9. [Frequently Asked Questions](#frequently-asked-questions)

## Installation

### Prerequisites
- Python 3.8 or higher
- ClamAV antivirus engine
- GTK+ 3.0 or higher

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/clamav-gui.git
   cd clamav-gui
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Getting Started

### Main Interface
When you first launch ClamAV GUI, you'll see the main dashboard with the following options:
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
