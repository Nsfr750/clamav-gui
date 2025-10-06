#!/usr/bin/env python3
"""
Build script for ClamAV GUI using Nuitka.

This script compiles the ClamAV GUI application into a standalone executable
using Nuitka. It handles all necessary dependencies and build configurations.
"""
import os
import sys
import shutil
import argparse
import platform
import subprocess
from pathlib import Path

# Project information
PROJECT_NAME = "clamav-gui"
MAIN_SCRIPT = "clamav_gui/__main__.py"
VERSION_FILE = "clamav_gui/version.py"

# Get version from version.py
version = {}
with open(VERSION_FILE, "r", encoding="utf-8") as f:
    exec(f.read(), version)
VERSION = version["__version__"]

# Build directories
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
SPEC_DIR = Path("spec")

# Platform-specific configurations
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

def clean_build():
    """Clean up build directories."""
    for directory in [BUILD_DIR, DIST_DIR, SPEC_DIR]:
        if directory.exists():
            print(f"Removing {directory}...")
            shutil.rmtree(directory, ignore_errors=True)

def build_nuitka(standalone=True, onefile=False, clean=False, debug=False):
    """
    Build the application using Nuitka.
    
    Args:
        standalone: If True, create a standalone build.
        onefile: If True, create a single executable file.
        clean: If True, clean build directories before building.
        debug: If True, include debug information and disable optimizations.
    """
    if clean:
        clean_build()
    
    # Create output directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    SPEC_DIR.mkdir(exist_ok=True)
    
    # Base Nuitka command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--follow-imports",
        "--show-progress",
        "--show-memory",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyside6",
        "--enable-plugin=no-qt" if not IS_WINDOWS else "--enable-plugin=qt-plugins=all",
        "--windows-icon-from-ico=assets/icon.ico" if IS_WINDOWS and os.path.exists("assets/icon.ico") else "",
        "--windows-disable-console" if IS_WINDOWS and not debug else "",
        "--output-dir", str(BUILD_DIR),
        "--windows-company-name=Tuxxle",
        f"--windows-file-version={VERSION}",
        f"--windows-product-version={VERSION}",
        f"--windows-product-name={PROJECT_NAME}",
        f"--windows-file-description={PROJECT_NAME} - A graphical interface for ClamAV Antivirus",
        f"--version-file={VERSION_FILE}",
        "--copyright=© Copyright 2025 Nsfr750 - All Rights Reserved",
        "--msvc=latest" if IS_WINDOWS else "",
        "--lto=yes" if not debug else "--lto=no",
        "--standalone" if standalone else "",
        "--onefile" if onefile else "--no-onefile",
        "--remove-output" if clean else "",
        "--include-package=clamav_gui",
        "--include-package-data=clamav_gui/*.ui,clamav_gui/*.qss,clamav_gui/*.png",
        "--include-data-dir=assets=assets" if os.path.exists("assets") else "",
        "--windows-uac-admin" if IS_WINDOWS else "",
        "--windows-uac-uiaccess" if IS_WINDOWS else "",
        "--windows-target-version=10" if IS_WINDOWS else "",
    ]
    
    # Debug options
    if debug:
        cmd.extend([
            "--debug",
            "--show-modules",
            "--show-scons",
            "--show-progress",
            "--verbose",
        ])
    else:
        cmd.extend([
            "--remove-output",
            "--follow-imports",
            "--jobs=0",  # Use all available CPU cores
        ])
    
    # Add main script
    cmd.append(str(MAIN_SCRIPT))
    
    # Filter out empty strings from command list
    cmd = [arg for arg in cmd if arg]
    
    print("Running command:", " ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild completed successfully!")
        print(f"Output directory: {DIST_DIR.absolute()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}", file=sys.stderr)
        return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Build ClamAV GUI with Nuitka")
    parser.add_argument("--clean", action="store_true", help="Clean build directories before building")
    parser.add_argument("--debug", action="store_true", help="Build with debug information")
    parser.add_argument("--onefile", action="store_true", help="Create a single executable file")
    parser.add_argument("--standalone", action="store_true", default=True, help="Create a standalone build (default: True)")
    return parser.parse_args()

def build():
    base_path = Path(__file__).parent
    icon_path = base_path / 'assets' / 'icon.ico'
    main_script = base_path / 'clamav_gui' / '__main__.py'
    
    # Version information
    version_file = base_path / 'clamav_gui' / 'version.py'
    version_info = {}
    with open(version_file, 'r') as f:
        exec(f.read(), version_info)
    
    version = version_info.get('__version__', '1.0.0')
    
    # Clean previous builds
    clean_build_dirs()
    
    # PyInstaller configuration
    # Common PyInstaller arguments
    pyi_args = [
        str(main_script),
        '--name=ClamAV-GUI',
        '--onefile',
        '--windowed',
        f'--icon={icon_path}',
        '--noconsole',
        '--clean',
        '--workpath=build',
        '--distpath=dist',
        '--add-data=assets;assets',
        '--add-data=clamav_gui/lang;clamav_gui/lang',
        # Removed non-existent clamav directory
        '--hidden-import=PySide6',
        '--hidden-import=clamav_gui',
        '--hidden-import=clamav_gui.ui',
        '--hidden-import=clamav_gui.utils',
        '--hidden-import=clamav_gui.lang',
        '--hidden-import=logging.handlers',
        '--hidden-import=packaging',
        '--hidden-import=packaging.version',
        '--exclude-module=test',
        '--exclude-module=unittest',
        '--exclude-module=email',
        f'--version-file={base_path / "version_info.txt"}'
    ]
    
    # Add version info if on Windows
    if sys.platform == 'win32':
        # Create version info file
        version_info = {
            'CompanyName': 'Tuxxle',
            'FileDescription': 'ClamAV GUI - Antivirus Interface',
            'FileVersion': f'{version}.0',
            'InternalName': 'ClamAV-GUI',
            'LegalCopyright': '© 2025 Nsfr750 - All Rights Reserved',
            'OriginalFilename': 'ClamAV-GUI.exe',
            'ProductName': 'ClamAV GUI',
            'ProductVersion': f'{version}.0'
        }
        
        # Create version info file with proper formatting
        version_parts = list(map(int, version.split('.')))
        version_tuple = tuple(version_parts + [0])  # Add the 4th version component (build number)
        
        with open('version_info.txt', 'w', encoding='utf-8') as f:
            f.write('VSVersionInfo(\n')
            f.write('    ffi=FixedFileInfo(\n')
            f.write(f'        filevers={version_tuple},\n')
            f.write(f'        prodvers={version_tuple},\n')
            f.write('        mask=0x3f,\n')
            f.write('        flags=0x0,\n')
            f.write('        OS=0x40004,\n')
            f.write('        fileType=0x1,\n')
            f.write('        subtype=0x0,\n')
            f.write('        date=(0, 0)\n')
            f.write('    ),\n')
            f.write('    kids=[\n')
            f.write('        StringFileInfo(\n')
            f.write('            [\n')
            f.write('                StringTable(\n')
            f.write('                    \'040904B0\',\n')
            f.write('                    [\n')
            for key, value in version_info.items():
                if key not in ['FileVersion', 'ProductVersion']:  # Already handled above
                    f.write(f'                        StringStruct(\'{key}\', \'{value}\'),\n')
            f.write('                    ]\n')
            f.write('                )\n')
            f.write('            ]\n')
            f.write('        ),\n')
            f.write('        VarFileInfo([VarStruct(\'Translation\', [1033, 1200])])\n')
            f.write('    ]\n')
            f.write(')\n')
    
    # Run PyInstaller
    print("Starting build process...")
    PyInstaller.__main__.run(pyi_args)
    
    # Clean up
    try:
        if os.path.exists('version_info.txt'):
            os.remove('version_info.txt')
        if os.path.exists('ClamAV-GUI.spec'):
            os.remove('ClamAV-GUI.spec')
    except Exception as e:
        print(f"Warning: Error during cleanup: {e}")
    
    output_exe = base_path / 'dist' / ('ClamAV-GUI.exe' if sys.platform == 'win32' else 'ClamAV-GUI')
    
    if output_exe.exists():
        print("\n✅ Build completed successfully!")
        print(f"The executable is located at: {output_exe}")
        print("\n📝 Note: Make sure to include these directories alongside the executable:")
        print("  - assets/")
        print("  - clamav_gui/lang/")
        
        # Copy required directories to dist folder if they don't exist
        for dir_name in ['assets', 'clamav_gui/lang']:
            src = base_path / dir_name
            dst = base_path / 'dist' / dir_name
            if src.exists() and not dst.exists():
                try:
                    shutil.copytree(src, dst)
                    print(f"✅ Copied {dir_name} to dist folder")
                except Exception as e:
                    print(f"⚠️  Failed to copy {dir_name}: {e}")
    else:
        print("\n❌ Build completed, but the output executable was not found.")
        print("Please check the build logs for any errors.")

if __name__ == '__main__':
    build()
