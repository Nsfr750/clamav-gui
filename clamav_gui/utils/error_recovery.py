"""
Error recovery system with automatic retry mechanisms for failed operations.
Provides resilient operation handling for network timeouts, file access errors, and system failures.
"""
import time
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be recovered from."""
    NETWORK_TIMEOUT = "network_timeout"
    FILE_ACCESS = "file_access"
    DATABASE_ERROR = "database_error"
    SCAN_INTERRUPTION = "scan_interruption"
    MEMORY_ERROR = "memory_error"
    PERMISSION_ERROR = "permission_error"
    SYSTEM_ERROR = "system_error"


class RetryStrategy(Enum):
    """Retry strategies for different error types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


class ErrorRecoveryManager:
    """Manages error recovery and retry mechanisms for various operations."""

    def __init__(self):
        """Initialize the error recovery manager."""
        self.retry_attempts = {
            ErrorType.NETWORK_TIMEOUT: 3,
            ErrorType.FILE_ACCESS: 2,
            ErrorType.DATABASE_ERROR: 2,
            ErrorType.SCAN_INTERRUPTION: 1,
            ErrorType.MEMORY_ERROR: 1,
            ErrorType.PERMISSION_ERROR: 1,
            ErrorType.SYSTEM_ERROR: 2,
        }

        self.retry_delays = {
            ErrorType.NETWORK_TIMEOUT: [1, 2, 5],  # Exponential backoff
            ErrorType.FILE_ACCESS: [0.5, 1],       # Linear backoff
            ErrorType.DATABASE_ERROR: [1, 2],      # Linear backoff
            ErrorType.SCAN_INTERRUPTION: [0],      # Immediate retry
            ErrorType.MEMORY_ERROR: [0],           # Immediate retry
            ErrorType.PERMISSION_ERROR: [0],       # Immediate retry
            ErrorType.SYSTEM_ERROR: [1, 3],        # Linear backoff
        }

        self.error_history = []
        self.max_history_size = 100

    def classify_error(self, error: Exception) -> ErrorType:
        """Classify an exception into an error type.

        Args:
            error: The exception to classify

        Returns:
            ErrorType enum value
        """
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()

        if any(term in error_msg for term in ['timeout', 'connection', 'network']):
            return ErrorType.NETWORK_TIMEOUT
        elif any(term in error_msg for term in ['permission', 'access denied', 'forbidden']):
            return ErrorType.PERMISSION_ERROR
        elif any(term in error_msg for term in ['file not found', 'no such file', 'path not found']):
            return ErrorType.FILE_ACCESS
        elif any(term in error_msg for term in ['database', 'sqlite', 'connection']):
            return ErrorType.DATABASE_ERROR
        elif any(term in error_msg for term in ['memory', 'out of memory']):
            return ErrorType.MEMORY_ERROR
        elif any(term in error_msg for term in ['interrupted', 'cancelled']):
            return ErrorType.SCAN_INTERRUPTION
        else:
            return ErrorType.SYSTEM_ERROR

    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if an operation should be retried.

        Args:
            error_type: Type of error that occurred
            attempt: Current attempt number (0-based)

        Returns:
            True if should retry, False otherwise
        """
        max_attempts = self.retry_attempts.get(error_type, 1)
        return attempt < max_attempts

    def get_retry_delay(self, error_type: ErrorType, attempt: int) -> float:
        """Get the delay before retrying an operation.

        Args:
            error_type: Type of error that occurred
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delays = self.retry_delays.get(error_type, [0])
        if attempt < len(delays):
            return delays[attempt]
        else:
            # Default to last delay or exponential backoff
            return delays[-1] if delays else 1.0

    def execute_with_retry(self, func: Callable, *args, error_type: ErrorType = None, **kwargs) -> Any:
        """Execute a function with automatic retry on failures.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            error_type: Override error type classification (optional)
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        max_attempts = self.retry_attempts.get(error_type or ErrorType.SYSTEM_ERROR, 3)

        for attempt in range(max_attempts):
            try:
                result = func(*args, **kwargs)

                # Log successful retry if not first attempt
                if attempt > 0:
                    logger.info(f"Operation succeeded after {attempt + 1} attempts")

                return result

            except Exception as e:
                last_error = e
                error_type_actual = error_type or self.classify_error(e)

                # Log the error
                self._log_error(e, attempt + 1, max_attempts)

                # Check if we should retry
                if not self.should_retry(error_type_actual, attempt):
                    break

                # Wait before retry
                delay = self.get_retry_delay(error_type_actual, attempt)
                if delay > 0:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        # All retries failed
        logger.error(f"All retry attempts failed after {max_attempts} attempts")
        raise last_error

    def _log_error(self, error: Exception, attempt: int, max_attempts: int):
        """Log an error occurrence."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'error_type': type(error).__name__,
            'attempt': attempt,
            'max_attempts': max_attempts,
            'traceback': str(error.__traceback__) if hasattr(error, '__traceback__') else None
        }

        self.error_history.append(error_entry)

        # Keep history size manageable
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]

        logger.warning(f"Error on attempt {attempt}/{max_attempts}: {error}")

    def get_error_statistics(self) -> Dict:
        """Get statistics about error occurrences.

        Returns:
            Dictionary with error statistics
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'error_types': {},
                'recent_errors': 0,
                'success_rate': 100.0
            }

        # Count errors by type
        error_types = {}
        for entry in self.error_history:
            error_type = entry.get('error_type', 'Unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Count recent errors (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = 0
        for entry in self.error_history:
            try:
                error_time = datetime.fromisoformat(entry['timestamp'])
                if error_time > cutoff:
                    recent_errors += 1
            except:
                pass

        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'recent_errors': recent_errors,
            'success_rate': 100.0  # This would need to be calculated based on actual success/failure tracking
        }

    def clear_error_history(self):
        """Clear the error history."""
        self.error_history.clear()
        logger.info("Error history cleared")


def retry_on_error(max_attempts: int = 3, delay: float = 1.0, error_types: List[ErrorType] = None):
    """Decorator for automatic retry on specific error types.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
        error_types: List of error types to retry on (if None, retry on all)

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            recovery_manager = ErrorRecoveryManager()

            # Override retry settings for specific error types
            for error_type in (error_types or []):
                recovery_manager.retry_attempts[error_type] = max_attempts
                recovery_manager.retry_delays[error_type] = [delay] * max_attempts

            return recovery_manager.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator


class NetworkErrorRecovery:
    """Specialized error recovery for network operations."""

    def __init__(self):
        """Initialize network error recovery."""
        self.recovery_manager = ErrorRecoveryManager()

    def download_with_retry(self, url: str, download_func: Callable, *args, **kwargs) -> Any:
        """Download a file with automatic retry on network errors.

        Args:
            url: URL to download from
            download_func: Function that performs the download
            *args, **kwargs: Arguments for the download function

        Returns:
            Result of the download function
        """
        return self.recovery_manager.execute_with_retry(
            download_func,
            url,
            *args,
            error_type=ErrorType.NETWORK_TIMEOUT,
            **kwargs
        )


class DatabaseErrorRecovery:
    """Specialized error recovery for database operations."""

    def __init__(self):
        """Initialize database error recovery."""
        self.recovery_manager = ErrorRecoveryManager()

    def execute_query_with_retry(self, query_func: Callable, *args, **kwargs) -> Any:
        """Execute a database query with automatic retry.

        Args:
            query_func: Function that executes the database query
            *args, **kwargs: Arguments for the query function

        Returns:
            Result of the query function
        """
        return self.recovery_manager.execute_with_retry(
            query_func,
            *args,
            error_type=ErrorType.DATABASE_ERROR,
            **kwargs
        )


class ScanErrorRecovery:
    """Specialized error recovery for scan operations."""

    def __init__(self):
        """Initialize scan error recovery."""
        self.recovery_manager = ErrorRecoveryManager()

    def scan_with_retry(self, scan_func: Callable, *args, **kwargs) -> Any:
        """Perform a scan operation with automatic retry.

        Args:
            scan_func: Function that performs the scan
            *args, **kwargs: Arguments for the scan function

        Returns:
            Result of the scan function
        """
        return self.recovery_manager.execute_with_retry(
            scan_func,
            *args,
            error_type=ErrorType.SCAN_INTERRUPTION,
            **kwargs
        )
