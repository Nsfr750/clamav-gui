#!/usr/bin/env python3
"""
Script di compilazione per ClamAV GUI
Crea un eseguibile Windows (.exe) con tutte le dipendenze necessarie.

Utilizzo: python compile_app.py [opzioni]

Opzioni:
  --debug       Crea una build di debug (console visibile)
  --clean       Pulisce la directory di build prima della compilazione
  --no-upx      Non comprime l'eseguibile con UPX
  --onefile     Crea un singolo file eseguibile (default)
  --onedir      Crea una directory con eseguibile e dipendenze separate

Autore: Nsfr750
Versione: 1.2.5
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

# Configurazione dell'applicazione
APP_NAME = "ClamAV-GUI"
APP_VERSION = "1.2.5"
APP_DESCRIPTION = "ClamAV GUI - Antivirus Interface with Enhanced Scanning and Quarantine Management"
APP_AUTHOR = "Nsfr750"
APP_EMAIL = "nsfr750@yandex.com"
APP_COMPANY = "Tuxxle"
APP_COPYRIGHT = "© Copyright 2025 Nsfr750 - All rights reserved"
APP_URL = "https://github.com/Nsfr750/clamav-gui"
MAIN_SCRIPT = "clamav_gui.__main__:main"

class AppCompiler:
    def __init__(self):
        self.root_dir = Path(__file__).parent.absolute()
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.output_dir = self.root_dir / "dist" / f"{APP_NAME}_Package"
        self.spec_file = self.root_dir / f"{APP_NAME}.spec"

    def print_banner(self):
        """Stampa il banner informativo."""
        print("=" * 60)
        print(f"🔧 COMPILATORE ClamAV GUI v{APP_VERSION}")
        print("=" * 60)
        print(f"Descrizione: {APP_DESCRIPTION}")
        print(f"Autore: {APP_AUTHOR} <{APP_EMAIL}>")
        print(f"Copyright: {APP_COPYRIGHT}")
        print(f"Repository: {APP_URL}")
        print("=" * 60)

    def clean_build(self):
        """Pulisce le directory di build e distribuzione."""
        print("\n🧹 Pulizia directory di build...")

        directories_to_clean = [
            self.build_dir,
            self.dist_dir,
            self.output_dir
        ]

        for directory in directories_to_clean:
            if directory.exists():
                print(f"   Rimuovendo: {directory}")
                shutil.rmtree(directory)
            else:
                print(f"   Già pulito: {directory}")

        print("✅ Pulizia completata!")

    def create_version_info(self):
        """Crea il file version_info.txt per PyInstaller."""
        version_content = f'''VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=({APP_VERSION.replace('.', ', ')}, 0),
        prodvers=({APP_VERSION.replace('.', ', ')}, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    '040904B0',
                    [
                        StringStruct('CompanyName', '{APP_COMPANY}'),
                        StringStruct('FileDescription', '{APP_DESCRIPTION}'),
                        StringStruct('FileVersion', '{APP_VERSION}'),
                        StringStruct('InternalName', '{APP_NAME}'),
                        StringStruct('LegalCopyright', '{APP_COPYRIGHT}'),
                        StringStruct('OriginalFilename', '{APP_NAME}.exe'),
                        StringStruct('ProductName', 'ClamAV GUI'),
                        StringStruct('ProductVersion', '{APP_VERSION}'),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)
'''
        version_file = self.root_dir / "version_info.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_content)

        print(f"📝 Creato file versione: {version_file}")
        return version_file

    def find_icon(self):
        """Cerca l'icona dell'applicazione."""
        possible_icons = [
            self.root_dir / "clamav_gui" / "assets" / "icon.ico",
            self.root_dir / "clamav_gui" / "assets" / "icon.png",
        ]

        for icon_path in possible_icons:
            if icon_path.exists():
                print(f"🎨 Icona trovata: {icon_path}")
                # Return full path for command line
                return str(icon_path)

    def _find_clamav_libraries(self):
        """Cerca e restituisce i percorsi delle librerie ClamAV per il bundling."""
        lib_paths = []

        # Percorsi comuni per le librerie ClamAV su Windows
        common_paths = [
            "C:/Program Files/ClamAV/libclamav.dll",
            "C:/Program Files (x86)/ClamAV/libclamav.dll",
            "C:/ClamAV/libclamav.dll",
        ]

        for path in common_paths:
            if os.path.exists(path):
                print(f"🔍 Libreria ClamAV trovata: {path}")
                lib_paths.append(path)
            else:
                print(f"🔍 Libreria ClamAV non trovata: {path}")

        # Cerca anche nelle directory di sistema
        try:
            import glob
            system_paths = [
                "C:/Windows/System32/libclamav*.dll",
                "C:/Windows/SysWOW64/libclamav*.dll",
            ]

            for pattern in system_paths:
                found = glob.glob(pattern)
                for path in found:
                    if path not in lib_paths:
                        lib_paths.append(path)
                        print(f"🔍 Libreria ClamAV di sistema trovata: {path}")
        except:
            pass

        if lib_paths:
            print(f"✅ Trovate {len(lib_paths)} librerie ClamAV per il bundling")
        else:
            print("⚠️  Nessuna libreria ClamAV trovata - l'integrazione diretta potrebbe non funzionare")

        return lib_paths

    def create_spec_file(self, debug=False, use_upx=True, onefile=True):
        """Crea il file .spec per PyInstaller."""
        icon_path = self.find_icon()

        # Determina il tipo di build
        console = "false" if not debug else "true"

        # Configurazione PyInstaller
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['clamav_gui/__main__.py'],
    pathex=['X:/GitHub/clamav-gui'],
    binaries=[
        # ClamAV libraries will be added dynamically
    ],
    datas=[
        ('clamav_gui', 'clamav_gui'),
        ('script', 'script'),
        ('config', 'config'),
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'scipy',
        'scipy.sparse',
        'scipy.stats',
        'scipy.stats.distributions',
        'scipy.stats._distn_infrastructure',
        'scipy.special',
        'scipy._lib',
        'sklearn',
        'sklearn.utils',
        'sklearn.utils._param_validation',
        'sklearn.utils.validation',
        'sklearn.utils._array_api',
        'sklearn.utils.fixes',
        'sklearn.base',
        'numpy',
        'numpy.random',
        'numpy.linalg',
        'numpy.fft',
        'numpy.core',
        'numpy.lib',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_qt5agg',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'tests',
        'matplotlib',
        'PIL',
        'wand',  # Escludiamo wand per usare pillow invece
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug={str(debug).lower()},
    bootloader_ignore_signals=False,
    strip=False,
    upx={str(use_upx).lower()},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='{str(self.root_dir / "version_info.txt")}',
    icon={f"['{icon_path}']" if icon_path else "None"},
)
'''

        if onefile:
            spec_content = spec_content.replace(
                "exe = EXE(",
                "exe = EXE(\n    a.binaries,\n    a.zipfiles,\n    a.datas,\n    [],"
            )
        else:
            # Aggiungi configurazione per onedir
            spec_content += f'''

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx={str(use_upx).lower()},
    upx_exclude=[],
    name='{APP_NAME}',
)
'''

        # Trova librerie ClamAV per aggiungerle al spec file
        clamav_binaries = []
        clamav_lib_paths = self._find_clamav_libraries()
        for lib_path in clamav_lib_paths:
            if lib_path:
                lib_filename = os.path.basename(lib_path)
                clamav_binaries.append(f"('{lib_path}', '{lib_filename}')")

        if clamav_binaries:
            binaries_str = ",\n        ".join(clamav_binaries)
            spec_content = spec_content.replace(
                "    binaries=[\n        # ClamAV libraries will be added dynamically\n    ],",
                f"    binaries=[\n        {binaries_str},\n    ],"
            )

        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)

        print(f"📋 Creato file spec: {self.spec_file}")
        return self.spec_file

    def install_dependencies(self):

        requirements = [
            "pyinstaller>=6.0.0",
            "pywin32>=306",
            "pefile>=2022.5.30,!=2024.8.26",  # Per analisi PE
        ]

        for req in requirements:
            print(f"   Installando: {req}")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", req, "--upgrade"
                ])
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  Errore nell'installazione di {req}: {e}")
                print(f"   Continuando comunque...")

    def compile_application(self, debug=False, clean=False, use_upx=True, onefile=True):
        """Compila l'applicazione."""
        print(f"\n🔨 Compilazione applicazione ({'debug' if debug else 'release'})...")

        # Crea comando PyInstaller diretto invece di usare spec file
        # Usa il modulo per evitare problemi di PATH su Windows
        cmd = [sys.executable, "-m", "PyInstaller", "--clean"]

        if onefile:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")

        if not use_upx:
            cmd.append("--noupx")

        if debug:
            cmd.append("--console")  # Solo per debug
        else:
            cmd.append("--windowed")  # No console per release builds

        # Aggiungi dati necessari (immagini, script, config, docs)
        data_files = [
            ("clamav_gui", "clamav_gui"),
            ("script", "script"),
            ("config", "config"),
            ("docs", "docs"),
        ]

        for src, dst in data_files:
            if os.path.exists(src):
                cmd.extend(["--add-data", f"{src};{dst}"])

        # Aggiungi file immagini separatamente per sicurezza
        img_dir = "clamav_gui/assets"
        if os.path.exists(img_dir):
            cmd.extend(["--add-data", f"{img_dir};{img_dir}"])

        # Aggiungi hidden imports per librerie scientifiche
        hidden_imports = [
            'scipy', 'scipy.sparse', 'scipy.stats', 'scipy.stats.distributions',
            'scipy.stats._distn_infrastructure', 'scipy.special', 'scipy._lib',
            'sklearn', 'sklearn.utils', 'sklearn.utils._param_validation',
            'sklearn.utils.validation', 'sklearn.utils._array_api', 'sklearn.utils.fixes',
            'sklearn.base', 'numpy', 'numpy.random', 'numpy.linalg', 'numpy.fft',
            'numpy.core', 'numpy.lib', 'matplotlib', 'matplotlib.pyplot',
            'matplotlib.backends', 'matplotlib.backends.backend_qt5agg',
            'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'
        ]

        for hidden_import in hidden_imports:
            cmd.extend(['--hidden-import', hidden_import])

        # Aggiungi supporto per librerie ClamAV se disponibili
        clamav_lib_paths = self._find_clamav_libraries()
        for lib_path in clamav_lib_paths:
            if lib_path:
                # Usa la sintassi corretta SOURCE:DEST per PyInstaller
                lib_filename = os.path.basename(lib_path)
                cmd.extend([f"--add-binary={lib_path};{lib_filename}"])

        # Aggiungi icona se disponibile
        icon_path = self.find_icon()
        if icon_path:
            # Usa il percorso completo per l'icona
            full_icon_path = self.root_dir / icon_path
            cmd.extend(["--icon", str(full_icon_path)])

        # Script principale
        cmd.append("clamav_gui/__main__.py")

        print(f"   Comando: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=self.root_dir)
            print("✅ Compilazione completata con successo!")

            if result.stdout:
                print("📋 Output di compilazione:")
                print(result.stdout)

        except subprocess.CalledProcessError as e:
            print(f"❌ Errore durante la compilazione: {e}")
            if e.stdout:
                print("📋 Output:")
                print(e.stdout)
            if e.stderr:
                print("📋 Errori:")
                print(e.stderr)
            return False

        return True

    def create_distribution_package(self):
        """Crea il package di distribuzione finale."""
        print("\n📦 Creazione package di distribuzione...")

        # Crea directory di output se non esiste
        self.output_dir.mkdir(exist_ok=True)

        # Trova il file eseguibile creato
        exe_patterns = [
            self.dist_dir / f"{APP_NAME}.exe",
            self.dist_dir / APP_NAME / f"{APP_NAME}.exe",
        ]

        exe_source = None
        for pattern in exe_patterns:
            if pattern.exists():
                exe_source = pattern
                break

        if not exe_source:
            print("❌ Eseguibile non trovato dopo la compilazione!")
            return False

        print(f"📋 Eseguibile trovato: {exe_source}")

        # Attesa per rilasciare eventuali lock dei file
        import time
        time.sleep(2)

        # Funzione helper per operazioni con retry
        def retry_file_operation(operation, max_retries=3, delay=1):
            """Esegue un'operazione su file con retry in caso di lock."""
            for attempt in range(max_retries):
                try:
                    return operation()
                except (OSError, IOError) as e:
                    if attempt < max_retries - 1:
                        print(f"   ⚠️  Tentativo {attempt + 1} fallito: {e}")
                        print(f"   ⏳ Attesa {delay} secondi prima del prossimo tentativo...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"   ❌ Operazione fallita dopo {max_retries} tentativi: {e}")
                        raise

        # Copia eseguibile nella directory di destinazione
        exe_dest = self.output_dir / f"{APP_NAME}.exe"
        try:
            retry_file_operation(lambda: shutil.copy2(exe_source, exe_dest))
            print(f"   📋 Eseguibile copiato: {exe_dest}")
        except (OSError, IOError) as e:
            print(f"❌ Errore durante la copia dell'eseguibile: {e}")
            return False

        # Se è una build onedir, copia anche la directory
        source_dir = self.dist_dir / APP_NAME
        if source_dir.exists() and source_dir.is_dir():
            print(f"📂 Copiando directory {APP_NAME}...")
            dest_dir = self.output_dir / APP_NAME

            try:
                # Rimuovi directory destinazione se esiste
                if dest_dir.exists():
                    retry_file_operation(lambda: shutil.rmtree(dest_dir))

                # Copia directory
                retry_file_operation(lambda: shutil.copytree(source_dir, dest_dir))
                print(f"   📋 Directory copiata: {dest_dir}")

            except (OSError, IOError) as e:
                print(f"❌ Errore durante la copia della directory: {e}")
                print("   ℹ️  Continuando senza la directory delle dipendenze...")
                # Continua anche se la copia della directory fallisce

        # Crea file README nella directory di distribuzione
        readme_content = f'''# ClamAV GUI {APP_VERSION}

{APP_DESCRIPTION}

## Installazione
1. Scarica il contenuto di questa cartella
2. Esegui {APP_NAME}.exe
3. L'applicazione è pronta per l'uso!

## Informazioni
- Autore: {APP_AUTHOR} <{APP_EMAIL}>
- Copyright: {APP_COPYRIGHT}
- Repository: {APP_URL}

## Requisiti di sistema
- Windows 10/11 (64-bit)
- ClamAV installato (opzionale, ma raccomandato)

---
Creato automaticamente dal compilatore ClamAV GUI
'''
        readme_file = self.output_dir / "README.txt"

        try:
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"   📋 File README creato: {readme_file}")
        except (OSError, IOError) as e:
            print(f"❌ Errore durante la creazione del README: {e}")

        print(f"✅ Package creato in: {self.output_dir}")
        print(f"📋 Contenuto del package:")

        try:
            for file in self.output_dir.rglob("*"):
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"   📄 {file.relative_to(self.output_dir)} ({size_mb:.2f} MB)")
        except (OSError, IOError) as e:
            print(f"   ⚠️  Errore durante la scansione dei file: {e}")

        return True

    def run(self, debug=False, clean=False, use_upx=True, onefile=True):
        """Esegue l'intero processo di compilazione."""
        self.print_banner()

        if clean:
            self.clean_build()

        # Crea versione file
        self.create_version_info()

        # Installa dipendenze se necessario
        self.install_dependencies()

        # Compila direttamente senza spec file
        if not self.compile_application(debug, clean, use_upx, onefile):
            return False

        # Crea package di distribuzione
        if not self.create_distribution_package():
            return False

        print("\n🎉 COMPILAZIONE COMPLETATA CON SUCCESSO!")
        print(f"📦 Package disponibile in: {self.output_dir}")
        print(f"🚀 Eseguibile: {self.output_dir / f'{APP_NAME}.exe'}")

        return True

def main():
    parser = argparse.ArgumentParser(
        description="Compilatore per ClamAV GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Crea build di debug con console visibile'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Pulisce le directory di build prima della compilazione'
    )

    parser.add_argument(
        '--no-upx',
        action='store_true',
        help='Non comprime l\'eseguibile con UPX'
    )

    parser.add_argument(
        '--onedir',
        action='store_true',
        help='Crea directory con eseguibile e dipendenze separate (default: onefile)'
    )

    args = parser.parse_args()

    # Determina il tipo di build
    onefile = not args.onedir

    # Crea e esegui il compilatore
    compiler = AppCompiler()

    try:
        success = compiler.run(
            debug=args.debug,
            clean=args.clean,
            use_upx=not args.no_upx,
            onefile=onefile
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Compilazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore durante la compilazione: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
