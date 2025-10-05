"""
Logging configuration for ClamAV GUI.

This module provides a centralized way to configure and access the application logger.
All logs are saved in the 'logs' directory with comprehensive traceback information.
"""
import os
import sys
import logging
import logging.handlers
import traceback
import threading
import inspect
from pathlib import Path
from datetime import datetime
from types import TracebackType
from typing import Optional, Union, Dict, Any, Type, Callable, Tuple, List

# Log levels mapping
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def get_logs_dir() -> Path:
    """Get the logs directory, create it if it doesn't exist."""
    base_dir = Path(__file__).parent.parent.parent  # Go up from script/utils to project root
    log_dir = base_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def format_traceback(exc_type: Type[BaseException], 
                    exc_value: BaseException, 
                    exc_traceback: Optional[TracebackType]) -> str:
    """Format exception information and stack trace entries."""
    if exc_traceback is None:
        return str(exc_value)
    return ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

# Global variables for exception handling
_handling_exception = False
original_excepthook = None
original_threading_excepthook = None

def setup_logger(name: str = 'ClamAVGUI', 
                log_level: Union[str, int] = 'DEBUG',
                log_dir: Union[str, Path, None] = None,
                max_bytes: int = 20 * 1024 * 1024,  # 20MB per file
                backup_count: int = 14,  # Keep logs for 2 weeks
                log_to_console: bool = True,
                log_to_file: bool = True) -> logging.Logger:
    """
    Configure and return a logger with the specified settings.
    
    Args:
        name: Name of the logger (default: 'ClamAVGUI')
        log_level: Logging level as string ('DEBUG', 'INFO', etc.) or int (default: 'INFO')
        log_dir: Directory to store log files (default: 'logs')
        max_bytes: Maximum log file size in bytes before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 7)
        log_to_console: Whether to log to console (default: True)
        log_to_file: Whether to log to file (default: True)
        
    Returns:
        Configured logger instance
    """
    # Convert string log level to logging constant if needed
    if isinstance(log_level, str):
        log_level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    # Create formatter with detailed format including thread name and process ID
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(process)d - %(threadName)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'  # Milliseconds are added in the format string
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        try:
            # Get or create logs directory
            if log_dir is None:
                log_dir_path = get_logs_dir()
            else:
                log_dir_path = Path(log_dir)
                log_dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create log file with current date in the logs directory
            current_date = datetime.now().strftime('%Y-%m-%d')
            log_file = log_dir_path / f"{name}_{current_date}.log"
            
            # Create rotating file handler with error handling
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8',
                delay=True  # Delay file opening until first write
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_file.absolute()}")
            logger.debug(f"Log level set to: {logging.getLevelName(log_level)}")
            
        except Exception as e:
            logger.critical(
                f"Critical error setting up file logging: {e}", 
                exc_info=True
            )
            # If we can't log to file, at least log to stderr
            if not log_to_console:
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setFormatter(formatter)
                console_handler.setLevel(log_level)
                logger.addHandler(console_handler)
                logger.error("Falling back to stderr logging due to file logging failure")
    
    # Store the original exception handler
    global original_excepthook, original_threading_excepthook
    original_excepthook = sys.excepthook
    original_threading_excepthook = threading.excepthook if hasattr(threading, 'excepthook') else None
    
    # Flag to prevent recursive error handling (already defined at module level)
    
    def handle_exception(exc_type: Type[BaseException], exc_value: BaseException, 
                        exc_traceback: Optional[TracebackType]) -> None:
        """Handle uncaught exceptions with full traceback and context information."""
        global _handling_exception
        
        # Prevent recursive error handling
        if _handling_exception:
            if original_excepthook:
                return original_excepthook(exc_type, exc_value, exc_traceback)
            return
            
        _handling_exception = True
        
        try:
            # Skip keyboard interrupt to allow the program to exit
            if exc_type is not None and issubclass(exc_type, KeyboardInterrupt):
                if original_excepthook:
                    return original_excepthook(exc_type, exc_value, exc_traceback)
                return
            
            # Get the full traceback
            tb_text = format_traceback(exc_type, exc_value, exc_traceback)
            
            # Log the exception with full traceback, but handle potential logging errors
            try:
                logger.critical(
                    "Unhandled exception: %s\nFull traceback:\n%s",
                    str(exc_value) if exc_value else 'No error message',
                    tb_text
                )
            except Exception as log_err:
                # If logging fails, write to stderr as last resort
                sys.stderr.write(f"Error in logging system: {log_err}\n")
                sys.stderr.write(f"Original error: {exc_type.__name__}: {exc_value}\n")
                sys.stderr.write(f"{tb_text}\n")
        
            # Also log the current thread information
            try:
                current_thread = threading.current_thread()
                logger.debug(
                    "Exception in thread %s (alive=%s, daemon=%s, ident=%s)",
                    getattr(current_thread, 'name', 'unknown'),
                    getattr(current_thread, 'is_alive', lambda: 'N/A')(),
                    getattr(current_thread, 'daemon', 'N/A'),
                    getattr(current_thread, 'ident', 'N/A')
                )
            except Exception as e:
                try:
                    logger.error("Error while gathering thread info: %s", str(e))
                except:
                    sys.stderr.write(f"Error while gathering thread info: {e}\n")
            
            # Also log to stderr if not already going there
            try:
                if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stderr 
                          for h in logger.handlers):
                    sys.stderr.write(f"\nUnhandled exception: {tb_text}\n")
            except Exception as e:
                sys.stderr.write(f"Error writing to stderr: {e}\n")
                
        finally:
            _handling_exception = False
            
        # Call the original exception handler if available
        if original_excepthook and original_excepthook != sys.__excepthook__:
            original_excepthook(exc_type, exc_value, exc_traceback)
    
    def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
        """Handle uncaught exceptions in threads with full context."""
        global _handling_exception
        
        # Prevent recursive error handling
        if _handling_exception:
            if original_threading_excepthook:
                return original_threading_excepthook(args)
            return
            
        _handling_exception = True
        
        try:
            thread_name = 'unknown'
            if hasattr(args, 'thread') and args.thread:
                thread = args.thread
                thread_name = getattr(thread, 'name', 'unnamed')
            
            # Safely get exception info from args
            exc_type = getattr(args, 'exc_type', type(args.exc_value) if hasattr(args, 'exc_value') else type(None))
            exc_value = getattr(args, 'exc_value', None)
            exc_traceback = getattr(args, 'exc_traceback', None)
                
            tb_text = format_traceback(exc_type, exc_value, exc_traceback)
            
            # Safely log the error
            try:
                logger.error(
                    "Unhandled exception in thread %s: %s\nFull traceback:\n%s",
                    thread_name,
                    str(exc_value) if exc_value else 'No error message',
                    tb_text
                )
            except Exception as log_err:
                sys.stderr.write(f"Error in thread exception handler logging: {log_err}\n")
                sys.stderr.write(f"Original error in thread {thread_name}: {exc_type.__name__}: {exc_value}\n")
                sys.stderr.write(f"{tb_text}\n")
                
        except Exception as e:
            try:
                logger.critical("Critical error in thread exception handler: %s", str(e))
            except:
                sys.stderr.write(f"Critical error in thread exception handler: {e}\n")
        finally:
            _handling_exception = False
            
            # Call the original exception handler if available
            if original_threading_excepthook and original_threading_excepthook != threading.excepthook:
                original_threading_excepthook(args)
    
    # Set the exception handlers only if they haven't been overridden by something else
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = handle_exception
    
    # Check for threading.excepthook and threading.__excepthook__ safely
    if hasattr(threading, 'excepthook'):
        original_threading_excepthook = getattr(threading, 'excepthook', None)
        threading_excepthook_default = getattr(threading, '__excepthook__', None)
        
        # Only set the excepthook if it hasn't been overridden
        if original_threading_excepthook == threading_excepthook_default:
            threading.excepthook = handle_thread_exception
    
    # Redirect stdout and stderr to logger with thread safety
    class StreamToLogger:
        """Thread-safe stream redirection to logger with protection against recursion."""
        def __init__(self, logger_instance: logging.Logger, log_level: int = logging.INFO):
            self.logger = logger_instance
            self.log_level = log_level
            self.linebuf = ''
            self._lock = threading.RLock()  # Thread lock for thread safety
            self._in_write = False  # Flag to prevent recursion (nn True)
            
        def write(self, buf: str) -> None:
            """Safely write buffer to logger, handling thread safety and preventing recursion."""
            # Skip empty buffers and prevent recursive calls
            if not buf.strip() or self._in_write:
                return
                
            self._in_write = True
            try:
                with self._lock:
                    try:
                        # Safely get the buffer content
                        try:
                            buf_str = str(buf) if buf else ''
                        except Exception as e:
                            sys.__stderr__.write(f"Error converting buffer to string: {e}\n")
                            return
                            
                        # Filter out empty lines and control characters
                        lines = []
                        try:
                            lines = [line for line in buf_str.rstrip().splitlines() if line.strip()]
                        except Exception as e:
                            sys.__stderr__.write(f"Error processing log lines: {e}\n")
                            return
                            
                        for line in lines:
                            # Skip common control messages and potential recursive patterns
                            skip_patterns = (
                                'Not in scanner thread!',
                                'Error in logging system:',
                                'Error while gathering thread info:',
                                'Error writing to stderr:',
                                'Error in thread exception handler logging:',
                                'Critical error in thread exception handler:'
                            )
                            
                            if any(pattern in line for pattern in skip_patterns):
                                continue
                                
                            try:
                                self.logger.log(self.log_level, line.rstrip())
                            except Exception as e:
                                # If logging fails, write to original stderr as last resort
                                # Use direct write to avoid recursion
                                try:
                                    sys.__stderr__.write(f"[Logging Error] {e}: {line}\n")
                                except:
                                    pass  # If even this fails, we're out of options
                    except Exception as e:
                        try:
                            sys.__stderr__.write(f"[Critical Logging Error] {e}\n")
                        except:
                            pass  # If we can't write to stderr, there's nothing more we can do
            finally:
                self._in_write = False
                
        def flush(self) -> None:
            """Flush the stream (no-op as we write immediately)."""
            try:
                sys.__stderr__.flush()
            except:
                pass
    
    # Only redirect if not already redirected to avoid infinite recursion
    # and only in the main thread to prevent Qt thread issues
    if threading.current_thread() is threading.main_thread():
        if not isinstance(sys.stdout, StreamToLogger):
            sys.stdout = StreamToLogger(logger, logging.INFO)
        if not isinstance(sys.stderr, StreamToLogger):
            sys.stderr = StreamToLogger(logger, logging.ERROR)
    else:
        logger.debug("Not in main thread, skipping stream redirection")
    
    # Log Python warnings through the logging system
    logging.captureWarnings(True)
    
    logger.debug("Logger initialized")
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Name of the logger. If None, returns the root logger.
            
    Returns:
        Logger instance with proper configuration
    """
    logger = logging.getLogger(name)
    
    # If this is a new logger, ensure it has at least one handler
    if not logger.handlers and logging.getLogger().handlers:
        # Use the root logger's handlers if available
        logger.handlers = logging.getLogger().handlers
        logger.propagate = False
    
    return logger

# Create default logger instance
logger = setup_logger()

# Example usage:
if __name__ == "__main__":
    # Test logging at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    try:
        1 / 0  # This will cause a division by zero error
    except Exception as e:
        logger.exception("An error occurred")  # This will include the traceback
