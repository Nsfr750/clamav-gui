#!/usr/bin/env python3
"""Debug script to check what's happening."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Python path:")
for p in sys.path[:5]:
    print(f"  {p}")

print("\nChecking module locations:")
try:
    import clamav_gui
    print(f"clamav_gui location: {clamav_gui.__file__}")

    import clamav_gui.__main__
    print(f"clamav_gui.__main__ location: {clamav_gui.__main__.__file__}")
except Exception as e:
    print(f"Error importing: {e}")

print("\nChecking file content around line 103:")
try:
    with open('clamav_gui/__main__.py', 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[100:110], 101):
            print(f"{i:3}: {line.rstrip()}")
except Exception as e:
    print(f"Error reading file: {e}")
