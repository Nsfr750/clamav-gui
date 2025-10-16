#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

print('Before import:')
print('ClamAVGUI module file:', end=' ')
try:
    import clamav_gui.main_window
    print(clamav_gui.main_window.__file__)
except:
    print('Not found')

print('\\nImporting ClamAVGUI...')
from clamav_gui.main_window import ClamAVGUI

print('\\nAfter import:')
import inspect
print('Source file:', inspect.getfile(ClamAVGUI))
print('MRO:', [cls.__name__ for cls in ClamAVGUI.__mro__])

# Check if __init__ has been modified
init_method = ClamAVGUI.__init__
print(f'\\n__init__ method from: {init_method.__qualname__}')
print(f'__init__ signature: {inspect.signature(init_method)}')

# Get source if possible
try:
    source = inspect.getsource(init_method)
    print('\\n__init__ source:')
    print(source[:200] + '...' if len(source) > 200 else source)
except:
    print('Could not get source')
