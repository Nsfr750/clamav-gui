"""Home tab for ClamAV GUI application showing welcome screen and quick actions."""
import os
import psutil
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)

# Import application version
try:
    from clamav_gui import __version__
except ImportError:
    __version__ = "Unknown"


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
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "logo.png")
        try:
            if os.path.exists(logo_path):
                logo.setPixmap(QtGui.QPixmap(logo_path).scaled(200, 200, QtCore.Qt.KeepAspectRatio))
                logo.setAlignment(QtCore.Qt.AlignCenter)
                logo.setVisible(True)
            else:
                # Hide logo if file doesn't exist
                logo.setVisible(False)
        except Exception:
            # Hide logo if loading fails
            logo.setVisible(False)

        # Show Actions - System Information Display
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setSpacing(5)

        # Application version (centered)
        self.version_label = QLabel(f"Version: {__version__}")
        self.version_label.setAlignment(QtCore.Qt.AlignCenter)
        self.version_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff; padding: 5px;")
        self.actions_layout.addWidget(self.version_label)

        # Current date and time (centered) - will be updated by timer
        self.datetime_label = QLabel()
        self.datetime_label.setAlignment(QtCore.Qt.AlignCenter)
        self.datetime_label.setStyleSheet("font-size: 12px; color: #fff; padding: 3px;")
        self.actions_layout.addWidget(self.datetime_label)

        # Free memory available (centered)
        self.memory_label = QLabel()
        self.memory_label.setAlignment(QtCore.Qt.AlignCenter)
        self.memory_label.setStyleSheet("font-size: 12px; color: #fff; padding: 3px;")
        self.actions_layout.addWidget(self.memory_label)

        # Timer to update date/time every second
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)  # Update every second

        # Initial update
        self.update_datetime()

        # Add all components to layout
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(logo)
        layout.addLayout(self.actions_layout)
        layout.addStretch(1)

    def update_datetime(self):
        """Update the current date/time and memory information."""
        # Update current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.datetime_label.setText(f"Current Date & Time: {current_datetime}")
        self.datetime_label.setStyleSheet("font-size: 12px; color: #fff; padding: 3px;")

        # Update free memory
        try:
            memory = psutil.virtual_memory()
            free_memory_gb = memory.available / (1024**3)
            self.memory_label.setText(f"Free Memory: {free_memory_gb:.1f} GB")
            self.memory_label.setStyleSheet("font-size: 12px; color: #fff; padding: 3px;")
        except Exception:
            # Fallback if psutil fails
            self.memory_label.setText("Free Memory: N/A")
            self.memory_label.setStyleSheet("font-size: 12px; color: #fff; padding: 3px;")
