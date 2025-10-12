"""
Email scanning functionality for ClamAV GUI.
Supports scanning .eml, .msg files and email server connections.
"""
import os
import email
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class EmailScanner:
    """Scans email files and email servers for malware."""

    def __init__(self, clamscan_path: str = "clamscan"):
        """Initialize the email scanner.

        Args:
            clamscan_path: Path to clamscan executable
        """
        self.clamscan_path = clamscan_path
        self.temp_dir = None

    def scan_email_file(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """Scan an email file (.eml or .msg) for malware.

        Args:
            file_path: Path to the email file

        Returns:
            Tuple of (is_clean: bool, scan_result: str, threats: List[str])
        """
        if not os.path.exists(file_path):
            return False, f"Email file not found: {file_path}", []

        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == '.eml':
                return self._scan_eml_file(file_path)
            elif file_ext == '.msg':
                return self._scan_msg_file(file_path)
            else:
                return False, f"Unsupported email format: {file_ext}", []

        except Exception as e:
            logger.error(f"Error scanning email file {file_path}: {e}")
            return False, f"Error scanning email file: {str(e)}", []

    def _scan_eml_file(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """Scan an .eml file for malware."""
        threats = []
        scan_details = []

        try:
            # Parse the .eml file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                email_content = f.read()

            # Parse email headers and body
            email_message = email.message_from_string(email_content)

            # Check for suspicious headers
            suspicious_headers = [
                'X-Virus-Scanned', 'X-Spam-Status', 'X-Phishing-Score',
                'Received', 'From', 'Subject'
            ]

            scan_details.append(f"Email from: {email_message.get('From', 'Unknown')}")
            scan_details.append(f"Subject: {email_message.get('Subject', 'No Subject')}")

            # Check attachments
            attachments = []
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                filename = part.get_filename()
                if filename:
                    attachments.append(filename)

                    # Save attachment to temp file for scanning
                    temp_file = self._save_attachment_to_temp(part, filename)
                    if temp_file:
                        # Scan the attachment
                        is_clean, result, attachment_threats = self._scan_with_clamav(temp_file)
                        if not is_clean:
                            threats.extend(attachment_threats)
                            scan_details.append(f"Attachment threat: {filename} - {result}")
                        else:
                            scan_details.append(f"Attachment clean: {filename}")

                        # Clean up temp file
                        try:
                            os.unlink(temp_file)
                        except:
                            pass

            # Scan email body content (basic heuristic check)
            body_content = self._extract_email_body(email_message)
            if body_content:
                # Check for suspicious content patterns
                suspicious_patterns = [
                    'urgent', 'account suspension', 'verify your account',
                    'click here', 'download attachment', 'bank details'
                ]

                body_lower = body_content.lower()
                suspicious_matches = [
                    pattern for pattern in suspicious_patterns
                    if pattern in body_lower
                ]

                if suspicious_matches:
                    scan_details.append(f"Suspicious content detected: {', '.join(suspicious_matches)}")
                    threats.append("Suspicious email content")

            # Overall result
            is_clean = len(threats) == 0
            result = "Clean" if is_clean else f"Threats found: {len(threats)}"

            return is_clean, result, threats

        except Exception as e:
            return False, f"Error parsing EML file: {str(e)}", []

    def _scan_msg_file(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """Scan a .msg file for malware (Outlook format)."""
        # For .msg files, we'll use a different approach
        # Since .msg files are compound files, we'll scan them directly with clamscan
        return self._scan_with_clamav(file_path)

    def _scan_with_clamav(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """Scan a file with ClamAV."""
        try:
            cmd = [self.clamscan_path, '--no-summary', file_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse ClamAV output
            output = result.stdout + result.stderr
            threats = []

            # Look for infected files in output
            for line in output.split('\n'):
                if 'FOUND' in line or 'infected' in line.lower():
                    threats.append(line.strip())

            is_clean = result.returncode == 0 and len(threats) == 0
            result_text = "Clean" if is_clean else f"Infected: {'; '.join(threats)}"

            return is_clean, result_text, threats

        except subprocess.TimeoutExpired:
            return False, "Scan timeout", ["Scan timeout"]
        except Exception as e:
            return False, f"Scan error: {str(e)}", [str(e)]

    def _save_attachment_to_temp(self, part, filename: str) -> Optional[str]:
        """Save an email attachment to a temporary file."""
        try:
            # Create temp directory if needed
            if self.temp_dir is None:
                self.temp_dir = tempfile.mkdtemp()

            # Generate safe filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
            if not safe_filename:
                safe_filename = f"attachment_{hash(part)}"

            temp_path = os.path.join(self.temp_dir, safe_filename)

            # Save attachment content
            with open(temp_path, 'wb') as f:
                f.write(part.get_payload(decode=True) or b'')

            return temp_path

        except Exception as e:
            logger.error(f"Error saving attachment: {e}")
            return None

    def _extract_email_body(self, email_message) -> str:
        """Extract the text content from an email message."""
        body_parts = []

        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    content = part.get_payload(decode=True)
                    if content:
                        body_parts.append(content.decode('utf-8', errors='ignore'))
                except:
                    continue

        return '\n'.join(body_parts)

    def scan_email_server(self, server_config: Dict) -> Tuple[bool, str, List[str]]:
        """Scan an email server for malware (IMAP/POP3).

        Args:
            server_config: Dictionary with server connection details
                - host: Server hostname
                - port: Server port
                - username: Login username
                - password: Login password
                - protocol: 'imap' or 'pop3'
                - use_ssl: Boolean for SSL/TLS

        Returns:
            Tuple of (success: bool, result: str, threats: List[str])
        """
        # This is a placeholder for email server scanning
        # Implementation would require additional dependencies like imaplib2
        return False, "Email server scanning not yet implemented", []

    def cleanup_temp_files(self):
        """Clean up temporary files created during scanning."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                logger.error(f"Error cleaning up temp files: {e}")


class EmailScanThread(QThread):
    """Thread for scanning email files asynchronously."""
    update_progress = Signal(int)
    update_output = Signal(str)
    finished = Signal(bool, str, list)

    def __init__(self, scanner: EmailScanner, email_files: List[str]):
        super().__init__()
        self.scanner = scanner
        self.email_files = email_files

    def run(self):
        """Run the email scanning process."""
        total_files = len(self.email_files)
        processed_files = 0
        all_threats = []

        for file_path in self.email_files:
            try:
                self.update_output.emit(f"Scanning email file: {os.path.basename(file_path)}")

                is_clean, result, threats = self.scanner.scan_email_file(file_path)

                if not is_clean:
                    self.update_output.emit(f"  Result: {result}")
                    all_threats.extend(threats)
                else:
                    self.update_output.emit(f"  Result: Clean")

                processed_files += 1
                progress = int((processed_files / total_files) * 100)
                self.update_progress.emit(progress)

            except Exception as e:
                self.update_output.emit(f"  Error: {str(e)}")
                processed_files += 1
                progress = int((processed_files / total_files) * 100)
                self.update_progress.emit(progress)

        # Clean up
        self.scanner.cleanup_temp_files()

        # Overall result
        success = len(all_threats) == 0
        result_message = f"Scanned {total_files} email files. {'No threats found' if success else f'{len(all_threats)} threats detected'}"

        self.finished.emit(success, result_message, all_threats)
