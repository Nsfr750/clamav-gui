"""
Advanced reporting system with analytics and threat intelligence for ClamAV GUI.
Provides detailed scan reports, threat analysis, and export capabilities.
"""
import os
import json
import csv
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class AdvancedReporting:
    """Advanced reporting system for ClamAV scan results and threat analysis."""

    def __init__(self, scan_history_file: str = None):
        """Initialize the advanced reporting system.

        Args:
            scan_history_file: Path to scan history file (default: user's AppData/ClamAV/scan_history.json)
        """
        if scan_history_file is None:
            app_data = os.getenv('APPDATA') if os.name == 'nt' else os.path.expanduser('~')
            clamav_dir = os.path.join(app_data, 'ClamAV')
            os.makedirs(clamav_dir, exist_ok=True)
            self.scan_history_file = os.path.join(clamav_dir, 'scan_history.json')
        else:
            self.scan_history_file = scan_history_file

        self.scan_history = self.load_scan_history()
        self.threat_intelligence = self.load_threat_intelligence()

    def load_scan_history(self) -> List[Dict]:
        """Load scan history from file."""
        try:
            if os.path.exists(self.scan_history_file):
                with open(self.scan_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading scan history: {e}")
            return []

    def save_scan_history(self):
        """Save scan history to file."""
        try:
            with open(self.scan_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.scan_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving scan history: {e}")

    def add_scan_result(self, scan_data: Dict):
        """Add a scan result to the history.

        Args:
            scan_data: Dictionary containing scan information
        """
        scan_entry = {
            'timestamp': datetime.now().isoformat(),
            'scan_type': scan_data.get('scan_type', 'unknown'),
            'target': scan_data.get('target', ''),
            'total_files': scan_data.get('total_files', 0),
            'scanned_files': scan_data.get('scanned_files', 0),
            'threats_found': scan_data.get('threats_found', 0),
            'threats': scan_data.get('threats', []),
            'scan_time_seconds': scan_data.get('scan_time_seconds', 0),
            'clamav_version': scan_data.get('clamav_version', ''),
            'database_version': scan_data.get('database_version', ''),
            'settings_used': scan_data.get('settings_used', {})
        }

        self.scan_history.append(scan_entry)

        # Keep history manageable (last 1000 scans)
        if len(self.scan_history) > 1000:
            self.scan_history = self.scan_history[-1000:]

        self.save_scan_history()

    def load_threat_intelligence(self) -> Dict:
        """Load threat intelligence data."""
        # In a real implementation, this would connect to threat intelligence feeds
        # For now, we'll use a basic local database
        try:
            app_data = os.getenv('APPDATA') if os.name == 'nt' else os.path.expanduser('~')
            ti_file = os.path.join(app_data, 'ClamAV', 'threat_intelligence.json')

            if os.path.exists(ti_file):
                with open(ti_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_threat_intelligence()
        except Exception as e:
            logger.error(f"Error loading threat intelligence: {e}")
            return self._get_default_threat_intelligence()

    def _get_default_threat_intelligence(self) -> Dict:
        """Get default threat intelligence data."""
        return {
            'threat_categories': {
                'Trojan': {'description': 'Malicious software that disguises itself as legitimate software', 'severity': 'high'},
                'Virus': {'description': 'Self-replicating malware that infects files', 'severity': 'high'},
                'Worm': {'description': 'Self-replicating malware that spreads via networks', 'severity': 'high'},
                'Adware': {'description': 'Software that displays unwanted advertisements', 'severity': 'medium'},
                'Spyware': {'description': 'Software that secretly monitors user activity', 'severity': 'medium'},
                'PUA': {'description': 'Potentially Unwanted Application', 'severity': 'low'},
                'HackTool': {'description': 'Tools used by hackers for malicious purposes', 'severity': 'high'}
            },
            'common_threats': [
                'Win.Trojan.Generic',
                'Win.Virus.Generic',
                'Win.Worm.Generic',
                'Win.Adware.Generic',
                'Win.Spyware.Generic'
            ]
        }

    def generate_scan_report(self, scan_id: str = None, format_type: str = 'html') -> str:
        """Generate a comprehensive scan report.

        Args:
            scan_id: Specific scan ID to report on (None for latest)
            format_type: Report format ('html', 'pdf', 'json')

        Returns:
            Generated report as string
        """
        # Get scan data
        if scan_id:
            scan_data = self._find_scan_by_id(scan_id)
        else:
            scan_data = self.scan_history[-1] if self.scan_history else None

        if not scan_data:
            return "No scan data available"

        # Generate report based on format
        if format_type.lower() == 'html':
            return self._generate_html_report(scan_data)
        elif format_type.lower() == 'json':
            return json.dumps(scan_data, indent=2, ensure_ascii=False)
        else:
            return self._generate_text_report(scan_data)

    def _generate_html_report(self, scan_data: Dict) -> str:
        """Generate HTML format report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ClamAV Scan Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .threat {{ background-color: #ffebee; padding: 10px; margin: 5px 0; border-left: 4px solid #f44336; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ClamAV Advanced Scan Report</h1>
                <p><strong>Scan Date:</strong> {datetime.fromisoformat(scan_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Target:</strong> {scan_data['target']}</p>
                <p><strong>Scan Type:</strong> {scan_data['scan_type']}</p>
            </div>

            <div class="stats">
                <div class="stat-box">
                    <h3>Files Scanned</h3>
                    <p style="font-size: 24px; color: #2196f3;">{scan_data['scanned_files']:,}</p>
                </div>
                <div class="stat-box">
                    <h3>Threats Found</h3>
                    <p style="font-size: 24px; color: #f44336;">{scan_data['threats_found']:,}</p>
                </div>
                <div class="stat-box">
                    <h3>Scan Time</h3>
                    <p style="font-size: 24px; color: #4caf50;">{scan_data['scan_time_seconds']:.1f}s</p>
                </div>
            </div>

            <div class="section">
                <h2>Threat Analysis</h2>
        """

        if scan_data['threats']:
            html += """
                <table>
                    <tr><th>Threat Name</th><th>Category</th><th>Severity</th><th>Description</th></tr>
            """

            for threat in scan_data['threats']:
                threat_name = threat.get('name', 'Unknown')
                category = self._categorize_threat(threat_name)
                severity = self._get_threat_severity(category)
                description = self._get_threat_description(category)

                html += f"""
                    <tr>
                        <td>{threat_name}</td>
                        <td>{category}</td>
                        <td><span style="color: {self._get_severity_color(severity)};">{severity}</span></td>
                        <td>{description}</td>
                    </tr>
                """

            html += "</table>"
        else:
            html += "<p>No threats detected in this scan.</p>"

        html += """
            </div>

            <div class="section">
                <h2>Scan Configuration</h2>
                <table>
        """

        settings = scan_data.get('settings_used', {})
        for key, value in settings.items():
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"

        html += """
                </table>
            </div>
        </body>
        </html>
        """

        return html

    def _generate_text_report(self, scan_data: Dict) -> str:
        """Generate text format report."""
        report = []
        report.append("ClamAV Advanced Scan Report")
        report.append("=" * 50)
        report.append(f"Scan Date: {datetime.fromisoformat(scan_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Target: {scan_data['target']}")
        report.append(f"Scan Type: {scan_data['scan_type']}")
        report.append("")
        report.append("Scan Statistics:")
        report.append(f"  Files Scanned: {scan_data['scanned_files']:,}")
        report.append(f"  Threats Found: {scan_data['threats_found']:,}")
        report.append(f"  Scan Time: {scan_data['scan_time_seconds']:.1f} seconds")
        report.append("")

        if scan_data['threats']:
            report.append("Threats Detected:")
            report.append("-" * 20)
            for i, threat in enumerate(scan_data['threats'], 1):
                threat_name = threat.get('name', 'Unknown')
                category = self._categorize_threat(threat_name)
                severity = self._get_threat_severity(category)
                report.append(f"{i}. {threat_name}")
                report.append(f"   Category: {category}")
                report.append(f"   Severity: {severity}")
                report.append(f"   Description: {self._get_threat_description(category)}")
                report.append("")
        else:
            report.append("No threats detected in this scan.")

        return "\n".join(report)

    def generate_analytics_report(self, days: int = 30) -> Dict:
        """Generate analytics report for the specified period.

        Args:
            days: Number of days to include in the report

        Returns:
            Dictionary containing analytics data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_scans = []

        for scan in self.scan_history:
            try:
                scan_date = datetime.fromisoformat(scan['timestamp'])
                if scan_date > cutoff_date:
                    recent_scans.append(scan)
            except:
                continue

        if not recent_scans:
            return {'error': 'No scan data available for the specified period'}

        # Calculate statistics
        total_scans = len(recent_scans)
        total_files = sum(scan['scanned_files'] for scan in recent_scans)
        total_threats = sum(scan['threats_found'] for scan in recent_scans)
        total_scan_time = sum(scan['scan_time_seconds'] for scan in recent_scans)

        # Threat analysis
        threat_counts = Counter()
        threat_categories = Counter()

        for scan in recent_scans:
            for threat in scan['threats']:
                threat_name = threat.get('name', 'Unknown')
                threat_counts[threat_name] += 1
                category = self._categorize_threat(threat_name)
                threat_categories[category] += 1

        # Scan type distribution
        scan_types = Counter(scan['scan_type'] for scan in recent_scans)

        # Performance metrics
        avg_scan_time = total_scan_time / total_scans if total_scans > 0 else 0
        avg_files_per_scan = total_files / total_scans if total_scans > 0 else 0
        threat_rate = (total_threats / total_files * 100) if total_files > 0 else 0

        return {
            'period_days': days,
            'total_scans': total_scans,
            'total_files_scanned': total_files,
            'total_threats_found': total_threats,
            'average_scan_time': round(avg_scan_time, 2),
            'average_files_per_scan': round(avg_files_per_scan, 0),
            'threat_detection_rate': round(threat_rate, 4),
            'most_common_threats': threat_counts.most_common(10),
            'threat_categories': dict(threat_categories),
            'scan_types': dict(scan_types),
            'trends': self._calculate_trends(recent_scans)
        }

    def _calculate_trends(self, scans: List[Dict]) -> Dict:
        """Calculate scan trends over time."""
        # Group scans by day
        daily_stats = defaultdict(lambda: {'scans': 0, 'files': 0, 'threats': 0, 'time': 0})

        for scan in scans:
            try:
                scan_date = datetime.fromisoformat(scan['timestamp'])
                day_key = scan_date.strftime('%Y-%m-%d')

                daily_stats[day_key]['scans'] += 1
                daily_stats[day_key]['files'] += scan['scanned_files']
                daily_stats[day_key]['threats'] += scan['threats_found']
                daily_stats[day_key]['time'] += scan['scan_time_seconds']
            except:
                continue

        # Calculate daily averages
        trends = []
        for day, stats in sorted(daily_stats.items()):
            trends.append({
                'date': day,
                'scans': stats['scans'],
                'files_scanned': stats['files'],
                'threats_found': stats['threats'],
                'avg_scan_time': round(stats['time'] / stats['scans'], 2) if stats['scans'] > 0 else 0,
                'threat_rate': round((stats['threats'] / stats['files'] * 100), 4) if stats['files'] > 0 else 0
            })

        return trends

    def generate_threat_intelligence_report(self) -> str:
        """Generate a threat intelligence report."""
        analytics = self.generate_analytics_report(30)  # Last 30 days

        if 'error' in analytics:
            return analytics['error']

        report = []
        report.append("ClamAV Threat Intelligence Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("Executive Summary:")
        report.append(f"  Total Scans: {analytics['total_scans']}")
        report.append(f"  Files Scanned: {analytics['total_files_scanned']:,}")
        report.append(f"  Threats Detected: {analytics['total_threats_found']:,}")
        report.append(f"  Threat Detection Rate: {analytics['threat_detection_rate']:.2f}%")
        report.append("")

        if analytics['most_common_threats']:
            report.append("Most Common Threats:")
            for threat, count in analytics['most_common_threats'][:10]:
                percentage = (count / analytics['total_threats_found'] * 100) if analytics['total_threats_found'] > 0 else 0
                report.append(f"  {threat}: {count} occurrences ({percentage:.1f}%)")
            report.append("")

        report.append("Threat Categories:")
        for category, count in analytics['threat_categories'].items():
            percentage = (count / analytics['total_threats_found'] * 100) if analytics['total_threats_found'] > 0 else 0
            severity = self._get_threat_severity(category)
            report.append(f"  {category}: {count} ({percentage:.1f}%) - {severity} severity")

        return "\n".join(report)

    def export_report(self, report_data: str, file_path: str, format_type: str = 'txt') -> bool:
        """Export a report to a file.

        Args:
            report_data: Report content as string
            file_path: Path to save the report
            format_type: File format ('txt', 'html', 'csv', 'json')

        Returns:
            True if successful, False otherwise
        """
        try:
            if format_type.lower() == 'csv':
                return self._export_csv(report_data, file_path)
            elif format_type.lower() == 'json':
                return self._export_json(report_data, file_path)
            else:
                # Default to text file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_data)
                return True

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False

    def _export_csv(self, report_data: str, file_path: str) -> bool:
        """Export report as CSV."""
        try:
            lines = report_data.split('\n')
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for line in lines:
                    if ':' in line and not line.startswith('='):
                        key, value = line.split(':', 1)
                        writer.writerow([key.strip(), value.strip()])
                    else:
                        writer.writerow([line])
            return True
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return False

    def _export_json(self, report_data: str, file_path: str) -> bool:
        """Export report as JSON."""
        try:
            # Try to parse as JSON, otherwise create structured data
            try:
                json_data = json.loads(report_data)
            except:
                # Convert text report to structured format
                json_data = {'report_text': report_data, 'export_time': datetime.now().isoformat()}
                json_data.update(self.generate_analytics_report())

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return False

    def _find_scan_by_id(self, scan_id: str) -> Optional[Dict]:
        """Find a scan by its ID."""
        for scan in self.scan_history:
            if scan.get('id') == scan_id:
                return scan
        return None

    def _categorize_threat(self, threat_name: str) -> str:
        """Categorize a threat based on its name."""
        threat_lower = threat_name.lower()

        if any(term in threat_lower for term in ['trojan', 'troj']):
            return 'Trojan'
        elif any(term in threat_lower for term in ['virus', 'vir']):
            return 'Virus'
        elif any(term in threat_lower for term in ['worm']):
            return 'Worm'
        elif any(term in threat_lower for term in ['adware', 'adw']):
            return 'Adware'
        elif any(term in threat_lower for term in ['spyware', 'spy']):
            return 'Spyware'
        elif any(term in threat_lower for term in ['pua', 'pup']):
            return 'PUA'
        elif any(term in threat_lower for term in ['hacktool', 'hack']):
            return 'HackTool'
        else:
            return 'Unknown'

    def _get_threat_severity(self, category: str) -> str:
        """Get severity level for a threat category."""
        ti = self.threat_intelligence.get('threat_categories', {})
        return ti.get(category, {}).get('severity', 'medium')

    def _get_threat_description(self, category: str) -> str:
        """Get description for a threat category."""
        ti = self.threat_intelligence.get('threat_categories', {})
        return ti.get(category, {}).get('description', 'Unknown threat type')

    def _get_severity_color(self, severity: str) -> str:
        """Get color code for severity level."""
        colors = {
            'high': '#f44336',
            'medium': '#ff9800',
            'low': '#4caf50'
        }
        return colors.get(severity.lower(), '#757575')
