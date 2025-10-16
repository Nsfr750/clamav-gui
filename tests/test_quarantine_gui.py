#!/usr/bin/env python3
import sys
import os
sys.path.append('x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.main_window import ClamAVGUI
    from PySide6.QtWidgets import QApplication

    # Create QApplication first
    app = QApplication.instance() or QApplication([])

    # Create GUI instance with proper parameters
    gui = ClamAVGUI()  # lang_manager and parent are optional
    print('ClamAVGUI created successfully')

    # Check if quarantine_manager is initialized
    if hasattr(gui, 'quarantine_manager') and gui.quarantine_manager is not None:
        print('✓ Quarantine manager initialized successfully')
        print(f'  Type: {type(gui.quarantine_manager)}')

        # Test calling a method
        try:
            stats = gui.quarantine_manager.get_quarantine_stats()
            print(f'  Stats retrieved: {stats.get("total_quarantined", 0)} files')
        except Exception as e:
            print(f'  Error calling method: {e}')
    else:
        print('✗ Quarantine manager not initialized or is None')
        if hasattr(gui, 'quarantine_manager'):
            print(f'  quarantine_manager value: {gui.quarantine_manager}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
