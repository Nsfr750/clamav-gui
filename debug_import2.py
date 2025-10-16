#!/usr/bin/env python3
import sys
import os

# Clear any cached modules
modules_to_clear = [k for k in sys.modules.keys() if k.startswith('clamav_gui')]
for module in modules_to_clear:
    del sys.modules[module]

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

print('Importing step by step...')

# Import the module
import clamav_gui.main_window
print('Module imported')

# Check the class
from clamav_gui.main_window import ClamAVGUI
import inspect

print('Class definition:')
print(f'File: {inspect.getfile(ClamAVGUI)}')
print(f'MRO: {[cls.__name__ for cls in ClamAVGUI.__mro__]}')

# Check the __init__ method
init_method = ClamAVGUI.__init__
print(f'\\n__init__ method from: {init_method.__qualname__}')
print(f'__init__ signature: {inspect.signature(init_method)}')

# Check if there are any descriptors or other modifications
print(f'\\nClass dict keys: {list(ClamAVGUI.__dict__.keys())}')
