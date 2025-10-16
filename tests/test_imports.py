#!/usr/bin/env python3
"""Test imports directly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    from clamav_gui.main_window import ClamAVGUI
    print("✓ ClamAVGUI imported successfully")
except Exception as e:
    print(f"✗ Failed to import ClamAVGUI: {e}")

try:
    from clamav_gui.ui.main_ui import MainUIWindow
    print("✓ MainUIWindow imported successfully")
except Exception as e:
    print(f"✗ Failed to import MainUIWindow: {e}")

# Check which one is being used in __main__.py
print("\nChecking __main__.py imports...")
with open('clamav_gui/__main__.py', 'r') as f:
    content = f.read()
    if 'from clamav_gui.main_window import ClamAVGUI' in content:
        print("✓ __main__.py correctly imports ClamAVGUI")
    else:
        print("✗ __main__.py does not import ClamAVGUI")

    if 'from clamav_gui.ui.main_ui import MainUIWindow' in content:
        print("✗ __main__.py still imports MainUIWindow")
    else:
        print("✓ __main__.py does not import MainUIWindow")
