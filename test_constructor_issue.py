#!/usr/bin/env python3
import sys
import os
sys.path.append('x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.main_window import ClamAVGUI
    print('Import successful')

    # Try to inspect the constructor
    import inspect
    sig = inspect.signature(ClamAVGUI.__init__)
    print(f'ClamAVGUI.__init__ signature: {sig}')

    # Try to create instance with different parameters
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    try:
        gui = ClamAVGUI()
        print('✓ ClamAVGUI() created successfully')
    except Exception as e:
        print(f'✗ ClamAVGUI() failed: {e}')

    try:
        gui = ClamAVGUI(None, None)
        print('✓ ClamAVGUI(None, None) created successfully')
    except Exception as e:
        print(f'✗ ClamAVGUI(None, None) failed: {e}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
