#!/usr/bin/env python3
import sys
import os

# Clear any cached modules
for k in list(sys.modules.keys()):
    if k.startswith('clamav_gui'):
        del sys.modules[k]

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

# Import and check before any other imports
print('Importing main_window...')
import clamav_gui.main_window

print('Checking class...')
from clamav_gui.main_window import ClamAVGUI
import inspect

print(f'Initial __init__ signature: {inspect.signature(ClamAVGUI.__init__)}')

# Now import other modules that might modify it
print('Importing UI...')
import clamav_gui.ui.UI

print(f'After UI import: {inspect.signature(ClamAVGUI.__init__)}')

print('Importing utils...')
import clamav_gui.utils

print(f'After utils import: {inspect.signature(ClamAVGUI.__init__)}')
