#!/usr/bin/env python3
import sys
import os

# Monkey patch to track when __init__ is modified
original_setattr = setattr

def track_setattr(obj, name, value):
    if name == '__init__' and hasattr(obj, '__name__') and obj.__name__ == 'ClamAVGUI':
        print(f'WARNING: __init__ of ClamAVGUI is being modified!')
        import traceback
        traceback.print_stack()
    return original_setattr(obj, name, value)

# Monkey patch setattr
import builtins
builtins.setattr = track_setattr

# Clear cache and import
for k in list(sys.modules.keys()):
    if k.startswith('clamav_gui'):
        del sys.modules[k]

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

print('Importing with tracking...')
import clamav_gui.main_window
