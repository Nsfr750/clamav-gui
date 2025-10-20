#!/usr/bin/env python3
"""
Advanced report generator for ClamAV GUI.
Creates comprehensive scan reports with statistics and analysis.
"""
import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class ReportGenerator:
    """Advanced report generator for ClamAV scan results."""

    def __init__(self, output_dir=None):
        """Initialize the report generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir or self.get_default_output_dir()
        self.setup_logging()

    def get_default_output_dir(self):
        """Get the default output directory."""
        if os.name == 'nt':  # Windows
            return os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'ClamAV-GUI', 'reports')
        else:  # Unix-like
            return os.path.expanduser('~/.clamav-gui/reports')

    def setup_logging(self):
        """Setup logging configuration."""
        log_level = logging.INFO

        # Create logs directory
        logs_dir = os.path.dirname(self.output_dir) if self.output_dir else os.path.expanduser('~/.clamav-gui')
        os.makedirs(logs_dir, exist_ok=True)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger('ReportGenerator')

    def generate_scan_report(self, scan_data, output_format='html'):
        """Generate a comprehensive scan report.

        Args:
            scan_data: Dictionary containing scan results and metadata
            output_format: 'html', 'json', 'txt', or 'pdf'
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"scan_report_{timestamp}.{output_format}"

        if output_format == 'html':
            return self.generate_html_report(scan_data, filename)
        elif output_format == 'json':
            return self.generate_json_report(scan_data, filename)
        elif output_format == 'txt':
            return self.generate_text_report(scan_data, filename)
        elif output_format == 'pdf':
            return self.generate_pdf_report(scan_data, filename)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def generate_html_report(self, scan_data, filename):
        """Generate HTML scan report."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClamAV Scan Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        .threat-item {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
        }}
        .threat-clean {{ background-color: #d4edda; color: #155724; }}
        .threat-infected {{ background-color: #f8d7da; color: #721c24; }}
        .threat-error {{ background-color: #fff3cd; color: #856404; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #6c757d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ClamAV GUI Scan Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>Scan Summary</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Files</h3>
                <div class="value">{scan_data.get('total_files', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Clean Files</h3>
                <div class="value" style="color: #28a745;">{scan_data.get('clean_files', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Infected Files</h3>
                <div class="value" style="color: #dc3545;">{scan_data.get('infected_files', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Scan Duration</h3>
                <div class="value">{scan_data.get('duration', 'N/A')}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Scan Details</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Start Time</td><td>{scan_data.get('start_time', 'N/A')}</td></tr>
            <tr><td>End Time</td><td>{scan_data.get('end_time', 'N/A')}</td></tr>
            <tr><td>Target Path</td><td>{scan_data.get('target_path', 'N/A')}</td></tr>
            <tr><td>Scan Options</td><td>{', '.join(scan_data.get('scan_options', []))}</td></tr>
            <tr><td>ClamAV Version</td><td>{scan_data.get('clamav_version', 'N/A')}</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Threat Analysis</h2>
        {self.generate_threats_html(scan_data)}
    </div>

    <div class="section">
        <h2>File Type Analysis</h2>
        <table>
            <tr><th>File Type</th><th>Count</th><th>Percentage</th></tr>
            {self.generate_file_types_html(scan_data)}
        </table>
    </div>

    <div class="footer">
        <p>Report generated by ClamAV GUI - Advanced Antivirus Solution</p>
        <p>© 2025 ClamAV GUI. All rights reserved.</p>
    </div>
</body>
</html>
"""

        # Save HTML file
        output_path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def generate_threats_html(self, scan_data):
        """Generate HTML for threats section."""
        threats = scan_data.get('threats', [])
        if not threats:
            return "<p>No threats detected during this scan.</p>"

        html = []
        for threat in threats:
            status_class = {
                'CLEAN': 'threat-clean',
                'INFECTED': 'threat-infected',
                'ERROR': 'threat-error'
            }.get(threat.get('status', 'UNKNOWN'), 'threat-error')

            html.append(f"""
            <div class="threat-item {status_class}">
                <strong>{threat.get('file', 'Unknown')}</strong><br>
                Status: {threat.get('status', 'Unknown')}<br>
                {f"Threat: {threat.get('threat_name', 'N/A')}<br>" if threat.get('threat_name') else ""}
                {f"Details: {threat.get('details', 'N/A')}" if threat.get('details') else ""}
            </div>
            """)

        return "".join(html)

    def generate_file_types_html(self, scan_data):
        """Generate HTML for file type analysis."""
        file_types = scan_data.get('file_types', {})
        if not file_types:
            return '<tr><td colspan="3">No file type data available</td></tr>'

        html = []
        total = sum(file_types.values())

        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100 if total > 0 else 0
            html.append(f"<tr><td>{ext}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>")

        return "".join(html)

    def generate_json_report(self, scan_data, filename):
        """Generate JSON scan report."""
        output_path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scan_data, f, indent=2, default=str)

        return output_path

    def generate_text_report(self, scan_data, filename):
        """Generate plain text scan report."""
        text_content = f"""
ClamAV GUI Scan Report
{'=' * 40}

Scan Information:
- Start Time: {scan_data.get('start_time', 'N/A')}
- End Time: {scan_data.get('end_time', 'N/A')}
- Duration: {scan_data.get('duration', 'N/A')}
- Target Path: {scan_data.get('target_path', 'N/A')}
- ClamAV Version: {scan_data.get('clamav_version', 'N/A')}

Scan Summary:
- Total Files: {scan_data.get('total_files', 0)}
- Clean Files: {scan_data.get('clean_files', 0)}
- Infected Files: {scan_data.get('infected_files', 0)}

Scan Options:
{chr(10).join(f'- {opt}' for opt in scan_data.get('scan_options', []))}

Threats Detected:
{self.generate_threats_text(scan_data)}

File Type Analysis:
{self.generate_file_types_text(scan_data)}

Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        output_path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        return output_path

    def generate_threats_text(self, scan_data):
        """Generate text for threats section."""
        threats = scan_data.get('threats', [])
        if not threats:
            return "No threats detected."

        text = []
        for threat in threats:
            text.append(f"- {threat.get('file', 'Unknown')}: {threat.get('status', 'Unknown')}")
            if threat.get('threat_name'):
                text.append(f"  Threat: {threat.get('threat_name')}")
            if threat.get('details'):
                text.append(f"  Details: {threat.get('details')}")

        return "\n".join(text)

    def generate_file_types_text(self, scan_data):
        """Generate text for file type analysis."""
        file_types = scan_data.get('file_types', {})
        if not file_types:
            return "No file type data available."

        text = []
        total = sum(file_types.values())

        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100 if total > 0 else 0
            text.append(f"- {ext}: {count} files ({percentage:.1f}%)")

        return "\n".join(text)

    def generate_pdf_report(self, scan_data, filename):
        """Generate PDF scan report (requires reportlab)."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            output_path = os.path.join(self.output_dir, filename)
            os.makedirs(self.output_dir, exist_ok=True)

            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title = Paragraph("ClamAV GUI Scan Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))

            # Summary table
            summary_data = [
                ['Property', 'Value'],
                ['Start Time', scan_data.get('start_time', 'N/A')],
                ['End Time', scan_data.get('end_time', 'N/A')],
                ['Total Files', str(scan_data.get('total_files', 0))],
                ['Clean Files', str(scan_data.get('clean_files', 0))],
                ['Infected Files', str(scan_data.get('infected_files', 0))],
            ]

            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))

            # Threats section
            if scan_data.get('threats'):
                story.append(Paragraph("Threats Detected:", styles['Heading2']))

                for threat in scan_data['threats']:
                    threat_text = f"- {threat.get('file', 'Unknown')}: {threat.get('status', 'Unknown')}"
                    if threat.get('threat_name'):
                        threat_text += f" (Threat: {threat.get('threat_name')})"

                    story.append(Paragraph(threat_text, styles['Normal']))
                    if threat.get('details'):
                        story.append(Paragraph(f"  Details: {threat.get('details')}", styles['Normal']))

                story.append(Spacer(1, 20))

            # Build PDF
            doc.build(story)
            return output_path

        except ImportError:
            print("PDF generation requires reportlab. Install with: pip install reportlab")
            return None


def main():
    """Main function for command line interface."""
    parser = argparse.ArgumentParser(description='ClamAV GUI Report Generator')

    parser.add_argument('input', help='Input file containing scan data (JSON format)')
    parser.add_argument('-f', '--format', choices=['html', 'json', 'txt', 'pdf'],
                       default='html', help='Output format (default: html)')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('--sample', action='store_true', help='Generate sample report')

    args = parser.parse_args()

    generator = ReportGenerator(args.output)

    if args.sample:
        # Generate sample scan data
        sample_data = {
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': '2 minutes 30 seconds',
            'target_path': '/home/user/Documents',
            'total_files': 1500,
            'clean_files': 1495,
            'infected_files': 5,
            'scan_options': ['recursive', 'archives', 'heuristics'],
            'clamav_version': 'ClamAV 1.0.0',
            'threats': [
                {
                    'file': '/home/user/Documents/malware.exe',
                    'status': 'INFECTED',
                    'threat_name': 'Win.Trojan.Agent-12345',
                    'details': 'Trojan horse detected'
                }
            ],
            'file_types': {
                '.exe': 50,
                '.pdf': 200,
                '.docx': 150,
                '.jpg': 800,
                '.txt': 300
            }
        }

        output_file = generator.generate_scan_report(sample_data, args.format)
        if output_file:
            print(f"Sample report generated: {output_file}")

    else:
        # Load scan data from file
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}")
            return

        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                scan_data = json.load(f)

            output_file = generator.generate_scan_report(scan_data, args.format)
            if output_file:
                print(f"Report generated: {output_file}")

        except Exception as e:
            print(f"Error generating report: {e}")


if __name__ == '__main__':
    main()
