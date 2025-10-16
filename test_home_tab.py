#!/usr/bin/env python3
import sys
import os

# Set up environment to prevent GUI windows
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.ui.home_tab import HomeTab
    print('✓ HomeTab import successful')

    # Test creating the widget
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    home_tab = HomeTab()
    print('✓ HomeTab created successfully')

    # Test the update method
    home_tab.update_datetime()
    print('✓ update_datetime() called successfully')

    # Check if labels are populated
    print(f'✓ Version label: {home_tab.version_label.text()}')
    print(f'✓ Datetime label: {home_tab.datetime_label.text()}')
    print(f'✓ Memory label: {home_tab.memory_label.text()}')

    print('\\n✅ All tests passed!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
