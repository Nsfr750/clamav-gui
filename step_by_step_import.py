#!/usr/bin/env python3
import sys
import os

# Clear cache
for k in list(sys.modules.keys()):
    if k.startswith('clamav_gui'):
        del sys.modules[k]

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

print('Importing modules one by one...')

# Import base modules first
import clamav_gui.ui.UI
print('UI imported')

import clamav_gui.utils
print('utils imported')

import clamav_gui.lang
print('lang imported')

# Now import main_window
import clamav_gui.main_window
print('main_window imported')

# Check the class
from clamav_gui.main_window import ClamAVGUI
import inspect

print(f'\\nFinal __init__ signature: {inspect.signature(ClamAVGUI.__init__)}')
