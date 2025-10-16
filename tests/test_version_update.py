#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

def test_version_files():
    """Test that all version files have been updated to 1.2.0"""

    # Test clamav_gui/version.py
    try:
        from clamav_gui.version import VERSION, __version__, __date__, get_version_history
        print("✓ clamav_gui/version.py loaded successfully")
        assert VERSION == (1, 2, 0), f"Expected VERSION=(1, 2, 0), got {VERSION}"
        assert __version__ == "1.2.0", f"Expected __version__='1.2.0', got {__version__}"
        assert __date__ == "2025-10-16", f"Expected __date__='2025-10-16', got {__date__}"

        history = get_version_history()
        assert len(history) >= 1, "Version history should have at least one entry"
        assert history[0]["version"] == "1.2.0", f"Latest version should be 1.2.0, got {history[0]['version']}"
        print("✓ clamav_gui/version.py version check passed")

    except Exception as e:
        print(f"❌ Error in clamav_gui/version.py: {e}")
        return False

    # Test clamav_gui/utils/version.py
    try:
        from clamav_gui.utils.version import VERSION, __version__, __date__, get_version_history
        print("✓ clamav_gui/utils/version.py loaded successfully")
        assert VERSION == (1, 2, 0), f"Expected VERSION=(1, 2, 0), got {VERSION}"
        assert __version__ == "1.2.0", f"Expected __version__='1.2.0', got {__version__}"
        assert __date__ == "2025-10-16", f"Expected __date__='2025-10-16', got {__date__}"

        history = get_version_history()
        assert len(history) >= 1, "Version history should have at least one entry"
        assert history[0]["version"] == "1.2.0", f"Latest version should be 1.2.0, got {history[0]['version']}"
        print("✓ clamav_gui/utils/version.py version check passed")

    except Exception as e:
        print(f"❌ Error in clamav_gui/utils/version.py: {e}")
        return False

    # Test version_info.txt
    try:
        with open('version_info.txt', 'r') as f:
            content = f.read()
        assert 'filevers=(1, 2, 0, 0)' in content, "version_info.txt should contain filevers=(1, 2, 0, 0)"
        assert "'FileVersion', '1.2.0'" in content, "version_info.txt should contain FileVersion 1.2.0"
        assert "'ProductVersion', '1.2.0'" in content, "version_info.txt should contain ProductVersion 1.2.0"
        print("✓ version_info.txt version check passed")

    except Exception as e:
        print(f"❌ Error in version_info.txt: {e}")
        return False

    # Test version_info.py
    try:
        from version_info import vs_version_info
        # Check that the version info contains the correct version tuple
        assert hasattr(vs_version_info, 'ffi'), "vs_version_info should have ffi attribute"
        # The version info structure should contain the version numbers somewhere
        print("✓ version_info.py structure check passed")

    except Exception as e:
        print(f"❌ Error in version_info.py: {e}")
        return False

    # Test pyinstaller.py
    try:
        with open('pyinstaller.py', 'r') as f:
            content = f.read()
        assert 'VERSION = "1.2.0"' in content, "pyinstaller.py should contain VERSION = '1.2.0'"
        print("✓ pyinstaller.py version check passed")

    except Exception as e:
        print(f"❌ Error in pyinstaller.py: {e}")
        return False

    return True

if __name__ == "__main__":
    if test_version_files():
        print("\n✅ All version files have been successfully updated to 1.2.0!")
    else:
        print("\n❌ Some version files were not updated correctly.")
        sys.exit(1)
