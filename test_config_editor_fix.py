#!/usr/bin/env python3
import sys
import os
sys.path.append('x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.main_window import ClamAVGUI
    from PySide6.QtWidgets import QApplication

    # Create QApplication first
    app = QApplication.instance() or QApplication([])

    # Create GUI instance
    gui = ClamAVGUI()
    print('ClamAVGUI created successfully')

    # Check if config_editor_tab exists and has the expected widgets
    if hasattr(gui, 'config_editor_tab'):
        print('✓ config_editor_tab exists')

        # Try to access some widgets that should be in the config editor
        # We can't directly access them without showing the GUI, but we can check if they exist
        config_tab = gui.config_editor_tab

        # Check if it has the expected attributes (these would be set during tab creation)
        expected_attrs = ['config_selector', 'config_editor', 'save_btn', 'status_label']
        for attr in expected_attrs:
            if hasattr(config_tab, attr):
                print(f'✓ {attr} exists in config tab')
            else:
                print(f'✗ {attr} missing in config tab')
    else:
        print('✗ config_editor_tab does not exist')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
