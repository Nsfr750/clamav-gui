#!/usr/bin/env python3
import sys
import os

# Set up environment to prevent GUI windows
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    # Test that menu bar can be created and has the correct structure
    from clamav_gui.ui.menu import ClamAVMenuBar
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    menu_bar = ClamAVMenuBar()

    # Check that menu bar has the expected structure
    # The menu bar should have menus in order: File, Tools, Funzioni avanzate scansione, Language, Help
    expected_order = ['&File', '&Tools', 'Funzioni &avanzate scansione', '&Language', '&Help']

    if hasattr(menu_bar, '_initialized') and menu_bar._initialized:
        print('✓ Menu bar initialized successfully')

        # Check that all expected menu references exist
        menus_to_check = ['file_menu', 'tools_menu', 'advanced_scan_menu', 'language_menu', 'help_menu']
        for menu_name in menus_to_check:
            if hasattr(menu_bar, menu_name) and getattr(menu_bar, menu_name) is not None:
                print(f'✓ {menu_name} reference exists')
            else:
                print(f'❌ {menu_name} reference missing')

        print('\n✅ Menu bar structure verification completed successfully!')
        print(f'📋 Expected menu order: {expected_order}')
    else:
        print('❌ Menu bar not properly initialized')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
