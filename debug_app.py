#!/usr/bin/env python3
"""
Script di debug per ClamAV GUI.
Da eseguire nella directory dell'applicazione compilata.
"""

import sys
import os

print("[INFO] DEBUG CLAMAV GUI")
print("=" * 50)

# Aggiungi la directory corrente al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    print(f"[INFO] Directory corrente: {current_dir}")
    print(f"[INFO] Python version: {sys.version}")

    # Test import principali
    print("\n[INFO] Testing imports...")

    try:
        import PySide6.QtWidgets as QtWidgets
        print("[SUCCESS] PySide6.QtWidgets")
    except ImportError as e:
        print(f"[ERROR] PySide6.QtWidgets: {e}")

    try:
        import scipy
        print(f"[SUCCESS] SciPy {scipy.__version__}")
    except ImportError as e:
        print(f"[ERROR] SciPy: {e}")

    try:
        import numpy
        print(f"[SUCCESS] NumPy {numpy.__version__}")
    except ImportError as e:
        print(f"[ERROR] NumPy: {e}")

    # Test creazione applicazione
    print("\n[INFO] Testing application creation...")

    try:
        # Create QApplication first - this is required before creating any Qt widgets
        app = QtWidgets.QApplication(sys.argv)

        from clamav_gui.main_window import ClamAVGUI
        from clamav_gui.lang.lang_manager import SimpleLanguageManager

        lang_manager = SimpleLanguageManager()
        window = ClamAVGUI(lang_manager)
        print("[SUCCESS] Main window created successfully")

        # Clean up
        window.close()
        app.quit()

    except Exception as e:
        print(f"[ERROR] Application creation failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n[SUCCESS] Debug completed")

except Exception as e:
    print(f"[ERROR] Debug failed: {e}")
    import traceback
    traceback.print_exc()
