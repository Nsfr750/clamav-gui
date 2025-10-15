"""Home tab for ClamAV GUI application showing welcome screen and quick actions."""
import os
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)


class HomeTab(QWidget):
    """Home tab widget showing welcome screen and quick actions."""

    def __init__(self, parent=None):
        """Initialize the home tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Welcome title
        title = QLabel("ClamAV GUI")
        try:
            title.setStyleSheet("font-size: 22px; font-weight: bold;")
        except Exception:
            pass

        # Welcome subtitle
        subtitle = QLabel("Welcome! Use the tabs above to scan, update, and manage quarantine.")

        # Logo
        logo = QLabel()
        logo.setPixmap(QtWidgets.QPixmap("clamav_gui\ui\images\clamav_logo.png"))
        logo.setFixedSize(100, 100)
        logo.setAlignment(QtCore.Qt.AlignCenter)

        # Spacer
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Expanding,
                                      QtWidgets.QSizePolicy.Policy.Expanding)                                     

        # Quick action buttons
        actions = QHBoxLayout()

        quick_scan_btn = QPushButton("Quick Scan...")
        quick_scan_btn.clicked.connect(self._on_quick_scan_clicked)
        actions.addWidget(quick_scan_btn)

        updates_btn = QPushButton("Check for Updates")
        updates_btn.clicked.connect(self._on_check_updates_clicked)
        actions.addWidget(updates_btn)

        open_logs_btn = QPushButton("Open Logs Folder")
        open_logs_btn.clicked.connect(self._on_open_logs_clicked)
        actions.addWidget(open_logs_btn)

        # Add all components to layout
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(actions)
        layout.addStretch(1)

    def _on_quick_scan_clicked(self):
        """Handle quick scan button click."""
        if hasattr(self.parent, 'tabs'):
            # Switch to scan tab (index 0)
            self.parent.tabs.setCurrentIndex(0)

    def _on_check_updates_clicked(self):
        """Handle check for updates button click."""
        if hasattr(self.parent, '_do_check_updates'):
            self.parent._do_check_updates()
        else:
            # Fallback: try to find update method
            if hasattr(self.parent, 'update_database'):
                self.parent.update_database()

    def _on_open_logs_clicked(self):
        """Handle open logs folder button click."""
        try:
            from clamav_gui.utils.logger import ensure_logs_dir
            logs_dir = ensure_logs_dir()
            os.startfile(str(logs_dir))
            if hasattr(self.parent, 'set_status'):
                self.parent.set_status(f"Opened logs: {logs_dir}")
        except Exception:
            if hasattr(self.parent, 'set_status'):
                self.parent.set_status("Could not open logs folder", 4000)
