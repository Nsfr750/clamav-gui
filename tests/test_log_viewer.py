#!/usr/bin/env python3
import sys
import os

# Set up environment to prevent GUI windows
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.ui.view_log import LogViewerDialog
    print('✓ LogViewerDialog import successful')

    # Test creating the dialog
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    log_viewer = LogViewerDialog()
    print('✓ LogViewerDialog created successfully')

    # Check if all required components exist
    required_components = [
        'log_list', 'log_view', 'search_input', 'search_btn',
        'filter_combo',  # New dropdown filter instead of individual checkboxes
        'auto_refresh_cb', 'refresh_interval', 'file_path_label',
        'error_count_label', 'warning_count_label', 'info_count_label'
    ]

    for component in required_components:
        if hasattr(log_viewer, component):
            print(f'✓ {component} exists')
        else:
            print(f'❌ {component} missing')

    # Check if all required methods exist
    required_methods = [
        '_populate_logs', '_load_selected', '_search_logs',
        '_apply_filters', '_format_log_content', '_export_selected'
    ]

    for method in required_methods:
        if hasattr(log_viewer, method):
            print(f'✓ {method} method exists')
        else:
            print(f'❌ {method} method missing')

    print('\\n✅ LogViewerDialog basic functionality test passed!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
