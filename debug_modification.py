#!/usr/bin/env python3
# Let's check if there's some kind of dynamic modification happening
import sys
import os

# Clear cache
for k in list(sys.modules.keys()):
    if k.startswith('clamav_gui'):
        del sys.modules[k]

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

# Monkey patch to catch any modifications
original_setattr = setattr

def debug_setattr(obj, name, value):
    if hasattr(obj, '__name__') and 'ClamAVGUI' in obj.__name__ and name == '__init__':
        print(f'MODIFYING {obj.__name__}.__init__!')
        import traceback
        traceback.print_stack()
    return original_setattr(obj, name, value)

import builtins
builtins.setattr = debug_setattr

print('Importing main_window with debugging...')
import clamav_gui.main_window

from clamav_gui.main_window import ClamAVGUI
import inspect

print(f'Final signature: {inspect.signature(ClamAVGUI.__init__)}')
