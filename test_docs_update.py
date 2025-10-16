#!/usr/bin/env python3
import sys
import os

def test_documentation_updates():
    """Test that all documentation files have been updated to version 1.2.0"""

    files_to_check = [
        'CHANGELOG.md',
        'README.md',
        'TO_DO.md',
        'docs/ROADMAP.md',
        'docs/STRUCT.md',
        'docs/USER_GUIDE.md'
    ]

    all_updated = True

    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if file contains version 1.2.0
            if '1.2.0' in content:
                print(f"✓ {file_path} contains version 1.2.0")
            else:
                print(f"❌ {file_path} does not contain version 1.2.0")
                all_updated = False

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            all_updated = False

    # Check specific version references
    print("\n📋 Checking specific version references:")

    # CHANGELOG.md should have 1.2.0 as first version
    try:
        with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
            content = f.read()
        if content.startswith('# Changelog') and '## [1.2.0]' in content:
            print("✓ CHANGELOG.md has 1.2.0 as latest version")
        else:
            print("❌ CHANGELOG.md version format incorrect")
            all_updated = False
    except Exception as e:
        print(f"❌ Error checking CHANGELOG.md: {e}")
        all_updated = False

    # README.md should have version badge 1.2.0
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        if 'Version-1.2.0' in content:
            print("✓ README.md has version badge 1.2.0")
        else:
            print("❌ README.md version badge not updated")
            all_updated = False
    except Exception as e:
        print(f"❌ Error checking README.md: {e}")
        all_updated = False

    # TO_DO.md should have 1.2.0 completed features
    try:
        with open('TO_DO.md', 'r', encoding='utf-8') as f:
            content = f.read()
        if '## Completed in v1.2.0' in content:
            print("✓ TO_DO.md has 1.2.0 completed section")
        else:
            print("❌ TO_DO.md missing 1.2.0 completed section")
            all_updated = False
    except Exception as e:
        print(f"❌ Error checking TO_DO.md: {e}")
        all_updated = False

    # ROADMAP.md should have 1.2.0 as current
    try:
        with open('docs/ROADMAP.md', 'r', encoding='utf-8') as f:
            content = f.read()
        if '## Version 1.2.0 (Current Release)' in content:
            print("✓ ROADMAP.md has 1.2.0 as current version")
        else:
            print("❌ ROADMAP.md version not updated")
            all_updated = False
    except Exception as e:
        print(f"❌ Error checking ROADMAP.md: {e}")
        all_updated = False

    # STRUCT.md should mention 1.2.0
    try:
        with open('docs/STRUCT.md', 'r', encoding='utf-8') as f:
            content = f.read()
        if 'version 1.2.0' in content.lower():
            print("✓ STRUCT.md mentions version 1.2.0")
        else:
            print("❌ STRUCT.md version not updated")
            all_updated = False
    except Exception as e:
        print(f"❌ Error checking STRUCT.md: {e}")
        all_updated = False

    # USER_GUIDE.md should have 1.2.0 reference
    try:
        with open('docs/USER_GUIDE.md', 'r', encoding='utf-8') as f:
            content = f.read()
        if 'ClamAV GUI v1.2.0' in content:
            print("✓ USER_GUIDE.md has version 1.2.0 reference")
        else:
            print("❌ USER_GUIDE.md version not updated")
            all_updated = False
    except Exception as e:
        print(f"❌ Error checking USER_GUIDE.md: {e}")
        all_updated = False

    return all_updated

if __name__ == "__main__":
    if test_documentation_updates():
        print("\n✅ All documentation files have been successfully updated to version 1.2.0!")
    else:
        print("\n❌ Some documentation files were not updated correctly.")
        sys.exit(1)
