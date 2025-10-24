# Changelog

All notable changes to this project will be documented in this file.

## [1.2.5] - 2025-10-24

### New Features Added

- **Database Configuration Section**: Added visible database path configuration in settings tab with browse functionality
- **Enhanced Database Path Detection**: Improved automatic detection of ClamAV database location using multiple fallback methods
- **Settings Persistence**: Database path now properly saved to settings.json configuration file

### Enhancements and Improvements

- **Settings Tab UI**: Fixed missing Virus Database Configuration section visibility in the settings interface
- **Database Path Management**: Better integration between settings and database detection systems
- **Configuration Loading**: Enhanced loading of database settings from config files with validation
- **Settings Validation**: Added path validation and user confirmation for invalid database paths

## [1.2.0] - 2025-10-16

### Added

- **Enhanced Log Viewer**: Advanced log viewing with search, filtering, color coding, and statistics
- **Config Editor Tab**: Separate tab for editing ClamAV configuration files
- **Advanced Scanning Menu**: New menu with smart scanning, ML detection, email scanning, and batch analysis
- **Help Menu Positioning**: Moved Help menu to the right side of the menu bar for better UX

### Improved

- **Menu Organization**: Reorganized menu structure for better user experience
- **Log Analysis**: Comprehensive log viewer with filtering and search capabilities
- **Configuration Management**: Dedicated tab for editing configuration files

## [1.1.1] - 2025-10-15

### Added

- **Enhanced UI Styling**: Improved scan progress bar with animated blue gradient visualization
- **Color-coded Action Buttons**: Green "Start Scan" and red "Stop Scan" buttons with hover effects for better user experience
- **Visual Feedback Improvements**: Better visual consistency across scan interface with modern styling

### Improved

- **Progress Bar Visualization**: Enhanced animated progress indicators with gradient effects
- **Button Design**: Color-coded action buttons for improved user interface clarity
- **User Experience**: Better visual feedback for scan operations and status indication

## [1.1.0] - 2025-10-12

### Added

- **Machine Learning Integration**: AI-powered threat detection with feature extraction and ML models for advanced threat analysis beyond traditional signatures
- **Error Recovery System**: Automatic retry mechanisms for failed operations with exponential backoff strategies for different error types (network, file access, database, scan interruptions)
- **Advanced Reporting**: Comprehensive analytics, threat intelligence reports, historical scan data analysis, trend detection, and multiple export formats (HTML, JSON, CSV, text)
- **Sandbox Analysis**: Behavioral analysis of suspicious files in isolated environments with system activity monitoring (network, processes, file I/O) and risk assessment
- **Email Scanning**: Complete email file scanning with support for .eml and .msg formats including attachment analysis and content inspection
- **Network Drive Scanning**: Full UNC path support (\\\\server\\share) with network connectivity validation and accessibility checks
- **Enhanced Quarantine Management**: Complete restore/delete functionality with bulk operations, metadata display, and advanced file management
- **Async Scanning**: Non-blocking UI during large scans with progress cancellation support and improved responsiveness
- **Smart Scanning**: Hash database system to skip known safe files, significantly reducing scan times for repeated scans
- **Incremental Database Updates**: Differential virus database updates for faster downloads and better reliability
- **Enhanced Error Handling**: Improved detection and handling of missing ClamAV installations with automatic path detection and installation guidance
- **Comprehensive Scan Reports**: Advanced scan report generation with HTML and text formats, including detailed statistics and threat analysis
- **Quarantine Management System**: Complete quarantine functionality for infected files with metadata tracking, restore/delete operations, and export capabilities
- **Extended Configuration Options**: Added performance settings (max file size, scan time limits), file pattern filtering (include/exclude), and advanced scan options
- **Real-time Statistics**: Enhanced progress tracking and scan statistics display throughout the application

### Improved

- **User Experience**: Better error messages, user feedback, and status reporting throughout the application
- **Robustness**: Enhanced handling of corrupted or incomplete metadata files
- **Performance**: Improved scan progress visualization and file filtering controls
- **Code Quality**: Better error handling and defensive programming practices

## [1.0.0] - 2025-09-25

### Added

- Initial release of ClamAV GUI
- Basic scanning and updating functionality
- English and Italian language support
- Configuration management
- Automatic update checking

---

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
