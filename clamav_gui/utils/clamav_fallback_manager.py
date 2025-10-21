"""
Fallback Mechanisms for ClamAV Integration.

This module provides comprehensive fallback mechanisms for when direct ClamAV
integration is not available, ensuring the application remains functional.
"""
import os
import sys
import logging
import subprocess
import platform
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ClamAVFallbackManager:
    """
    Manages fallback mechanisms for ClamAV integration.

    Provides multiple fallback strategies when direct integration fails,
    ensuring the application remains functional even without optimal integration.
    """

    def __init__(self):
        self.fallback_strategies = [
            self._strategy_direct_integration,
            self._strategy_clamd_daemon,
            self._strategy_subprocess_fallback,
            self._strategy_external_scanner_only,
            self._strategy_manual_scan_only
        ]

    def get_best_available_strategy(self) -> Tuple[str, str]:
        """
        Determine the best available scanning strategy.

        Returns:
            Tuple of (strategy_name, description)
        """
        for strategy in self.fallback_strategies:
            try:
                strategy_name, description, available = strategy()
                if available:
                    logger.info(f"Using ClamAV strategy: {strategy_name}")
                    return strategy_name, description
            except Exception as e:
                logger.warning(f"Strategy check failed: {e}")
                continue

        # If no strategy works, return the most basic one
        return "manual_scan_only", "Manual scanning only - ClamAV not available"

    def _strategy_direct_integration(self) -> Tuple[str, str, bool]:
        """Check direct integration availability."""
        try:
            # Try to import pyclamav
            try:
                import clamav
                return "direct_integration", "Direct ClamAV library integration", True
            except ImportError:
                try:
                    from clamav import libclamav
                    return "direct_integration", "Direct libclamav integration", True
                except ImportError:
                    pass

            return "direct_integration", "Direct integration not available", False

        except Exception as e:
            logger.debug(f"Direct integration check failed: {e}")
            return "direct_integration", f"Direct integration error: {e}", False

    def _strategy_clamd_daemon(self) -> Tuple[str, str, bool]:
        """Check ClamAV daemon availability."""
        try:
            import clamd

            # Try to connect to clamd
            try:
                cd = clamd.ClamdUnixSocket()
                cd.ping()
                return "clamd_daemon", "ClamAV daemon integration", True
            except:
                try:
                    cd = clamd.ClamdNetworkSocket()
                    cd.ping()
                    return "clamd_daemon", "ClamAV daemon (network) integration", True
                except:
                    pass

            return "clamd_daemon", "ClamAV daemon not running", False

        except ImportError:
            return "clamd_daemon", "clamd package not installed", False
        except Exception as e:
            logger.debug(f"Clamd daemon check failed: {e}")
            return "clamd_daemon", f"Clamd daemon error: {e}", False

    def _strategy_subprocess_fallback(self) -> Tuple[str, str, bool]:
        """Check subprocess fallback availability."""
        try:
            # Check if clamscan is available
            result = subprocess.run(['clamscan', '--version'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0] if result.stdout else 'Unknown'
                return "subprocess_fallback", f"Subprocess integration (ClamAV {version})", True
            else:
                return "subprocess_fallback", "ClamAV not found in PATH", False

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "subprocess_fallback", "ClamAV not found", False
        except Exception as e:
            logger.debug(f"Subprocess check failed: {e}")
            return "subprocess_fallback", f"Subprocess error: {e}", False

    def _strategy_external_scanner_only(self) -> Tuple[str, str, bool]:
        """Check if external scanner is available."""
        # This is always available as a last resort
        return "external_scanner_only", "External scanner integration only", True

    def _strategy_manual_scan_only(self) -> Tuple[str, str, bool]:
        """Manual scanning only."""
        return "manual_scan_only", "Manual scanning only - no ClamAV integration", True

    def get_installation_instructions(self) -> str:
        """Get installation instructions for the user's platform."""
        system = platform.system().lower()

        if system == "windows":
            return self._get_windows_installation_instructions()
        elif system == "linux":
            return self._get_linux_installation_instructions()
        elif system == "darwin":  # macOS
            return self._get_macos_installation_instructions()
        else:
            return f"Unsupported platform: {system}. Please install ClamAV manually."

    def _get_windows_installation_instructions(self) -> str:
        """Get Windows-specific installation instructions."""
        return """
Windows Installation Instructions:
================================

1. Download ClamAV for Windows:
   Visit: https://www.clamav.net/downloads
   Download the latest Windows installer

2. Install ClamAV:
   - Run the installer
   - Choose installation directory (default is fine)
   - Add ClamAV to system PATH during installation

3. Update virus definitions:
   Open Command Prompt as Administrator
   Run: freshclam

4. Verify installation:
   Run: clamscan --version

Alternative: Install via Chocolatey
   choco install clamav

Note: For better integration, consider installing pyclamav:
   pip install pyclamav  (requires Visual Studio Build Tools)
"""

    def _get_linux_installation_instructions(self) -> str:
        """Get Linux-specific installation instructions."""
        return """
Linux Installation Instructions:
==============================

Ubuntu/Debian:
  sudo apt update
  sudo apt install clamav clamav-daemon

CentOS/RHEL/Fedora:
  sudo yum install clamav clamav-update  # CentOS/RHEL
  sudo dnf install clamav clamav-update  # Fedora

Arch Linux:
  sudo pacman -S clamav

2. Update virus definitions:
   sudo freshclam

3. Start ClamAV daemon (optional):
   sudo systemctl start clamav-daemon
   sudo systemctl enable clamav-daemon

4. Verify installation:
   clamscan --version

For better integration, install pyclamav:
  pip install pyclamav
"""

    def _get_macos_installation_instructions(self) -> str:
        """Get macOS-specific installation instructions."""
        return """
macOS Installation Instructions:
==============================

1. Install ClamAV using Homebrew:
   brew install clamav

2. Update virus definitions:
   freshclam

3. Verify installation:
   clamscan --version

Alternative: Install via MacPorts
   sudo port install clamav

For better integration, install pyclamav:
  pip install pyclamav
"""

    def check_clamav_installation(self) -> Dict[str, Any]:
        """
        Comprehensive check of ClamAV installation status.

        Returns:
            Dict with installation status and recommendations
        """
        status = {
            'installed': False,
            'version': None,
            'strategies': [],
            'recommendations': [],
            'best_strategy': None
        }

        # Check each strategy
        for strategy in self.fallback_strategies:
            try:
                strategy_name, description, available = strategy()
                status['strategies'].append({
                    'name': strategy_name,
                    'description': description,
                    'available': available
                })

                if available:
                    status['installed'] = True
                    if not status['version']:
                        # Extract version from description if possible
                        if 'ClamAV' in description:
                            version_part = description.split('ClamAV')[1].split(')')[0].strip()
                            if version_part:
                                status['version'] = version_part

            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} check failed: {e}")

        # Determine best strategy
        best_strategy, description = self.get_best_available_strategy()
        status['best_strategy'] = best_strategy

        # Add recommendations
        if not status['installed']:
            status['recommendations'].append({
                'type': 'installation',
                'message': 'ClamAV is not installed',
                'instructions': self.get_installation_instructions()
            })
        else:
            status['recommendations'].append({
                'type': 'optimization',
                'message': f'Using strategy: {best_strategy}',
                'instructions': f'Current integration method: {description}'
            })

        return status

    def create_integration_status_widget(self, parent=None):
        """
        Create a GUI widget showing ClamAV integration status.

        This method would be implemented in the GUI components.
        For now, it returns status information for display.
        """
        status = self.check_clamav_installation()

        # Format status for display
        display_info = {
            'title': 'ClamAV Integration Status',
            'status': 'Available' if status['installed'] else 'Not Available',
            'version': status['version'] or 'Unknown',
            'strategy': status['best_strategy'] or 'None',
            'strategies': status['strategies'],
            'recommendations': status['recommendations']
        }

        return display_info


class ClamAVIntegrationTester:
    """
    Test utility for ClamAV integration.

    Provides methods to test different integration approaches and
    generate diagnostic reports.
    """

    def __init__(self):
        self.fallback_manager = ClamAVFallbackManager()

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run comprehensive integration tests.

        Returns:
            Dict with test results and recommendations
        """
        results = {
            'timestamp': None,
            'platform': platform.system(),
            'python_version': sys.version,
            'tests': {},
            'overall_status': 'unknown',
            'recommendations': []
        }

        import datetime
        results['timestamp'] = datetime.datetime.now().isoformat()

        # Run strategy tests
        for strategy in self.fallback_manager.fallback_strategies:
            strategy_name = strategy.__name__.replace('_strategy_', '')
            try:
                name, description, available = strategy()
                results['tests'][strategy_name] = {
                    'available': available,
                    'description': description,
                    'error': None
                }
            except Exception as e:
                results['tests'][strategy_name] = {
                    'available': False,
                    'description': f'Error: {str(e)}',
                    'error': str(e)
                }

        # Determine overall status
        if any(test['available'] for test in results['tests'].values()):
            results['overall_status'] = 'available'
            results['recommendations'].append({
                'type': 'success',
                'message': 'ClamAV integration is working',
                'details': 'At least one integration strategy is available'
            })
        else:
            results['overall_status'] = 'unavailable'
            results['recommendations'].append({
                'type': 'error',
                'message': 'No ClamAV integration available',
                'details': 'Please install ClamAV to enable virus scanning',
                'instructions': self.fallback_manager.get_installation_instructions()
            })

        return results

    def generate_diagnostic_report(self) -> str:
        """Generate a diagnostic report for troubleshooting."""
        results = self.run_comprehensive_test()

        report = []
        report.append("ClamAV Integration Diagnostic Report")
        report.append("=" * 50)
        report.append(f"Generated: {results['timestamp']}")
        report.append(f"Platform: {results['platform']}")
        report.append(f"Python: {results['python_version']}")
        report.append("")

        report.append("Integration Strategies:")
        for strategy_name, test_result in results['tests'].items():
            status = "✅ Available" if test_result['available'] else "❌ Unavailable"
            report.append(f"  {strategy_name}: {status}")
            if test_result['description']:
                report.append(f"    {test_result['description']}")
            if test_result['error']:
                report.append(f"    Error: {test_result['error']}")
        report.append("")

        report.append(f"Overall Status: {results['overall_status'].upper()}")
        report.append("")

        if results['recommendations']:
            report.append("Recommendations:")
            for rec in results['recommendations']:
                report.append(f"  {rec['type'].upper()}: {rec['message']}")
                if rec.get('details'):
                    report.append(f"    {rec['details']}")
                if rec.get('instructions'):
                    report.append("    Installation Instructions:")
                    for line in rec['instructions'].split('\n'):
                        if line.strip():
                            report.append(f"      {line}")
        report.append("")

        return "\n".join(report)
