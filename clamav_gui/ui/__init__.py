"""
UI components for ClamAV GUI.
"""

# Import main window class
from .UI import ClamAVMainWindow

# Import other UI components
try:
    from . import about
    from . import help
    from . import menu
    from . import settings_tab
    from . import sponsor
    from . import updates_dialog
except ImportError:
    pass

__all__ = ['ClamAVMainWindow']
