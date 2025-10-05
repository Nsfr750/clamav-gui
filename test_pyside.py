import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

def main():
    app = QApplication(sys.argv)
    
    # Create a simple window
    window = QWidget()
    window.setWindowTitle("Test PySide6")
    window.setGeometry(100, 100, 300, 200)
    
    # Create a button
    button = QPushButton("Click me!")
    
    # Set up layout
    layout = QVBoxLayout()
    layout.addWidget(button)
    window.setLayout(layout)
    
    # Show the window
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
