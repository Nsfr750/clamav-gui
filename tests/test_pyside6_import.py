from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QAction
from PySide6.QtCore import Qt
import sys

print("PySide6 imports successful!")
print(f"PySide6 version: {__import__('PySide6').__version__}")

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()
button = QPushButton("Test Button")
layout.addWidget(button)
window.setLayout(layout)
window.show()
sys.exit(app.exec())
