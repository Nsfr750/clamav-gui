#!/usr/bin/env python3
import sys
import os
sys.path.append('x:\\GitHub\\clamav-gui')

# Check the source code directly
import inspect
from clamav_gui.main_window import ClamAVGUI

# Get the source code of the __init__ method
source = inspect.getsource(ClamAVGUI.__init__)
print('Source code of ClamAVGUI.__init__:')
print(source)

# Check if the class has been modified
print(f'ClamAVGUI.__init__ signature: {inspect.signature(ClamAVGUI.__init__)}')
