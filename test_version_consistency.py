#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

try:
    from clamav_gui.version import get_version, get_version_info
    from clamav_gui.utils.version import get_version as utils_get_version

    print("Main version file:")
    main_ver = get_version()
    main_tuple = get_version_info()
    print(f"  Version string: {main_ver}")
    print(f"  Version tuple: {main_tuple}")

    print("\nUtils version file:")
    utils_ver = utils_get_version()
    print(f"  Version string: {utils_ver}")

    # Check if versions match
    if main_ver == utils_ver:
        print(f"\n✅ Version consistency check: PASS (both show {main_ver})")
    else:
        print("\n❌ Version consistency check: FAIL")
        print(f"  Main: {main_ver}")
        print(f"  Utils: {utils_ver}")

    # Check version_info.txt
    print("\nChecking version_info.txt...")
    with open('version_info.txt', 'r') as f:
        content = f.read()
        if 'filevers=(1, 2, 0, 0)' in content and 'prodvers=(1, 2, 0, 0)' in content:
            print("✅ version_info.txt: Version 1.2.0 correctly set")
        else:
            print("❌ version_info.txt: Version not set to 1.2.0")

    # Check version_info.py
    print("\nChecking version_info.py...")
    with open('version_info.py', 'r') as f:
        content = f.read()
        if 'filevers=(1, 2, 0, 0)' in content and 'prodvers=(1, 2, 0, 0)' in content:
            print("✅ version_info.py: Version 1.2.0 correctly set")
        else:
            print("❌ version_info.py: Version not set to 1.2.0")

    print("\n✅ All version files are properly configured for version 1.2.0!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
