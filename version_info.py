#!/usr/bin/env python3
"""
Version information for ClamAV-GUI PyInstaller builds.

This module contains the version information structure used by PyInstaller
to embed version metadata in the Windows executable.
"""

from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct

vs_version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 1, 1, 0),
        prodvers=(1, 1, 1, 0),
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
                        StringStruct('CompanyName', 'Tuxxle'),
                        StringStruct('FileDescription', 'ClamAV GUI - Antivirus Interface with Enhanced Scanning and Quarantine Management'),
                        StringStruct('FileVersion', '1.1.1'),
                        StringStruct('InternalName', 'ClamAV-GUI'),
                        StringStruct('LegalCopyright', '© 2025 Nsfr750 - All Rights Reserved'),
                        StringStruct('OriginalFilename', 'ClamAV-GUI.exe'),
                        StringStruct('ProductName', 'ClamAV GUI'),
                        StringStruct('ProductVersion', '1.1.1'),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)
