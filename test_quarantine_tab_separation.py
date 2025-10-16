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

    # Check if quarantine tab exists and is properly initialized
    if hasattr(gui, 'quarantine_tab'):
        print('✓ Quarantine tab exists')

        # Check if it has the expected widgets
        quarantine_tab = gui.quarantine_tab
        expected_widgets = ['quarantine_stats_text', 'quarantine_files_list', 'refresh_btn']

        for widget_name in expected_widgets:
            if hasattr(quarantine_tab, widget_name):
                print(f'✓ {widget_name} exists in quarantine tab')
            else:
                print(f'✗ {widget_name} missing in quarantine tab')

        # Check if quarantine manager is properly set
        if hasattr(quarantine_tab, 'quarantine_manager') and quarantine_tab.quarantine_manager:
            print('✓ Quarantine manager is properly initialized')
        else:
            print('✗ Quarantine manager not properly initialized')
    else:
        print('✗ Quarantine tab does not exist')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
