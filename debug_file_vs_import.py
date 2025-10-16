#!/usr/bin/env python3
import sys
import os

# Clear any cached modules completely
for k in list(sys.modules.keys()):
    if k.startswith('clamav_gui'):
        del sys.modules[k]

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

print('Direct file reading:')
with open('x:\\GitHub\\clamav-gui\\clamav_gui\\main_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[71:85], 71):
        print(f'{i:3}: {line.rstrip()}')

print('\\nImporting...')
import clamav_gui.main_window
from clamav_gui.main_window import ClamAVGUI
import inspect

print(f'\\nAfter import:')
print(f'__init__ signature: {inspect.signature(ClamAVGUI.__init__)}')

# Check if there are any metaclass or descriptor modifications
print(f'Class dict has __init__: {"__init__" in ClamAVGUI.__dict__}')
print(f'Method resolution order: {[cls.__name__ for cls in ClamAVGUI.__mro__]}')
