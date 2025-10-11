"""
Scan report generator and parser for ClamAV GUI.
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Individual scan result for a file."""
    file_path: str
    status: str  # 'clean', 'infected', 'error', 'skipped'
    threat_name: str = ""
    details: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScanSummary:
    """Summary statistics for a scan."""
    total_files: int = 0
    scanned_files: int = 0
    clean_files: int = 0
    infected_files: int = 0
    errors: int = 0
    skipped: int = 0
    scan_time: float = 0.0
    threats_found: List[str] = None

    def __post_init__(self):
        if self.threats_found is None:
            self.threats_found = []

    def to_dict(self) -> dict:
        data = asdict(self)
        data['threats_found'] = list(set(self.threats_found))  # Remove duplicates
        return data


class ScanReportGenerator:
    """Generates detailed scan reports from ClamAV output."""

    def __init__(self):
        self.scan_results: List[ScanResult] = []
        self.scan_summary = ScanSummary()
        self.start_time = None

    def start_scan(self):
        """Start timing the scan."""
        self.start_time = datetime.now()
        self.scan_results.clear()
        self.scan_summary = ScanSummary()

    def parse_line(self, line: str) -> Optional[ScanResult]:
        """Parse a single line of ClamAV output and return a ScanResult if applicable."""
        line = line.strip()
        if not line:
            return None

        # Pattern for infected files
        infected_pattern = r'(.+):\s*(.+)\s*FOUND'
        infected_match = re.search(infected_pattern, line)

        # Pattern for clean files
        clean_pattern = r'(.+):\s*OK$'
        clean_match = re.search(clean_pattern, line)

        # Pattern for errors
        error_pattern = r'(.+):\s*(.+)\s*ERROR'
        error_match = re.search(error_pattern, line)

        # Pattern for access denied or similar issues
        access_pattern = r'(.+):\s*(Access denied|Permission denied|No such file or directory)'
        access_match = re.search(access_pattern, line, re.IGNORECASE)

        # Pattern for symbolic links or skipped files
        skip_pattern = r'(.+):\s*(Symbolic link|Empty file|Excluded)'
        skip_match = re.search(skip_pattern, line, re.IGNORECASE)

        if infected_match:
            file_path = infected_match.group(1).strip()
            threat_name = infected_match.group(2).strip()
            return ScanResult(
                file_path=file_path,
                status='infected',
                threat_name=threat_name,
                details=f"Infected with: {threat_name}",
                timestamp=datetime.now().isoformat()
            )

        elif clean_match:
            file_path = clean_match.group(1).strip()
            return ScanResult(
                file_path=file_path,
                status='clean',
                details="No threats detected",
                timestamp=datetime.now().isoformat()
            )

        elif error_match:
            file_path = error_match.group(1).strip()
            error_msg = error_match.group(2).strip()
            return ScanResult(
                file_path=file_path,
                status='error',
                details=f"Error: {error_msg}",
                timestamp=datetime.now().isoformat()
            )

        elif access_match:
            file_path = access_match.group(1).strip()
            error_msg = access_match.group(2).strip()
            return ScanResult(
                file_path=file_path,
                status='error',
                details=f"Access error: {error_msg}",
                timestamp=datetime.now().isoformat()
            )

        elif skip_match:
            file_path = skip_match.group(1).strip()
            skip_reason = skip_match.group(2).strip()
            return ScanResult(
                file_path=file_path,
                status='skipped',
                details=f"Skipped: {skip_reason}",
                timestamp=datetime.now().isoformat()
            )

        return None

    def process_scan_output(self, output: str) -> ScanSummary:
        """Process complete scan output and generate summary."""
        lines = output.split('\n')
        results = []

        for line in lines:
            result = self.parse_line(line)
            if result:
                results.append(result)

        # Update summary statistics
        for result in results:
            self.scan_summary.total_files += 1

            if result.status == 'infected':
                self.scan_summary.infected_files += 1
                self.scan_summary.threats_found.append(result.threat_name)
            elif result.status == 'clean':
                self.scan_summary.clean_files += 1
            elif result.status == 'error':
                self.scan_summary.errors += 1
            elif result.status == 'skipped':
                self.scan_summary.skipped += 1

            self.scan_results.append(result)

        # Calculate scan time
        if self.start_time:
            self.scan_summary.scan_time = (datetime.now() - self.start_time).total_seconds()

        return self.scan_summary

    def generate_html_report(self) -> str:
        """Generate an HTML report of the scan results."""
        summary = self.scan_summary

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ClamAV Scan Report</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
                .stat-card {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
                .results {{ margin-top: 20px; }}
                .result-item {{ margin-bottom: 10px; padding: 10px; border-radius: 3px; }}
                .infected {{ background-color: #ffeaa7; border-left: 4px solid #fdcb6e; }}
                .clean {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
                .error {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
                .skipped {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
                .threat-badge {{ background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px; }}
                .timestamp {{ color: #6c757d; font-size: 14px; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ClamAV Scan Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="summary">
                <div class="stat-card">
                    <div class="stat-value">{summary.total_files}</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary.clean_files}</div>
                    <div class="stat-label">Clean Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: {'#e74c3c' if summary.infected_files > 0 else '#28a745'};">{summary.infected_files}</div>
                    <div class="stat-label">Infected Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: {'#dc3545' if summary.errors > 0 else '#28a745'};">{summary.errors}</div>
                    <div class="stat-label">Errors</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary.skipped}</div>
                    <div class="stat-label">Skipped</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary.scan_time:.1f}s</div>
                    <div class="stat-label">Scan Time</div>
                </div>
            </div>
        """

        if summary.threats_found:
            html += f'<h3>Threats Found ({len(set(summary.threats_found))} unique)</h3>'
        else:
            html += '<h3>No Threats Found</h3>'

        html += '<div class="results">'

        if summary.threats_found:
            threat_counts = {}
            for threat in summary.threats_found:
                threat_counts[threat] = threat_counts.get(threat, 0) + 1

            html += "<div style='margin-bottom: 20px;'>"
            for threat, count in sorted(threat_counts.items()):
                html += f'<span class="threat-badge">{threat} ({count})</span> '
            html += "</div>"

        # Group results by status
        infected_results = [r for r in self.scan_results if r.status == 'infected']
        clean_results = [r for r in self.scan_results if r.status == 'clean']
        error_results = [r for r in self.scan_results if r.status == 'error']
        skipped_results = [r for r in self.scan_results if r.status == 'skipped']

        if infected_results:
            html += "<h4>Infected Files</h4>"
            for result in infected_results[:50]:  # Limit to first 50 for readability
                html += f"""
                <div class="result-item infected">
                    <strong>{result.file_path}</strong>
                    <span class="threat-badge">{result.threat_name}</span>
                    <div class="timestamp">{result.timestamp}</div>
                </div>
                """

        if error_results:
            html += "<h4>Errors</h4>"
            for result in error_results[:50]:  # Limit to first 50 for readability
                html += f"""
                <div class="result-item error">
                    <strong>{result.file_path}</strong>
                    <div>{result.details}</div>
                    <div class="timestamp">{result.timestamp}</div>
                </div>
                """

        if skipped_results:
            html += "<h4>Skipped Files</h4>"
            for result in skipped_results[:20]:  # Limit to first 20 for readability
                html += f"""
                <div class="result-item skipped">
                    <strong>{result.file_path}</strong>
                    <div>{result.details}</div>
                </div>
                """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def generate_text_report(self) -> str:
        """Generate a plain text report of the scan results."""
        summary = self.scan_summary

        report = f"""
ClamAV Scan Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 50}

SUMMARY:
--------
Total Files:     {summary.total_files}
Clean Files:     {summary.clean_files}
Infected Files:  {summary.infected_files}
Errors:          {summary.errors}
Skipped:         {summary.skipped}
Scan Time:       {summary.scan_time:.1f} seconds

"""

        if summary.threats_found:
            threat_counts = {}
            for threat in summary.threats_found:
                threat_counts[threat] = threat_counts.get(threat, 0) + 1

            report += """THREATS FOUND:
--------------
"""
            for threat, count in sorted(threat_counts.items()):
                report += f"  {threat}: {count} files\n"

        # Show infected files
        infected_results = [r for r in self.scan_results if r.status == 'infected']
        if infected_results:
            report += """
INFECTED FILES:
---------------
"""
            for result in infected_results[:20]:  # Limit for readability
                report += f"  {result.file_path} -> {result.threat_name}\n"

        # Show errors
        error_results = [r for r in self.scan_results if r.status == 'error']
        if error_results:
            report += """
ERRORS:
-------
"""
            for result in error_results[:10]:  # Limit for readability
                report += f"  {result.file_path} -> {result.details}\n"

        return report
