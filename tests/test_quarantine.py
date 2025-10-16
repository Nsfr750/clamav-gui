#!/usr/bin/env python3
import sys
import os
sys.path.append('x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.main_window import ClamAVGUI
    print('Testing quarantine functionality...')

    # Test that quarantine manager exists
    gui = ClamAVGUI.__new__(ClamAVGUI)  # Create instance without calling __init__
    gui.quarantine_manager = None  # Simulate None case

    # Test refresh methods handle None correctly
    from PySide6.QtWidgets import QApplication, QTextEdit, QListWidget, QListWidgetItem
    from PySide6.QtCore import Qt

    app = QApplication.instance() or QApplication([])

    # Test stats refresh with None manager
    gui.quarantine_stats_text = QTextEdit()
    gui.refresh_quarantine_stats()
    stats_text = gui.quarantine_stats_text.toPlainText()
    print(f'✓ Stats refresh with None manager: {len(stats_text)} chars')

    # Test files refresh with None manager
    gui.quarantine_files_list = QListWidget()
    gui.refresh_quarantine_files()
    files_count = gui.quarantine_files_list.count()
    print(f'✓ Files refresh with None manager: {files_count} items')

    print('Quarantine error handling test passed!')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
