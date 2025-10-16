#!/usr/bin/env python3
import sys
import os

# Let's check if the file content matches what we expect
with open('x:\\GitHub\\clamav-gui\\clamav_gui\\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the file contains the expected __init__ method
if 'def __init__(self, lang_manager=None, parent=None):' in content:
    print('File contains correct __init__ method')
else:
    print('File does NOT contain correct __init__ method')

# Check if the file contains the wrong __init__ method
if 'def __init__(self, command, enable_smart_scanning=False):' in content:
    print('File contains WRONG __init__ method')
else:
    print('File does NOT contain wrong __init__ method')
