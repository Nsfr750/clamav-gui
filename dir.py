#!/usr/bin/env python3
"""
PyInstaller compilation script for ClamAV GUI.
Creates a directory containing the executable and all its dependencies.
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path

# Setup logging with ASCII-only characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pyinstaller_build.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PyInstallerBuilder:
    """PyInstaller build manager for ClamAV GUI."""

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.spec_file = self.project_root / 'ClamAV-GUI.spec'
        self.version_file = self.project_root / 'version_info.txt'
        self.main_script = self.project_root / 'clamav_gui' / '__main__.py'
        self.logo_file = self.project_root / 'assets' / 'logo.png'
        self.icon_file = self.project_root / 'assets' / 'icon.ico'
        self.requirements_file = self.project_root / 'requirements.txt'

        # Build directories
        self.build_dir = self.project_root / 'build'
        self.dist_dir = self.project_root / 'dist'

        # Application info
        self.app_name = 'ClamAV-GUI'
        self.app_version = '1.2.0'

    def check_prerequisites(self):
        """Check if all prerequisites are met before building."""
        logger.info("[INFO] Checking prerequisites...")

        # Check main script exists
        if not self.main_script.exists():
            raise FileNotFoundError(f"Main script not found: {self.main_script}")

        # Check version file exists
        if not self.version_file.exists():
            logger.warning(f"Version file not found: {self.version_file}")
            logger.info("[INFO] Creating default version file...")
            self.create_default_version_file()

        # Check icon exists
        if not self.icon_file.exists():
            logger.warning(f"Icon file not found: {self.icon_file}")

        # Check requirements.txt exists
        if not self.requirements_file.exists():
            logger.warning(f"Requirements file not found: {self.requirements_file}")

        logger.info("[SUCCESS] Prerequisites check completed")

    def create_default_version_file(self):
        """Create a default version_info.txt file if it doesn't exist."""
        version_content = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx

VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(1, 2, 0, 0),
    prodvers=(1, 2, 0, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - Application
    fileType=0x1,
    # The function of the file.
    # 0x0 - not defined
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Tuxxle'),
        StringStruct(u'FileDescription', u'ClamAV GUI - Antivirus Interface with Enhanced Scanning and Quarantine Management'),
        StringStruct(u'FileVersion', u'1.2.0'),
        StringStruct(u'InternalName', u'ClamAV-GUI'),
        StringStruct(u'LegalCopyright', u' 2025 Nsfr750 - All Rights Reserved'),
        StringStruct(u'OriginalFilename', u'ClamAV-GUI.exe'),
        StringStruct(u'ProductName', u'ClamAV GUI'),
        StringStruct(u'ProductVersion', u'1.2.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''

        try:
            self.version_file.write_text(version_content)
            logger.info(f"[SUCCESS] Created default version file: {self.version_file}")
        except Exception as e:
            logger.error(f"Failed to create version file: {e}")
            raise

    def clean_build_directories(self):
        """Clean build and dist directories."""
        logger.info("[INFO] Cleaning build directories...")

        try:
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                logger.info(f"[SUCCESS] Removed build directory: {self.build_dir}")

            if self.dist_dir.exists():
                # Keep any existing directories for backup
                existing_dir = self.dist_dir / self.app_name
                if existing_dir.exists():
                    backup_dir = self.dist_dir / f"{self.app_name}_backup"
                    if backup_dir.exists():
                        shutil.rmtree(backup_dir)
                    shutil.copytree(existing_dir, backup_dir)
                    logger.info(f"[SUCCESS] Backed up existing directory to: {backup_dir}")

                shutil.rmtree(self.dist_dir)
                logger.info(f"[SUCCESS] Removed dist directory: {self.dist_dir}")

        except Exception as e:
            logger.warning(f"Failed to clean directories: {e}")

    def create_spec_file(self):
        """Create or update the PyInstaller spec file."""
        logger.info("[INFO] Creating/updating PyInstaller spec file...")

        # Hidden imports for scientific computing libraries
        hidden_imports = [
            'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
            'PySide6.QtNetwork', 'PySide6.QtSvg',
            'scipy._lib.messagestream', 'scipy.sparse.csgraph._validation',
            'scipy.special._ufuncs_cxx', 'scipy._lib._util',
            'sklearn.utils._joblib', 'sklearn.utils._openmp_helpers',
            'sklearn.utils._heap', 'sklearn.utils._cython_blas',
            'sklearn.neighbors._partition_nodes',
            'scipy.stats._stats_py', 'scipy.stats.distributions',
            'scipy.stats._distn_infrastructure',
            'scipy._lib._ccallback_c', 'scipy._lib._threadsafety',
            'numpy.random.common', 'numpy.random.bounded_integers',
            'numpy.random.entropy'
        ]

        # Excludes for test modules
        excludes = [
            'scipy.stats.tests', 'scipy.sparse.tests', 'scipy._lib.tests',
            'sklearn.tests', 'sklearn.cluster.tests', 'sklearn.compose.tests',
            'sklearn.covariance.tests', 'sklearn.cross_decomposition.tests',
            'sklearn.datasets.tests', 'sklearn.decomposition.tests',
            'sklearn.dummy.tests', 'sklearn.ensemble.tests',
            'sklearn.exceptions', 'sklearn.experimental.tests',
            'sklearn.feature_extraction.tests', 'sklearn.feature_selection.tests',
            'sklearn.gaussian_process.tests', 'sklearn.impute.tests',
            'sklearn.inspection.tests', 'sklearn.kernel_approximation.tests',
            'sklearn.kernel_ridge.tests', 'sklearn.linear_model.tests',
            'sklearn.manifold.tests', 'sklearn.metrics.tests',
            'sklearn.mixture.tests', 'sklearn.model_selection.tests',
            'sklearn.multiclass.tests', 'sklearn.multioutput.tests',
            'sklearn.naive_bayes.tests', 'sklearn.neighbors.tests',
            'sklearn.neural_network.tests', 'sklearn.pipeline.tests',
            'sklearn.preprocessing.tests', 'sklearn.random_projection.tests',
            'sklearn.regression.tests', 'sklearn.semi_supervised.tests',
            'sklearn.svm.tests', 'sklearn.tree.tests', 'sklearn.utils.tests'
        ]

        # Prepare icon list
        icon_list = f"['{self.icon_file}']" if self.icon_file.exists() else "[]"

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.absolute()

a = Analysis(
    ['{self.main_script}'],
    pathex=[],
    binaries=[],
    datas=[
        (str(project_root / 'assets'), 'assets'),
        (str(project_root / 'clamav_gui' / 'lang'), 'clamav_gui/lang'),
    ],
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={excludes},
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(project_root / 'version_info.txt'),
    icon={icon_list},
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{self.app_name}',
)
'''

        try:
            # Replace placeholders in the spec content
            spec_content = spec_content.replace('{hidden_imports}', str(hidden_imports))
            spec_content = spec_content.replace('{excludes}', str(excludes))

            self.spec_file.write_text(spec_content)
            logger.info(f"[SUCCESS] Created spec file: {self.spec_file}")

        except Exception as e:
            logger.error(f"Failed to create spec file: {e}")
            raise

    def run_pyinstaller(self):
        """Run PyInstaller to build the executable."""
        logger.info("[INFO] Starting PyInstaller build...")

        try:
            # Change to project directory
            os.chdir(self.project_root)

            # Run PyInstaller with -D option (creates directory with dependencies)
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '-D',  # Creates directory instead of single file (equivalent to --dir)
                '--clean',
                '--noconfirm',
                '--debug=all',
                '--name', self.app_name,
                str(self.main_script)
            ]

            logger.info(f"Running command: {' '.join(cmd)}")

            # Run PyInstaller
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )

            if result.returncode == 0:
                logger.info("[SUCCESS] PyInstaller build completed successfully")
                self.verify_build()
            else:
                logger.error(f"[ERROR] PyInstaller failed with return code: {result.returncode}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                raise RuntimeError(f"PyInstaller failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("[ERROR] PyInstaller timed out after 30 minutes")
            raise
        except Exception as e:
            logger.error(f"[ERROR] PyInstaller build failed: {e}")
            raise

    def verify_build(self):
        """Verify the build was successful."""
        logger.info("[INFO] Verifying build...")

        # For -D mode, PyInstaller creates a directory with the executable and dependencies
        app_directory = self.dist_dir / self.app_name

        if app_directory.exists() and app_directory.is_dir():
            logger.info(f"[SUCCESS] Application directory created: {app_directory}")

            # Check for main executable
            executable = app_directory / f"{self.app_name}.exe"
            if executable.exists():
                size = executable.stat().st_size
                logger.info(f"[SUCCESS] Main executable found: {executable}")
                logger.info(f"[INFO] Executable size: {size:,} bytes ({size/1024/1024:.1f} MB)")

                # Count total files in directory
                total_files = sum(1 for _, _, files in os.walk(app_directory) for _ in files)
                total_size = sum(
                    os.path.getsize(os.path.join(root, file))
                    for root, _, files in os.walk(app_directory)
                    for file in files
                )

                logger.info(f"[INFO] Total files: {total_files}")
                logger.info(f"[INFO] Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

                # List main files
                logger.info("[INFO] Directory contents:")
                for item in sorted(os.listdir(app_directory)):
                    item_path = app_directory / item
                    if item_path.is_file():
                        item_size = item_path.stat().st_size
                        logger.info(f"   [FILE] {item} ({item_size:,} bytes)")

                # Check if executable runs (basic test)
                try:
                    test_result = subprocess.run(
                        [str(executable), '--help'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if test_result.returncode == 0:
                        logger.info("[SUCCESS] Executable runs successfully")
                    else:
                        logger.warning(f"[WARNING] Executable returned non-zero exit code: {test_result.returncode}")
                except Exception as e:
                    logger.warning(f"[WARNING] Could not test executable: {e}")
            else:
                raise FileNotFoundError(f"Main executable not found in directory: {executable}")
        else:
            raise FileNotFoundError(f"Application directory not found at: {app_directory}")

    def build(self):
        """Main build process."""
        logger.info("[INFO] Starting ClamAV GUI directory build process...")

        try:
            # Check prerequisites
            self.check_prerequisites()

            # Clean build directories
            self.clean_build_directories()

            # Create spec file
            self.create_spec_file()

            # Run PyInstaller
            self.run_pyinstaller()

            logger.info("[SUCCESS] Build completed successfully!")
            app_directory = self.dist_dir / self.app_name
            logger.info(f"[INFO] Application directory: {app_directory}")
            logger.info(f"[INFO] To run: {app_directory / self.app_name}.exe")

        except Exception as e:
            logger.error(f"[ERROR] Build failed: {e}")
            raise

def main():
    """Main entry point."""
    try:
        builder = PyInstallerBuilder()
        builder.build()
        return 0
    except KeyboardInterrupt:
        logger.info("[INFO] Build interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"[ERROR] Build failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
