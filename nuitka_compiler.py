#!/usr/bin/env python3
"""
Nuitka Compiler for ClamAV GUI

This script compiles the ClamAV GUI application into a standalone executable
using Nuitka with optimized settings for Windows.
"""

import os
import sys
import shutil
import logging
import platform
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Nuitka-Compiler")

# Constants
PROJECT_NAME = "ClamAV-GUI"
VERSION = "1.1.0"  # Will be updated from version.py
IS_WINDOWS = platform.system() == "Windows"

# Paths
BASE_DIR = Path(__file__).parent.absolute()
SRC_DIR = BASE_DIR / "clamav_gui"
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"
ICON_PATH = BASE_DIR / "assets" / "icon.ico"
VERSION_FILE = SRC_DIR / "version.py"
LOGS_DIR = BASE_DIR / "logs"

# Configure logging
def setup_logging():
    """Configure logging to save to both console and file."""
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Setup logger
    logger = logging.getLogger("Nuitka-Compiler")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = LOGS_DIR / "nuitka_compiler.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logging()

def get_version():
    """Get the current version from version.py"""
    try:
        # Import the version module directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("version", VERSION_FILE)
        version_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(version_module)
        return version_module.__version__
    except Exception as e:
        logger.warning(f"Could not read version from {VERSION_FILE}: {e}")
        return VERSION

def clean_build():
    """Clean up build directories."""
    for directory in [BUILD_DIR, DIST_DIR]:
        if directory.exists():
            logger.info(f"Removing directory: {directory}")
            try:
                shutil.rmtree(directory)
            except Exception as e:
                logger.error(f"Failed to remove {directory}: {e}")

def build_nuitka(onefile=True, clean=False, debug=False, jobs=None, show_console=False):
    """
    Build the application using Nuitka.
    
    Args:
        onefile: If True, create a single executable file.
        clean: If True, clean build directories before building.
        debug: If True, create a debug build.
        jobs: Number of parallel jobs for compilation.
        show_console: If True, keep console window visible for debugging.
    """
    version = get_version()
    logger.info(f"Building {PROJECT_NAME} v{version}")
    
    if clean:
        clean_build()
    
    # Create output directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    
    # Base Nuitka command - use MinGW64 to avoid Windows path issues
    cmd = [
        sys.executable, "-m", "nuitka",
        "--follow-imports",
        "--show-progress",
        "--standalone",
        # Use MinGW64 to avoid MSVC Windows path issues
        "--mingw64",
        # Minimal options to avoid Scons issues
        "--assume-yes-for-downloads",
        # Windows-specific optimizations
        "--windows-disable-console" if (IS_WINDOWS and not show_console) else None,
        # Output configuration
        f"--output-dir={DIST_DIR}",
        f"--windows-icon-from-ico={ICON_PATH}" if (IS_WINDOWS and ICON_PATH.exists()) else None,
        # Use onefile format
        "--onefile",
        # Package and data inclusion
        "--include-package=clamav_gui",
        f"--include-data-dir={BASE_DIR / 'assets'}=assets",
        f"--include-data-dir={BASE_DIR / 'clamav_gui' / 'lang'}=clamav_gui/lang",
        # Minimal PySide6 support
        "--enable-plugin=pyside6",
        "--include-qt-plugins=platforms",
        # Windows metadata
        "--windows-company-name=Tuxxle",
        "--output-filename=ClamAV-GUI.exe" if IS_WINDOWS else "--output-filename=ClamAV-GUI",
        f"--windows-file-version={version}",
        f"--windows-product-version={version}",
        f"--windows-product-name={PROJECT_NAME}",
        f"--windows-file-description={PROJECT_NAME} - A graphical interface for ClamAV Antivirus",
        "--copyright=© Copyright 2025 Nsfr750 - All Rights Reserved",
        # Main script
        str(SRC_DIR / "__main__.py")
    ]
    
    # Filter out None values
    cmd = [arg for arg in cmd if arg is not None]
    
    # Log the command for debugging
    logger.debug("Command: %s", " ".join(f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in cmd))
    
    # Run Nuitka
    logger.info("Starting Nuitka compilation...")
    
    try:
        # Run the command with the current environment
        env = os.environ.copy()
        if IS_WINDOWS:
            # Remove MSVC environment variables when using MinGW64
            env.pop("VSCMD_VERB_LOGGER", None)
            # Fix Windows path issues for MinGW64
            env["NUITKA_NO_DEPLOYMENT_FLAG_SELF_EXECUTION"] = "1"
        
        logger.info("Executing Nuitka command...")
        result = subprocess.run(
            cmd,
            check=False,  # We'll handle the error ourselves
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1800  # 30 minute timeout for compilation
        )
        
        # Log the output with better formatting
        if result.stdout:
            logger.debug("Nuitka stdout:\n%s", result.stdout)
        if result.stderr:
            # Only log stderr as error if compilation failed
            if result.returncode != 0:
                logger.error("Nuitka stderr:\n%s", result.stderr)
            else:
                logger.debug("Nuitka stderr:\n%s", result.stderr)
            
        if result.returncode != 0:
            logger.error("Nuitka compilation failed with return code %d", result.returncode)
            logger.error("Check the logs above for detailed error information")
            return False
            
        logger.info("Compilation completed successfully!")
        logger.info(f"Executable is available in: {DIST_DIR}")
        
        # Verify the output file exists
        output_file = DIST_DIR / ("ClamAV-GUI.exe" if IS_WINDOWS else "ClamAV-GUI")
        if output_file.exists():
            size = output_file.stat().st_size
            logger.info(f"Output file size: {size / (1024*1024):.2f} MB")
        else:
            logger.warning("Output file not found after compilation!")
            
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Nuitka compilation timed out after 30 minutes")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Nuitka compilation failed with return code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Error during compilation: {e}", exc_info=True)
        return False


def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description=f"Build {PROJECT_NAME} with Nuitka")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building"
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        default=True,
        help="Create a single executable file (default)"
    )
    parser.add_argument(
        "--dir",
        dest="onefile",
        action="store_false",
        help="Create a directory with the executable and dependencies instead of a single file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--debug-build",
        dest="debug_build",
        action="store_true",
        help="Create a debug build with tracebacks and assertions"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        metavar="N",
        help="Number of parallel jobs for compilation (default: number of CPU cores)"
    )
    parser.add_argument(
        "--show-console",
        action="store_true",
        help="Keep console window visible for debugging (Windows only)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Handle custom output directory
    if hasattr(args, 'output_dir') and args.output_dir:
        global DIST_DIR
        DIST_DIR = Path(args.output_dir).absolute()
        logger.info(f"Using custom output directory: {DIST_DIR}")
    
    success = build_nuitka(
        onefile=args.onefile, 
        clean=args.clean,
        debug=args.debug_build,
        jobs=args.jobs,
        show_console=args.show_console
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
