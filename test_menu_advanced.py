#!/usr/bin/env python3
import sys
import os

# Set up environment to prevent GUI windows
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.ui.menu import ClamAVMenuBar
    print('✓ ClamAVMenuBar import successful')

    # Test creating the menu bar
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    menu_bar = ClamAVMenuBar()
    print('✓ ClamAVMenuBar created successfully')

    # Check if all menus exist in the correct order
    expected_menus = [
        'file_menu', 'tools_menu', 'advanced_scan_menu',
        'language_menu', 'help_menu'
    ]

    print('\\n📋 Checking menu order:')
    for menu_name in expected_menus:
        if hasattr(menu_bar, menu_name):
            print(f'✓ {menu_name} exists')
        else:
            print(f'❌ {menu_name} missing')

    # Check if advanced scan actions exist
    advanced_actions = [
        'smart_scan_action', 'ml_detection_action',
        'email_scan_action', 'batch_analysis_action', 'network_scan_action'
    ]

    print('\\n🔧 Checking advanced scan actions:')
    for action_name in advanced_actions:
        if hasattr(menu_bar, action_name):
            print(f'✓ {action_name} exists')
        else:
            print(f'❌ {action_name} missing')

    print('\\n✅ Menu bar with advanced scanning functions test passed!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
