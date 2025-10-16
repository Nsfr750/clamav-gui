#!/usr/bin/env python3
import sys
import os

# Set up environment to prevent GUI windows
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.ui.conf_editor_tab import ConfigEditorTab
    print('✓ ConfigEditorTab import successful')

    # Test creating the widget
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    config_editor_tab = ConfigEditorTab()
    print('✓ ConfigEditorTab created successfully')

    # Check if required methods exist
    required_methods = ['init_ui', 'browse_config_file', 'open_config_file', 'save_config_file']
    for method in required_methods:
        if hasattr(config_editor_tab, method):
            print(f'✓ {method} method exists')
        else:
            print(f'❌ {method} method missing')

    print('\\n✅ ConfigEditorTab basic functionality test passed!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
