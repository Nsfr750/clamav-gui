# Security Policy

## Overview

The ClamAV GUI is a Windows-based graphical user interface for the ClamAV antivirus engine. This document outlines our security policies, vulnerability reporting procedures, and security considerations for users and developers.

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.2.x   | :white_check_mark: | Active           |
| 1.1.x   | :white_check_mark: | Until 1.3.0      |
| 1.0.x   | :x:                | None             |
| < 1.0   | :x:                | None             |

## Reporting a Vulnerability

We take the security of our software seriously. If you discover a security vulnerability, we would appreciate your help in disclosing it to us in a responsible manner.

### How to Report

Please report security vulnerabilities by emailing directly to the maintainer [Nsfr750](mailto:nsfr750@yandex.com).

**Important**: Please do not create public GitHub issues for security vulnerabilities. Use the email contacts above instead.

### Response Time

You should receive an initial response within **48 hours**. If you don't receive a response, please follow up with another email to ensure your report was received.

### What to Include

When reporting a vulnerability, please include as much of the following information as possible:

- **Description**: A clear description of the vulnerability and its potential impact
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Affected Version**: The version of ClamAV GUI you're using
- **System Information**: Windows version, Python version, ClamAV version
- **Error Messages**: Any relevant error messages, logs, or crash dumps
- **Proof of Concept**: If applicable, provide a minimal proof of concept
- **Suggested Fix**: If you have identified a potential fix, please include it
- **Impact Assessment**: Your assessment of the vulnerability's severity

### Vulnerability Assessment

Once received, we will:

1. **Acknowledge** receipt within 48 hours
2. **Assess** the vulnerability's validity and severity
3. **Develop** a fix if the vulnerability is confirmed
4. **Test** the fix thoroughly
5. **Release** a security update
6. **Publish** a security advisory

### Version 1.2.5 Security Improvements

#### Enhanced Database Configuration Security

- **Secure Path Validation**: Database path configuration includes comprehensive path validation to prevent directory traversal attacks
- **Safe File Operations**: Database configuration changes use atomic file operations to prevent corruption
- **Input Sanitization**: All database path inputs are properly sanitized and validated before use
- **Error Handling**: Secure error handling prevents information disclosure during database path operations

#### Settings Management Security

- **Configuration File Security**: Enhanced security for settings.json file handling with proper file permissions
- **Path Security**: All configuration paths are validated to prevent access to unauthorized directories
- **Safe Serialization**: JSON parsing includes proper error handling to prevent injection attacks

### Version 1.2.0 Security Improvements

#### Enhanced Log Viewer Security

- **Secure Log Data Handling**: The enhanced log viewer processes log data locally without external transmission
- **Input Sanitization**: All log content is properly sanitized before display to prevent injection attacks
- **Access Control**: Log viewer respects file system permissions and only displays accessible log files
- **Search Function Security**: Search functionality uses safe string operations to prevent regex injection

#### Configuration Editor Security

- **Path Validation**: Configuration file paths are validated to prevent directory traversal attacks
- **Safe File Operations**: File editing operations include proper error handling and atomic writes
- **Permission Checks**: Editor verifies write permissions before attempting file modifications

#### Advanced Scanning Features Security

- **Network Path Security**: Network drive scanning validates UNC paths and handles access errors gracefully
- **Resource Management**: Proper cleanup of temporary resources during advanced scanning operations
- **Input Validation**: Enhanced validation of scan parameters and file paths

## Security Considerations

### Architecture Security

#### Local Processing Only

- All virus scanning operations are performed **locally** on the user's machine
- No files, scan results, or personal data are transmitted to external servers
- The application operates in complete isolation from internet services during scanning

#### No Network Dependencies for Core Functions

- Virus database updates require internet access but are optional
- Core scanning functionality works entirely offline
- Network operations are clearly indicated to the user

### Data Protection

#### File Handling

- Files are scanned in-place without modification unless quarantine is enabled
- Quarantined files are moved to a secure local directory
- No file contents are transmitted externally during normal operation

#### Settings Storage

- Application settings are stored in the user's local AppData directory
- Settings are stored in plain text but contain no sensitive information
- No authentication credentials or personal data are stored

#### Temporary Files

- Temporary files created during scanning are automatically cleaned up
- No sensitive data persists in temporary locations

### Permissions and Access Control

#### Minimal Privilege Requirements

- The application does **not** require administrative privileges for basic operation
- Standard user permissions are sufficient for all core functionality
- Elevated privileges are only requested when necessary (e.g., system-wide scans)

#### Windows Security Model

- Follows Windows security best practices for desktop applications
- Respects Windows User Account Control (UAC) guidelines
- No attempts to bypass Windows security mechanisms

### Secure Development Practices

#### Dependency Management

- All dependencies are regularly updated to address known vulnerabilities
- Dependencies are pinned to specific versions to prevent supply chain attacks
- Security advisories for dependencies are monitored and addressed promptly

#### Code Security

- Code reviews are performed for all changes
- Static analysis tools are used to identify potential security issues
- Input validation is implemented for all user-provided data
- Secure coding practices are followed throughout the codebase

#### Build Security

- Builds are performed in isolated environments
- No unsigned code is distributed
- Build artifacts are cryptographically signed

### Third-Party Components

#### ClamAV Engine

- Relies on the ClamAV engine for virus detection
- Inherits security properties of the underlying ClamAV installation
- Users should ensure their ClamAV installation is kept up-to-date

#### PySide6 GUI Framework

- Uses PySide6 for the graphical user interface
- Security considerations follow Qt framework security guidelines
- Regular updates ensure latest security patches

## Security Features

### Built-in Protections

#### Path Traversal Prevention

- All file paths are validated to prevent directory traversal attacks
- User input is sanitized before file operations

#### Command Injection Prevention

- Shell commands are properly escaped and validated
- No unsanitized user input is passed to system commands

#### Buffer Overflow Prevention

- Uses safe string handling practices
- Bounds checking is implemented where necessary

### Update Security

#### Secure Database Updates

- Virus database updates use HTTPS when available
- Database integrity is verified before use
- Corrupted databases are rejected and re-downloaded

#### Application Updates

- Application updates are distributed through secure channels
- Update packages are cryptographically signed
- Users are notified of available security updates

## Security Best Practices for Users

### Installation

- Download ClamAV GUI only from official sources (GitHub releases)
- Verify file integrity using provided checksums
- Keep the application updated to the latest version

### Usage

- Run regular virus scans on your system
- Keep virus databases up-to-date
- Use quarantine features for infected files
- Be cautious when restoring quarantined files

### System Security

- Maintain up-to-date Windows security patches
- Use antivirus software on your system
- Keep Python and other dependencies updated
- Avoid running untrusted code

## Security Updates

### Release Process

Security updates are released as:

1. **Patch releases** (e.g., 1.1.1, 1.1.2) for security fixes
2. **Minor releases** (e.g., 1.2.0) for new features with security improvements
3. **Emergency releases** for critical security issues

### Update Notifications

- Users are notified of security updates through the application's update system
- Critical security updates may be announced via email to registered users
- Release notes clearly indicate security fixes

### Backporting Policy

- Critical security fixes are backported to supported versions
- Non-critical fixes may only be available in newer versions
- Users are encouraged to upgrade to receive all security fixes

## Acknowledgments

We would like to thank the following individuals and organizations for responsibly disclosing security issues:

- **Security Researchers**: For helping improve our security posture
- **ClamAV Community**: For maintaining the underlying antivirus engine
- **Python Security Team**: For maintaining a secure Python ecosystem

## Contact Information

### Security Contact

- **Email**: [security@clamav-gui.org](mailto:security@clamav-gui.org)
- **Alternative**: [Nsfr750](mailto:nsfr750@yandex.com)

### General Contact

- **GitHub Issues**: [https://github.com/Nsfr750/clamav-gui/issues](https://github.com/Nsfr750/clamav-gui/issues)
- **Discussions**: [https://github.com/Nsfr750/clamav-gui/discussions](https://github.com/Nsfr750/clamav-gui/discussions)

### PGP Key

For sensitive communications, you may use our PGP key (available upon request).

---

*This security policy was last updated on October 24, 2025.*
