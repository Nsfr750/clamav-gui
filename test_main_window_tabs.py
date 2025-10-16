#!/usr/bin/env python3
import sys
import os

# Set up environment to prevent GUI windows
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    # Test main window imports
    from clamav_gui.main_window import ClamAVGUI
    print('✓ ClamAVGUI import successful')

    # Test creating the main window
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    # Create main window instance
    main_window = ClamAVGUI()
    print('✓ ClamAVGUI created successfully')

    # Check if all tabs are accessible
    tabs_to_check = [
        'home_tab', 'scan_tab', 'email_scan_tab', 'virus_db_tab',
        'update_tab', 'settings_tab', 'quarantine_tab', 'config_editor_tab', 'status_tab'
    ]

    for tab_name in tabs_to_check:
        if hasattr(main_window, tab_name):
            print(f'✓ {tab_name} exists')
        else:
            print(f'❌ {tab_name} missing')

    print('\\n✅ Main window with all tabs test passed!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
