from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
import sys

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()
button = QPushButton("ClamAV GUI - Test Button")
layout.addWidget(button)
window.setLayout(layout)
window.show()
sys.exit(app.exec())
