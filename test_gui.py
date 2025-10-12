import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Test GUI")
window.resize(400, 300)

central_widget = QWidget()
layout = QVBoxLayout(central_widget)
layout.addWidget(QLabel("Test GUI Window"))

window.setCentralWidget(central_widget)
window.show()

print("Window should be visible now")
sys.exit(app.exec())
