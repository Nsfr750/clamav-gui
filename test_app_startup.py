#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'x:\\GitHub\\clamav-gui')

try:
    from clamav_gui.__main__ import main
    print('Starting application...')
    main()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
