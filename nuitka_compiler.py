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
VERSION = "1.0.0"  # Will be updated from version.py
IS_WINDOWS = platform.system() == "Windows"

# Paths
BASE_DIR = Path(__file__).parent.absolute()
SRC_DIR = BASE_DIR / "clamav_gui"
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"
ICON_PATH = BASE_DIR / "assets" / "icon.ico"
VERSION_FILE = SRC_DIR / "version.py"

def get_version():
    """Get the current version from version.py"""
    version_info = {}
    try:
        with open(VERSION_FILE, 'r') as f:
            exec(f.read(), version_info)
        return version_info.get('__version__', VERSION)
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

def build_nuitka(onefile=True, clean=False):
    """
    Build the application using Nuitka.
    
    Args:
        onefile: If True, create a single executable file.
        clean: If True, clean build directories before building.
    """
    version = get_version()
    logger.info(f"Building {PROJECT_NAME} v{version}")
    
    if clean:
        clean_build()
    
    # Create output directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    
    # Base Nuitka command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--follow-imports",
        "--show-progress",
        "--standalone",
        "--windows-disable-console" if IS_WINDOWS else None,
        f"--output-dir={DIST_DIR}",
        f"--windows-icon-from-ico={ICON_PATH}" if (IS_WINDOWS and ICON_PATH.exists()) else None,
        "--onefile" if onefile else "--no-onefile",
        "--include-package=clamav_gui",
        f"--include-data-dir={BASE_DIR / 'assets'}=assets",
        f"--include-data-dir={BASE_DIR / 'clamav_gui' / 'lang'}=clamav_gui/lang",
        "--enable-plugin=pyside6",
        "--windows-company-name=Tuxxle",
        "--output-filename=ClamAV-GUI.exe" if IS_WINDOWS else "--output-filename=ClamAV-GUI",
        f"--windows-file-version={version}",
        f"--windows-product-version={version}",
        f"--windows-product-name={PROJECT_NAME}",
        f"--windows-file-description={PROJECT_NAME} - A graphical interface for ClamAV Antivirus",
        "--copyright=© Copyright 2025 Nsfr750 - All Rights Reserved",
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
            # Ensure we're using the correct MSVC compiler
            env["VSCMD_VERB_LOGGER"] = "1"
        
        result = subprocess.run(
            cmd,
            check=False,  # We'll handle the error ourselves
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log the output
        if result.stdout:
            logger.debug("Nuitka stdout:\n%s", result.stdout)
        if result.stderr:
            logger.error("Nuitka stderr:\n%s", result.stderr)
            
        if result.returncode != 0:
            logger.error("Nuitka compilation failed with return code %d", result.returncode)
            return False
            
        logger.info("\nCompilation completed successfully!")
        logger.info(f"Executable is available in: {DIST_DIR}")
        return True
        
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
        "--no-onefile",
        dest="onefile",
        action="store_false",
        help="Create a directory with the executable and dependencies instead of a single file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    success = build_nuitka(onefile=args.onefile, clean=args.clean)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
