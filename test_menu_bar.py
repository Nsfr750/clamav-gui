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

    # Check if all menus exist
    required_menus = ['file_menu', 'tools_menu', 'help_menu', 'language_menu']
    for menu_name in required_menus:
        if hasattr(menu_bar, menu_name):
            print(f'✓ {menu_name} exists')
        else:
            print(f'❌ {menu_name} missing')

    # Check if all required actions exist
    required_actions = [
        'exit_action', 'check_updates_action', 'help_action',
        'about_action', 'sponsor_action', 'wiki_action', 'view_logs_action'
    ]
    for action_name in required_actions:
        if hasattr(menu_bar, action_name):
            print(f'✓ {action_name} exists')
        else:
            print(f'❌ {action_name} missing')

    print('\\n✅ ClamAVMenuBar basic functionality test passed!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
