#!/usr/bin/env python3
import os
import glob

# Search for files containing 'class ClamAVGUI'
search_pattern = 'class ClamAVGUI'
found_files = []

for root, dirs, files in os.walk('x:\\GitHub\\clamav-gui'):
    # Skip venv directories
    if 'venv' in root:
        continue

    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if search_pattern in content:
                        found_files.append(filepath)
            except:
                pass

print(f"Found {len(found_files)} files containing 'class ClamAVGUI':")
for filepath in found_files:
    print(filepath)
