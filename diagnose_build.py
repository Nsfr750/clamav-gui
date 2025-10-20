#!/usr/bin/env python3
"""
Script di diagnosi per l'eseguibile ClamAV GUI creato con PyInstaller.
Aiuta a identificare problemi di dipendenze e percorsi.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_executable():
    """Verifica se l'eseguibile esiste e le sue proprietà."""
    exe_path = Path("dist/ClamAV-GUI/ClamAV-GUI.exe")
    app_dir = Path("dist/ClamAV-GUI")

    print("🔍 VERIFICA ESEGUIBILE")
    print("=" * 50)

    if not app_dir.exists():
        print(f"❌ Directory applicazione non trovata: {app_dir}")
        return False

    if not exe_path.exists():
        print(f"❌ Eseguibile non trovato: {exe_path}")
        return False

    # Verifica dimensione e permessi
    size = exe_path.stat().st_size
    print(f"✅ Eseguibile trovato: {exe_path}")
    print(f"[INFO] Dimensione: {size:,} bytes ({size/1024/1024:.1f} MB)")

    # Conta file totali
    total_files = sum(1 for _, _, files in os.walk(app_dir) for _ in files)
    total_size = sum(os.path.getsize(os.path.join(root, file))
                    for root, _, files in os.walk(app_dir) for file in files)

    print(f"[INFO] File totali: {total_files}")
    print(f"[INFO] Dimensione totale: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

    return True

def test_imports():
    """Testa se i moduli principali possono essere importati."""
    print("\n[INFO] TEST IMPORTAZIONI")
    print("=" * 50)

    try:
        # Test import principali
        import PySide6.QtWidgets
        print("[SUCCESS] PySide6.QtWidgets importato")

        import PySide6.QtCore
        print("[SUCCESS] PySide6.QtCore importato")

        import scipy
        print(f"[SUCCESS] SciPy importato (versione: {scipy.__version__})")

        import numpy
        print(f"[SUCCESS] NumPy importato (versione: {numpy.__version__})")

        import sklearn
        print(f"[SUCCESS] scikit-learn importato (versione: {sklearn.__version__})")

        # Test moduli specifici che potrebbero causare problemi
        import scipy.sparse
        print("[SUCCESS] scipy.sparse importato")

        import numpy.random
        print("[SUCCESS] numpy.random importato")

        return True

    except ImportError as e:
        print(f"[ERROR] Errore importazione: {e}")
        return False

def check_dependencies():
    """Verifica le dipendenze nella directory _internal."""
    print("\n[INFO] VERIFICA DIPENDENZE")
    print("=" * 50)

    internal_dir = Path("dist/ClamAV-GUI/_internal")

    if not internal_dir.exists():
        print(f"[ERROR] Directory _internal non trovata: {internal_dir}")
        return False

    # Verifica alcune dipendenze critiche
    critical_deps = [
        "PySide6",
        "scipy",
        "numpy",
        "sklearn"
    ]

    missing_deps = []

    for dep in critical_deps:
        dep_path = internal_dir / dep
        if dep_path.exists():
            # Conta file nella dipendenza
            file_count = sum(1 for _, _, files in os.walk(dep_path) for _ in files)
            print(f"[SUCCESS] {dep}: {file_count} file")
        else:
            print(f"[ERROR] {dep}: NON TROVATO")
            missing_deps.append(dep)

    return len(missing_deps) == 0

def test_execution():
    """Testa l'esecuzione dell'applicazione."""
    print("\n[INFO] TEST ESECUZIONE")
    print("=" * 50)

    exe_path = "dist/ClamAV-GUI/ClamAV-GUI.exe"

    try:
        # Test con --help
        print("[INFO] Testando con --help...")
        result = subprocess.run(
            [exe_path, "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd="dist/ClamAV-GUI"
        )

        print(f"[INFO] Exit code: {result.returncode}")

        if result.stdout:
            print(f"[INFO] STDOUT:\n{result.stdout}")

        if result.stderr:
            print(f"[INFO] STDERR:\n{result.stderr[:1000]}...")  # Limita output

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("[WARNING] Timeout durante l'esecuzione")
        return False
    except FileNotFoundError:
        print(f"[ERROR] File eseguibile non trovato: {exe_path}")
        return False
    except Exception as e:
        print(f"[ERROR] Errore durante l'esecuzione: {e}")
        return False

def create_debug_script():
    """Crea uno script di debug per l'applicazione."""
    print("\n[INFO] CREAZIONE SCRIPT DEBUG")
    print("=" * 50)

    debug_script = '''#!/usr/bin/env python3
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
    print("\\n[INFO] Testing imports...")

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
    print("\\n[INFO] Testing application creation...")

    try:
        from clamav_gui.main_window import ClamAVGUI
        from clamav_gui.lang.lang_manager import SimpleLanguageManager

        lang_manager = SimpleLanguageManager()
        window = ClamAVGUI(lang_manager)
        print("[SUCCESS] Main window created successfully")
        window.close()

    except Exception as e:
        print(f"[ERROR] Application creation failed: {e}")
        import traceback
        traceback.print_exc()

    print("\\n[SUCCESS] Debug completed")

except Exception as e:
    print(f"[ERROR] Debug failed: {e}")
    import traceback
    traceback.print_exc()
'''

    debug_path = Path("dist/ClamAV-GUI/debug_app.py")
    debug_path.write_text(debug_script)
    print(f"[SUCCESS] Script debug creato: {debug_path}")
    print("   Esegui: python debug_app.py")

def main():
    """Funzione principale di diagnosi."""
    print("[INFO] DIAGNOSI ESEGUIBILE CLAMAV GUI")
    print("=" * 60)

    # Test 1: Verifica eseguibile
    if not check_executable():
        print("\\n[ERROR] Eseguibile non valido - interrompo diagnosi")
        return 1

    # Test 2: Verifica importazioni
    imports_ok = test_imports()

    # Test 3: Verifica dipendenze
    deps_ok = check_dependencies()

    # Test 4: Test esecuzione
    exec_ok = test_execution()

    # Test 5: Crea script debug
    create_debug_script()

    # Riepilogo
    print("\\n[INFO] RIEPILOGO")
    print("=" * 50)
    print(f"[INFO] Eseguibile: {'[SUCCESS] OK' if True else '[ERROR] PROBLEMI'}")
    print(f"[INFO] Importazioni: {'[SUCCESS] OK' if imports_ok else '[ERROR] PROBLEMI'}")
    print(f"[INFO] Dipendenze: {'[SUCCESS] OK' if deps_ok else '[ERROR] PROBLEMI'}")
    print(f"[INFO] Esecuzione: {'[SUCCESS] OK' if exec_ok else '[ERROR] PROBLEMI'}")

    if not exec_ok:
        print("\\n[INFO] SUGGERIMENTI:")
        print("   1. Controlla i log di errore sopra")
        print("   2. Esegui lo script debug: python debug_app.py")
        print("   3. Verifica che tutte le dipendenze siano presenti in _internal/")
        print("   4. Controlla i permessi di esecuzione")
        return 1

    print("\\n[SUCCESS] L'eseguibile sembra funzionare correttamente!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
