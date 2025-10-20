#!/usr/bin/env python3
"""
Scan scheduler script for ClamAV GUI.
Allows scheduling automated scans with various options.
"""
import os
import sys
import json
import time
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


class ScanScheduler:
    """Scan scheduler for automated ClamAV scans."""

    def __init__(self, config_file=None):
        """Initialize the scan scheduler.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or self.get_default_config_path()
        self.config = self.load_config()
        self.setup_logging()

    def get_default_config_path(self):
        """Get the default configuration file path."""
        if os.name == 'nt':  # Windows
            app_data = os.getenv('APPDATA', os.path.expanduser('~'))
            return os.path.join(app_data, 'ClamAV-GUI', 'scheduler.json')
        else:  # Unix-like
            return os.path.expanduser('~/.clamav-gui/scheduler.json')

    def load_config(self):
        """Load scheduler configuration."""
        default_config = {
            'scheduled_scans': [],
            'clamscan_path': self.find_clamscan(),
            'log_level': 'INFO',
            'max_log_size': 10,  # MB
            'log_backup_count': 5
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                print("Using default configuration.")

        return default_config

    def save_config(self):
        """Save scheduler configuration."""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)

        except Exception as e:
            print(f"Error saving config: {e}")

    def setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config['log_level'].upper(), logging.INFO)

        # Create logs directory
        if os.name == 'nt':
            logs_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'ClamAV-GUI', 'logs')
        else:
            logs_dir = os.path.expanduser('~/.clamav-gui/logs')

        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, 'scheduler.log')

        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, maxBytes=self.config['max_log_size'] * 1024 * 1024),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger('ScanScheduler')

    def find_clamscan(self):
        """Find the clamscan executable."""
        common_paths = [
            "clamscan",
            "/usr/bin/clamscan",
            "/usr/local/bin/clamscan",
            "C:\\Program Files\\ClamAV\\clamscan.exe",
            "C:\\Program Files (x86)\\ClamAV\\clamscan.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def add_scheduled_scan(self, name, schedule_type, schedule_value, scan_paths, scan_options=None):
        """Add a new scheduled scan.

        Args:
            name: Name of the scheduled scan
            schedule_type: 'daily', 'weekly', 'monthly', or 'interval'
            schedule_value: Time value (hour for daily, day for weekly, etc.)
            scan_paths: List of paths to scan
            scan_options: Scan options dictionary
        """
        scan_config = {
            'name': name,
            'schedule_type': schedule_type,
            'schedule_value': schedule_value,
            'scan_paths': scan_paths,
            'scan_options': scan_options or {},
            'enabled': True,
            'last_run': None,
            'next_run': self.calculate_next_run(schedule_type, schedule_value),
            'created': datetime.now().isoformat()
        }

        self.config['scheduled_scans'].append(scan_config)
        self.save_config()
        self.logger.info(f"Added scheduled scan: {name}")

    def calculate_next_run(self, schedule_type, schedule_value):
        """Calculate the next run time for a scheduled scan."""
        now = datetime.now()

        if schedule_type == 'interval':
            # schedule_value is minutes
            next_run = now + timedelta(minutes=schedule_value)
        elif schedule_type == 'daily':
            # schedule_value is hour (0-23)
            next_run = now.replace(hour=schedule_value, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif schedule_type == 'weekly':
            # schedule_value is day of week (0=Monday, 6=Sunday)
            days_ahead = (schedule_value - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=2, minute=0, second=0, microsecond=0)  # 2 AM
        elif schedule_type == 'monthly':
            # schedule_value is day of month (1-31)
            next_run = now.replace(day=schedule_value, hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)

        return next_run.isoformat()

    def run_scheduled_scans(self):
        """Run all scheduled scans that are due."""
        now = datetime.now()
        scans_to_run = []

        for scan in self.config['scheduled_scans']:
            if not scan.get('enabled', True):
                continue

            next_run = datetime.fromisoformat(scan['next_run'])
            if now >= next_run:
                scans_to_run.append(scan)

        for scan in scans_to_run:
            self.run_scan(scan)

    def run_scan(self, scan_config):
        """Run a specific scan."""
        self.logger.info(f"Running scheduled scan: {scan_config['name']}")

        try:
            # Build clamscan command
            cmd = [self.config['clamscan_path']]

            # Add scan options
            options = scan_config.get('scan_options', {})
            if options.get('recursive', False):
                cmd.append('--recursive')
            if options.get('archives', False):
                cmd.append('--archives')
            if options.get('heuristics', True):
                cmd.append('--heuristic-alerts=yes')
            if options.get('pua', False):
                cmd.append('--detect-pua=yes')

            # Add paths
            for path in scan_config['scan_paths']:
                cmd.append(path)

            # Run scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            # Update scan record
            scan_config['last_run'] = datetime.now().isoformat()
            scan_config['next_run'] = self.calculate_next_run(
                scan_config['schedule_type'],
                scan_config['schedule_value']
            )

            # Log results
            if result.returncode == 0:
                self.logger.info(f"Scan completed successfully: {scan_config['name']}")
            else:
                self.logger.error(f"Scan failed: {scan_config['name']} - {result.stderr}")

        except Exception as e:
            self.logger.error(f"Error running scan {scan_config['name']}: {e}")

        self.save_config()

    def list_scheduled_scans(self):
        """List all scheduled scans."""
        if not self.config['scheduled_scans']:
            print("No scheduled scans configured.")
            return

        print("Scheduled Scans:")
        print("-" * 50)

        for i, scan in enumerate(self.config['scheduled_scans'], 1):
            enabled = "Enabled" if scan.get('enabled', True) else "Disabled"
            next_run = datetime.fromisoformat(scan['next_run']).strftime('%Y-%m-%d %H:%M')
            print(f"{i}. {scan['name']} ({enabled})")
            print(f"   Schedule: {scan['schedule_type']} {scan['schedule_value']}")
            print(f"   Next run: {next_run}")
            print(f"   Paths: {', '.join(scan['scan_paths'])}")
            print()

    def remove_scheduled_scan(self, name):
        """Remove a scheduled scan by name."""
        for scan in self.config['scheduled_scans']:
            if scan['name'] == name:
                self.config['scheduled_scans'].remove(scan)
                self.save_config()
                self.logger.info(f"Removed scheduled scan: {name}")
                print(f"Removed scheduled scan: {name}")
                return

        print(f"Scheduled scan not found: {name}")

    def enable_scan(self, name, enabled=True):
        """Enable or disable a scheduled scan."""
        for scan in self.config['scheduled_scans']:
            if scan['name'] == name:
                scan['enabled'] = enabled
                self.save_config()
                status = "enabled" if enabled else "disabled"
                self.logger.info(f"Scan {name} {status}")
                print(f"Scan '{name}' {status}")
                return

        print(f"Scheduled scan not found: {name}")


def main():
    """Main function for command line interface."""
    parser = argparse.ArgumentParser(description='ClamAV GUI Scan Scheduler')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add scan command
    add_parser = subparsers.add_parser('add', help='Add a scheduled scan')
    add_parser.add_argument('name', help='Name of the scheduled scan')
    add_parser.add_argument('schedule', help='Schedule (daily:HOUR, weekly:DAY, monthly:DAY, interval:MINUTES)')
    add_parser.add_argument('paths', nargs='+', help='Paths to scan')
    add_parser.add_argument('--recursive', action='store_true', help='Enable recursive scanning')
    add_parser.add_argument('--archives', action='store_true', help='Scan archives')

    # List scans command
    subparsers.add_parser('list', help='List scheduled scans')

    # Remove scan command
    remove_parser = subparsers.add_parser('remove', help='Remove a scheduled scan')
    remove_parser.add_argument('name', help='Name of the scan to remove')

    # Enable/disable scan command
    enable_parser = subparsers.add_parser('enable', help='Enable a scheduled scan')
    enable_parser.add_argument('name', help='Name of the scan to enable')

    disable_parser = subparsers.add_parser('disable', help='Disable a scheduled scan')
    disable_parser.add_argument('name', help='Name of the scan to disable')

    # Run scans command
    subparsers.add_parser('run', help='Run all due scheduled scans')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    scheduler = ScanScheduler()

    if args.command == 'add':
        # Parse schedule
        try:
            schedule_type, schedule_value = args.schedule.split(':')
            schedule_value = int(schedule_value)

            # Validate schedule
            if schedule_type == 'daily' and not (0 <= schedule_value <= 23):
                print("Error: Daily schedule must be hour 0-23")
                return
            elif schedule_type == 'weekly' and not (0 <= schedule_value <= 6):
                print("Error: Weekly schedule must be day 0-6 (0=Monday)")
                return
            elif schedule_type == 'monthly' and not (1 <= schedule_value <= 31):
                print("Error: Monthly schedule must be day 1-31")
                return
            elif schedule_type == 'interval' and schedule_value <= 0:
                print("Error: Interval must be positive minutes")
                return

        except (ValueError, IndexError):
            print("Error: Invalid schedule format. Use: daily:HOUR, weekly:DAY, monthly:DAY, or interval:MINUTES")
            return

        # Prepare scan options
        scan_options = {
            'recursive': args.recursive,
            'archives': args.archives,
            'heuristics': True,
            'pua': False
        }

        scheduler.add_scheduled_scan(args.name, schedule_type, schedule_value, args.paths, scan_options)
        print(f"Added scheduled scan: {args.name}")

    elif args.command == 'list':
        scheduler.list_scheduled_scans()

    elif args.command == 'remove':
        scheduler.remove_scheduled_scan(args.name)

    elif args.command == 'enable':
        scheduler.enable_scan(args.name, True)

    elif args.command == 'disable':
        scheduler.enable_scan(args.name, False)

    elif args.command == 'run':
        print("Running scheduled scans...")
        scheduler.run_scheduled_scans()
        print("Completed.")


if __name__ == '__main__':
    main()
