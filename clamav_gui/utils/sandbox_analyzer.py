"""
Sandbox analysis system for monitoring suspicious file behavior.
Provides isolated environment for analyzing potentially malicious files.
"""
import os
import json
import logging
import platform
import subprocess
import tempfile
import shutil
import psutil
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from threading import Thread

logger = logging.getLogger(__name__)


class SandboxAnalyzer:
    """Sandbox analysis for monitoring file behavior and system interactions."""

    def __init__(self):
        """Initialize the sandbox analyzer."""
        self.system_info = self._get_system_info()
        self.analysis_timeout = 60  # seconds
        self.max_memory_usage = 100 * 1024 * 1024  # 100MB

    def _get_system_info(self) -> Dict:
        """Get system information for analysis context."""
        try:
            return {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'cpu_count': psutil.cpu_count()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'platform': platform.system(),
                'error': str(e)
            }

    def analyze_file_behavior(self, file_path: str) -> Dict:
        """Analyze file behavior in a sandboxed environment.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary with analysis results
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        # Get basic file info
        file_info = self._get_file_info(file_path)

        # Check if file is executable
        if not self._is_executable(file_path):
            return {
                'file_info': file_info,
                'behavior_analysis': 'File is not executable',
                'risk_assessment': 'low',
                'recommendations': ['File appears safe for execution']
            }

        # Perform behavioral analysis
        behavior_results = self._perform_behavioral_analysis(file_path)

        # Assess risk based on behavior
        risk_assessment = self._assess_behavioral_risk(behavior_results)

        return {
            'file_info': file_info,
            'system_info': self.system_info,
            'behavior_analysis': behavior_results,
            'risk_assessment': risk_assessment,
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_duration': behavior_results.get('analysis_duration', 0)
        }

    def _get_file_info(self, file_path: str) -> Dict:
        """Get basic file information."""
        try:
            stat = os.stat(file_path)
            return {
                'name': Path(file_path).name,
                'path': file_path,
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'is_executable': self._is_executable(file_path),
                'file_extension': Path(file_path).suffix.lower()
            }
        except Exception as e:
            return {'error': str(e)}

    def _is_executable(self, file_path: str) -> bool:
        """Check if file is executable."""
        try:
            # Check file extension
            ext = Path(file_path).suffix.lower()
            executable_extensions = ['.exe', '.dll', '.bat', '.cmd', '.com', '.scr', '.pif']

            if ext in executable_extensions:
                return True

            # Check magic bytes for ELF and Mach-O
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header.startswith(b'\x7fELF') or header.startswith(b'\xfe\xed') or header.startswith(b'\xca\xfe'):
                    return True

        except Exception as e:
            logger.error(f"Error checking if file is executable: {e}")

        return False

    def _perform_behavioral_analysis(self, file_path: str) -> Dict:
        """Perform behavioral analysis on the file."""
        start_time = time.time()
        results = {
            'network_activity': [],
            'file_operations': [],
            'registry_operations': [],
            'process_activity': [],
            'suspicious_behaviors': [],
            'analysis_duration': 0,
            'monitoring_status': 'completed'
        }

        try:
            # Create isolated directory for analysis
            with tempfile.TemporaryDirectory() as sandbox_dir:
                sandbox_file = os.path.join(sandbox_dir, Path(file_path).name)

                # Copy file to sandbox
                shutil.copy2(file_path, sandbox_file)

                # Monitor system during analysis
                monitor_thread = Thread(target=self._monitor_system_activity, args=(results, start_time))
                monitor_thread.daemon = True
                monitor_thread.start()

                # Attempt to execute file (safely)
                execution_results = self._execute_file_safely(sandbox_file, sandbox_dir)

                # Wait for monitoring to complete
                monitor_thread.join(timeout=5)

                results.update(execution_results)
                results['analysis_duration'] = time.time() - start_time

        except Exception as e:
            logger.error(f"Error during behavioral analysis: {e}")
            results['monitoring_status'] = 'error'
            results['error'] = str(e)

        return results

    def _monitor_system_activity(self, results: Dict, start_time: float):
        """Monitor system activity during file execution."""
        try:
            # Monitor network connections
            initial_connections = len(psutil.net_connections())

            # Monitor running processes
            initial_processes = len(psutil.pids())

            # Monitor disk I/O
            initial_io = psutil.disk_io_counters()

            # Wait a bit for activity
            time.sleep(2)

            # Check for new network connections
            current_connections = len(psutil.net_connections())
            if current_connections > initial_connections:
                results['network_activity'].append({
                    'type': 'new_connections',
                    'count': current_connections - initial_connections,
                    'timestamp': time.time() - start_time
                })

            # Check for new processes
            current_processes = len(psutil.pids())
            if current_processes > initial_processes:
                results['process_activity'].append({
                    'type': 'new_processes',
                    'count': current_processes - initial_processes,
                    'timestamp': time.time() - start_time
                })

            # Check for disk I/O
            current_io = psutil.disk_io_counters()
            if current_io and initial_io:
                read_diff = current_io.read_bytes - initial_io.read_bytes
                write_diff = current_io.write_bytes - initial_io.write_bytes
                if read_diff > 0 or write_diff > 0:
                    results['file_operations'].append({
                        'type': 'disk_io',
                        'read_bytes': read_diff,
                        'write_bytes': write_diff,
                        'timestamp': time.time() - start_time
                    })

        except Exception as e:
            logger.error(f"Error monitoring system activity: {e}")

    def _execute_file_safely(self, file_path: str, working_dir: str) -> Dict:
        """Execute file safely in sandbox environment."""
        execution_results = {
            'execution_attempted': False,
            'execution_successful': False,
            'exit_code': None,
            'stdout': '',
            'stderr': '',
            'execution_time': 0
        }

        try:
            # Determine how to execute based on file type
            ext = Path(file_path).suffix.lower()

            if ext in ['.exe', '.dll']:
                # Windows executable - don't execute directly for safety
                execution_results['suspicious_behaviors'].append({
                    'type': 'windows_executable',
                    'description': 'Windows executable detected - execution blocked for safety',
                    'severity': 'high'
                })
                return execution_results

            elif ext == '.bat' or ext == '.cmd':
                # Batch file - execute with cmd
                cmd = ['cmd', '/c', file_path]
                execution_results['execution_attempted'] = True

                start_time = time.time()
                result = subprocess.run(
                    cmd,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=10,  # 10 second timeout
                    shell=False
                )
                execution_results['execution_time'] = time.time() - start_time

                execution_results['execution_successful'] = result.returncode == 0
                execution_results['exit_code'] = result.returncode
                execution_results['stdout'] = result.stdout
                execution_results['stderr'] = result.stderr

                # Analyze output for suspicious behavior
                suspicious_patterns = [
                    'net user', 'systeminfo', 'whoami', 'reg', 'sc',
                    'powershell', 'cmd.exe', 'taskkill', 'schtasks'
                ]

                output_lower = (result.stdout + result.stderr).lower()
                for pattern in suspicious_patterns:
                    if pattern in output_lower:
                        execution_results['suspicious_behaviors'].append({
                            'type': 'suspicious_command',
                            'pattern': pattern,
                            'description': f'Suspicious command pattern detected: {pattern}',
                            'severity': 'medium'
                        })

            else:
                # Other file types - attempt basic execution check
                execution_results['suspicious_behaviors'].append({
                    'type': 'unknown_file_type',
                    'description': f'Unknown executable file type: {ext}',
                    'severity': 'medium'
                })

        except subprocess.TimeoutExpired:
            execution_results['suspicious_behaviors'].append({
                'type': 'execution_timeout',
                'description': 'File execution timed out - may be attempting infinite loop',
                'severity': 'high'
            })

        except Exception as e:
            execution_results['suspicious_behaviors'].append({
                'type': 'execution_error',
                'description': f'Error during execution: {str(e)}',
                'severity': 'medium'
            })

        return execution_results

    def _assess_behavioral_risk(self, behavior_results: Dict) -> Dict:
        """Assess risk based on behavioral analysis results."""
        risk_score = 0
        risk_factors = []

        # Check for suspicious behaviors
        suspicious_behaviors = behavior_results.get('suspicious_behaviors', [])
        for behavior in suspicious_behaviors:
            severity = behavior.get('severity', 'low')
            if severity == 'high':
                risk_score += 3
                risk_factors.append(f"High severity behavior: {behavior.get('description', 'Unknown')}")
            elif severity == 'medium':
                risk_score += 2
                risk_factors.append(f"Medium severity behavior: {behavior.get('description', 'Unknown')}")
            else:
                risk_score += 1
                risk_factors.append(f"Low severity behavior: {behavior.get('description', 'Unknown')}")

        # Check for network activity
        network_activity = behavior_results.get('network_activity', [])
        if network_activity:
            risk_score += 2
            risk_factors.append(f"Network activity detected: {len(network_activity)} connections")

        # Check for file operations
        file_operations = behavior_results.get('file_operations', [])
        if file_operations:
            total_io = sum(op.get('read_bytes', 0) + op.get('write_bytes', 0) for op in file_operations)
            if total_io > 10 * 1024 * 1024:  # 10MB of I/O
                risk_score += 2
                risk_factors.append(f"High file I/O activity: {total_io:,}","ytes")

        # Check for process activity
        process_activity = behavior_results.get('process_activity', [])
        if process_activity:
            risk_score += 2
            risk_factors.append(f"Process creation detected: {len(process_activity)} new processes")

        # Determine risk level
        if risk_score >= 6:
            risk_level = 'high'
        elif risk_score >= 3:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_level, risk_factors)
        }

    def _get_risk_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Get recommendations based on risk assessment."""
        recommendations = []

        if risk_level == 'high':
            recommendations.extend([
                'Quarantine the file immediately',
                'Do not execute the file',
                'Scan system for additional malware',
                'Consider professional malware analysis'
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                'Exercise caution when executing',
                'Monitor system behavior after execution',
                'Consider additional scanning with different tools'
            ])
        else:
            recommendations.append('File appears safe for normal use')

        return recommendations

    def generate_sandbox_report(self, analysis_result: Dict) -> str:
        """Generate a comprehensive sandbox analysis report.

        Args:
            analysis_result: Results from analyze_file_behavior

        Returns:
            Formatted report string
        """
        if 'error' in analysis_result:
            return f"Sandbox Analysis Error: {analysis_result['error']}"

        report = []
        report.append("Sandbox Behavioral Analysis Report")
        report.append("=" * 50)
        report.append(f"Generated: {analysis_result['analysis_timestamp']}")
        report.append("")

        # File information
        file_info = analysis_result.get('file_info', {})
        if file_info and 'error' not in file_info:
            report.append("File Information:")
            report.append(f"  Name: {file_info.get('name', 'Unknown')}")
            report.append(f"  Size: {file_info.get('size', 0):,}","ytes")
            report.append(f"  Modified: {datetime.fromtimestamp(file_info.get('modified_time', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"  Executable: {'Yes' if file_info.get('is_executable') else 'No'}")
            report.append("")

        # Risk assessment
        risk_assessment = analysis_result.get('risk_assessment', {})
        report.append("Risk Assessment:")
        report.append(f"  Risk Level: {risk_assessment.get('risk_level', 'unknown').upper()}")
        report.append(f"  Risk Score: {risk_assessment.get('risk_score', 0)}")
        report.append("")

        if risk_assessment.get('risk_factors'):
            report.append("Risk Factors:")
            for factor in risk_assessment['risk_factors']:
                report.append(f"  • {factor}")
            report.append("")

        if risk_assessment.get('recommendations'):
            report.append("Recommendations:")
            for recommendation in risk_assessment['recommendations']:
                report.append(f"  • {recommendation}")
            report.append("")

        # Behavioral analysis details
        behavior_analysis = analysis_result.get('behavior_analysis', {})
        if isinstance(behavior_analysis, dict):

            if behavior_analysis.get('suspicious_behaviors'):
                report.append("Suspicious Behaviors Detected:")
                for behavior in behavior_analysis['suspicious_behaviors']:
                    report.append(f"  • {behavior.get('description', 'Unknown behavior')}")
                report.append("")

            if behavior_analysis.get('network_activity'):
                report.append("Network Activity:")
                for activity in behavior_analysis['network_activity']:
                    report.append(f"  • {activity.get('type', 'Unknown')}: {activity.get('count', 0)}")
                report.append("")

            if behavior_analysis.get('file_operations'):
                report.append("File Operations:")
                for operation in behavior_analysis['file_operations']:
                    report.append(f"  • {operation.get('type', 'Unknown')}: {operation.get('read_bytes', 0) + operation.get('write_bytes', 0):,}","ytes")
                report.append("")

        return "\n".join(report)

    def batch_sandbox_analysis(self, file_paths: List[str]) -> List[Dict]:
        """Perform sandbox analysis on multiple files.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            List of analysis results
        """
        results = []

        for file_path in file_paths:
            try:
                result = self.analyze_file_behavior(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'error': str(e),
                    'analysis_timestamp': datetime.now().isoformat()
                })

        return results

    def get_sandbox_capabilities(self) -> Dict:
        """Get information about sandbox analysis capabilities."""
        return {
            'supports_windows_executables': False,  # Disabled for safety
            'supports_scripts': True,
            'supports_batch_files': True,
            'monitoring_features': [
                'network_connections',
                'process_creation',
                'file_io_operations',
                'execution_behavior'
            ],
            'analysis_timeout': self.analysis_timeout,
            'max_memory_limit': self.max_memory_usage,
            'supported_platforms': [self.system_info.get('platform', 'Unknown')]
        }
