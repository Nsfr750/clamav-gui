#!/usr/bin/env python3
"""
Build script for ClamAV GUI using PyInstaller.
"""
import os
import sys
import shutil
import PyInstaller.__main__
from pathlib import Path

def clean_build_dirs():
    """Remove build and dist directories."""
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name} directory...")
            shutil.rmtree(dir_name)

def build():
    """Build the application using PyInstaller."""
    # Project paths
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
