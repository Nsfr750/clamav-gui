#!/usr/bin/env python3
"""Test script to verify the logo path construction."""

import os

# Test the path construction as it would happen in home_tab.py
test_file = 'clamav_gui/ui/home_tab.py'
base_dir = os.path.dirname(os.path.dirname(test_file))  # This should be 'clamav_gui/ui'
ui_dir = os.path.dirname(base_dir)  # This should be 'clamav_gui'
project_root = os.path.dirname(ui_dir)  # This should be the project root

print(f"test_file: {test_file}")
print(f"os.path.dirname(test_file): {os.path.dirname(test_file)}")
print(f"os.path.dirname(os.path.dirname(test_file)): {os.path.dirname(os.path.dirname(test_file))}")
print(f"os.path.dirname(os.path.dirname(os.path.dirname(test_file))): {os.path.dirname(os.path.dirname(os.path.dirname(test_file)))}")

# Test the corrected path construction
logo_path = os.path.join(os.path.dirname(os.path.dirname(test_file)), 'ui', 'img', 'logo.png')
print(f"\nConstructed logo path: {logo_path}")
print(f"Absolute logo path: {os.path.abspath(logo_path)}")
print(f"Logo file exists: {os.path.exists(logo_path)}")

# Alternative construction (going up from ui/ to project root, then down to ui/img/)
alt_logo_path = os.path.join(project_root, 'clamav_gui', 'ui', 'img', 'logo.png')
print(f"\nAlternative logo path: {alt_logo_path}")
print(f"Absolute alternative path: {os.path.abspath(alt_logo_path)}")
print(f"Alternative file exists: {os.path.exists(alt_logo_path)}")
