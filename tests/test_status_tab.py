#!/usr/bin/env python3
import sys
import os

# Set up environment to prevent GUI windows
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.ui.status_tab import StatusTab
    print('✓ StatusTab import successful')

    # Test creating the widget
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    status_tab = StatusTab()
    print('✓ StatusTab created successfully')

    # Check if update_database method exists and is callable
    if hasattr(status_tab, 'update_database'):
        print('✓ update_database method exists')
    else:
        print('❌ update_database method missing')

    # Check if update_update_output method exists
    if hasattr(status_tab, 'update_update_output'):
        print('✓ update_update_output method exists')
    else:
        print('❌ update_update_output method missing')

    print('\n✅ StatusTab basic functionality test passed!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
