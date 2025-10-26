import shutil
import os
from pathlib import Path

# Clear PyInstaller cache
cache_dir = Path("C:/Users/guara/AppData/Local/pyinstaller")
if cache_dir.exists():
    print(f"Clearing PyInstaller cache: {cache_dir}")
    try:
        shutil.rmtree(cache_dir)
        print("Cache cleared successfully")
    except Exception as e:
        print(f"Error clearing cache: {e}")
else:
    print("Cache directory does not exist")

# Also clear build directory
build_dir = Path("build")
if build_dir.exists():
    print(f"Clearing build directory: {build_dir}")
    try:
        shutil.rmtree(build_dir)
        print("Build directory cleared successfully")
    except Exception as e:
        print(f"Error clearing build directory: {e}")
else:
    print("Build directory does not exist")

# Also clear dist directory
build_dir = Path("dist")
if build_dir.exists():
    print(f"Clearing dist directory: {build_dir}")
    try:
        shutil.rmtree(build_dir)
        print("Dist directory cleared successfully")
    except Exception as e:
        print(f"Error clearing dist directory: {e}")
else:
    print("Dist directory does not exist")

